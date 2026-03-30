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
from datetime import date, timedelta

router = APIRouter()

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
    print("DEBUG: verifying membership")
    membership = db.query(OrgMember).filter(
        OrgMember.user_id == current_user.id,
        OrgMember.org_id == payment_data.org_id
    ).first()
    print("DEBUG: membership: ", membership)
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to the specified organization"
        )
        
    # 2. Strict Server-to-Server eSewa V2 Verification
    esewa_verify_url = "https://rc-epay.esewa.com.np/api/epay/transaction/status/"
    verify_params = {
        "product_code": "EPAYTEST", # Test merchant code
        "total_amount": payment_data.total_amount,
        "transaction_uuid": payment_data.product_id,
    }
    
    try:
        response = httpx.get(esewa_verify_url, params=verify_params, timeout=10.0)
        response.raise_for_status()
        
        verify_result = response.json()
        if verify_result.get("status") != "COMPLETE":
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
            cancel_at_period_end=False,
            payment_status="completed",
            payment_ref_id=payment_data.ref_id,
            payment_method="esewa"
        )
        db.add(subscription)
    
    db.commit()
    db.refresh(subscription)
    
    return {"status": "success", "message": "Subscription activated successfully"}

    