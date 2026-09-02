from pydantic import BaseModel
from typing import Optional
from datetime import date


class MemberRiskPredictionResponse(BaseModel):
    project_id: int
    user_id: int

    share_percent: float
    reserved_units: float
    required_next_year_amount: float
    remaining_amount_to_project_end: float = 0

    recorded_rounds_total: int = 0
    current_round_number: int = 0
    completed_rounds: int = 0
    remaining_recorded_rounds: int = 0
    overdue_rounds: int = 0
    average_payment_interval_days: int = 0
    scheduled_rounds_next_12_months: int = 0
    forecasted_additional_rounds_next_12_months: int = 0
    forecast_rounds_next_12_months: int = 0
    estimated_remaining_rounds_to_project_end: int = 0
    estimated_amount_per_forecast_round: float = 0
    forecast_horizon_end: Optional[date] = None

    total_scheduled_amount: float
    total_due_amount: float
    total_paid_amount: float
    unpaid_amount: float
    due_unpaid_amount: float

    payment_completion_ratio: float
    due_payment_completion_ratio: float
    unpaid_amount_ratio: float
    due_unpaid_amount_ratio: float

    paid_late_count: int
    overdue_count: int
    prepaid_installment_count: int = 0
    prepaid_amount: float = 0
    unused_prepayment_count: int = 0
    unused_prepayment_amount: float = 0
    accrued_penalty_amount: float = 0
    average_delay_days: float
    max_delay_days: int

    predicted_risk_label: str
    risk_score_estimate: Optional[float] = None
    model_accuracy: Optional[float] = None

    risk_explanation: str
    model_note: str