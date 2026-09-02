from pathlib import Path
from typing import Callable, Optional
from datetime import date

import pandas as pd
import numpy as np

from sqlalchemy.orm import Session
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_absolute_error, accuracy_score
from sklearn.model_selection import train_test_split

from app.models.project import Project
from app.models.project_participant import ProjectParticipant
from app.models.payment import Payment
from app.services.payment_service import get_payments_by_project
from app.ml.forecast_service import forecast_economic_indicators
from app.ml.member_risk_service import predict_member_financial_risk
from app.schemas.project_delay import ProjectDelayPredictionResponse
from prediction_services_v2 import predict_project_delay as predict_project_delay_v2


DATASET_PATH = Path("data/construction_delay_dataset.csv")
SYNTHETIC_DELAY_MAE_MONTHS = 5.1166


def _emit_progress(
    progress_callback: Optional[Callable[[str, int], None]],
    message: str,
    progress: int,
):
    if progress_callback is not None:
        progress_callback(message, progress)


FEATURE_COLUMNS = [
    "planned_duration_months",
    "total_units",
    "predicted_construction_cost_growth",
    "predicted_general_inflation_rate",
    "predicted_usd_growth",
    "project_payment_completion_ratio",
    "overdue_payment_ratio",
    "paid_late_payment_ratio",
    "low_risk_member_ratio",
    "medium_risk_member_ratio",
    "high_risk_member_ratio",
    "cash_flow_pressure_ratio",
]


def _calculate_planned_duration_months(project: Project) -> int:
    if not project.start_date or not project.expected_end_date:
        return 24

    start = project.start_date
    end = project.expected_end_date

    months = (end.year - start.year) * 12 + (end.month - start.month)

    if end.day >= start.day:
        months += 1

    return max(months, 1)


def _calculate_forecast_horizon_months(project: Project) -> int:
    """Use the selected project's expected end date as the macro forecast horizon."""
    if not project.expected_end_date:
        return 12

    today = date.today()
    end = project.expected_end_date

    months = (end.year - today.year) * 12 + (end.month - today.month)
    if end.day >= today.day:
        months += 1

    return max(1, min(months, 60))


def _calculate_project_payment_metrics(db: Session, project_id: int) -> dict:
    payments = get_payments_by_project(db=db, project_id=project_id)

    if not payments:
        return {
            "project_payment_completion_ratio": 0.0,
            "overdue_payment_ratio": 0.0,
            "paid_late_payment_ratio": 0.0,
            "cash_flow_pressure_ratio": 0.5,
        }

    # Penalty rows are fee collections, not construction-funding obligations.
    # Temporary prepayment rows do represent cash already contributed and are
    # included in the funding ratio, while delinquency ratios use installments only.
    funding_rows = [
        p for p in payments
        if p.payment_type in {"installment", "down_payment", "cost_share", "prepayment"}
    ]
    installment_rows = [p for p in payments if p.payment_type == "installment"]

    total_scheduled_amount = sum(float(p.amount or 0) for p in funding_rows)
    total_paid_amount = sum(
        float(p.amount or 0)
        for p in funding_rows
        if p.paid_date is not None
    )

    total_payments = len(installment_rows)
    paid_late_count = sum(1 for p in installment_rows if p.status == "paid_late")
    overdue_count = sum(1 for p in installment_rows if p.status == "overdue")

    payment_completion_ratio = (
        min(total_paid_amount / total_scheduled_amount, 1.0)
        if total_scheduled_amount > 0
        else 0.0
    )

    overdue_payment_ratio = overdue_count / total_payments if total_payments > 0 else 0.0
    paid_late_payment_ratio = paid_late_count / total_payments if total_payments > 0 else 0.0

    cash_flow_pressure_ratio = (
        (1 - payment_completion_ratio) * 0.55
        + overdue_payment_ratio * 0.30
        + paid_late_payment_ratio * 0.15
    )

    cash_flow_pressure_ratio = max(0.0, min(cash_flow_pressure_ratio, 1.0))

    return {
        "project_payment_completion_ratio": round(payment_completion_ratio, 4),
        "overdue_payment_ratio": round(overdue_payment_ratio, 4),
        "paid_late_payment_ratio": round(paid_late_payment_ratio, 4),
        "cash_flow_pressure_ratio": round(cash_flow_pressure_ratio, 4),
    }


def _calculate_member_risk_ratios(
    db: Session,
    project_id: int,
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> dict:
    participants = (
        db.query(ProjectParticipant)
        .filter(ProjectParticipant.project_id == project_id)
        .all()
    )

    if not participants:
        return {
            "low_risk_member_ratio": 0.0,
            "medium_risk_member_ratio": 0.0,
            "high_risk_member_ratio": 0.0,
        }

    low_count = 0
    medium_count = 0
    high_count = 0
    valid_count = 0

    total_participants = len(participants)

    for index, participant in enumerate(participants, start=1):
        try:
            _emit_progress(
                progress_callback,
                f"Calculating member risk ratios ({index}/{total_participants})...",
                55 + int((index / total_participants) * 15),
            )
            risk = predict_member_financial_risk(
                db=db,
                project_id=project_id,
                user_id=participant.user_id,
            )

            label = (
                risk.get("predicted_risk_label")
                if isinstance(risk, dict)
                else risk.predicted_risk_label
            )

            if label == "low":
                low_count += 1
                valid_count += 1
            elif label == "medium":
                medium_count += 1
                valid_count += 1
            elif label == "high":
                high_count += 1
                valid_count += 1

        except Exception:
            continue

    if valid_count == 0:
        return {
            "low_risk_member_ratio": 0.0,
            "medium_risk_member_ratio": 0.0,
            "high_risk_member_ratio": 0.0,
        }

    return {
        "low_risk_member_ratio": round(low_count / valid_count, 4),
        "medium_risk_member_ratio": round(medium_count / valid_count, 4),
        "high_risk_member_ratio": round(high_count / valid_count, 4),
    }


def _load_delay_dataset() -> pd.DataFrame:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Construction delay dataset not found at {DATASET_PATH}. "
            "Place construction_delay_dataset.csv inside backend/data/"
        )

    df = pd.read_csv(DATASET_PATH)

    required_columns = FEATURE_COLUMNS + [
        "predicted_delay_months",
        "delay_risk_level",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(
            f"Construction delay dataset is missing columns: {missing_columns}"
        )

    df = df.dropna(subset=required_columns)

    return df


def _train_delay_models():
    df = _load_delay_dataset()

    X = df[FEATURE_COLUMNS]
    y_delay = df["predicted_delay_months"]
    y_risk = df["delay_risk_level"]

    X_train, X_test, y_delay_train, y_delay_test = train_test_split(
        X,
        y_delay,
        test_size=0.2,
        random_state=42,
    )

    regressor = RandomForestRegressor(
        n_estimators=250,
        random_state=42,
        max_depth=12,
        min_samples_leaf=3,
    )

    regressor.fit(X_train, y_delay_train)

    delay_predictions = regressor.predict(X_test)
    mae = mean_absolute_error(y_delay_test, delay_predictions)

    X_train_cls, X_test_cls, y_risk_train, y_risk_test = train_test_split(
        X,
        y_risk,
        test_size=0.2,
        random_state=42,
        stratify=y_risk,
    )

    classifier = RandomForestClassifier(
        n_estimators=250,
        random_state=42,
        max_depth=12,
        min_samples_leaf=3,
        class_weight="balanced",
    )

    classifier.fit(X_train_cls, y_risk_train)

    risk_predictions = classifier.predict(X_test_cls)
    accuracy = accuracy_score(y_risk_test, risk_predictions)

    # Retrain on full dataset for final prediction
    regressor.fit(X, y_delay)
    classifier.fit(X, y_risk)

    return regressor, classifier, mae, accuracy


def _build_delay_factors(features: dict) -> list[str]:
    factors = []

    if features["predicted_construction_cost_growth"] >= 60:
        factors.append("High construction cost growth")

    if features["predicted_general_inflation_rate"] >= 45:
        factors.append("High general inflation")

    if features["predicted_usd_growth"] >= 55:
        factors.append("High USD growth pressure")

    if features["project_payment_completion_ratio"] < 0.6:
        factors.append("Low project payment completion")

    if features["overdue_payment_ratio"] >= 0.25:
        factors.append("High overdue payment ratio")

    if features["paid_late_payment_ratio"] >= 0.25:
        factors.append("Frequent late payments")

    if features["high_risk_member_ratio"] >= 0.30:
        factors.append("High ratio of financially risky members")

    if features["cash_flow_pressure_ratio"] >= 0.55:
        factors.append("High project cash-flow pressure")

    if not factors:
        factors.append("No major delay factor detected based on current project data")

    return factors


def predict_project_delay(
    db: Session,
    project_id: int,
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> ProjectDelayPredictionResponse:
    _emit_progress(progress_callback, "Loading selected project...", 5)

    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise ValueError("Project not found")

    _emit_progress(progress_callback, "Calculating planned project duration...", 12)
    planned_duration_months = _calculate_planned_duration_months(project)
    forecast_horizon_months = _calculate_forecast_horizon_months(project)

    _emit_progress(progress_callback, "Forecasting project-horizon economic pressure indicators...", 15)
    forecast = forecast_economic_indicators(
        db=db,
        horizon_months=forecast_horizon_months,
    )

    _emit_progress(progress_callback, "Analyzing project payments and cash flow...", 45)
    payment_metrics = _calculate_project_payment_metrics(db, project_id)

    _emit_progress(progress_callback, "Calculating member risk ratios...", 55)
    member_risk_ratios = _calculate_member_risk_ratios(
        db,
        project_id,
        progress_callback=progress_callback,
    )

    features = {
        "planned_duration_months": planned_duration_months,
        "total_units": project.total_units or 0,
       "predicted_construction_cost_growth": float(
    forecast.get("predicted_construction_cost_growth", 0)
        ),
        "predicted_general_inflation_rate": float(
    forecast.get("predicted_general_inflation_rate", 0)
        ),
        "predicted_usd_growth": float(
    forecast.get("predicted_usd_growth", 0)
        ),
        "project_payment_completion_ratio": payment_metrics["project_payment_completion_ratio"],
        "overdue_payment_ratio": payment_metrics["overdue_payment_ratio"],
        "paid_late_payment_ratio": payment_metrics["paid_late_payment_ratio"],
        "low_risk_member_ratio": member_risk_ratios["low_risk_member_ratio"],
        "medium_risk_member_ratio": member_risk_ratios["medium_risk_member_ratio"],
        "high_risk_member_ratio": member_risk_ratios["high_risk_member_ratio"],
        "cash_flow_pressure_ratio": payment_metrics["cash_flow_pressure_ratio"],
    }

    _emit_progress(progress_callback, "Running project delay ML v2 model...", 80)

    v2_result = predict_project_delay_v2(features)

    predicted_delay_months = float(v2_result["predicted_delay_months"])
    predicted_risk_label = str(v2_result["delay_risk_level"])

    estimated_actual_duration_months = (
        planned_duration_months + predicted_delay_months
    )

    _emit_progress(progress_callback, "Preparing project delay response...", 95)

    return ProjectDelayPredictionResponse(
        project_id=project.id,
        project_name=project.name,
        planned_duration_months=planned_duration_months,
        predicted_delay_months=round(predicted_delay_months, 2),
        estimated_actual_duration_months=round(estimated_actual_duration_months, 2),
        delay_risk_level=predicted_risk_label,
        predicted_construction_cost_growth=round(
            features["predicted_construction_cost_growth"], 4
        ),
        predicted_general_inflation_rate=round(
            features["predicted_general_inflation_rate"], 4
        ),
        predicted_usd_growth=round(
            features["predicted_usd_growth"], 4
        ),
        project_payment_completion_ratio=features["project_payment_completion_ratio"],
        overdue_payment_ratio=features["overdue_payment_ratio"],
        paid_late_payment_ratio=features["paid_late_payment_ratio"],
        low_risk_member_ratio=features["low_risk_member_ratio"],
        medium_risk_member_ratio=features["medium_risk_member_ratio"],
        high_risk_member_ratio=features["high_risk_member_ratio"],
        cash_flow_pressure_ratio=features["cash_flow_pressure_ratio"],
        main_delay_factors=v2_result.get("reasons") or _build_delay_factors(features),
        model_mae=round(float(SYNTHETIC_DELAY_MAE_MONTHS), 4),
        model_note=(
            "Project delay is predicted using the ML v2 delay-month regressor with "
            "Iran-context weighted post-processing. Payment behavior and cash-flow pressure "
            "carry the largest weight, construction-cost growth is the main cost-side driver, "
            "and USD/inflation pressure is treated as a modifier rather than a stand-alone "
            "high-risk trigger. Economic pressure is forecast using the selected "
            f"project horizon ({forecast_horizon_months} months), not a fixed one-year horizon. "
            "The construction-delay dataset is synthetic, so this MAE is an internal prototype "
            "validation metric, not verified real-world accuracy. "
            f"Model version: {v2_result.get('model_version')}."
        ),
    )