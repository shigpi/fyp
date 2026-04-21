from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base

class Plan(Base):
    __tablename__ = "plan"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    price_month = Column(Numeric(12, 2), nullable=False, default=0)
    price_year = Column(Numeric(12, 2), nullable=False, default=0)
    token_quota = Column(Integer, nullable=False, default=0)
    max_users = Column(Integer, nullable=False, default=1)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")
