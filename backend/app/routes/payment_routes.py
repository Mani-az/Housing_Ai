from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    MarkPaymentPaidRequest,
    MemberPaymentSummaryResponse,
    NextPaymentRoundRequest,
    NextMemberDueRequest,
    NextPaymentRoundPreviewResponse,
    GenerateNextPaymentRoundResponse,
    NextMemberDueResponse,
    RecordInstallmentPaymentRequest,
    RecordInstallmentPaymentResponse,
    PaymentPlanResponse,
)
from app.services.payment_service import (
    create_payment,
    get_payments,
    get_payment_by_id,
    get_payments_by_project,
    get_payments_by_user,
    mark_payment_as_paid,
    get_member_payment_summary,
    calculate_next_payment_round,
    calculate_next_member_due,
    generate_next_payment_round,
    record_installment_payment,
    get_payment_plan_summary,
)


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post("/", response_model=PaymentResponse)
def create_new_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
):
    return create_payment(
        db=db,
        payment_data=payment_data,
    )


@router.get("/", response_model=list[PaymentResponse])
def read_payments(
    db: Session = Depends(get_db),
):
    return get_payments(db=db)


@router.get(
    "/project/{project_id}/plan",
    response_model=PaymentPlanResponse,
)
def read_payment_plan(
    project_id: int,
    db: Session = Depends(get_db),
):
    return get_payment_plan_summary(db=db, project_id=project_id)


@router.get("/project/{project_id}", response_model=list[PaymentResponse])
def read_payments_by_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    return get_payments_by_project(
        db=db,
        project_id=project_id,
    )


@router.get("/user/{user_id}", response_model=list[PaymentResponse])
def read_payments_by_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    return get_payments_by_user(
        db=db,
        user_id=user_id,
    )


@router.patch("/{payment_id}/mark-paid", response_model=PaymentResponse)
def mark_payment_paid(
    payment_id: int,
    request_data: MarkPaymentPaidRequest,
    db: Session = Depends(get_db),
):
    return mark_payment_as_paid(
        db=db,
        payment_id=payment_id,
        paid_date=request_data.paid_date,
    )


@router.get(
    "/project/{project_id}/member/{user_id}/summary",
    response_model=MemberPaymentSummaryResponse,
)
def read_member_payment_summary(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    return get_member_payment_summary(
        db=db,
        project_id=project_id,
        user_id=user_id,
    )

@router.post(
    "/next-round/preview",
    response_model=NextPaymentRoundPreviewResponse,
)
def preview_next_payment_round(
    request_data: NextPaymentRoundRequest,
    db: Session = Depends(get_db),
):
    return calculate_next_payment_round(
        db=db,
        project_id=request_data.project_id,
        due_date=request_data.due_date,
        installment_count=request_data.installment_count,
        extra_cost_total=request_data.extra_cost_total,
    )


@router.post(
    "/next-due/member",
    response_model=NextMemberDueResponse,
)
def preview_next_member_due(
    request_data: NextMemberDueRequest,
    db: Session = Depends(get_db),
):
    return calculate_next_member_due(
        db=db,
        project_id=request_data.project_id,
        user_id=request_data.user_id,
        due_date=request_data.due_date,
        installment_count=request_data.installment_count,
        extra_cost_total=request_data.extra_cost_total,
        as_of_date=request_data.as_of_date,
    )


@router.post(
    "/installment-payment",
    response_model=RecordInstallmentPaymentResponse,
)
def record_member_installment_payment(
    request_data: RecordInstallmentPaymentRequest,
    db: Session = Depends(get_db),
):
    return record_installment_payment(
        db=db,
        project_id=request_data.project_id,
        user_id=request_data.user_id,
        amount=request_data.amount,
        due_date=request_data.due_date,
        paid_date=request_data.paid_date,
        installment_count=request_data.installment_count,
        extra_cost_total=request_data.extra_cost_total,
        description=request_data.description,
    )


@router.post(
    "/next-round/generate",
    response_model=GenerateNextPaymentRoundResponse,
)
def create_next_payment_round(
    request_data: NextPaymentRoundRequest,
    db: Session = Depends(get_db),
):
    return generate_next_payment_round(
        db=db,
        project_id=request_data.project_id,
        due_date=request_data.due_date,
        installment_count=request_data.installment_count,
        extra_cost_total=request_data.extra_cost_total,
        description=request_data.description,
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
def read_payment(
    payment_id: int,
    db: Session = Depends(get_db),
):
    return get_payment_by_id(
        db=db,
        payment_id=payment_id,
    )