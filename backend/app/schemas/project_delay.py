from pydantic import BaseModel
from typing import List, Optional


class ProjectDelayPredictionResponse(BaseModel):
    project_id: int
    project_name: str

    planned_duration_months: int
    predicted_delay_months: float
    estimated_actual_duration_months: float
    delay_risk_level: str

    predicted_construction_cost_growth: float
    predicted_general_inflation_rate: float
    predicted_usd_growth: float

    project_payment_completion_ratio: float
    overdue_payment_ratio: float
    paid_late_payment_ratio: float

    low_risk_member_ratio: float
    medium_risk_member_ratio: float
    high_risk_member_ratio: float

    cash_flow_pressure_ratio: float

    main_delay_factors: List[str]
    model_mae: Optional[float] = None
    model_note: str