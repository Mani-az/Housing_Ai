from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EconomicIndicatorResponse(BaseModel):
    id: int
    year: int
    month: int

    general_inflation_rate: Optional[float] = None

    cpi_index: Optional[float] = None
    cpi_yoy_growth_from_index: Optional[float] = None

    housing_cpi_index: Optional[float] = None
    housing_cpi_growth: Optional[float] = None

    producer_price_index: Optional[float] = None
    producer_price_yoy_growth: Optional[float] = None

    construction_cost_growth: Optional[float] = None

    interest_rate: Optional[float] = None

    usd_rate_toman: Optional[float] = None
    usd_rate_irr: Optional[float] = None
    usd_growth: Optional[float] = None

    transaction_volume: Optional[float] = None
    transaction_volume_growth: Optional[float] = None

    avg_price_per_sqm_million_irr: Optional[float] = None
    housing_growth_rate: Optional[float] = None

    source: Optional[str] = None
    notes: Optional[str] = None

    created_at: datetime

    class Config:
        from_attributes = True


class EconomicIndicatorSummaryResponse(BaseModel):
    total_records: int
    latest_year: Optional[int] = None
    latest_month: Optional[int] = None

    average_general_inflation_rate: Optional[float] = None
    average_housing_growth_rate: Optional[float] = None
    average_construction_cost_growth: Optional[float] = None
    average_transaction_volume_growth: Optional[float] = None
    average_usd_growth: Optional[float] = None