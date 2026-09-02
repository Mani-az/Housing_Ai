from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class ProjectOwnerAssignRequest(BaseModel):
    project_id: int
    owner_user_id: int


class ProjectOwnerAssignmentResponse(BaseModel):
    id: int
    project_id: int
    owner_user_id: int
    assigned_at: datetime

    class Config:
        from_attributes = True


class OwnerProjectSummary(BaseModel):
    id: int
    name: str
    location: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class ProjectOwnerSummary(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


class DemoAccountResponse(BaseModel):
    id: str
    user_id: Optional[int] = None
    displayName: str
    email: str
    phone_number: Optional[str] = None
    role: str
    roleLabel: str
    accessLabel: str
    projectIds: Optional[list[str]] = None
    projectNames: list[str] = []
    username: Optional[str] = None


class DemoLoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class ProjectOwnerCreateAccountRequest(BaseModel):
    full_name: str = Field(..., min_length=2)
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=3, max_length=120)
    phone_number: Optional[str] = None
    national_id: Optional[str] = None
    role: str = Field(default="OWNER", min_length=1, max_length=30)

    @field_validator("phone_number")
    @classmethod
    def validate_iran_phone(cls, value):
        if value in (None, ""):
            raise ValueError("Phone number is required.")
        normalized = re.sub(r"[\s-]", "", str(value))
        if not re.fullmatch(r"(?:09\d{9}|\+989\d{9})", normalized):
            raise ValueError("Phone number must be a valid Iranian number (09123456789 or +989123456789).")
        return normalized
