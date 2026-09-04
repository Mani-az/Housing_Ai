from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from datetime import date
from app.models.economic_indicator import EconomicIndicator
from app.ml.forecast_service import forecast_economic_indicators
from app.models.project import Project
from app.models.property_listing import PropertyListing
from app.schemas.project import ProjectCreate
from app.models.project_participant import ProjectParticipant
from app.models.payment import Payment
from app.models.expense import Expense
from app.models.risk_data import RiskPredictionData
from app.models.project_owner import ProjectOwnerAssignment
from app.models.payment_plan import PaymentPlan
from app.models.membership_request import MembershipRequest


def create_project(db: Session, project_data: ProjectCreate) -> Project:
    new_project = Project(
        name=project_data.name,
        location=project_data.location,
        neighborhood_english=project_data.neighborhood_english,
        total_units=project_data.total_units,
        average_unit_area=project_data.average_unit_area,
        estimated_total_cost=project_data.estimated_total_cost,
        start_date=project_data.start_date,
        expected_end_date=project_data.expected_end_date,
        status=project_data.status,
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


def get_projects(db: Session) -> list[Project]:
    projects = db.query(Project).order_by(Project.id.desc()).all()
    _attach_marketplace_metrics(db, projects)
    return projects


def get_project_by_id(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    _attach_marketplace_metrics(db, [project])
    return project


def _attach_marketplace_metrics(db: Session, projects: list[Project]) -> None:
    """Attach backend-derived metrics shared by Owner and Member views.

    The existing Owner table calls this value payment progress: collected
    principal divided by collected principal plus outstanding principal. Fee
    (penalty) rows are intentionally excluded, while accrued penalties on
    overdue installments remain part of the outstanding amount.
    """
    if not projects:
        return

    project_ids = [project.id for project in projects]
    payments = db.query(Payment).filter(Payment.project_id.in_(project_ids)).all()
    participants = (
        db.query(ProjectParticipant.project_id, ProjectParticipant.reserved_units)
        .filter(ProjectParticipant.project_id.in_(project_ids))
        .all()
    )
    payment_by_project: dict[int, list[Payment]] = {}
    for payment in payments:
        payment_by_project.setdefault(payment.project_id, []).append(payment)

    reserved_by_project: dict[int, float] = {}
    for project_id, reserved_units in participants:
        reserved_by_project[project_id] = reserved_by_project.get(project_id, 0.0) + float(reserved_units or 0)

    today = date.today()
    for project in projects:
        collected = 0.0
        outstanding = 0.0
        for payment in payment_by_project.get(project.id, []):
            if str(payment.payment_type or "installment").lower() == "penalty":
                continue
            amount = float(payment.amount or 0)
            if payment.paid_date is not None:
                collected += amount
            else:
                outstanding += amount
                if payment.due_date and today > payment.due_date:
                    outstanding += float(payment.accrued_penalty_amount or 0)

        scheduled = collected + outstanding
        progress = (collected / scheduled * 100) if scheduled > 0 else 0.0
        # Pydantic's from_attributes reads these attributes from the ORM
        # instance without adding denormalized columns to the database.
        project.payment_progress = round(progress, 2)
        project.progress = round(progress, 2)
        project.available_units = max(
            int(project.total_units or 0) - int(reserved_by_project.get(project.id, 0.0)),
            0,
        )


def delete_project(db: Session, project_id: int) -> None:
    """Delete a project and all records that depend on it."""
    project = get_project_by_id(db=db, project_id=project_id)

    try:
        # These tables have non-null project foreign keys and no database-level
        # cascade, so remove dependent records before the parent row.
        for model in (
            Payment,
            Expense,
            RiskPredictionData,
            ProjectParticipant,
            ProjectOwnerAssignment,
            MembershipRequest,
            PaymentPlan,
        ):
            db.query(model).filter(model.project_id == project_id).delete(
                synchronize_session=False
            )

        db.delete(project)
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_project_market_estimate(db: Session, project_id: int):
    project = get_project_by_id(db=db, project_id=project_id)

    if not project.neighborhood_english:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project neighborhood_english is required for market estimation.",
        )

    if not project.average_unit_area:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project average_unit_area is required for market estimation.",
        )

    market_stats = (
        db.query(
            func.count(PropertyListing.id).label("market_samples_used"),
            func.avg(PropertyListing.adjusted_price_per_square_meter).label(
                "average_adjusted_price_per_meter"
            ),
        )
        .filter(
            PropertyListing.neighborhood_english.ilike(
                f"%{project.neighborhood_english}%"
            )
        )
        .first()
    )

    if not market_stats or market_stats.market_samples_used == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No market data found for this project neighborhood.",
        )

    average_price_per_meter = market_stats.average_adjusted_price_per_meter

    estimated_unit_price = average_price_per_meter * project.average_unit_area
    estimated_total_project_value = estimated_unit_price * project.total_units

    return {
        "project_id": project.id,
        "project_name": project.name,
        "location": project.location,
        "neighborhood_english": project.neighborhood_english,
        "total_units": project.total_units,
        "average_unit_area": project.average_unit_area,
        "average_adjusted_price_per_meter": average_price_per_meter,
        "estimated_unit_price": estimated_unit_price,
        "estimated_total_project_value": estimated_total_project_value,
        "market_samples_used": market_stats.market_samples_used,
    }


def _compound_value(value: float, annual_rate_percent: float, years: int) -> float:
    return value * ((1 + annual_rate_percent / 100) ** years)


def _calculate_market_condition(real_housing_growth: float | None) -> str:
    if real_housing_growth is None:
        return "unknown"

    if real_housing_growth < -5:
        return "real_value_decline"

    if -5 <= real_housing_growth <= 5:
        return "real_value_stagnation"

    return "real_value_growth"


def _calculate_cost_overrun_risk(construction_growth: float | None) -> str:
    if construction_growth is None:
        return "unknown"

    if construction_growth >= 60:
        return "high"

    if construction_growth >= 35:
        return "medium"

    return "low"


def _calculate_margin_ratio(
    future_total_project_value: float | None,
    future_construction_cost: float | None,
) -> float | None:
    if future_total_project_value is None or future_construction_cost is None:
        return None

    if future_total_project_value == 0:
        return None

    margin = future_total_project_value - future_construction_cost

    return (margin / future_total_project_value) * 100


def _calculate_financial_feasibility(margin_ratio: float | None) -> str:
    if margin_ratio is None:
        return "unknown"

    if margin_ratio < 0:
        return "not_feasible"

    if 0 <= margin_ratio < 10:
        return "feasible_but_tight"

    if 10 <= margin_ratio < 25:
        return "feasible"

    return "strongly_feasible"


def _calculate_overall_project_risk(
    margin_ratio: float | None,
    cost_overrun_risk: str,
    market_condition: str,
) -> str:
    if margin_ratio is None:
        return "unknown"

    if margin_ratio < 0:
        return "high"

    if margin_ratio < 10:
        return "medium_high"

    if cost_overrun_risk == "high" and market_condition in [
        "real_value_decline",
        "real_value_stagnation",
    ]:
        return "medium"

    if cost_overrun_risk == "high":
        return "medium"

    if cost_overrun_risk == "medium":
        return "medium_low"

    return "low"


def _generate_recommendation(
    financial_feasibility: str,
    overall_project_risk: str,
    cost_overrun_risk: str,
    market_condition: str,
) -> str:
    if financial_feasibility == "not_feasible":
        return (
            "The project is not financially feasible under the current forecast. "
            "Consider reducing construction cost, increasing unit price, or shortening delivery time."
        )

    if financial_feasibility == "feasible_but_tight":
        return (
            "The project is feasible but has a tight margin. "
            "Cost control and shorter delivery time are strongly recommended."
        )

    if overall_project_risk in ["medium", "medium_high"] and cost_overrun_risk == "high":
        return (
            "The project is financially feasible, but construction cost growth is a major risk. "
            "Use phased purchasing, supplier contracts, and contingency budgeting."
        )

    if market_condition == "real_value_stagnation":
        return (
            "The project is feasible, but real market growth is weak. "
            "Avoid overpricing and keep delivery time under control."
        )

    return (
        "The project appears financially acceptable under the current forecast, "
        "but market and construction cost assumptions should be reviewed regularly."
    )


def get_project_future_estimate(
    db: Session,
    project_id: int,
    years: int = 2,
):
    if years < 1:
        years = 1

    if years > 5:
        years = 5

    current_market_estimate = get_project_market_estimate(
        db=db,
        project_id=project_id,
    )

    project = get_project_by_id(db=db, project_id=project_id)

    forecast = forecast_economic_indicators(db=db, years=years)

    predicted_general_inflation = forecast.get("predicted_general_inflation_rate")
    predicted_housing_growth = forecast.get("predicted_housing_cpi_growth")
    predicted_construction_growth = forecast.get("predicted_construction_cost_growth")
    predicted_usd_growth = forecast.get("predicted_usd_growth")

    current_unit_price = current_market_estimate.get("estimated_unit_price")
    current_total_project_value = current_market_estimate.get(
        "estimated_total_project_value"
    )

    future_unit_price = None
    future_total_project_value = None

    if current_unit_price is not None and predicted_housing_growth is not None:
        future_unit_price = _compound_value(
            value=current_unit_price,
            annual_rate_percent=predicted_housing_growth,
            years=years,
        )

    if current_total_project_value is not None and predicted_housing_growth is not None:
        future_total_project_value = _compound_value(
            value=current_total_project_value,
            annual_rate_percent=predicted_housing_growth,
            years=years,
        )

    future_construction_cost = None

    if predicted_construction_growth is not None:
        future_construction_cost = _compound_value(
            value=project.estimated_total_cost,
            annual_rate_percent=predicted_construction_growth,
            years=years,
        )

    real_housing_growth = None

    if predicted_housing_growth is not None and predicted_general_inflation is not None:
        real_housing_growth = (
            ((1 + predicted_housing_growth / 100) /
             (1 + predicted_general_inflation / 100))
            - 1
        ) * 100

    estimated_project_margin = None

    if future_total_project_value is not None and future_construction_cost is not None:
        estimated_project_margin = future_total_project_value - future_construction_cost

    market_condition = _calculate_market_condition(real_housing_growth)
    cost_overrun_risk = _calculate_cost_overrun_risk(predicted_construction_growth)

    margin_ratio_percent = _calculate_margin_ratio(
        future_total_project_value=future_total_project_value,
        future_construction_cost=future_construction_cost,
    )

    financial_feasibility = _calculate_financial_feasibility(
        margin_ratio=margin_ratio_percent,
    )

    overall_project_risk = _calculate_overall_project_risk(
        margin_ratio=margin_ratio_percent,
        cost_overrun_risk=cost_overrun_risk,
        market_condition=market_condition,
    )

    recommendation = _generate_recommendation(
        financial_feasibility=financial_feasibility,
        overall_project_risk=overall_project_risk,
        cost_overrun_risk=cost_overrun_risk,
        market_condition=market_condition,
    )

    return {
        "project_id": project.id,
        "project_name": project.name,
        "neighborhood_english": project.neighborhood_english,
        "delivery_horizon_years": years,

        "current_estimated_unit_price": current_unit_price,
        "current_estimated_total_project_value": current_total_project_value,

        "current_estimated_construction_cost": project.estimated_total_cost,
        "future_estimated_construction_cost": future_construction_cost,

        "predicted_general_inflation_rate": predicted_general_inflation,
        "predicted_housing_growth_rate": predicted_housing_growth,
        "predicted_construction_cost_growth": predicted_construction_growth,
        "predicted_usd_growth": predicted_usd_growth,

        "future_estimated_unit_price": future_unit_price,
        "future_estimated_total_project_value": future_total_project_value,

        "real_housing_growth_estimate": real_housing_growth,
        "estimated_project_margin": estimated_project_margin,
        "margin_ratio_percent": margin_ratio_percent,

        "market_condition": market_condition,
        "cost_overrun_risk": cost_overrun_risk,
        "financial_feasibility": financial_feasibility,
        "overall_project_risk": overall_project_risk,
        "recommendation": recommendation,

        "model_note": forecast.get("model_note"),
    }

def calculate_annual_cost_split(
    db: Session,
    project_id: int,
    year: int,
    annual_cost: float,
):
    project = get_project_by_id(db=db, project_id=project_id)

    if annual_cost <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="annual_cost must be greater than zero.",
        )

    participants = (
        db.query(ProjectParticipant)
        .filter(ProjectParticipant.project_id == project.id)
        .all()
    )

    if not participants:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No participants found for this project.",
        )

    participants_with_share = [
        participant
        for participant in participants
        if participant.share_percent is not None
    ]

    if len(participants_with_share) != len(participants):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All participants must have share_percent for share-based allocation.",
        )

    total_registered_share_percent = sum(
        participant.share_percent
        for participant in participants
        if participant.share_percent is not None
    )

    if total_registered_share_percent <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total registered share_percent must be greater than zero.",
        )

    members = []

    for participant in participants:
        allocated_amount = annual_cost * (participant.share_percent / 100)

        members.append(
            {
                "user_id": participant.user_id,
                "role": participant.role,
                "share_percent": participant.share_percent,
                "reserved_units": participant.reserved_units,
                "allocated_amount": allocated_amount,
            }
        )

    allocated_total_amount = sum(member["allocated_amount"] for member in members)
    unallocated_amount = annual_cost - allocated_total_amount

    return {
        "project_id": project.id,
        "year": year,
        "annual_cost": annual_cost,
        "allocation_method": "share_percent_of_total_project",
        "total_share_percent": total_registered_share_percent,
        "unallocated_amount": max(float(unallocated_amount), 0.0),
        "participants_count": len(participants),
        "members": members,
    }


def _get_stabilized_construction_growth(
    db: Session,
    raw_ml_growth: float | None,
) -> float | None:
    if raw_ml_growth is None:
        return None

    records = (
        db.query(EconomicIndicator)
        .filter(EconomicIndicator.construction_cost_growth.isnot(None))
        .order_by(EconomicIndicator.year.asc(), EconomicIndicator.month.asc())
        .all()
    )

    historical_values = [
        record.construction_cost_growth
        for record in records
        if record.construction_cost_growth is not None
    ]

    if len(historical_values) < 6:
        return raw_ml_growth

    historical_series = sorted(historical_values)
    historical_average = sum(historical_values) / len(historical_values)

    recent_values = historical_values[-6:]
    recent_average = sum(recent_values) / len(recent_values)

    blended_growth = (
        0.30 * raw_ml_growth
        + 0.35 * recent_average
        + 0.35 * historical_average
    )

    lower_index = int(len(historical_series) * 0.10)
    upper_index = int(len(historical_series) * 0.75)

    lower_bound = historical_series[lower_index]
    upper_bound = historical_series[min(upper_index, len(historical_series) - 1)]

    stabilized_growth = max(
        lower_bound,
        min(blended_growth, upper_bound),
    )

    return stabilized_growth


def calculate_next_year_cost_split(
    db: Session,
    project_id: int,
):
    project = get_project_by_id(db=db, project_id=project_id)

    participants = (
        db.query(ProjectParticipant)
        .filter(ProjectParticipant.project_id == project.id)
        .all()
    )

    if not participants:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No participants found for this project.",
        )

    participants_with_share = [
        participant
        for participant in participants
        if participant.share_percent is not None
    ]

    if len(participants_with_share) != len(participants):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All participants must have share_percent for cost allocation.",
        )

    total_registered_share_percent = sum(
        participant.share_percent
        for participant in participants
        if participant.share_percent is not None
    )

    if total_registered_share_percent <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total registered share_percent must be greater than zero.",
        )

    forecast = forecast_economic_indicators(db=db, years=1)

    raw_predicted_construction_growth = forecast.get(
        "predicted_construction_cost_growth"
    )

    predicted_construction_growth = _get_stabilized_construction_growth(
        db=db,
        raw_ml_growth=raw_predicted_construction_growth,
    )

    next_year_estimated_construction_cost = None

    if predicted_construction_growth is not None:
        next_year_estimated_construction_cost = _compound_value(
            value=project.estimated_total_cost,
            annual_rate_percent=predicted_construction_growth,
            years=1,
        )

    current_year = date.today().year
    target_year = current_year + 1

    members = []

    if next_year_estimated_construction_cost is not None:
        for participant in participants:
            required_amount = next_year_estimated_construction_cost * (
                participant.share_percent / 100
            )

            members.append(
                {
                    "user_id": participant.user_id,
                    "role": participant.role,
                    "share_percent": participant.share_percent,
                    "reserved_units": participant.reserved_units,
                    "required_amount": required_amount,
                }
            )

    allocated_total_amount = sum(member["required_amount"] for member in members)

    return {
        "project_id": project.id,
        "project_name": project.name,
        "target_year": target_year,

        "current_construction_cost": project.estimated_total_cost,
        "predicted_construction_cost_growth": predicted_construction_growth,
        "next_year_estimated_construction_cost": next_year_estimated_construction_cost,

        "allocation_method": "share_percent_of_total_project",
        "total_registered_share_percent": total_registered_share_percent,
        "unallocated_amount": max(
            float(next_year_estimated_construction_cost or 0) - float(allocated_total_amount),
            0.0,
        ),
        "participants_count": len(participants),

        "members": members,

        "model_note": (
    (forecast.get("model_note") or "")
    + " Construction cost growth is stabilized using historical average, "
      "recent trend, and percentile-based bounds."
    )
}
