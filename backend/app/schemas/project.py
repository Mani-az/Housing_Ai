from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional
from datetime import date, datetime


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    location: Optional[str] = Field(default=None, max_length=200)
    neighborhood_english: Optional[str] = Field(default=None, max_length=150)

    total_units: int = Field(gt=0)
    average_unit_area: Optional[float] = Field(default=None, gt=0)

    estimated_total_cost: float = Field(gt=0)

    start_date: Optional[date] = None
    expected_end_date: Optional[date] = None

    status: str = Field(default="planning", min_length=1, max_length=30)

    @model_validator(mode="after")
    def validate_date_order(self):
        if (
            self.start_date is not None
            and self.expected_end_date is not None
            and self.expected_end_date < self.start_date
        ):
            raise ValueError("expected_end_date cannot be before start_date")
        return self


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    # Payment collection progress used by the Owner and Member project views.
    # This is derived by the backend from persisted payment records.
    payment_progress: float = 0.0
    progress: float = 0.0
    available_units: int | None = None

    model_config = ConfigDict(from_attributes=True)


class ProjectMarketEstimateResponse(BaseModel):
    project_id: int
    project_name: str
    location: Optional[str] = None
    neighborhood_english: Optional[str] = None

    total_units: int
    average_unit_area: Optional[float] = None

    average_adjusted_price_per_meter: Optional[float] = None
    estimated_unit_price: Optional[float] = None
    estimated_total_project_value: Optional[float] = None

    market_samples_used: int


class ProjectFutureEstimateResponse(BaseModel):
    project_id: int
    project_name: str
    neighborhood_english: Optional[str] = None
    delivery_horizon_years: int

    current_estimated_unit_price: Optional[float] = None
    current_estimated_total_project_value: Optional[float] = None

    current_estimated_construction_cost: float
    future_estimated_construction_cost: Optional[float] = None

    predicted_general_inflation_rate: Optional[float] = None
    predicted_housing_growth_rate: Optional[float] = None
    predicted_construction_cost_growth: Optional[float] = None
    predicted_usd_growth: Optional[float] = None

    future_estimated_unit_price: Optional[float] = None
    future_estimated_total_project_value: Optional[float] = None

    real_housing_growth_estimate: Optional[float] = None
    estimated_project_margin: Optional[float] = None

    margin_ratio_percent: float | None = None
    financial_feasibility: str
    overall_project_risk: str
    recommendation: str

    market_condition: str
    cost_overrun_risk: str
    model_note: str

class AnnualCostSplitMemberResponse(BaseModel):
    user_id: int
    role: str
    share_percent: float | None = None
    reserved_units: float
    allocated_amount: float


class AnnualCostSplitResponse(BaseModel):
    project_id: int
    year: int
    annual_cost: float
    allocation_method: str
    total_share_percent: float
    unallocated_amount: float = 0
    participants_count: int
    members: list[AnnualCostSplitMemberResponse]

class NextYearCostSplitMemberResponse(BaseModel):
    user_id: int
    role: str
    share_percent: float | None = None
    reserved_units: float
    required_amount: float


class NextYearCostSplitResponse(BaseModel):
    project_id: int
    project_name: str
    target_year: int

    current_construction_cost: float
    predicted_construction_cost_growth: float | None = None
    next_year_estimated_construction_cost: float | None = None

    allocation_method: str
    total_registered_share_percent: float
    unallocated_amount: float = 0
    participants_count: int

    members: list[NextYearCostSplitMemberResponse]

    model_note: str
