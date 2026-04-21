from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class OrgType(str, enum.Enum):
    individual = "individual"
    team = "team"

class Organization(Base):
    __tablename__ = "organization"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    type = Column(SAEnum(OrgType, name="org_type", create_constraint=True, native_enum=True), default=OrgType.individual)

    # Relationships
    owner = relationship("User", back_populates="owned_organizations", foreign_keys=[owner_id])
    members = relationship("OrgMember", back_populates="organization")
    subscriptions = relationship("Subscription", back_populates="organization")
