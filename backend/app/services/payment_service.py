from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.business_rules import (
    INSTALLMENT_AMOUNT_TOLERANCE,
    MONTHLY_LATE_PENALTY_RATE,
    calculate_simple_late_penalty,
    overdue_calendar_months,
)
from app.models.payment import Payment
from app.models.payment_plan import PaymentPlan
from app.models.project import Project
from app.models.user import User
from app.models.project_participant import ProjectParticipant
from app.schemas.payment import PaymentCreate


FIXED_LATE_PENALTY_RATE = MONTHLY_LATE_PENALTY_RATE
MANUAL_PAYMENT_TYPES = {"down_payment", "cost_share"}
SYSTEM_PAYMENT_TYPES = {"installment", "penalty", "prepayment"}
CONTRACT_PAYMENT_TYPES = {"installment", "down_payment", "cost_share"}


def _money(value: float | int | None) -> float:
    return round(float(value or 0), 2)


def _calculate_payment_status(
    due_date: date,
    paid_date: date | None = None,
) -> tuple[str, int]:
    today = date.today()

    if paid_date:
        delay_days = max((paid_date - due_date).days, 0)
        if delay_days > 0:
            return "paid_late", delay_days
        return "paid", 0

    if today > due_date:
        delay_days = (today - due_date).days
        return "overdue", delay_days

    return "unpaid", 0


def _refresh_payment_status(payment: Payment) -> Payment:
    status_value, delay_days = _calculate_payment_status(
        due_date=payment.due_date,
        paid_date=payment.paid_date,
    )
    payment.status = status_value
    payment.delay_days = delay_days
    return payment


def _get_project(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    return project


def _get_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


def _get_participant(db: Session, project_id: int, user_id: int) -> ProjectParticipant:
    participant = (
        db.query(ProjectParticipant)
        .filter(
            ProjectParticipant.project_id == project_id,
            ProjectParticipant.user_id == user_id,
        )
        .first()
    )
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a participant in this project.",
        )
    return participant


def _validate_installment_count(value: int | None) -> int:
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "This project does not have a payment plan yet. "
                "The owner must choose the total installment count before the first round is generated."
            ),
        )
    try:
        count = int(value)
    except (TypeError, ValueError):
        count = 0
    if count <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Installment count must be greater than zero.",
        )
    return count


def _resolve_payment_plan(
    db: Session,
    project_id: int,
    installment_count: int | None,
    *,
    create_if_missing: bool,
) -> PaymentPlan | None:
    plan = db.query(PaymentPlan).filter(PaymentPlan.project_id == project_id).first()
    if plan:
        if installment_count is not None and int(plan.installment_count) != int(installment_count):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"This project already uses {plan.installment_count} installments. "
                    f"The installment count cannot be changed to {int(installment_count)} after the plan has started."
                ),
            )
        return plan

    if not create_if_missing:
        return None

    requested_count = _validate_installment_count(installment_count)
    plan = PaymentPlan(
        project_id=project_id,
        installment_count=requested_count,
        payment_interval_months=1,
        monthly_late_penalty_rate=FIXED_LATE_PENALTY_RATE,
    )
    db.add(plan)
    db.flush()
    return plan


def _effective_installment_count(
    db: Session,
    project_id: int,
    requested_count: int | None,
) -> int:
    plan = _resolve_payment_plan(
        db=db,
        project_id=project_id,
        installment_count=requested_count,
        create_if_missing=False,
    )
    if plan:
        return int(plan.installment_count)
    return _validate_installment_count(requested_count)


def _project_round_due_dates(db: Session, project_id: int) -> list[date]:
    rows = (
        db.query(Payment.due_date)
        .filter(
            Payment.project_id == project_id,
            Payment.payment_type == "installment",
        )
        .distinct()
        .all()
    )
    return sorted(row[0] for row in rows if row[0] is not None)


def _validate_round_slot(
    db: Session,
    *,
    project_id: int,
    due_date: date,
    installment_count: int,
) -> dict:
    round_dates = _project_round_due_dates(db, project_id)
    if due_date in round_dates:
        round_number = round_dates.index(due_date) + 1
        return {
            "is_existing_round": True,
            "round_number": round_number,
            "created_rounds": len(round_dates),
            "rounds_remaining_after_generation": max(installment_count - len(round_dates), 0),
            "last_due_date": round_dates[-1] if round_dates else None,
        }

    if len(round_dates) >= installment_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"All {installment_count} installment rounds have already been created for this project. "
                "No additional round can be generated."
            ),
        )

    if round_dates and due_date <= round_dates[-1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"The next round due date must be later than the previous round ({round_dates[-1].isoformat()})."
            ),
        )

    return {
        "is_existing_round": False,
        "round_number": len(round_dates) + 1,
        "created_rounds": len(round_dates),
        "rounds_remaining_after_generation": max(installment_count - len(round_dates) - 1, 0),
        "last_due_date": round_dates[-1] if round_dates else None,
    }


def get_payment_plan_summary(db: Session, project_id: int) -> dict:
    project = _get_project(db, project_id)
    plan = _resolve_payment_plan(
        db=db,
        project_id=project_id,
        installment_count=None,
        create_if_missing=False,
    )
    round_dates = _project_round_due_dates(db, project_id)
    if not plan:
        return {
            "project_id": project_id,
            "project_name": project.name,
            "exists": False,
            "installment_count": None,
            "created_rounds": len(round_dates),
            "remaining_rounds": None,
            "last_due_date": round_dates[-1] if round_dates else None,
            "monthly_late_penalty_rate": FIXED_LATE_PENALTY_RATE,
        }
    return {
        "project_id": project_id,
        "project_name": project.name,
        "exists": True,
        "installment_count": int(plan.installment_count),
        "created_rounds": len(round_dates),
        "remaining_rounds": max(int(plan.installment_count) - len(round_dates), 0),
        "last_due_date": round_dates[-1] if round_dates else None,
        "monthly_late_penalty_rate": float(plan.monthly_late_penalty_rate or FIXED_LATE_PENALTY_RATE),
    }

def _calculate_base_installment(
    *,
    project: Project,
    participant: ProjectParticipant,
    installment_count: int,
) -> float:
    if installment_count <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Installment count must be greater than zero.",
        )
    if not project.total_units or project.total_units <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project total units must be greater than zero.",
        )

    per_unit_total_price = float(project.estimated_total_cost or 0) / float(project.total_units)
    reserved_units = float(participant.reserved_units or 1)
    return _money((per_unit_total_price * reserved_units) / float(installment_count))


def _calculate_extra_cost_share(
    db: Session,
    *,
    project_id: int,
    participant: ProjectParticipant,
    extra_cost_total: float,
) -> float:
    if not extra_cost_total or extra_cost_total <= 0:
        return 0.0

    participants = (
        db.query(ProjectParticipant)
        .filter(ProjectParticipant.project_id == project_id)
        .all()
    )
    total_reserved_units = sum(float(item.reserved_units or 0) for item in participants)
    if total_reserved_units <= 0:
        total_reserved_units = float(len(participants) or 1)

    reserved_units = float(participant.reserved_units or 1)
    return _money(float(extra_cost_total) * (reserved_units / total_reserved_units))


def _unused_prepayments(db: Session, project_id: int, user_id: int) -> list[Payment]:
    return (
        db.query(Payment)
        .filter(
            Payment.project_id == project_id,
            Payment.user_id == user_id,
            Payment.payment_type == "prepayment",
            Payment.paid_date.isnot(None),
        )
        .order_by(Payment.paid_date.asc(), Payment.id.asc())
        .all()
    )


def _payment_penalty(payment: Payment, as_of_date: date) -> float:
    if (
        payment.payment_type != "installment"
        or payment.paid_date is not None
        or not payment.due_date
        or as_of_date <= payment.due_date
    ):
        return 0.0
    return calculate_simple_late_penalty(
        principal=float(payment.amount or 0),
        due_date=payment.due_date,
        as_of_date=as_of_date,
        monthly_rate=FIXED_LATE_PENALTY_RATE,
    )


def _update_participant_paid_amount(
    db: Session,
    project_id: int,
    user_id: int,
):
    participant = (
        db.query(ProjectParticipant)
        .filter(
            ProjectParticipant.project_id == project_id,
            ProjectParticipant.user_id == user_id,
        )
        .first()
    )
    if not participant:
        return

    paid_rows = (
        db.query(Payment)
        .filter(
            Payment.project_id == project_id,
            Payment.user_id == user_id,
            Payment.paid_date.isnot(None),
            Payment.payment_type != "penalty",
        )
        .all()
    )
    participant.paid_amount = _money(sum(float(row.amount or 0) for row in paid_rows))


def create_payment(db: Session, payment_data: PaymentCreate) -> Payment:
    _get_project(db, payment_data.project_id)
    _get_user(db, payment_data.user_id)
    _get_participant(db, payment_data.project_id, payment_data.user_id)

    payment_type = (payment_data.payment_type or "installment").strip().lower()
    if payment_type in SYSTEM_PAYMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"{payment_type} records are system-managed. "
                "Use Generate Payment Round for installment obligations and the installment-payment endpoint for collections/prepayments."
            ),
        )
    if payment_type not in MANUAL_PAYMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported manual payment type: {payment_type}.",
        )

    if payment_data.paid_date and payment_data.paid_date > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paid date cannot be in the future.",
        )


    status_value, delay_days = _calculate_payment_status(
        due_date=payment_data.due_date,
        paid_date=payment_data.paid_date,
    )

    new_payment = Payment(
        project_id=payment_data.project_id,
        user_id=payment_data.user_id,
        amount=_money(payment_data.amount),
        due_date=payment_data.due_date,
        paid_date=payment_data.paid_date,
        status=status_value,
        delay_days=delay_days,
        payment_type=payment_type,
        description=payment_data.description,
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    _update_participant_paid_amount(db, payment_data.project_id, payment_data.user_id)
    db.commit()
    db.refresh(new_payment)
    return new_payment


def get_payments(db: Session) -> list[Payment]:
    payments = db.query(Payment).order_by(Payment.id.desc()).all()
    for payment in payments:
        _refresh_payment_status(payment)
    db.commit()
    return payments


def get_payment_by_id(db: Session, payment_id: int) -> Payment:
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )
    _refresh_payment_status(payment)
    db.commit()
    db.refresh(payment)
    return payment


def get_payments_by_project(db: Session, project_id: int) -> list[Payment]:
    payments = (
        db.query(Payment)
        .filter(Payment.project_id == project_id)
        .order_by(Payment.due_date.asc(), Payment.id.asc())
        .all()
    )
    for payment in payments:
        _refresh_payment_status(payment)
    db.commit()
    return payments


def get_payments_by_user(db: Session, user_id: int) -> list[Payment]:
    payments = (
        db.query(Payment)
        .filter(Payment.user_id == user_id)
        .order_by(Payment.due_date.asc(), Payment.id.asc())
        .all()
    )
    for payment in payments:
        _refresh_payment_status(payment)
    db.commit()
    return payments


def _create_penalty_payment(
    db: Session,
    *,
    project_id: int,
    user_id: int,
    amount: float,
    paid_date: date,
    description: str,
) -> Payment | None:
    if amount <= INSTALLMENT_AMOUNT_TOLERANCE:
        return None
    penalty = Payment(
        project_id=project_id,
        user_id=user_id,
        amount=_money(amount),
        due_date=paid_date,
        paid_date=paid_date,
        status="paid",
        delay_days=0,
        payment_type="penalty",
        description=description,
    )
    db.add(penalty)
    db.flush()
    return penalty


def mark_payment_as_paid(
    db: Session,
    payment_id: int,
    paid_date: date | None = None,
) -> Payment:
    payment = get_payment_by_id(db=db, payment_id=payment_id)
    paid_date = paid_date or date.today()

    if paid_date > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paid date cannot be in the future.",
        )

    if payment.payment_type == "installment":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Installments cannot be marked paid directly. "
                "Use /payments/installment-payment so overdue principal, monthly late penalties and prepayments are validated together."
            ),
        )
    if payment.payment_type in {"penalty", "prepayment"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{payment.payment_type} records are system-managed and cannot be marked paid manually.",
        )

    if payment.paid_date is not None:
        return payment

    payment.paid_date = paid_date
    _refresh_payment_status(payment)
    db.commit()
    db.refresh(payment)
    _update_participant_paid_amount(db, payment.project_id, payment.user_id)
    db.commit()
    db.refresh(payment)
    return payment

def get_member_payment_summary(db: Session, project_id: int, user_id: int):
    _get_participant(db, project_id, user_id)

    payments = (
        db.query(Payment)
        .filter(Payment.project_id == project_id, Payment.user_id == user_id)
        .all()
    )
    for payment in payments:
        _refresh_payment_status(payment)
    db.commit()

    today = date.today()
    obligation_payments = [
        p for p in payments if p.payment_type in CONTRACT_PAYMENT_TYPES
    ]
    installment_payments = [p for p in payments if p.payment_type == "installment"]
    unused_prepayments = [p for p in payments if p.payment_type == "prepayment"]

    total_scheduled_amount = _money(
        sum(float(p.amount or 0) for p in obligation_payments)
        + sum(float(p.amount or 0) for p in unused_prepayments)
    )

    due_obligations = [p for p in obligation_payments if p.due_date <= today]
    total_due_amount = _money(sum(float(p.amount or 0) for p in due_obligations))
    due_paid_amount = _money(
        sum(float(p.amount or 0) for p in due_obligations if p.paid_date is not None)
    )

    total_paid_amount = _money(
        sum(float(p.amount or 0) for p in obligation_payments if p.paid_date is not None)
        + sum(float(p.amount or 0) for p in unused_prepayments)
    )

    accrued_penalty_amount = _money(
        sum(_payment_penalty(p, today) for p in installment_payments)
    )
    principal_unpaid_amount = max(total_scheduled_amount - total_paid_amount, 0.0)
    due_unpaid_principal = max(total_due_amount - due_paid_amount, 0.0)
    unpaid_amount = _money(principal_unpaid_amount + accrued_penalty_amount)
    due_unpaid_amount = _money(due_unpaid_principal + accrued_penalty_amount)

    payment_completion_ratio = (
        min(total_paid_amount / total_scheduled_amount, 1.0)
        if total_scheduled_amount > 0
        else 0.0
    )
    due_payment_completion_ratio = (
        min(due_paid_amount / total_due_amount, 1.0)
        if total_due_amount > 0
        else 0.0
    )

    paid_on_time_count = sum(
        1
        for p in installment_payments
        if p.paid_date is not None and p.paid_date <= p.due_date
    )
    paid_late_count = sum(1 for p in installment_payments if p.status == "paid_late")
    unpaid_count = sum(1 for p in installment_payments if p.status == "unpaid")
    overdue_count = sum(1 for p in installment_payments if p.status == "overdue")

    prepaid_consumed = [
        p
        for p in installment_payments
        if (
            p.paid_date is not None
            and p.paid_date < p.due_date
            and (
                "prepaid installment" in str(p.description or "").lower()
                or "prepayment" in str(p.description or "").lower()
                or (p.due_date - p.paid_date).days >= 7
            )
        )
    ]
    prepaid_installment_count = len(prepaid_consumed) + len(unused_prepayments)
    prepaid_amount = _money(
        sum(float(p.amount or 0) for p in prepaid_consumed)
        + sum(float(p.amount or 0) for p in unused_prepayments)
    )

    delayed_payments = [
        p.delay_days
        for p in installment_payments
        if p.status in {"paid_late", "overdue"} and int(p.delay_days or 0) > 0
    ]
    average_delay_days = (
        sum(delayed_payments) / len(delayed_payments) if delayed_payments else 0.0
    )
    max_delay_days = max(delayed_payments) if delayed_payments else 0

    _update_participant_paid_amount(db, project_id, user_id)
    db.commit()

    return {
        "project_id": project_id,
        "user_id": user_id,
        "total_scheduled_amount": total_scheduled_amount,
        "total_due_amount": total_due_amount,
        "total_paid_amount": total_paid_amount,
        "unpaid_amount": unpaid_amount,
        "due_unpaid_amount": due_unpaid_amount,
        "accrued_penalty_amount": accrued_penalty_amount,
        "payment_completion_ratio": payment_completion_ratio,
        "due_payment_completion_ratio": due_payment_completion_ratio,
        "total_payments": len(installment_payments),
        "paid_on_time_count": paid_on_time_count,
        "paid_late_count": paid_late_count,
        "unpaid_count": unpaid_count,
        "overdue_count": overdue_count,
        "prepaid_installment_count": prepaid_installment_count,
        "prepaid_amount": prepaid_amount,
        "unused_prepayment_count": len(unused_prepayments),
        "unused_prepayment_amount": _money(sum(float(p.amount or 0) for p in unused_prepayments)),
        "average_delay_days": average_delay_days,
        "max_delay_days": max_delay_days,
    }


def calculate_next_payment_round(
    db: Session,
    project_id: int,
    due_date: date,
    installment_count: int | None = None,
    extra_cost_total: float = 0,
    as_of_date: date | None = None,
):
    project = _get_project(db, project_id)
    effective_installment_count = _effective_installment_count(
        db, project_id, installment_count
    )
    round_state = _validate_round_slot(
        db,
        project_id=project_id,
        due_date=due_date,
        installment_count=effective_installment_count,
    )
    if extra_cost_total < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extra cost share cannot be negative.",
        )

    participants = (
        db.query(ProjectParticipant)
        .filter(ProjectParticipant.project_id == project_id)
        .all()
    )
    if not participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has no participants.",
        )

    reference_date = as_of_date or due_date
    members = []

    for participant in participants:
        user = db.query(User).filter(User.id == participant.user_id).first()
        if not user:
            continue

        base_installment = _calculate_base_installment(
            project=project,
            participant=participant,
            installment_count=effective_installment_count,
        )
        extra_cost_share_amount = _calculate_extra_cost_share(
            db,
            project_id=project_id,
            participant=participant,
            extra_cost_total=extra_cost_total,
        )

        member_payments = (
            db.query(Payment)
            .filter(
                Payment.project_id == project_id,
                Payment.user_id == participant.user_id,
            )
            .all()
        )
        for payment in member_payments:
            _refresh_payment_status(payment)

        installment_payments = [p for p in member_payments if p.payment_type == "installment"]
        previous_unpaid = [
            p for p in installment_payments if p.paid_date is None and p.due_date < due_date
        ]
        previous_overdue_amount = _money(sum(float(p.amount or 0) for p in previous_unpaid))

        current_installment = next(
            (p for p in installment_payments if p.due_date == due_date),
            None,
        )
        current_installment_due = 0.0
        if current_installment is None:
            current_installment_due = base_installment
        elif current_installment.paid_date is None:
            current_installment_due = float(current_installment.amount or 0)

        unused_credits = [p for p in member_payments if p.payment_type == "prepayment"]
        credit_amount = 0.0
        if current_installment is None and unused_credits:
            credit_amount = min(base_installment, float(unused_credits[0].amount or 0))

        current_cost_share = next(
            (
                p
                for p in member_payments
                if p.payment_type == "cost_share" and p.due_date == due_date
            ),
            None,
        )
        if current_cost_share is not None:
            extra_cost_share_amount = (
                0.0 if current_cost_share.paid_date is not None else float(current_cost_share.amount or 0)
            )

        late_penalty_amount = _money(
            sum(_payment_penalty(p, reference_date) for p in previous_unpaid)
        )
        if current_installment_due > credit_amount and reference_date > due_date:
            late_penalty_amount += calculate_simple_late_penalty(
                principal=current_installment_due - credit_amount,
                due_date=due_date,
                as_of_date=reference_date,
                monthly_rate=FIXED_LATE_PENALTY_RATE,
            )
            late_penalty_amount = _money(late_penalty_amount)

        total_due_amount = _money(
            previous_overdue_amount
            + max(current_installment_due - credit_amount, 0.0)
            + late_penalty_amount
            + extra_cost_share_amount
        )

        late_paid_payments = [p for p in installment_payments if p.status == "paid_late"]
        overdue_now = [p for p in installment_payments if p.status == "overdue"]
        overdue_months_max = max(
            [overdue_calendar_months(p.due_date, reference_date) for p in previous_unpaid]
            + [0]
        )

        members.append({
            "project_id": project_id,
            "user_id": participant.user_id,
            "full_name": user.full_name,
            "email": user.email,
            "reserved_units": float(participant.reserved_units or 1),
            "base_installment": base_installment,
            "previous_overdue_amount": previous_overdue_amount,
            "late_penalty_amount": late_penalty_amount,
            "extra_cost_share_amount": _money(extra_cost_share_amount),
            "credit_amount": _money(credit_amount),
            "total_due_amount": total_due_amount,
            "late_paid_count": len(late_paid_payments),
            "overdue_count": len(overdue_now),
            "unpaid_due_count": len(previous_unpaid),
            "overdue_months_max": overdue_months_max,
            "unused_prepayment_count": len(unused_credits),
        })

    db.commit()

    return {
        "project_id": project_id,
        "project_name": project.name,
        "due_date": due_date,
        "installment_count": effective_installment_count,
        "round_number": round_state["round_number"],
        "created_rounds": round_state["created_rounds"],
        "rounds_remaining_after_generation": round_state["rounds_remaining_after_generation"],
        "is_existing_round": round_state["is_existing_round"],
        "fixed_late_penalty_rate": FIXED_LATE_PENALTY_RATE,
        "extra_cost_total": _money(extra_cost_total),
        "members": members,
        "total_base_installment": _money(sum(m["base_installment"] for m in members)),
        "total_previous_overdue": _money(sum(m["previous_overdue_amount"] for m in members)),
        "total_late_penalty": _money(sum(m["late_penalty_amount"] for m in members)),
        "total_extra_cost_share": _money(sum(m["extra_cost_share_amount"] for m in members)),
        "total_credit_amount": _money(sum(m["credit_amount"] for m in members)),
        "total_due_amount": _money(sum(m["total_due_amount"] for m in members)),
    }


def calculate_next_member_due(
    db: Session,
    project_id: int,
    user_id: int,
    due_date: date,
    installment_count: int | None = None,
    extra_cost_total: float = 0,
    as_of_date: date | None = None,
):
    preview = calculate_next_payment_round(
        db=db,
        project_id=project_id,
        due_date=due_date,
        installment_count=installment_count,
        extra_cost_total=extra_cost_total,
        as_of_date=as_of_date,
    )
    for member in preview["members"]:
        if int(member["user_id"]) == int(user_id):
            return {
                **member,
                "project_name": preview["project_name"],
                "due_date": preview["due_date"],
                "installment_count": preview["installment_count"],
                "fixed_late_penalty_rate": preview["fixed_late_penalty_rate"],
            }
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Member is not assigned to this project.",
    )


def _consume_prepayment_for_round(
    db: Session,
    *,
    project_id: int,
    user_id: int,
    due_date: date,
    base_installment: float,
    description: str | None,
) -> Payment | None:
    credit = (
        db.query(Payment)
        .filter(
            Payment.project_id == project_id,
            Payment.user_id == user_id,
            Payment.payment_type == "prepayment",
            Payment.paid_date.isnot(None),
        )
        .order_by(Payment.paid_date.asc(), Payment.id.asc())
        .first()
    )
    if not credit:
        return None

    if abs(float(credit.amount or 0) - float(base_installment)) > INSTALLMENT_AMOUNT_TOLERANCE:
        return None

    original_paid_date = credit.paid_date
    credit.payment_type = "installment"
    credit.amount = _money(base_installment)
    credit.due_date = due_date
    credit.description = (
        "Prepaid installment applied to generated round"
        + (f" | {description}" if description else "")
    )
    credit.paid_date = original_paid_date
    _refresh_payment_status(credit)
    db.flush()
    return credit


def generate_next_payment_round(
    db: Session,
    project_id: int,
    due_date: date,
    installment_count: int | None = None,
    extra_cost_total: float = 0,
    description: str | None = None,
):
    _get_project(db, project_id)
    # Preview validates owner-selected installment count, round capacity and due-date ordering
    # before a new plan is persisted. This avoids leaving a half-created plan after a bad request.
    preview = calculate_next_payment_round(
        db=db,
        project_id=project_id,
        due_date=due_date,
        installment_count=installment_count,
        extra_cost_total=extra_cost_total,
        as_of_date=due_date,
    )
    _resolve_payment_plan(
        db,
        project_id,
        preview["installment_count"],
        create_if_missing=True,
    )

    generated_payment_ids: list[int] = []
    consumed_prepayment_ids: list[int] = []
    skipped_count = 0

    for member in preview["members"]:
        member_created = False
        existing_installment = (
            db.query(Payment)
            .filter(
                Payment.project_id == project_id,
                Payment.user_id == member["user_id"],
                Payment.due_date == due_date,
                Payment.payment_type == "installment",
            )
            .first()
        )

        if not existing_installment:
            consumed = _consume_prepayment_for_round(
                db,
                project_id=project_id,
                user_id=member["user_id"],
                due_date=due_date,
                base_installment=float(member["base_installment"]),
                description=description,
            )
            if consumed:
                generated_payment_ids.append(consumed.id)
                consumed_prepayment_ids.append(consumed.id)
                member_created = True
            else:
                new_installment = Payment(
                    project_id=project_id,
                    user_id=member["user_id"],
                    amount=_money(member["base_installment"]),
                    due_date=due_date,
                    paid_date=None,
                    status="unpaid",
                    delay_days=0,
                    payment_type="installment",
                    description=description or "Generated base installment",
                )
                _refresh_payment_status(new_installment)
                db.add(new_installment)
                db.flush()
                generated_payment_ids.append(new_installment.id)
                member_created = True

        extra_share = float(member["extra_cost_share_amount"] or 0)
        if extra_share > INSTALLMENT_AMOUNT_TOLERANCE:
            existing_cost_share = (
                db.query(Payment)
                .filter(
                    Payment.project_id == project_id,
                    Payment.user_id == member["user_id"],
                    Payment.due_date == due_date,
                    Payment.payment_type == "cost_share",
                )
                .first()
            )
            if not existing_cost_share:
                cost_share = Payment(
                    project_id=project_id,
                    user_id=member["user_id"],
                    amount=_money(extra_share),
                    due_date=due_date,
                    paid_date=None,
                    status="unpaid",
                    delay_days=0,
                    payment_type="cost_share",
                    description=description or "Generated extra cost share",
                )
                _refresh_payment_status(cost_share)
                db.add(cost_share)
                db.flush()
                generated_payment_ids.append(cost_share.id)
                member_created = True

        if not member_created:
            skipped_count += 1

    db.commit()

    for member in preview["members"]:
        _update_participant_paid_amount(db, project_id, member["user_id"])
    db.commit()

    preview["generated_count"] = len(generated_payment_ids)
    preview["skipped_count"] = skipped_count
    preview["generated_payment_ids"] = generated_payment_ids
    preview["consumed_prepayment_ids"] = consumed_prepayment_ids
    return preview


def record_installment_payment(
    db: Session,
    *,
    project_id: int,
    user_id: int,
    amount: float,
    due_date: date,
    paid_date: date,
    installment_count: int | None = None,
    extra_cost_total: float = 0,
    description: str | None = None,
):
    if paid_date > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paid date cannot be in the future.",
        )
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than zero.",
        )

    project = _get_project(db, project_id)
    _get_user(db, user_id)
    participant = _get_participant(db, project_id, user_id)
    plan = _resolve_payment_plan(
        db,
        project_id,
        installment_count,
        create_if_missing=False,
    )
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "This project has no payment plan yet. "
                "The owner must choose the installment count and generate the first payment round before recording installment payments."
            ),
        )
    effective_count = int(plan.installment_count)
    base_installment = _calculate_base_installment(
        project=project,
        participant=participant,
        installment_count=effective_count,
    )

    current_installment = (
        db.query(Payment)
        .filter(
            Payment.project_id == project_id,
            Payment.user_id == user_id,
            Payment.due_date == due_date,
            Payment.payment_type == "installment",
        )
        .first()
    )
    if current_installment is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No scheduled installment exists for this due date. "
                "Generate the payment round first, then record the member payment."
            ),
        )
    if current_installment.paid_date is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This installment is already paid; another payment cannot be applied to the same round.",
        )

    extra_share = _calculate_extra_cost_share(
        db,
        project_id=project_id,
        participant=participant,
        extra_cost_total=extra_cost_total,
    )
    if extra_share > INSTALLMENT_AMOUNT_TOLERANCE:
        current_cost_share = (
            db.query(Payment)
            .filter(
                Payment.project_id == project_id,
                Payment.user_id == user_id,
                Payment.due_date == due_date,
                Payment.payment_type == "cost_share",
            )
            .first()
        )
        if not current_cost_share:
            current_cost_share = Payment(
                project_id=project_id,
                user_id=user_id,
                amount=extra_share,
                due_date=due_date,
                paid_date=None,
                status="unpaid",
                delay_days=0,
                payment_type="cost_share",
                description=description or "Extra cost share recorded with installment payment",
            )
            db.add(current_cost_share)
            db.flush()

    due_obligations = (
        db.query(Payment)
        .filter(
            Payment.project_id == project_id,
            Payment.user_id == user_id,
            Payment.payment_type.in_(["installment", "cost_share"]),
            Payment.paid_date.is_(None),
            Payment.due_date <= due_date,
        )
        .order_by(Payment.due_date.asc(), Payment.id.asc())
        .all()
    )

    principal_due = _money(sum(float(p.amount or 0) for p in due_obligations))
    penalty_due = _money(
        sum(_payment_penalty(p, paid_date) for p in due_obligations if p.payment_type == "installment")
    )
    required_due = _money(principal_due + penalty_due)
    provided = _money(amount)

    if provided + INSTALLMENT_AMOUNT_TOLERANCE < required_due:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Installment underpayment is not allowed. "
                f"Current required amount is {round(required_due)} "
                f"(principal {round(principal_due)} + penalty {round(penalty_due)}), "
                f"but received {round(provided)}."
            ),
        )

    extra = _money(provided - required_due)
    prepaid_count = 0
    if extra > INSTALLMENT_AMOUNT_TOLERANCE:
        if base_installment <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Base installment amount is invalid.",
            )
        prepaid_count = int(round(extra / base_installment))
        expected_extra = _money(prepaid_count * base_installment)
        if prepaid_count <= 0 or abs(extra - expected_extra) > INSTALLMENT_AMOUNT_TOLERANCE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Arbitrary overpayment is not allowed. After paying the current due amount, "
                    "any extra amount must equal a whole number of future base installments. "
                    f"Current due: {round(required_due)}; base installment: {round(base_installment)}. "
                    f"Examples of valid totals are {round(required_due)}, "
                    f"{round(required_due + base_installment)}, "
                    f"{round(required_due + 2 * base_installment)}."
                ),
            )

    existing_installment_dates = {
        row[0]
        for row in (
            db.query(Payment.due_date)
            .filter(
                Payment.project_id == project_id,
                Payment.user_id == user_id,
                Payment.payment_type == "installment",
            )
            .distinct()
            .all()
        )
        if row[0] is not None
    }
    existing_prepayment_count = (
        db.query(Payment)
        .filter(
            Payment.project_id == project_id,
            Payment.user_id == user_id,
            Payment.payment_type == "prepayment",
        )
        .count()
    )
    remaining_future_slots = max(
        effective_count - len(existing_installment_dates) - existing_prepayment_count,
        0,
    )
    if prepaid_count > remaining_future_slots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"This member can prepay at most {remaining_future_slots} more installment(s) "
                f"under the owner-defined {effective_count}-installment plan. "
                f"The submitted amount attempts to prepay {prepaid_count}."
            ),
        )

    settled_ids: list[int] = []
    for obligation in due_obligations:
        obligation.paid_date = paid_date
        _refresh_payment_status(obligation)
        settled_ids.append(obligation.id)

    penalty_payment = None
    if penalty_due > INSTALLMENT_AMOUNT_TOLERANCE:
        penalty_payment = _create_penalty_payment(
            db,
            project_id=project_id,
            user_id=user_id,
            amount=penalty_due,
            paid_date=paid_date,
            description=(
                f"Monthly late penalty ({FIXED_LATE_PENALTY_RATE * 100:.0f}% simple per overdue month) "
                f"for {len([p for p in due_obligations if p.payment_type == 'installment' and paid_date > p.due_date])} late installment(s)"
            ),
        )

    prepayment_ids: list[int] = []
    for index in range(prepaid_count):
        prepayment = Payment(
            project_id=project_id,
            user_id=user_id,
            amount=base_installment,
            due_date=paid_date,
            paid_date=paid_date,
            status="paid",
            delay_days=0,
            payment_type="prepayment",
            description=(
                description
                or f"Advance payment for future installment {index + 1} of {prepaid_count}"
            ),
        )
        db.add(prepayment)
        db.flush()
        prepayment_ids.append(prepayment.id)

    db.commit()
    _update_participant_paid_amount(db, project_id, user_id)
    db.commit()

    message = (
        f"Payment recorded: {round(principal_due)} applied to due principal"
        + (f", {round(penalty_due)} paid as late penalty" if penalty_due > 0 else "")
        + (
            f", and {prepaid_count} future installment(s) prepaid."
            if prepaid_count > 0
            else "."
        )
    )

    return {
        "project_id": project_id,
        "user_id": user_id,
        "amount_received": provided,
        "required_due_amount": required_due,
        "principal_settled_amount": principal_due,
        "penalty_paid_amount": penalty_due,
        "prepaid_installments_count": prepaid_count,
        "prepaid_amount": _money(prepaid_count * base_installment),
        "base_installment": base_installment,
        "settled_payment_ids": settled_ids,
        "prepayment_payment_ids": prepayment_ids,
        "penalty_payment_id": penalty_payment.id if penalty_payment else None,
        "message": message,
    }
