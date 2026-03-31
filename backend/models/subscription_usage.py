from sqlalchemy import Column, Integer, ForeignKey, Numeric, DateTime, func
from sqlalchemy.orm import relationship
from backend.core.database import Base

class SubscriptionUsage(Base):
    __tablename__ = "subscription_usage"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organization.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscription.id"), nullable=False)
    minutes_used = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    organization = relationship("Organization")
    subscription = relationship("Subscription")
