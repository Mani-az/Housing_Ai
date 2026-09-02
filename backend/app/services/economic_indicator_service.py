from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.economic_indicator import EconomicIndicator


def get_economic_indicators(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    year: int | None = None,
):
    query = db.query(EconomicIndicator)

    if year:
        query = query.filter(EconomicIndicator.year == year)

    return (
        query
        .order_by(EconomicIndicator.year.desc(), EconomicIndicator.month.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_economic_indicator_summary(db: Session):
    latest_record = (
        db.query(EconomicIndicator)
        .order_by(EconomicIndicator.year.desc(), EconomicIndicator.month.desc())
        .first()
    )

    result = (
        db.query(
            func.count(EconomicIndicator.id).label("total_records"),
            func.avg(EconomicIndicator.general_inflation_rate).label("average_general_inflation_rate"),
            func.avg(EconomicIndicator.housing_growth_rate).label("average_housing_growth_rate"),
            func.avg(EconomicIndicator.construction_cost_growth).label("average_construction_cost_growth"),
            func.avg(EconomicIndicator.transaction_volume_growth).label("average_transaction_volume_growth"),
            func.avg(EconomicIndicator.usd_growth).label("average_usd_growth"),
        )
        .first()
    )

    return {
        "total_records": result.total_records,
        "latest_year": latest_record.year if latest_record else None,
        "latest_month": latest_record.month if latest_record else None,
        "average_general_inflation_rate": result.average_general_inflation_rate,
        "average_housing_growth_rate": result.average_housing_growth_rate,
        "average_construction_cost_growth": result.average_construction_cost_growth,
        "average_transaction_volume_growth": result.average_transaction_volume_growth,
        "average_usd_growth": result.average_usd_growth,
    }