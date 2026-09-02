"""
ML v2 training script for Housing AI.

Usage:
    python train_models_v2.py \
      --buyer buyer_risk_dataset.csv \
      --delay construction_delay_dataset.csv \
      --economic economic_indicators.csv \
      --out models

This script trains:
- Buyer risk score regressor + label classifier
- Project delay month regressor + label classifier
- Economic hybrid forecaster artifact

The runtime prediction helpers are in prediction_services_v2.py.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split


def _safe_div(a: Any, b: Any) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return np.where(b != 0, a / b, 0.0)


def add_buyer_features(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    if {"total_paid_amount", "total_scheduled_amount"}.issubset(d.columns):
        d["payment_completion_ratio_calc"] = _safe_div(d["total_paid_amount"], d["total_scheduled_amount"])
        d["unpaid_amount_calc"] = d["total_scheduled_amount"] - d["total_paid_amount"]
        d["unpaid_amount_ratio_calc"] = _safe_div(d["unpaid_amount_calc"], d["total_scheduled_amount"])

    if {"total_paid_amount", "total_due_amount"}.issubset(d.columns):
        d["due_payment_completion_ratio_calc"] = np.clip(
            _safe_div(d["total_paid_amount"], d["total_due_amount"]), 0, 1
        )

    if {"due_unpaid_amount", "total_due_amount"}.issubset(d.columns):
        d["due_unpaid_amount_ratio_calc"] = _safe_div(d["due_unpaid_amount"], d["total_due_amount"])

    if {"paid_late_count", "total_payments"}.issubset(d.columns):
        d["late_payment_ratio"] = _safe_div(d["paid_late_count"], d["total_payments"])

    if {"overdue_count", "total_payments"}.issubset(d.columns):
        d["overdue_payment_count_ratio"] = _safe_div(d["overdue_count"], d["total_payments"])

    if {"paid_on_time_count", "total_payments"}.issubset(d.columns):
        d["on_time_payment_ratio"] = _safe_div(d["paid_on_time_count"], d["total_payments"])

    if {"required_next_year_amount", "total_paid_amount"}.issubset(d.columns):
        d["future_payment_pressure_ratio"] = _safe_div(
            d["required_next_year_amount"], d["total_paid_amount"] + 1
        )

    if {"required_next_year_amount", "total_scheduled_amount"}.issubset(d.columns):
        d["required_to_scheduled_ratio"] = _safe_div(
            d["required_next_year_amount"], d["total_scheduled_amount"] + 1
        )

    return d


def add_delay_features(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    d["payment_stress_index"] = (
        (1 - d.get("project_payment_completion_ratio", 0)) * 0.35
        + d.get("overdue_payment_ratio", 0) * 0.35
        + d.get("paid_late_payment_ratio", 0) * 0.30
    )
    d["member_risk_weighted_score"] = (
        d.get("low_risk_member_ratio", 0) * 0.15
        + d.get("medium_risk_member_ratio", 0) * 0.50
        + d.get("high_risk_member_ratio", 0) * 1.00
    )
    d["economic_pressure_index"] = (
        d.get("predicted_construction_cost_growth", 0) * 0.45
        + d.get("predicted_general_inflation_rate", 0) * 0.25
        + d.get("predicted_usd_growth", 0) * 0.30
    )
    d["risk_ratio_gap"] = d.get("high_risk_member_ratio", 0) - d.get("low_risk_member_ratio", 0)
    d["duration_unit_load"] = d.get("planned_duration_months", 0) * np.log1p(d.get("total_units", 0))

    return d


def buyer_label_from_score(score: Any) -> np.ndarray:
    s = np.asarray(score, dtype=float)
    return np.where(s < 35, "low", np.where(s < 65, "medium", "high"))


def delay_label_from_months(months: Any) -> np.ndarray:
    m = np.asarray(months, dtype=float)
    return np.select(
        [m <= 6, m <= 12, m <= 24, m <= 60],
        ["acceptable_delay", "low", "medium", "high"],
        default="critical",
    )


def train_buyer_risk(path: Path, out_dir: Path) -> dict[str, Any]:
    df = pd.read_csv(path)
    df = add_buyer_features(df)

    drop_cols = ["sample_id", "risk_score", "risk_label"]
    features = [
        c for c in df.columns
        if c not in drop_cols and pd.api.types.is_numeric_dtype(df[c])
    ]

    x = df[features]
    y_score = df["risk_score"]
    y_label = df["risk_label"]

    x_train, x_test, ys_train, ys_test, yl_train, yl_test = train_test_split(
        x, y_score, y_label, test_size=0.25, random_state=42, stratify=y_label
    )

    regressor = RandomForestRegressor(
        n_estimators=160,
        max_depth=9,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    regressor.fit(x_train, ys_train)
    pred_score = np.clip(regressor.predict(x_test), 0, 100)
    pred_label_from_score = buyer_label_from_score(pred_score)

    classifier = RandomForestClassifier(
        n_estimators=160,
        max_depth=9,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    classifier.fit(x_train, yl_train)
    pred_label = classifier.predict(x_test)

    metrics = {
        "score_mae": float(mean_absolute_error(ys_test, pred_score)),
        "score_r2": float(r2_score(ys_test, pred_score)),
        "label_accuracy_from_regressor_thresholds": float(accuracy_score(yl_test, pred_label_from_score)),
        "label_macro_f1_from_regressor_thresholds": float(f1_score(yl_test, pred_label_from_score, average="macro")),
        "classifier_accuracy": float(accuracy_score(yl_test, pred_label)),
        "classifier_macro_f1": float(f1_score(yl_test, pred_label, average="macro")),
        "label_thresholds": {"low": "<35", "medium": "35-64.999", "high": ">=65"},
    }

    artifact = {
        "regressor": regressor,
        "classifier": classifier,
        "features": features,
        "metrics": metrics,
        "label_thresholds": {"low_max_exclusive": 35, "medium_max_exclusive": 65},
    }

    joblib.dump(artifact, out_dir / "buyer_risk_v2.joblib")
    return metrics


def train_project_delay(path: Path, out_dir: Path) -> dict[str, Any]:
    df = pd.read_csv(path)
    df = add_delay_features(df)

    drop_cols = ["sample_id", "predicted_delay_months", "delay_risk_level"]
    features = [
        c for c in df.columns
        if c not in drop_cols and pd.api.types.is_numeric_dtype(df[c])
    ]

    x = df[features]
    y_months = df["predicted_delay_months"]
    y_label = df["delay_risk_level"]

    x_train, x_test, ym_train, ym_test, yl_train, yl_test = train_test_split(
        x, y_months, y_label, test_size=0.25, random_state=42, stratify=y_label
    )

    regressor = RandomForestRegressor(
        n_estimators=180,
        max_depth=10,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    regressor.fit(x_train, ym_train)
    pred_months = np.clip(regressor.predict(x_test), 0, 120)
    pred_label_from_months = delay_label_from_months(pred_months)

    classifier = RandomForestClassifier(
        n_estimators=180,
        max_depth=10,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    classifier.fit(x_train, yl_train)
    pred_label = classifier.predict(x_test)

    metrics = {
        "delay_months_mae": float(mean_absolute_error(ym_test, pred_months)),
        "delay_months_r2": float(r2_score(ym_test, pred_months)),
        "label_accuracy_from_regressor_thresholds": float(accuracy_score(yl_test, pred_label_from_months)),
        "label_macro_f1_from_regressor_thresholds": float(f1_score(yl_test, pred_label_from_months, average="macro")),
        "classifier_accuracy": float(accuracy_score(yl_test, pred_label)),
        "classifier_macro_f1": float(f1_score(yl_test, pred_label, average="macro")),
        "label_thresholds": {
            "acceptable_delay": "<=6 months",
            "low": ">6 and <=12 months",
            "medium": ">12 and <=24 months",
            "high": ">24 and <=60 months",
            "critical": ">60 months",
        },
    }

    artifact = {
        "regressor": regressor,
        "classifier": classifier,
        "features": features,
        "metrics": metrics,
        "label_thresholds": {
            "acceptable_delay_max": 6,
            "low_max": 12,
            "medium_max": 24,
            "high_max": 60,
        },
    }

    joblib.dump(artifact, out_dir / "project_delay_v2.joblib")
    return metrics


def build_economic_artifact(path: Path, out_dir: Path) -> dict[str, Any]:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    artifact = {
        "history": df.assign(date=df["date"].dt.strftime("%Y-%m-%d")).to_dict(orient="records"),
        "targets": {
            "general_inflation_rate": {"clip": [25, 75]},
            "construction_cost_growth": {"clip": [25, 110]},
            "usd_growth": {"clip": [10, 150]},
            "housing_cpi_growth": {"clip": [15, 80]},
        },
        "method": "hybrid_last_value_ewma_trend_with_staleness_confidence",
    }

    joblib.dump(artifact, out_dir / "economic_forecaster_v2.joblib")

    coverage = {}
    for col in artifact["targets"]:
        valid = df.dropna(subset=[col])
        coverage[col] = {
            "non_null_rows": int(valid.shape[0]),
            "first_non_null_date": str(valid["date"].min().date()) if not valid.empty else None,
            "last_non_null_date": str(valid["date"].max().date()) if not valid.empty else None,
            "last_value": float(valid[col].iloc[-1]) if not valid.empty else None,
        }
    return coverage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--buyer", type=Path, required=True)
    parser.add_argument("--delay", type=Path, required=True)
    parser.add_argument("--economic", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("models"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    metrics = {
        "buyer_risk": train_buyer_risk(args.buyer, args.out),
        "project_delay": train_project_delay(args.delay, args.out),
        "economic_data_coverage": build_economic_artifact(args.economic, args.out),
    }

    (args.out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
