from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional
from datetime import datetime


class ProjectParticipantBase(BaseModel):
    project_id: int
    user_id: int

    role: str = Field(default="buyer", min_length=1, max_length=50)

    share_percent: Optional[float] = Field(default=None, ge=0, le=100)
    reserved_units: float = Field(default=1, gt=0)

    # This is retained for response compatibility, but the service always
    # initializes it from payment records rather than trusting client input.
    paid_amount: float = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_share(self):
        if self.share_percent is not None and self.share_percent <= 0:
            raise ValueError("share_percent must be greater than zero when provided")
        return self


class ProjectParticipantCreate(ProjectParticipantBase):
    pass


class ProjectParticipantResponse(ProjectParticipantBase):
    id: int
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)
