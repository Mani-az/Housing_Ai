from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.ml.forecast_service import (
    forecast_economic_indicators,
    evaluate_economic_forecast_model,
)
from app.routes.sse_utils import stream_db_job
from app.schemas.ml_forecast import (
    EconomicForecastResponse,
    EconomicForecastEvaluationResponse,
)


router = APIRouter(
    prefix="/ml",
    tags=["Machine Learning"],
)


@router.get(
    "/forecast/economic-indicators",
    response_model=EconomicForecastResponse,
)
def read_economic_indicator_forecast(
    years: int = Query(default=1, ge=1, le=5),
    months: int | None = Query(default=None, ge=1, le=60),
    db: Session = Depends(get_db),
):
    return forecast_economic_indicators(db=db, years=years, horizon_months=months)


@router.get("/forecast/economic-indicators/stream")
async def stream_economic_indicator_forecast(
    years: int = Query(default=1, ge=1, le=5),
    months: int | None = Query(default=None, ge=1, le=60),
):
    return stream_db_job(
        forecast_economic_indicators,
        done_message="Economic forecast completed.",
        years=years,
        horizon_months=months,
    )


@router.get(
    "/evaluate/economic-indicators",
    response_model=EconomicForecastEvaluationResponse,
)
def read_economic_indicator_model_evaluation(
    db: Session = Depends(get_db),
):
    return evaluate_economic_forecast_model(db=db)
