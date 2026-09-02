"""Reproducible ML evaluation for thesis/demo presentation.

Run from the backend directory:

    python -m app.scripts.evaluate_ml_accuracy
    python -m app.scripts.evaluate_ml_accuracy --json

Buyer-risk and project-delay datasets are synthetic scenario data. Their metrics
measure consistency with synthetic labels, not verified real-world accuracy.
The economic module is evaluated with chronological rolling-origin backtesting.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split


BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import prediction_services_v2 as prediction_runtime  # noqa: E402


DATA_DIR = BACKEND_DIR / "data"
MODEL_DIR = BACKEND_DIR / "models"


def _round(value: float) -> float:
    return round(float(value), 6)


def _classification_metrics(y_true, y_pred) -> dict:
    return {
        "accuracy": _round(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": _round(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": _round(f1_score(y_true, y_pred, average="macro")),
    }


def _regression_metrics(y_true, y_pred) -> dict:
    return {
        "mae": _round(mean_absolute_error(y_true, y_pred)),
        "rmse": _round(mean_squared_error(y_true, y_pred) ** 0.5),
        "r2": _round(r2_score(y_true, y_pred)),
    }


def evaluate_buyer_risk() -> dict:
    df = pd.read_csv(DATA_DIR / "buyer_risk_dataset.csv")
    artifact = joblib.load(MODEL_DIR / "buyer_risk_v2.joblib")
    x = df[artifact["features"]]
    y_label = df["risk_label"]
    y_score = df["risk_score"]
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    cv_labels = cross_val_predict(
        clone(artifact["classifier"]),
        x,
        y_label,
        cv=cv,
        n_jobs=-1,
    )
    cv_scores = cross_val_predict(
        clone(artifact["regressor"]),
        x,
        y_score,
        cv=cv.split(x, y_label),
        n_jobs=-1,
    )

    indices = np.arange(len(df))
    _, test_indices = train_test_split(
        indices,
        test_size=0.20,
        random_state=42,
        stratify=y_label,
    )
    test = df.iloc[test_indices]
    test_x = test[artifact["features"]]
    raw_scores = np.clip(artifact["regressor"].predict(test_x), 0, 100)
    classifier_labels = artifact["classifier"].predict(test_x)
    runtime_scores = [
        prediction_runtime._buyer_score_consistent_with_label(score, label)
        for score, label in zip(raw_scores, classifier_labels)
    ]
    runtime_labels = [
        prediction_runtime.buyer_label_from_score(score)
        for score in runtime_scores
    ]

    return {
        "dataset_rows": int(len(df)),
        "provenance": "synthetic_scenario_data",
        "five_fold_classifier": _classification_metrics(y_label, cv_labels),
        "five_fold_regressor": _regression_metrics(y_score, cv_scores),
        "held_out_test_rows": int(len(test)),
        "runtime_classifier": _classification_metrics(test["risk_label"], runtime_labels),
        "runtime_regressor": _regression_metrics(test["risk_score"], runtime_scores),
    }


def evaluate_project_delay() -> dict:
    raw_df = pd.read_csv(DATA_DIR / "construction_delay_dataset.csv")
    df = prediction_runtime.add_delay_features(raw_df)
    artifact = joblib.load(MODEL_DIR / "project_delay_v2.joblib")
    x = df[artifact["features"]]
    y_label = df["delay_risk_level"]
    y_months = df["predicted_delay_months"]
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    cv_labels = cross_val_predict(
        clone(artifact["classifier"]),
        x,
        y_label,
        cv=cv,
        n_jobs=-1,
    )
    cv_months = cross_val_predict(
        clone(artifact["regressor"]),
        x,
        y_months,
        cv=cv.split(x, y_label),
        n_jobs=-1,
    )

    indices = np.arange(len(df))
    _, test_indices = train_test_split(
        indices,
        test_size=0.25,
        random_state=42,
        stratify=y_label,
    )
    test = df.iloc[test_indices]
    test_x = test[artifact["features"]]
    raw_months = np.clip(artifact["regressor"].predict(test_x), 0, 120)
    classifier_labels = artifact["classifier"].predict(test_x)

    runtime_labels = []
    runtime_months = []
    for (_, row), raw_month, classifier_label in zip(
        test.iterrows(), raw_months, classifier_labels
    ):
        context = prediction_runtime.calculate_contextual_delay_score(row)
        label = prediction_runtime._cap_delay_label_for_healthy_operations(
            str(classifier_label), row, context["score"]
        )
        runtime_labels.append(label)
        runtime_months.append(
            prediction_runtime._delay_months_consistent_with_label(raw_month, label)
        )

    return {
        "dataset_rows": int(len(df)),
        "provenance": "synthetic_scenario_data",
        "five_fold_classifier": _classification_metrics(y_label, cv_labels),
        "five_fold_regressor": _regression_metrics(y_months, cv_months),
        "held_out_test_rows": int(len(test)),
        "runtime_classifier": _classification_metrics(test["delay_risk_level"], runtime_labels),
        "runtime_regressor": _regression_metrics(test["predicted_delay_months"], runtime_months),
    }


def evaluate_economic_forecast() -> dict:
    artifact = joblib.load(MODEL_DIR / "economic_forecaster_v2.joblib")
    df = pd.DataFrame(artifact["history"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")
    df = df.reindex(pd.date_range(df.index.min(), df.index.max(), freq="MS"))
    model_errors = []
    persistence_errors = []
    horizons = {}

    for target, config in artifact["targets"].items():
        target_results = {}
        for horizon in [1, 3, 6, 12]:
            actuals = []
            predictions = []
            persistence_predictions = []

            for cutoff in range(7, len(df) - horizon):
                actual = df[target].iloc[cutoff + horizon]
                prefix = df[target].iloc[: cutoff + 1]
                if pd.isna(actual) or prefix.notna().sum() < 8:
                    continue

                prediction, _, _ = prediction_runtime._hybrid_forecast_series(
                    prefix,
                    *config["clip"],
                    horizon,
                )
                persistence = float(prefix.dropna().iloc[-1])
                actuals.append(float(actual))
                predictions.append(prediction)
                persistence_predictions.append(persistence)

            if not actuals:
                continue

            model_mae = mean_absolute_error(actuals, predictions)
            persistence_mae = mean_absolute_error(actuals, persistence_predictions)
            target_results[f"{horizon}_month"] = {
                "test_cases": len(actuals),
                "model_mae": _round(model_mae),
                "persistence_mae": _round(persistence_mae),
            }
            model_errors.extend(
                np.abs(np.asarray(actuals) - np.asarray(predictions)).tolist()
            )
            persistence_errors.extend(
                np.abs(np.asarray(actuals) - np.asarray(persistence_predictions)).tolist()
            )

        horizons[target] = target_results

    return {
        "provenance": "real_macro_history_with_sparse_targets",
        "evaluation": "chronological_rolling_origin",
        "test_cases": len(model_errors),
        "aggregate_model_mae": _round(np.mean(model_errors)),
        "aggregate_persistence_mae": _round(np.mean(persistence_errors)),
        "horizons": horizons,
    }


def evaluate_all() -> dict:
    return {
        "warning": (
            "Buyer-risk and project-delay metrics measure synthetic-scenario "
            "consistency, not verified real-world accuracy."
        ),
        "buyer_risk": evaluate_buyer_risk(),
        "project_delay": evaluate_project_delay(),
        "economic_forecast": evaluate_economic_forecast(),
    }


def _print_human_report(results: dict) -> None:
    buyer = results["buyer_risk"]
    delay = results["project_delay"]
    economic = results["economic_forecast"]

    print("Housing AI ML Evaluation")
    print("=" * 72)
    print("WARNING:", results["warning"])
    print()
    print("Member financial risk")
    print(f"  Rows: {buyer['dataset_rows']} ({buyer['provenance']})")
    print(f"  5-fold accuracy: {buyer['five_fold_classifier']['accuracy']:.4f}")
    print(f"  5-fold macro F1: {buyer['five_fold_classifier']['macro_f1']:.4f}")
    print(f"  5-fold score MAE: {buyer['five_fold_regressor']['mae']:.4f}")
    print(f"  Held-out runtime accuracy: {buyer['runtime_classifier']['accuracy']:.4f}")
    print(f"  Held-out runtime score MAE: {buyer['runtime_regressor']['mae']:.4f}")
    print()
    print("Project delay")
    print(f"  Rows: {delay['dataset_rows']} ({delay['provenance']})")
    print(f"  5-fold accuracy: {delay['five_fold_classifier']['accuracy']:.4f}")
    print(f"  5-fold macro F1: {delay['five_fold_classifier']['macro_f1']:.4f}")
    print(f"  5-fold months MAE: {delay['five_fold_regressor']['mae']:.4f}")
    print(f"  Held-out runtime accuracy: {delay['runtime_classifier']['accuracy']:.4f}")
    print(f"  Held-out runtime months MAE: {delay['runtime_regressor']['mae']:.4f}")
    print()
    print("Economic forecast")
    print(f"  Evaluation: {economic['evaluation']}")
    print(f"  Rolling-origin cases: {economic['test_cases']}")
    print(f"  Aggregate model MAE: {economic['aggregate_model_mae']:.4f}")
    print(f"  Persistence baseline MAE: {economic['aggregate_persistence_mae']:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()
    results = evaluate_all()

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        _print_human_report(results)


if __name__ == "__main__":
    main()
