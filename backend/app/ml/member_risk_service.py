from __future__ import annotations

from datetime import date, timedelta
from math import ceil
from statistics import median
from typing import Callable, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ml.forecast_service import forecast_economic_indicators
from app.models.payment import Payment
from app.models.project import Project
from app.models.project_participant import ProjectParticipant
from app.services.payment_service import get_member_payment_summary
from prediction_services_v2 import predict_buyer_risk as predict_buyer_risk_v2


def _emit_progress(
    progress_callback: Optional[Callable[[str, int], None]],
    message: str,
    progress: int,
):
    if progress_callback is not None:
        progress_callback(message, progress)


def _calculate_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator) / float(denominator)


def _get_participant(
    db: Session,
    project_id: int,
    user_id: int,
) -> ProjectParticipant:
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found for this project.",
        )

    return participant


def _get_project(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    return project


def _get_member_payments(
    db: Session,
    project_id: int,
    user_id: int,
) -> list[Payment]:
    return (
        db.query(Payment)
        .filter(
            Payment.project_id == project_id,
            Payment.user_id == user_id,
        )
        .order_by(Payment.due_date.asc(), Payment.id.asc())
        .all()
    )


def _median_payment_interval_days(payments: list[Payment]) -> int:
    unique_due_dates = sorted({
        payment.due_date
        for payment in payments
        if payment.due_date and payment.payment_type == "installment"
    })

    intervals = [
        (current - previous).days
        for previous, current in zip(unique_due_dates, unique_due_dates[1:])
        if (current - previous).days > 0
    ]

    if not intervals:
        return 60

    # Prevent one irregular seed date from creating unrealistic annual estimates.
    return int(max(30, min(round(median(intervals)), 180)))


def _typical_installment_amount(payments: list[Payment]) -> float:
    installment_payments = [p for p in payments if p.payment_type == "installment"]
    usable = [
        float(payment.amount or 0)
        for payment in installment_payments[-5:]
        if float(payment.amount or 0) > 0
    ]

    if not usable:
        return 0.0

    return float(median(usable))


def _remaining_project_months(project: Project, today: date) -> int:
    if not project.expected_end_date or project.expected_end_date <= today:
        return 12

    return max(1, ceil((project.expected_end_date - today).days / 30.4375))


def _group_payments_by_due_date(payments: list[Payment]) -> dict[date, list[Payment]]:
    grouped: dict[date, list[Payment]] = {}

    for payment in payments:
        if not payment.due_date or payment.payment_type != "installment":
            continue
        grouped.setdefault(payment.due_date, []).append(payment)

    return grouped


def _project_round_forecast_context(
    *,
    project: Project,
    payments: list[Payment],
) -> dict[str, int | date | list[date]]:
    """Describe the recorded and inferred payment-round timeline.

    A round is one unique due date for the selected member. Recorded rounds come
    from database payment rows. Forecast rounds are inferred only after the last
    currently scheduled future round, using the median observed interval.
    """
    today = date.today()
    one_year_from_today = today + timedelta(days=365)
    interval_days = _median_payment_interval_days(payments)
    grouped = _group_payments_by_due_date(payments)
    recorded_due_dates = sorted(grouped)

    completed_rounds = sum(
        1
        for due_date in recorded_due_dates
        if grouped[due_date] and all(payment.paid_date is not None for payment in grouped[due_date])
    )
    overdue_rounds = sum(
        1
        for due_date in recorded_due_dates
        if due_date < today and any(payment.paid_date is None for payment in grouped[due_date])
    )
    remaining_recorded_due_dates = [
        due_date
        for due_date in recorded_due_dates
        if any(payment.paid_date is None for payment in grouped[due_date])
    ]

    if project.expected_end_date:
        if project.expected_end_date > today:
            horizon_end = min(one_year_from_today, project.expected_end_date)
            project_end = project.expected_end_date
        else:
            horizon_end = today
            project_end = today
    else:
        horizon_end = one_year_from_today
        project_end = horizon_end

    scheduled_due_dates_next_year = [
        due_date
        for due_date in remaining_recorded_due_dates
        if today <= due_date <= horizon_end
    ]

    next_year_inferred_dates: list[date] = []
    coverage_date = (
        max(scheduled_due_dates_next_year)
        if scheduled_due_dates_next_year
        else today
    )
    next_due_date = coverage_date + timedelta(days=interval_days)

    while next_due_date <= horizon_end and len(next_year_inferred_dates) < 24:
        next_year_inferred_dates.append(next_due_date)
        next_due_date += timedelta(days=interval_days)

    scheduled_due_dates_to_end = [
        due_date
        for due_date in remaining_recorded_due_dates
        if today <= due_date <= project_end
    ]
    remaining_inferred_dates_to_end: list[date] = []
    coverage_to_end = (
        max(scheduled_due_dates_to_end)
        if scheduled_due_dates_to_end
        else today
    )
    next_due_to_end = coverage_to_end + timedelta(days=interval_days)

    while next_due_to_end <= project_end and len(remaining_inferred_dates_to_end) < 60:
        remaining_inferred_dates_to_end.append(next_due_to_end)
        next_due_to_end += timedelta(days=interval_days)

    recorded_rounds_total = len(recorded_due_dates)
    remaining_recorded_rounds = len(remaining_recorded_due_dates)

    if recorded_rounds_total == 0:
        current_round_number = 0
    else:
        started_rounds = sum(
            1 for due_date in recorded_due_dates
            if due_date <= today
        )
        # Before the first due date, the project is considered to be in round 1.
        # After all due dates have passed, it remains on the final recorded round.
        current_round_number = min(
            max(started_rounds, 1),
            recorded_rounds_total,
        )

    return {
        "recorded_rounds_total": recorded_rounds_total,
        "current_round_number": current_round_number,
        "completed_rounds": completed_rounds,
        "remaining_recorded_rounds": remaining_recorded_rounds,
        "overdue_rounds": overdue_rounds,
        "average_payment_interval_days": interval_days if recorded_due_dates else 0,
        "scheduled_rounds_next_12_months": len(scheduled_due_dates_next_year),
        "forecasted_additional_rounds_next_12_months": len(next_year_inferred_dates),
        "forecast_rounds_next_12_months": (
            len(scheduled_due_dates_next_year) + len(next_year_inferred_dates)
        ),
        "estimated_remaining_rounds_to_project_end": (
            overdue_rounds
            + len(scheduled_due_dates_to_end)
            + len(remaining_inferred_dates_to_end)
        ),
        "forecast_horizon_end": horizon_end,
        "scheduled_due_dates_next_year": scheduled_due_dates_next_year,
        "next_year_inferred_dates": next_year_inferred_dates,
    }



def _remaining_member_amount(
    *,
    project: Project,
    participant: ProjectParticipant,
    total_paid_amount: float,
) -> float:
    """Return the member's current estimated contractual balance to project end."""
    share_percent = max(float(participant.share_percent or 0), 0.0)
    contractual_member_total = max(
        float(project.estimated_total_cost or 0) * (share_percent / 100.0),
        0.0,
    )
    return round(
        max(contractual_member_total - float(total_paid_amount or 0), 0.0),
        2,
    )


def _estimate_required_next_year_amount(
    *,
    project: Project,
    participant: ProjectParticipant,
    payments: list[Payment],
    total_paid_amount: float,
    construction_cost_growth: float,
    round_context: dict[str, int | date | list[date]],
) -> float:
    """Estimate the contribution due over the explicitly reported rounds."""
    today = date.today()
    horizon_end = round_context["forecast_horizon_end"]

    share_percent = max(float(participant.share_percent or 0), 0.0)
    contractual_member_total = max(
        float(project.estimated_total_cost or 0) * (share_percent / 100.0),
        0.0,
    )
    remaining_contractual_amount = max(
        contractual_member_total - float(total_paid_amount or 0),
        0.0,
    )

    if remaining_contractual_amount <= 0 or not isinstance(horizon_end, date) or horizon_end <= today:
        return 0.0

    scheduled_dates = set(round_context["scheduled_due_dates_next_year"])
    future_scheduled_amount = sum(
        float(payment.amount or 0)
        for payment in payments
        if (
            payment.due_date in scheduled_dates
            and payment.paid_date is None
            and payment.payment_type in {"installment", "cost_share"}
        )
    )

    typical_installment = _typical_installment_amount(payments)
    missing_rounds = int(
        round_context["forecasted_additional_rounds_next_12_months"]
    )
    estimated_unscheduled_amount = typical_installment * missing_rounds

    # Existing scheduled amounts are already fixed. Only inferred rounds receive
    # a bounded average construction-cost uplift.
    bounded_growth = max(0.0, min(float(construction_cost_growth or 0), 100.0))
    average_year_exposure_multiplier = 1.0 + bounded_growth / 200.0

    cadence_based_estimate = (
        future_scheduled_amount
        + estimated_unscheduled_amount * average_year_exposure_multiplier
    )

    if cadence_based_estimate <= 0:
        remaining_months = _remaining_project_months(project, today)
        next_year_fraction = min(12.0 / remaining_months, 1.0)
        cadence_based_estimate = remaining_contractual_amount * next_year_fraction

    return round(min(cadence_based_estimate, remaining_contractual_amount), 2)


def _build_risk_explanation(
    predicted_label: str,
    reasons: list[str],
) -> str:
    readable_reasons = reasons or ["stable due-payment behavior"]
    return (
        f"Predicted risk is {predicted_label} based on "
        + ", ".join(readable_reasons)
        + "."
    )


def predict_member_financial_risk(
    db: Session,
    project_id: int,
    user_id: int,
    progress_callback: Optional[Callable[[str, int], None]] = None,
):
    _emit_progress(progress_callback, "Loading selected member and project...", 10)

    participant = _get_participant(db=db, project_id=project_id, user_id=user_id)
    project = _get_project(db=db, project_id=project_id)

    _emit_progress(progress_callback, "Reading member payment history...", 25)

    summary = get_member_payment_summary(
        db=db,
        project_id=project_id,
        user_id=user_id,
    )
    payments = _get_member_payments(
        db=db,
        project_id=project_id,
        user_id=user_id,
    )

    if summary.get("total_payments", 0) == 0:
        round_context = _project_round_forecast_context(
            project=project,
            payments=payments,
        )
        required_next_year_amount = _estimate_required_next_year_amount(
            project=project,
            participant=participant,
            payments=payments,
            total_paid_amount=0,
            construction_cost_growth=0,
            round_context=round_context,
        )
        remaining_amount_to_project_end = _remaining_member_amount(
            project=project,
            participant=participant,
            total_paid_amount=0,
        )

        _emit_progress(progress_callback, "Preparing insufficient-history result...", 95)

        return {
            "project_id": project_id,
            "user_id": user_id,
            "share_percent": participant.share_percent or 0,
            "reserved_units": participant.reserved_units,
            "required_next_year_amount": required_next_year_amount,
            "remaining_amount_to_project_end": remaining_amount_to_project_end,
            "recorded_rounds_total": round_context["recorded_rounds_total"],
            "current_round_number": round_context["current_round_number"],
            "completed_rounds": round_context["completed_rounds"],
            "remaining_recorded_rounds": round_context["remaining_recorded_rounds"],
            "overdue_rounds": round_context["overdue_rounds"],
            "average_payment_interval_days": round_context["average_payment_interval_days"],
            "scheduled_rounds_next_12_months": round_context["scheduled_rounds_next_12_months"],
            "forecasted_additional_rounds_next_12_months": round_context["forecasted_additional_rounds_next_12_months"],
            "forecast_rounds_next_12_months": round_context["forecast_rounds_next_12_months"],
            "estimated_remaining_rounds_to_project_end": round_context["estimated_remaining_rounds_to_project_end"],
            "estimated_amount_per_forecast_round": 0,
            "forecast_horizon_end": round_context["forecast_horizon_end"],
            "total_scheduled_amount": 0,
            "total_due_amount": 0,
            "total_paid_amount": 0,
            "unpaid_amount": 0,
            "due_unpaid_amount": 0,
            "payment_completion_ratio": 0,
            "due_payment_completion_ratio": 0,
            "unpaid_amount_ratio": 0,
            "due_unpaid_amount_ratio": 0,
            "paid_late_count": 0,
            "overdue_count": 0,
            "prepaid_installment_count": 0,
            "prepaid_amount": 0,
            "unused_prepayment_count": 0,
            "unused_prepayment_amount": 0,
            "accrued_penalty_amount": 0,
            "average_delay_days": 0,
            "max_delay_days": 0,
            "predicted_risk_label": "insufficient_payment_history",
            "risk_score_estimate": None,
            "model_accuracy": None,
            "risk_explanation": (
                "No payment schedule or payment history exists for this member yet. "
                "Financial risk prediction requires at least one scheduled payment."
            ),
            "model_note": (
                "Member risk prediction was not performed because the member has no "
                "payment history in the system."
            ),
        }

    _emit_progress(progress_callback, "Forecasting 12-month economic pressure...", 45)

    forecast = forecast_economic_indicators(db=db, years=1)

    total_scheduled_amount = float(summary.get("total_scheduled_amount", 0) or 0)
    total_due_amount = float(summary.get("total_due_amount", 0) or 0)
    total_paid_amount = float(summary.get("total_paid_amount", 0) or 0)
    unpaid_amount = float(summary.get("unpaid_amount", 0) or 0)
    due_unpaid_amount = float(summary.get("due_unpaid_amount", 0) or 0)

    unpaid_amount_ratio = _calculate_ratio(unpaid_amount, total_scheduled_amount)
    due_unpaid_amount_ratio = _calculate_ratio(due_unpaid_amount, total_due_amount)

    general_inflation_rate = float(
        forecast.get("predicted_general_inflation_rate") or 0
    )
    construction_cost_growth = float(
        forecast.get("predicted_construction_cost_growth") or 0
    )
    usd_growth = float(forecast.get("predicted_usd_growth") or 0)

    _emit_progress(progress_callback, "Estimating the member's next 12-month contribution...", 60)

    round_context = _project_round_forecast_context(
        project=project,
        payments=payments,
    )
    required_next_year_amount = _estimate_required_next_year_amount(
        project=project,
        participant=participant,
        payments=payments,
        total_paid_amount=total_paid_amount,
        construction_cost_growth=construction_cost_growth,
        round_context=round_context,
    )
    remaining_amount_to_project_end = _remaining_member_amount(
        project=project,
        participant=participant,
        total_paid_amount=total_paid_amount,
    )
    forecast_round_count = int(round_context["forecast_rounds_next_12_months"])
    estimated_amount_per_forecast_round = (
        required_next_year_amount / forecast_round_count
        if forecast_round_count > 0
        else 0.0
    )

    current_construction_cost = float(project.estimated_total_cost or 0)
    next_year_estimated_construction_cost = current_construction_cost * (
        1.0 + construction_cost_growth / 100.0
    )

    features = {
        "total_units": project.total_units or 0,
        "reserved_units": participant.reserved_units,
        "share_percent": participant.share_percent or 0,
        "current_construction_cost": current_construction_cost,
        "construction_cost_growth": construction_cost_growth,
        "next_year_estimated_construction_cost": next_year_estimated_construction_cost,
        "required_next_year_amount": required_next_year_amount,
        "total_scheduled_amount": total_scheduled_amount,
        "total_due_amount": total_due_amount,
        "total_paid_amount": total_paid_amount,
        "unpaid_amount": unpaid_amount,
        "due_unpaid_amount": due_unpaid_amount,
        "payment_completion_ratio": summary.get("payment_completion_ratio", 0),
        "due_payment_completion_ratio": summary.get(
            "due_payment_completion_ratio", 0
        ),
        "unpaid_amount_ratio": unpaid_amount_ratio,
        "due_unpaid_amount_ratio": due_unpaid_amount_ratio,
        "total_payments": summary.get("total_payments", 0),
        "paid_on_time_count": summary.get("paid_on_time_count", 0),
        "paid_late_count": summary.get("paid_late_count", 0),
        "unpaid_count": summary.get("unpaid_count", 0),
        "overdue_count": summary.get("overdue_count", 0),
        "prepaid_installment_count": summary.get("prepaid_installment_count", 0),
        "prepaid_amount": summary.get("prepaid_amount", 0),
        "unused_prepayment_count": summary.get("unused_prepayment_count", 0),
        "unused_prepayment_amount": summary.get("unused_prepayment_amount", 0),
        "accrued_penalty_amount": summary.get("accrued_penalty_amount", 0),
        "average_delay_days": summary.get("average_delay_days", 0),
        "max_delay_days": summary.get("max_delay_days", 0),
        "general_inflation_rate": general_inflation_rate,
        "usd_growth": usd_growth,
    }

    _emit_progress(progress_callback, "Running calibrated member-risk model...", 80)

    v2_result = predict_buyer_risk_v2(features)
    predicted_label = v2_result["risk_label"]
    risk_score_estimate = v2_result["risk_score"]
    model_reasons = v2_result.get("reasons", [])

    _emit_progress(progress_callback, "Preparing member risk response...", 95)

    return {
        "project_id": project_id,
        "user_id": user_id,
        "share_percent": features["share_percent"],
        "reserved_units": features["reserved_units"],
        "required_next_year_amount": features["required_next_year_amount"],
        "remaining_amount_to_project_end": remaining_amount_to_project_end,
        "recorded_rounds_total": round_context["recorded_rounds_total"],
        "current_round_number": round_context["current_round_number"],
        "completed_rounds": round_context["completed_rounds"],
        "remaining_recorded_rounds": round_context["remaining_recorded_rounds"],
        "overdue_rounds": round_context["overdue_rounds"],
        "average_payment_interval_days": round_context["average_payment_interval_days"],
        "scheduled_rounds_next_12_months": round_context["scheduled_rounds_next_12_months"],
        "forecasted_additional_rounds_next_12_months": round_context["forecasted_additional_rounds_next_12_months"],
        "forecast_rounds_next_12_months": round_context["forecast_rounds_next_12_months"],
        "estimated_remaining_rounds_to_project_end": round_context["estimated_remaining_rounds_to_project_end"],
        "estimated_amount_per_forecast_round": round(estimated_amount_per_forecast_round, 2),
        "forecast_horizon_end": round_context["forecast_horizon_end"],
        "total_scheduled_amount": features["total_scheduled_amount"],
        "total_due_amount": features["total_due_amount"],
        "total_paid_amount": features["total_paid_amount"],
        "unpaid_amount": features["unpaid_amount"],
        "due_unpaid_amount": features["due_unpaid_amount"],
        "payment_completion_ratio": features["payment_completion_ratio"],
        "due_payment_completion_ratio": features["due_payment_completion_ratio"],
        "unpaid_amount_ratio": features["unpaid_amount_ratio"],
        "due_unpaid_amount_ratio": features["due_unpaid_amount_ratio"],
        "paid_late_count": features["paid_late_count"],
        "overdue_count": features["overdue_count"],
        "prepaid_installment_count": features["prepaid_installment_count"],
        "prepaid_amount": features["prepaid_amount"],
        "unused_prepayment_count": features["unused_prepayment_count"],
        "unused_prepayment_amount": features["unused_prepayment_amount"],
        "accrued_penalty_amount": features["accrued_penalty_amount"],
        "average_delay_days": features["average_delay_days"],
        "max_delay_days": features["max_delay_days"],
        "predicted_risk_label": predicted_label,
        "risk_score_estimate": risk_score_estimate,
        "model_accuracy": None,
        "risk_explanation": _build_risk_explanation(
            predicted_label=predicted_label,
            reasons=model_reasons,
        ),
        "model_note": (
            "Member financial risk uses the ML v2 score blended with payment-context "
            "rules. The next-12-month contribution explicitly reports how many recorded "
            "and inferred payment rounds it covers, the observed interval, and the "
            "estimated rounds remaining to project end. Only inferred future rounds "
            "receive a bounded construction-cost uplift. "
            "The buyer/member dataset is synthetic and supports prototype scenario "
            f"validation only. Model version: {v2_result.get('model_version')}."
        ),
    }
