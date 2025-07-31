from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from .models import RoleEnum, PlanEnum, StatusEnum

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int]
    role: Optional[RoleEnum]

class PasswordRecoverRequest(BaseModel):
    phone: str

class PasswordRecoverResponse(BaseModel):
    login: EmailStr
    password: str

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: Optional[str]
    phone: str
    agree_terms: bool
    agree_privacy: bool

class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str
    role: RoleEnum
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserReadAfterRegister(UserRead):
    token: str

class HostCreate(BaseModel):
    subdomain: str
    plan: PlanEnum

class HostRead(BaseModel):
    id: int
    subdomain: str
    plan: PlanEnum
    status: StatusEnum
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True

class HostDetail(HostRead):
    ftp_user: Optional[str]
    ftp_password: Optional[str]
    ssh_user: Optional[str]
    ssh_key: Optional[str]
    mysql_db: Optional[str]
    mysql_user: Optional[str]
    mysql_password: Optional[str]
    mail_user: Optional[str]
    mail_password: Optional[str]