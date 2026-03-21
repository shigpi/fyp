from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.core.database import Base
import enum

class OrgRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"

class OrgMember(Base):
    __tablename__ = "org_member"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organization.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(SAEnum(OrgRole, name="org_role", create_constraint=True, native_enum=True), default=OrgRole.member)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="org_memberships")
