from pydantic import BaseModel, EmailStr, field_validator
import re
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    national_id: Optional[str] = None
    role: str = "buyer"

    @field_validator("phone_number")
    @classmethod
    def validate_iran_phone(cls, value):
        if value in (None, ""):
            return value
        normalized = re.sub(r"[\s-]", "", str(value))
        if not re.fullmatch(r"(?:09\d{9}|\+989\d{9})", normalized):
            raise ValueError("Phone number must be a valid Iranian number (09123456789 or +989123456789).")
        return normalized

    @field_validator("role")
    @classmethod
    def normalize_role(cls, value):
        role = str(value or "").strip().upper()
        aliases = {"OWNER": "OWNER", "PROJECT_OWNER": "OWNER", "MEMBER": "MEMBER", "BUYER": "MEMBER", "ADMIN": "ADMIN"}
        return aliases.get(role, role)


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
