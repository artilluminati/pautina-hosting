from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import relationship
from .database import Base
import enum

class RoleEnum(str, enum.Enum):
    guest = "guest"
    user = "user"
    admin = "admin"
    system = "system"

class PlanEnum(str, enum.Enum):
    demo = "demo"
    yearly = "yearly"

class StatusEnum(str, enum.Enum):
    pending = "pending"
    active = "active"
    expiring = "expiring"
    disabled = "disabled"
    archived = "archived"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.user)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    hosts = relationship("Host", back_populates="owner")

class Host(Base):
    __tablename__ = "hosts"
    id = Column(Integer, primary_key=True, index=True)
    subdomain = Column(String, unique=True, index=True, nullable=False)
    plan = Column(Enum(PlanEnum), default=PlanEnum.demo)
    status = Column(Enum(StatusEnum), default=StatusEnum.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="hosts")
    ftp_user = Column(String, nullable=True)
    ftp_password = Column(String, nullable=True)
    ssh_user = Column(String, nullable=True)
    ssh_key = Column(String, nullable=True)
    mysql_db = Column(String, nullable=True)
    mysql_user = Column(String, nullable=True)
    mysql_password = Column(String, nullable=True)
    mail_user = Column(String, nullable=True)
    mail_password = Column(String, nullable=True)