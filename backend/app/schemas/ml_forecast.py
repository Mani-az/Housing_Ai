from pydantic import BaseModel
from typing import Optional


class EconomicForecastResponse(BaseModel):
    forecast_horizon_months: int
    forecast_horizon_years: float

    predicted_general_inflation_rate: Optional[float] = None
    predicted_housing_cpi_growth: Optional[float] = None
    predicted_construction_cost_growth: Optional[float] = None
    predicted_usd_growth: Optional[float] = None

    model_note: str


class RegressionMetricResponse(BaseModel):
    mae: Optional[float] = None
    rmse: Optional[float] = None
    r2_score: Optional[float] = None
    train_samples: int
    test_samples: int
    note: str


class EconomicForecastEvaluationResponse(BaseModel):
    general_inflation_rate: RegressionMetricResponse
    housing_cpi_growth: RegressionMetricResponse
    construction_cost_growth: RegressionMetricResponse
    usd_growth: RegressionMetricResponse