from sqlalchemy import Boolean, Column, Integer, String, DateTime, Date, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"
    super_admin = "super_admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String, default="free")
    role = Column(SAEnum(UserRole, name="user_role", create_constraint=True, native_enum=True), default=UserRole.user)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    dob = Column(Date, nullable=True)
    phone = Column(String(25), nullable=True)
    email_verified = Column(Boolean, default=False)

    # Relationships
    owned_organizations = relationship("Organization", back_populates="owner", foreign_keys="Organization.owner_id")
    org_memberships = relationship("OrgMember", back_populates="user")

    @property
    def organization_id(self):
        if self.org_memberships:
            return self.org_memberships[0].org_id
        return None
