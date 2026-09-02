from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Literal

class MembershipRequestCreate(BaseModel):
    project_id: int
    member_id: int

class MembershipRequestReview(BaseModel):
    status: Literal["PENDING", "APPROVED", "REJECTED", "pending", "approved", "rejected"]
    rejection_reason: Optional[str] = None
    reviewed_by: Optional[int] = None

class MembershipRequestResponse(BaseModel):
    id: int
    member_id: int
    project_id: int
    status: str
    risk_snapshot: Optional[str] = None
    risk_details: Optional[str] = None
    member_name: Optional[str] = None
    member_email: Optional[str] = None
    project_name: Optional[str] = None
    reviewed_by: Optional[int] = None
    has_history: Optional[bool] = None
    previous_projects: Optional[int] = None
    late_payments: Optional[int] = None
    overdue_payments: Optional[int] = None
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    reasons: Optional[list[str]] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
