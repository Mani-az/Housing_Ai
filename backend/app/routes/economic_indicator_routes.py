from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.economic_indicator import (
    EconomicIndicatorResponse,
    EconomicIndicatorSummaryResponse,
)
from app.services.economic_indicator_service import (
    get_economic_indicators,
    get_economic_indicator_summary,
)


router = APIRouter(
    prefix="/economic-indicators",
    tags=["Economic Indicators"],
)


@router.get("/", response_model=list[EconomicIndicatorResponse])
def read_economic_indicators(
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    year: int | None = None,
    db: Session = Depends(get_db),
):
    return get_economic_indicators(
        db=db,
        skip=skip,
        limit=limit,
        year=year,
    )


@router.get("/summary", response_model=EconomicIndicatorSummaryResponse)
def read_economic_indicator_summary(
    db: Session = Depends(get_db),
):
    return get_economic_indicator_summary(db=db)