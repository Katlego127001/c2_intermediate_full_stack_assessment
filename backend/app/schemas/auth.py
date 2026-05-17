"""Auth-related schemas."""
from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class CurrentUser(BaseModel):
    id: str
    email: EmailStr
    role: UserRole
    is_active: bool
    employee_id: str | None = None
    full_name: str | None = None
