from sqlalchemy import Column, Integer, ForeignKey, Date, Boolean, Enum as SAEnum, String
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class SubscriptionType(str, enum.Enum):
    monthly = "monthly"
    yearly = "yearly"

class Subscription(Base):
    __tablename__ = "subscription"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organization.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plan.id"), nullable=False)
    type = Column(SAEnum(SubscriptionType, name="subscription_type", create_constraint=True, native_enum=True), default=SubscriptionType.monthly)
    current_period_start = Column(Date, nullable=True)
    current_period_end = Column(Date, nullable=True)
    cancel_at_period_end = Column(Boolean, default=True)
    payment_provider_id = Column(Integer, nullable=True)

    # eSewa Payment Tracking
    payment_status = Column(String(50), default="pending")
    payment_ref_id = Column(String(255), nullable=True)
    payment_method = Column(String(50), default="esewa")

    # Relationships
    organization = relationship("Organization", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
