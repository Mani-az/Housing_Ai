from typing import Callable, Optional

import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from app.models.economic_indicator import EconomicIndicator
from prediction_services_v2 import forecast_economic_indicators as forecast_economic_indicators_v2


TARGET_COLUMNS = [
    "general_inflation_rate",
    "housing_cpi_growth",
    "construction_cost_growth",
    "usd_growth",
]


def _emit_progress(
    progress_callback: Optional[Callable[[str, int], None]],
    message: str,
    progress: int,
):
    if progress_callback is not None:
        progress_callback(message, progress)


TARGET_FEATURES = {
    "general_inflation_rate": [
        "year",
        "month",
        "general_inflation_rate",
        "cpi_index",
        "producer_price_index",
        "interest_rate",
        "usd_rate_toman",
    ],
    "housing_cpi_growth": [
        "year",
        "month",
        "general_inflation_rate",
        "cpi_index",
        "housing_cpi_index",
        "producer_price_index",
        "interest_rate",
        "usd_rate_toman",
    ],
    "construction_cost_growth": [
        "year",
        "month",
        "general_inflation_rate",
        "cpi_index",
        "producer_price_index",
        "construction_cost_growth",
        "interest_rate",
        "usd_rate_toman",
    ],
    "usd_growth": [
        "year",
        "month",
        "general_inflation_rate",
        "cpi_index",
        "producer_price_index",
        "interest_rate",
        "usd_rate_toman",
        "usd_growth",
    ],
}


def _load_indicators_dataframe(db: Session) -> pd.DataFrame:
    records = (
        db.query(EconomicIndicator)
        .order_by(EconomicIndicator.year.asc(), EconomicIndicator.month.asc())
        .all()
    )

    data = []

    for item in records:
        data.append(
            {
                "year": item.year,
                "month": item.month,
                "general_inflation_rate": item.general_inflation_rate,
                "cpi_index": item.cpi_index,
                "housing_cpi_index": item.housing_cpi_index,
                "housing_cpi_growth": item.housing_cpi_growth,
                "producer_price_index": item.producer_price_index,
                "producer_price_yoy_growth": item.producer_price_yoy_growth,
                "construction_cost_growth": item.construction_cost_growth,
                "interest_rate": item.interest_rate,
                "usd_rate_toman": item.usd_rate_toman,
                "usd_growth": item.usd_growth,
            }
        )

    return pd.DataFrame(data)


def _clean_time_series_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    working_df = df.copy()
    working_df = working_df.sort_values(["year", "month"]).reset_index(drop=True)

    numeric_columns = working_df.select_dtypes(include=["number"]).columns

    # Only carry information forward.  Backward filling (or calculating a
    # median over the full series) would let future observations influence an
    # earlier training row and invalidate chronological evaluation.  Rows that
    # still lack a required value are removed by _build_supervised_dataset.
    working_df[numeric_columns] = working_df[numeric_columns].ffill()

    return working_df


def _add_lag_features(df: pd.DataFrame, target_column: str) -> pd.DataFrame:
    working_df = df.copy()

    working_df[f"{target_column}_lag_1"] = working_df[target_column].shift(1)
    working_df[f"{target_column}_lag_2"] = working_df[target_column].shift(2)
    working_df[f"{target_column}_lag_3"] = working_df[target_column].shift(3)

    working_df[f"{target_column}_rolling_mean_3"] = (
        working_df[target_column]
        .shift(1)
        .rolling(window=3)
        .mean()
    )

    return working_df


def _get_feature_columns_for_target(target_column: str) -> list[str]:
    base_features = TARGET_FEATURES[target_column]

    lag_features = [
        f"{target_column}_lag_1",
        f"{target_column}_lag_2",
        f"{target_column}_lag_3",
        f"{target_column}_rolling_mean_3",
    ]

    return base_features + lag_features


def _build_supervised_dataset(df: pd.DataFrame, target_column: str):
    working_df = _clean_time_series_dataframe(df)
    working_df = _add_lag_features(working_df, target_column)

    working_df[f"next_{target_column}"] = working_df[target_column].shift(-1)

    feature_columns = _get_feature_columns_for_target(target_column)
    required_columns = feature_columns + [f"next_{target_column}"]

    model_df = working_df[required_columns].dropna()

    if len(model_df) < 8:
        return None, None, None

    X = model_df[feature_columns]
    y = model_df[f"next_{target_column}"]

    return X, y, feature_columns


def _candidate_models():
    return {
        "ridge": make_pipeline(
            StandardScaler(),
            Ridge(alpha=1.0),
        ),
        "random_forest": RandomForestRegressor(
            n_estimators=200,
            random_state=42,
            max_depth=6,
            min_samples_leaf=2,
        ),
        "gradient_boosting": GradientBoostingRegressor(
            random_state=42,
            n_estimators=120,
            max_depth=2,
            learning_rate=0.05,
        ),
    }


def _train_best_model(df: pd.DataFrame, target_column: str):
    X, y, feature_columns = _build_supervised_dataset(df, target_column)

    if X is None or y is None or feature_columns is None:
        return None

    if len(X) < 12:
        model = RandomForestRegressor(
            n_estimators=150,
            random_state=42,
            max_depth=5,
            min_samples_leaf=2,
        )
        model.fit(X, y)

        return {
            "model": model,
            "model_name": "random_forest_small_sample",
            "feature_columns": feature_columns,
            "feature_means": X.mean(numeric_only=True),
        }

    split_index = int(len(X) * 0.8)

    X_train = X.iloc[:split_index]
    X_validation = X.iloc[split_index:]
    y_train = y.iloc[:split_index]
    y_validation = y.iloc[split_index:]

    best_model = None
    best_model_name = None
    best_mae = None

    for model_name, model in _candidate_models().items():
        model.fit(X_train, y_train)
        predictions = model.predict(X_validation)
        mae = mean_absolute_error(y_validation, predictions)

        if best_mae is None or mae < best_mae:
            best_mae = mae
            best_model = model
            best_model_name = model_name

    best_model.fit(X, y)

    return {
        "model": best_model,
        "model_name": best_model_name,
        "feature_columns": feature_columns,
        "feature_means": X.mean(numeric_only=True),
    }


def _annual_rate_to_monthly_factor(annual_rate_percent: float) -> float:
    annual_rate = annual_rate_percent / 100
    return (1 + annual_rate) ** (1 / 12)


def _move_to_next_month(year: int, month: int):
    if month == 12:
        return year + 1, 1

    return year, month + 1


def _safe_average(values: list[Optional[float]]) -> Optional[float]:
    clean_values = [value for value in values if value is not None and pd.notna(value)]

    if not clean_values:
        return None

    return float(sum(clean_values) / len(clean_values))


def _build_future_feature_row(
    history_df: pd.DataFrame,
    target_column: str,
    year: int,
    month: int,
    current_values: dict,
    feature_columns: list[str],
    feature_means,
) -> pd.DataFrame:
    row = {
        "year": year,
        "month": month,
        "general_inflation_rate": current_values.get("general_inflation_rate"),
        "cpi_index": current_values.get("cpi_index"),
        "housing_cpi_index": current_values.get("housing_cpi_index"),
        "producer_price_index": current_values.get("producer_price_index"),
        "construction_cost_growth": current_values.get("construction_cost_growth"),
        "interest_rate": current_values.get("interest_rate"),
        "usd_rate_toman": current_values.get("usd_rate_toman"),
        "usd_growth": current_values.get("usd_growth"),
    }

    target_history = history_df[target_column].dropna().tolist()

    row[f"{target_column}_lag_1"] = target_history[-1] if len(target_history) >= 1 else None
    row[f"{target_column}_lag_2"] = target_history[-2] if len(target_history) >= 2 else None
    row[f"{target_column}_lag_3"] = target_history[-3] if len(target_history) >= 3 else None

    if len(target_history) >= 3:
        row[f"{target_column}_rolling_mean_3"] = sum(target_history[-3:]) / 3
    else:
        row[f"{target_column}_rolling_mean_3"] = None

    feature_row = pd.DataFrame([row])
    feature_row = feature_row[feature_columns]
    feature_row = feature_row.fillna(feature_means)

    return feature_row


def forecast_economic_indicators(
    db: Session,
    years: int = 1,
    horizon_months: Optional[int] = None,
    progress_callback: Optional[Callable[[str, int], None]] = None,
):
    _emit_progress(progress_callback, "Validating economic forecast horizon...", 5)

    if horizon_months is not None:
        horizon_months = max(1, min(int(horizon_months), 60))
        years = max(1, min(5, int((horizon_months + 11) // 12)))
    else:
        if years < 1:
            years = 1

        if years > 5:
            years = 5

        horizon_months = years * 12

    _emit_progress(progress_callback, "Loading ML v2 economic forecaster...", 25)
    v2_result = forecast_economic_indicators_v2(horizon_months=horizon_months)

    _emit_progress(progress_callback, "Preparing economic forecast response...", 95)

    forecasts = v2_result.get("forecasts", {})

    def _forecast_value(column: str):
        item = forecasts.get(column) or {}
        return item.get("value")

    confidence_parts = []
    for column, item in forecasts.items():
        confidence_parts.append(
            f"{column}: confidence={item.get('confidence')}, "
            f"last_observed={item.get('last_observed_date')}"
        )

    return {
        "forecast_horizon_months": horizon_months,
        "forecast_horizon_years": years,
        "predicted_general_inflation_rate": _forecast_value("general_inflation_rate"),
        "predicted_housing_cpi_growth": _forecast_value("housing_cpi_growth"),
        "predicted_construction_cost_growth": _forecast_value("construction_cost_growth"),
        "predicted_usd_growth": _forecast_value("usd_growth"),
        "model_note": (
            "ML v2 conservative hybrid economic forecast using real macroeconomic "
            "indicator history, rolling averages, lag behavior, project-horizon-aware "
            "bounded trend adjustment, and stale-data confidence checks. "
            f"Model version: {v2_result.get('model_version')}. "
            + " | ".join(confidence_parts)
        ),
    }

def _evaluate_single_target(df: pd.DataFrame, target_column: str):
    X, y, feature_columns = _build_supervised_dataset(df, target_column)

    if X is None or y is None or feature_columns is None:
        return {
            "mae": None,
            "rmse": None,
            "r2_score": None,
            "train_samples": 0,
            "test_samples": 0,
            "note": "Not enough clean samples for reliable evaluation.",
        }

    if len(X) < 8:
        return {
            "mae": None,
            "rmse": None,
            "r2_score": None,
            "train_samples": len(X),
            "test_samples": 0,
            "note": "Not enough samples for train-test evaluation.",
        }

    split_index = int(len(X) * 0.8)

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]
    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    if len(X_test) == 0:
        return {
            "mae": None,
            "rmse": None,
            "r2_score": None,
            "train_samples": len(X_train),
            "test_samples": 0,
            "note": "No test samples available after train/test split.",
        }

    best_model = None
    best_model_name = None
    best_mae = None

    for model_name, model in _candidate_models().items():
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        mae = mean_absolute_error(y_test, predictions)

        if best_mae is None or mae < best_mae:
            best_mae = mae
            best_model = model
            best_model_name = model_name

    predictions = best_model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    mse = mean_squared_error(y_test, predictions)
    rmse = mse ** 0.5

    if len(y_test) < 2:
        r2 = None
        note = "R² is not available with fewer than 2 test samples."
    else:
        r2 = r2_score(y_test, predictions)
        note = (
            "Evaluation uses chronological 80/20 train-test split, target-specific "
            f"features, lag features, and missing-value imputation. Best model: {best_model_name}."
        )

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "r2_score": float(r2) if r2 is not None else None,
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "note": note,
    }


def evaluate_economic_forecast_model(db: Session):
    df = _load_indicators_dataframe(db=db)

    if df.empty:
        empty_result = {
            "mae": None,
            "rmse": None,
            "r2_score": None,
            "train_samples": 0,
            "test_samples": 0,
            "note": "No economic indicator data found.",
        }

        return {
            "general_inflation_rate": empty_result,
            "housing_cpi_growth": empty_result,
            "construction_cost_growth": empty_result,
            "usd_growth": empty_result,
        }

    return {
        "general_inflation_rate": _evaluate_single_target(
            df=df,
            target_column="general_inflation_rate",
        ),
        "housing_cpi_growth": _evaluate_single_target(
            df=df,
            target_column="housing_cpi_growth",
        ),
        "construction_cost_growth": _evaluate_single_target(
            df=df,
            target_column="construction_cost_growth",
        ),
        "usd_growth": _evaluate_single_target(
            df=df,
            target_column="usd_growth",
        ),
    }
