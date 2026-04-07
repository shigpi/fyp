from typing import List
from datetime import date, timedelta

import os
import httpx

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.api import deps
from backend.models.org_member import OrgMember
from backend.models.organization import Organization
from backend.models.plan import Plan
from backend.models.subscription import Subscription, SubscriptionType
from backend.models.subscription_usage import SubscriptionUsage
from backend.models.user import User
from backend.schemas.plan import PlanResponse
from backend.schemas.subscription import EsewaPaymentVerify
from backend.schemas.user import UserResponse
from backend.services.security import limiter, API_LIMIT

router = APIRouter()


@router.get("/me/subscription")
@limiter.limit(API_LIMIT)
def get_my_subscription(
    request: Request,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    membership = db.query(OrgMember).filter(OrgMember.user_id == current_user.id).first()
    if not membership:
        return None

    subscription = db.query(Subscription).filter(
        Subscription.org_id == membership.org_id,
        Subscription.current_period_end >= date.today(),
    ).first()

    if not subscription:
        return None

    plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()

    return {
        "plan_id": subscription.plan_id,
        "plan_name": plan.name if plan else None,
        "type": subscription.type.value if subscription.type else None,
        "payment_status": subscription.payment_status,
        "current_period_end": str(subscription.current_period_end) if subscription.current_period_end else None,
    }


@router.delete("/me")
@limiter.limit(API_LIMIT)
def delete_my_account(
    request: Request,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    try:
        owned_orgs = db.query(Organization).filter(Organization.owner_id == current_user.id).all()
        for org in owned_orgs:
            org_subs = db.query(Subscription).filter(Subscription.org_id == org.id).all()
            for sub in org_subs:
                db.query(SubscriptionUsage).filter(SubscriptionUsage.subscription_id == sub.id).delete()
            db.query(Subscription).filter(Subscription.org_id == org.id).delete()
            db.query(OrgMember).filter(OrgMember.org_id == org.id).delete()
            db.delete(org)

        db.query(OrgMember).filter(OrgMember.user_id == current_user.id).delete()
        db.delete(current_user)
        db.commit()
        return {"status": "success", "message": "Account deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}",
        )


@router.get("/me", response_model=UserResponse)
@limiter.limit(API_LIMIT)
def read_users_me(
    request: Request,
    current_user: User = Depends(deps.get_current_user),
):
    return current_user


@router.get("/me/organizations")
@limiter.limit(API_LIMIT)
def read_user_organizations(
    request: Request,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    memberships = db.query(OrgMember).filter(OrgMember.user_id == current_user.id).all()
    return [
        {
            "id": m.id,
            "role": m.role.value,
            "organization": {
                "id": m.organization.id,
                "name": m.organization.name,
                "slug": m.organization.slug,
                "type": m.organization.type.value,
            },
        }
        for m in memberships
    ]


@router.get("/plans", response_model=List[PlanResponse])
@limiter.limit(API_LIMIT)
def read_plans(
    request: Request,
    db: Session = Depends(deps.get_db),
):
    return db.query(Plan).all()


@router.post("/subscription/esewa")
@limiter.limit(API_LIMIT)
def verify_esewa_payment(
    request: Request,
    payment_data: EsewaPaymentVerify,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    # 1. Verify user's membership in the organisation
    membership = db.query(OrgMember).filter(
        OrgMember.user_id == current_user.id,
        OrgMember.org_id == payment_data.org_id,
    ).first()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to the specified organization",
        )

    # 2. Server-to-server eSewa V2 verification
    esewa_verify_url = "https://rc.esewa.com.np/mobile/transaction"
    verify_params = {
        "productId": payment_data.product_id,
        "amount": payment_data.total_amount,
    }
    ESEWA_CLIENT_ID = os.getenv("ESEWA_CLIENT_ID")
    ESEWA_SECRET_KEY = os.getenv("ESEWA_SECRET_KEY")
    headers = {
        "merchantId": ESEWA_CLIENT_ID,
        "merchantSecret": ESEWA_SECRET_KEY,
        "Content-Type": "application/json",
    }
    try:
        resp = httpx.get(esewa_verify_url, params=verify_params, headers=headers, timeout=10.0)
        resp.raise_for_status()

        if "application/json" not in resp.headers.get("content-type", ""):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid eSewa response (not JSON): {resp.text[:200]}",
            )

        verify_result = resp.json()
        if not verify_result:
            raise HTTPException(status_code=400, detail="Empty response from eSewa")

        txn_status = verify_result[0]["transactionDetails"]["status"]
        if txn_status != "COMPLETE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="eSewa Server Verification failed: Transaction not COMPLETE",
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error connecting to eSewa: {str(exc)}",
        )

    # 3. Get plan details
    plan = db.query(Plan).filter(Plan.id == payment_data.plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    # 4. Create or update subscription
    subscription = db.query(Subscription).filter(Subscription.org_id == payment_data.org_id).first()
    now = date.today()
    period_end = now + (timedelta(days=365) if payment_data.type == SubscriptionType.yearly else timedelta(days=30))

    if subscription:
        subscription.plan_id = plan.id
        subscription.type = payment_data.type
        subscription.current_period_start = now
        subscription.current_period_end = period_end
        subscription.payment_status = "completed"
        subscription.payment_ref_id = payment_data.ref_id
        subscription.payment_method = "esewa"
        subscription.payment_provider_id = None
    else:
        subscription = Subscription(
            org_id=payment_data.org_id,
            plan_id=plan.id,
            type=payment_data.type,
            current_period_start=now,
            current_period_end=period_end,
            payment_status="completed",
            payment_ref_id=payment_data.ref_id,
            payment_method="esewa",
        )
        db.add(subscription)

    db.flush()

    subscription_usage = SubscriptionUsage(
        org_id=payment_data.org_id,
        subscription_id=subscription.id,
        minutes_used=0,
    )
    db.add(subscription_usage)
    db.commit()
    db.refresh(subscription)

    return {"status": "success", "message": "Subscription activated successfully"}