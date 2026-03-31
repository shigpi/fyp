from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.api import deps

from backend.models.user import User
from backend.schemas.user import UserResponse

from backend.models.org_member import OrgMember

from backend.models.plan import Plan
from backend.schemas.plan import PlanResponse

from backend.models.subscription import Subscription, SubscriptionType
from backend.schemas.subscription import EsewaPaymentVerify

from backend.models.subscription_usage import SubscriptionUsage
from backend.models.organization import Organization
from datetime import date, timedelta
from fastapi import HTTPException, status
import os

router = APIRouter()

@router.get("/me/subscription")
def get_my_subscription(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    membership = db.query(OrgMember).filter(OrgMember.user_id == current_user.id).first()
    if not membership:
        return None

    subscription = db.query(Subscription).filter(
        Subscription.org_id == membership.org_id,
        Subscription.current_period_end >= date.today()
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
def delete_my_account(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    try:
        # Delete owned organizations and their related data
        owned_orgs = db.query(Organization).filter(Organization.owner_id == current_user.id).all()
        for org in owned_orgs:
            # Delete subscription usage for this org's subscriptions
            org_subs = db.query(Subscription).filter(Subscription.org_id == org.id).all()
            for sub in org_subs:
                db.query(SubscriptionUsage).filter(SubscriptionUsage.subscription_id == sub.id).delete()
            # Delete subscriptions
            db.query(Subscription).filter(Subscription.org_id == org.id).delete()
            # Delete org members
            db.query(OrgMember).filter(OrgMember.org_id == org.id).delete()
            # Delete the organization
            db.delete(org)

        # Delete any remaining org memberships (non-owned orgs)
        db.query(OrgMember).filter(OrgMember.user_id == current_user.id).delete()

        # Delete the user
        db.delete(current_user)
        db.commit()

        return {"status": "success", "message": "Account deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(deps.get_current_user)):
    return current_user

@router.get("/me/organizations")
def read_user_organizations(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    # Fetch org members with the org included
    memberships = db.query(OrgMember).filter(OrgMember.user_id == current_user.id).all()
    
    result = []
    for m in memberships:
        result.append({
            "id": m.id,
            "role": m.role.value,
            "organization": {
                "id": m.organization.id,
                "name": m.organization.name,
                "slug": m.organization.slug,
                "type": m.organization.type.value
            }
        })
    return result

@router.get("/plans", response_model=List[PlanResponse])
def read_plans(db: Session = Depends(deps.get_db)):
    plans = db.query(Plan).all()
    return plans

@router.post("/subscription/esewa")
def verify_esewa_payment(
    payment_data: EsewaPaymentVerify,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    import httpx
    from fastapi import HTTPException, status
    
    # 1. Verify user's membership in the organization
    membership = db.query(OrgMember).filter(
        OrgMember.user_id == current_user.id,
        OrgMember.org_id == payment_data.org_id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to the specified organization"
        )
        
    # 2. Strict Server-to-Server eSewa V2 Verification
    esewa_verify_url = "https://rc.esewa.com.np/mobile/transaction"
    verify_params = {
        "productId": payment_data.product_id,
        "amount": payment_data.total_amount
    }

    # Test credentials
    ESEWA_CLIENT_ID = os.getenv("ESEWA_CLIENT_ID") # 
    ESEWA_SECRET_KEY = os.getenv("ESEWA_SECRET_KEY")
    
    headers = {
        "merchantId": ESEWA_CLIENT_ID,
        "merchantSecret": ESEWA_SECRET_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = httpx.get(esewa_verify_url, params=verify_params, headers=headers, timeout=10.0)
        print("VERIFY PARAMS:", verify_params)
        print("ESEWA RESPONSE STATUS:", response.status_code)
        # print("ESEWA RESPONSE BODY:", response.text)
        response.raise_for_status()
        
        print("CONTENT TYPE:", response.headers.get("content-type"))
        print("RAW BODY:", response.text)

        if "application/json" not in response.headers.get("content-type", ""):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid eSewa response (not JSON): {response.text[:200]}"
            )

        verify_result = response.json()

        if not verify_result:
            raise HTTPException(
                status_code=400,
                detail="Empty response from eSewa"
            )
        
        txn_status = verify_result[0]["transactionDetails"]["status"]

        if txn_status != "COMPLETE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="eSewa Server Verification failed: Transaction not COMPLETE"
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error connecting to eSewa: {str(exc)}"
        )

    # 3. Get Plan details
    plan = db.query(Plan).filter(Plan.id == payment_data.plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )

    # 4. Create or update subscription
    subscription = db.query(Subscription).filter(
        Subscription.org_id == payment_data.org_id
    ).first()
    
    now = date.today()
    if payment_data.type == SubscriptionType.yearly:
        period_end = now + timedelta(days=365)
    else:
        period_end = now + timedelta(days=30)
    
    

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
            payment_method="esewa"
        )
        db.add(subscription)

    db.flush()

    subscription_usage = SubscriptionUsage(
        org_id=payment_data.org_id,
        subscription_id=subscription.id,
        minutes_used=0
    )

    db.add(subscription_usage)
    
    db.commit()
    db.refresh(subscription)
    
    return {"status": "success", "message": "Subscription activated successfully"}

    