from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date, datetime



class PaymentBase(BaseModel):
    project_id: int
    user_id: int

    amount: float = Field(gt=0)

    due_date: date
    paid_date: Optional[date] = None

    payment_type: str = "installment"
    description: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentResponse(PaymentBase):
    id: int
    status: str
    delay_days: int
    overdue_months: int = 0
    accrued_penalty_amount: float = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarkPaymentPaidRequest(BaseModel):
    paid_date: Optional[date] = None


class MemberPaymentSummaryResponse(BaseModel):
    project_id: int
    user_id: int

    total_scheduled_amount: float
    total_due_amount: float
    total_paid_amount: float

    unpaid_amount: float
    due_unpaid_amount: float
    accrued_penalty_amount: float = 0

    payment_completion_ratio: float
    due_payment_completion_ratio: float

    total_payments: int
    paid_on_time_count: int
    paid_late_count: int
    unpaid_count: int
    overdue_count: int

    prepaid_installment_count: int = 0
    prepaid_amount: float = 0
    unused_prepayment_count: int = 0
    unused_prepayment_amount: float = 0

    average_delay_days: float
    max_delay_days: int


class PaymentPlanResponse(BaseModel):
    project_id: int
    project_name: str
    exists: bool
    installment_count: Optional[int] = None
    created_rounds: int
    remaining_rounds: Optional[int] = None
    last_due_date: Optional[date] = None
    monthly_late_penalty_rate: float


class NextPaymentRoundRequest(BaseModel):
    project_id: int
    due_date: date
    installment_count: Optional[int] = Field(default=None, gt=0)
    extra_cost_total: float = Field(default=0, ge=0)
    description: Optional[str] = None


class NextMemberDueRequest(BaseModel):
    project_id: int
    user_id: int
    due_date: date
    installment_count: Optional[int] = Field(default=None, gt=0)
    extra_cost_total: float = Field(default=0, ge=0)
    as_of_date: Optional[date] = None


class RecordInstallmentPaymentRequest(BaseModel):
    project_id: int
    user_id: int
    amount: float = Field(gt=0)
    due_date: date
    paid_date: date
    installment_count: Optional[int] = None
    extra_cost_total: float = Field(default=0, ge=0)
    description: Optional[str] = None


class RecordInstallmentPaymentResponse(BaseModel):
    project_id: int
    user_id: int
    amount_received: float
    required_due_amount: float
    principal_settled_amount: float
    penalty_paid_amount: float
    prepaid_installments_count: int
    prepaid_amount: float
    base_installment: float
    settled_payment_ids: list[int]
    prepayment_payment_ids: list[int]
    penalty_payment_id: Optional[int] = None
    message: str


class NextPaymentRoundMemberResponse(BaseModel):
    project_id: int
    user_id: int
    full_name: str
    email: Optional[str] = None

    reserved_units: float

    base_installment: float
    previous_overdue_amount: float
    late_penalty_amount: float
    extra_cost_share_amount: float
    credit_amount: float
    total_due_amount: float

    late_paid_count: int
    overdue_count: int
    unpaid_due_count: int
    overdue_months_max: int = 0
    unused_prepayment_count: int = 0


class NextPaymentRoundPreviewResponse(BaseModel):
    project_id: int
    project_name: str
    due_date: date
    installment_count: int
    round_number: int
    created_rounds: int
    rounds_remaining_after_generation: int
    is_existing_round: bool = False
    fixed_late_penalty_rate: float
    extra_cost_total: float

    members: list[NextPaymentRoundMemberResponse]

    total_base_installment: float
    total_previous_overdue: float
    total_late_penalty: float
    total_extra_cost_share: float
    total_credit_amount: float = 0
    total_due_amount: float


class GenerateNextPaymentRoundResponse(NextPaymentRoundPreviewResponse):
    generated_count: int
    skipped_count: int
    generated_payment_ids: list[int]
    consumed_prepayment_ids: list[int] = Field(default_factory=list)


class NextMemberDueResponse(NextPaymentRoundMemberResponse):
    project_name: str
    due_date: date
    installment_count: int
    fixed_late_penalty_rate: float
