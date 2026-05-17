"""Employee schemas."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
import re

from app.models.employee import EmploymentStatus
from app.models.user import UserRole


class EmployeeBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    phone_number: str | None = Field(default=None, max_length=40)
    department: str | None = Field(default=None, max_length=120)


class EmployeeCreate(EmployeeBase):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.EMPLOYEE
    employment_status: EmploymentStatus = EmploymentStatus.ACTIVE
    # Note: the frontend admin UI enforces phone_number and department as required fields.
    # Keep them optional at the API layer for backwards compatibility and tests.


class EmployeeUpdate(BaseModel):
    """Admin-side update (all fields optional)."""
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    phone_number: str | None = Field(default=None, max_length=40)
    department: str | None = Field(default=None, max_length=120)
    employment_status: EmploymentStatus | None = None
    role: UserRole | None = None


class EmployeeSelfUpdate(BaseModel):
    """Employee can only update their own phone number."""
    phone_number: str | None = Field(default=None, max_length=40)

    @field_validator("phone_number")
    def validate_phone(cls, v: str | None):
        # be defensive: accept strings, bytes, dict-like, or model-like inputs
        if v is None:
            return v

        # if it's already a string/bytes, use it
        if isinstance(v, (str, bytes)):
            raw = v
        else:
            # try dict-like access
            raw = None
            try:
                if isinstance(v, dict):
                    raw = v.get("phone_number")
                elif hasattr(v, "get"):
                    # mapping-like
                    raw = v.get("phone_number")
            except Exception:
                raw = None
            # try attribute access on model-like objects
            if raw is None and hasattr(v, "phone_number"):
                try:
                    raw = getattr(v, "phone_number")
                except Exception:
                    raw = None

            if raw is None:
                raise ValueError("Invalid phone number format")

        # permissive check: allow spaces, dashes, parentheses; require digits
        s = re.sub(r"[\s\-()]+", "", str(raw))
        if not re.fullmatch(r"\+?\d{7,15}", s):
            raise ValueError("Invalid phone number format")
        # Keep the original (human-friendly) formatting when returning so
        # clients receive the value they provided (tests depend on this).
        return str(raw)


class EmployeeStatusUpdate(BaseModel):
    employment_status: EmploymentStatus


class EmployeeOut(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr
    role: UserRole
    employment_status: EmploymentStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    full_name: str
