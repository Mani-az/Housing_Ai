"""Reproducible evaluation for the Housing AI model artifacts and runtime policy.

Run from the workspace root:
    python ml_evaluation/evaluate_models.py > ml_evaluation/metrics.json

The buyer-risk and project-delay datasets are synthetic. Their classification
metrics measure consistency with those synthetic labels, not field accuracy.
Economic forecasting uses chronological rolling-origin backtesting.
"""

from __future__ import annotations

import importlib.util
import argparse
import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split

# Some scikit-learn versions emit this warning once per tree when a persisted
# Random Forest was trained with parallel workers. It is not an evaluation
# failure and can otherwise produce megabytes of noise in the JSON report.
warnings.filterwarnings(
    "ignore",
    message=r"`sklearn\.utils\.parallel\.delayed` should be used",
)


ROOT = Path(__file__).resolve().parents[1]
CURRENT_BACKEND = ROOT / "extracted" / "backend"
# The calibrated runtime is now part of the backend package itself.  Keep the
# optional comparison path for historical experiments, but default to one
# canonical backend so a fresh checkout is evaluable without a second tree.
IMPROVED_BACKEND = CURRENT_BACKEND


def load_prediction_module(name: str, backend: Path):
    spec = importlib.util.spec_from_file_location(name, backend / "prediction_services_v2.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load prediction module from {backend}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


current = None
improved = None


def rounded(value: float) -> float:
    return round(float(value), 6)


def classification_metrics(y_true, y_pred, labels) -> dict:
    return {
        "accuracy": rounded(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": rounded(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": rounded(f1_score(y_true, y_pred, average="macro")),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        "label_order": labels,
    }


def regression_metrics(y_true, y_pred) -> dict:
    return {
        "mae": rounded(mean_absolute_error(y_true, y_pred)),
        "rmse": rounded(mean_squared_error(y_true, y_pred) ** 0.5),
        "r2": rounded(r2_score(y_true, y_pred)),
    }


def evaluate_buyer() -> dict:
    df = pd.read_csv(CURRENT_BACKEND / "data" / "buyer_risk_dataset.csv")
    artifact = joblib.load(CURRENT_BACKEND / "models" / "buyer_risk_v2.joblib")
    indices = np.arange(len(df))
    _, test_indices = train_test_split(
        indices,
        test_size=0.20,
        random_state=42,
        stratify=df["risk_label"],
    )
    test = df.iloc[test_indices]
    x_test = test[artifact["features"]]
    raw_scores = np.clip(artifact["regressor"].predict(x_test), 0, 100)
    classifier_labels = artifact["classifier"].predict(x_test)
    raw_threshold_labels = np.where(
        raw_scores < 35,
        "low",
        np.where(raw_scores < 65, "medium", "high"),
    )

    current_scores = []
    current_labels = []
    improved_scores = []
    improved_labels = []
    for (_, row), raw_score, classifier_label in zip(
        test.iterrows(), raw_scores, classifier_labels
    ):
        if CURRENT_BACKEND.resolve() == IMPROVED_BACKEND.resolve():
            # Evaluate the exact runtime policy shipped in the backend rather
            # than an older experimental contextual formula.
            prediction = current.predict_buyer_risk(row.to_dict())
            current_scores.append(float(prediction["risk_score"]))
            current_labels.append(str(prediction["risk_label"]))
            improved_scores.append(float(prediction["risk_score"]))
            improved_labels.append(str(prediction["risk_label"]))
        else:
            enriched = current.add_buyer_features(pd.DataFrame([row]))
            context = current.calculate_contextual_buyer_score(enriched.iloc[0], raw_score)
            current_scores.append(context["score"])
            current_labels.append(current.buyer_label_from_score(context["score"]))

            score = improved._buyer_score_consistent_with_label(raw_score, classifier_label)
            improved_scores.append(score)
            improved_labels.append(improved.buyer_label_from_score(score))

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_regression = cross_val_predict(
        clone(artifact["regressor"]),
        df[artifact["features"]],
        df["risk_score"],
        cv=cv.split(df[artifact["features"]], df["risk_label"]),
        # Keep evaluation deterministic and portable on constrained machines;
        # production training can still use parallel workers.
        n_jobs=1,
    )
    cv_threshold_labels = np.where(
        cv_regression < 35,
        "low",
        np.where(cv_regression < 65, "medium", "high"),
    )
    cv_classifier = cross_val_predict(
        clone(artifact["classifier"]),
        df[artifact["features"]],
        df["risk_label"],
        cv=cv,
        n_jobs=1,
    )

    labels = ["low", "medium", "high"]
    return {
        "dataset": {
            "rows": int(len(df)),
            "provenance": "synthetic_scenario_data",
            "label_distribution": df["risk_label"].value_counts().to_dict(),
        },
        "five_fold_cross_validation": {
            "regressor": regression_metrics(df["risk_score"], cv_regression),
            "regressor_threshold_labels": classification_metrics(
                df["risk_label"], cv_threshold_labels, labels
            ),
            "classifier": classification_metrics(df["risk_label"], cv_classifier, labels),
        },
        "fixed_held_out_test": {
            "test_rows": int(len(test)),
            "raw_regressor": regression_metrics(test["risk_score"], raw_scores),
            "raw_regressor_threshold_labels": classification_metrics(
                test["risk_label"], raw_threshold_labels, labels
            ),
            "raw_classifier": classification_metrics(
                test["risk_label"], classifier_labels, labels
            ),
            "current_runtime": {
                **regression_metrics(test["risk_score"], current_scores),
                **classification_metrics(test["risk_label"], current_labels, labels),
            },
            "improved_runtime": {
                **regression_metrics(test["risk_score"], improved_scores),
                **classification_metrics(test["risk_label"], improved_labels, labels),
            },
        },
    }


def delay_threshold_labels(values: np.ndarray) -> np.ndarray:
    return np.select(
        [values <= 6, values <= 12, values <= 24, values <= 60],
        ["acceptable_delay", "low", "medium", "high"],
        default="critical",
    )


def evaluate_delay() -> dict:
    raw_df = pd.read_csv(CURRENT_BACKEND / "data" / "construction_delay_dataset.csv")
    df = current.add_delay_features(raw_df)
    artifact = joblib.load(CURRENT_BACKEND / "models" / "project_delay_v2.joblib")
    indices = np.arange(len(df))
    _, test_indices = train_test_split(
        indices,
        test_size=0.25,
        random_state=42,
        stratify=df["delay_risk_level"],
    )
    test = df.iloc[test_indices]
    x_test = test[artifact["features"]]
    raw_months = np.clip(artifact["regressor"].predict(x_test), 0, 120)
    classifier_labels = artifact["classifier"].predict(x_test)
    raw_threshold_labels = delay_threshold_labels(raw_months)

    current_months = []
    current_labels = []
    improved_months = []
    improved_labels = []
    for (_, row), raw_month, classifier_label in zip(
        test.iterrows(), raw_months, classifier_labels
    ):
        if CURRENT_BACKEND.resolve() == IMPROVED_BACKEND.resolve():
            prediction = current.predict_project_delay(row.to_dict())
            current_labels.append(str(prediction["delay_risk_level"]))
            current_months.append(float(prediction["predicted_delay_months"]))
            improved_labels.append(str(prediction["delay_risk_level"]))
            improved_months.append(float(prediction["predicted_delay_months"]))
        else:
            context = current.calculate_contextual_delay_score(row)
            current_label = current.delay_label_from_context(context["score"], row)
            current_labels.append(current_label)
            current_months.append(
                current._delay_months_from_context(context["score"], current_label, raw_month)
            )

            improved_label = improved._cap_delay_label_for_healthy_operations(
                str(classifier_label), row, context["score"]
            )
            improved_labels.append(improved_label)
            improved_months.append(
                improved._delay_months_consistent_with_label(raw_month, improved_label)
            )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_regression = cross_val_predict(
        clone(artifact["regressor"]),
        df[artifact["features"]],
        df["predicted_delay_months"],
        cv=cv.split(df[artifact["features"]], df["delay_risk_level"]),
        n_jobs=1,
    )
    cv_classifier = cross_val_predict(
        clone(artifact["classifier"]),
        df[artifact["features"]],
        df["delay_risk_level"],
        cv=cv,
        n_jobs=1,
    )
    labels = ["acceptable_delay", "low", "medium", "high", "critical"]

    return {
        "dataset": {
            "rows": int(len(df)),
            "provenance": "synthetic_scenario_data",
            "label_distribution": df["delay_risk_level"].value_counts().to_dict(),
        },
        "five_fold_cross_validation": {
            "regressor": regression_metrics(df["predicted_delay_months"], cv_regression),
            "regressor_threshold_labels": classification_metrics(
                df["delay_risk_level"], delay_threshold_labels(cv_regression), labels
            ),
            "classifier": classification_metrics(
                df["delay_risk_level"], cv_classifier, labels
            ),
        },
        "fixed_held_out_test": {
            "test_rows": int(len(test)),
            "raw_regressor": regression_metrics(test["predicted_delay_months"], raw_months),
            "raw_regressor_threshold_labels": classification_metrics(
                test["delay_risk_level"], raw_threshold_labels, labels
            ),
            "raw_classifier": classification_metrics(
                test["delay_risk_level"], classifier_labels, labels
            ),
            "current_runtime": {
                **regression_metrics(test["predicted_delay_months"], current_months),
                **classification_metrics(test["delay_risk_level"], current_labels, labels),
            },
            "improved_runtime": {
                **regression_metrics(test["predicted_delay_months"], improved_months),
                **classification_metrics(test["delay_risk_level"], improved_labels, labels),
            },
        },
    }


def evaluate_economic() -> dict:
    artifact = joblib.load(CURRENT_BACKEND / "models" / "economic_forecaster_v2.joblib")
    df = pd.DataFrame(artifact["history"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")
    monthly_index = pd.date_range(df.index.min(), df.index.max(), freq="MS")
    df = df.reindex(monthly_index)

    output = {
        "dataset": {
            "rows": int(len(df)),
            "provenance": "real_macro_indicator_history",
        },
        "rolling_origin": {},
    }
    current_absolute_errors = []
    improved_absolute_errors = []
    persistence_absolute_errors = []

    for column, config in artifact["targets"].items():
        target_output = {}
        for horizon in [1, 3, 6, 12]:
            actuals = []
            current_predictions = []
            improved_predictions = []
            persistence_predictions = []

            for cutoff in range(7, len(df) - horizon):
                actual = df[column].iloc[cutoff + horizon]
                prefix = df[column].iloc[: cutoff + 1]
                if pd.isna(actual) or prefix.notna().sum() < 8:
                    continue

                current_prediction, _, _ = current._hybrid_forecast_series(
                    prefix, *config["clip"], horizon
                )
                improved_prediction, _, _ = improved._hybrid_forecast_series(
                    prefix, *config["clip"], horizon
                )
                persistence = float(prefix.dropna().iloc[-1])
                actuals.append(float(actual))
                current_predictions.append(current_prediction)
                improved_predictions.append(improved_prediction)
                persistence_predictions.append(persistence)

            if not actuals:
                continue

            current_metrics = regression_metrics(actuals, current_predictions)
            improved_metrics = regression_metrics(actuals, improved_predictions)
            persistence_metrics = regression_metrics(actuals, persistence_predictions)
            target_output[f"{horizon}_month"] = {
                "test_cases": len(actuals),
                "current_runtime": current_metrics,
                "improved_runtime": improved_metrics,
                "persistence_baseline": persistence_metrics,
            }
            current_absolute_errors.extend(
                np.abs(np.asarray(actuals) - np.asarray(current_predictions)).tolist()
            )
            improved_absolute_errors.extend(
                np.abs(np.asarray(actuals) - np.asarray(improved_predictions)).tolist()
            )
            persistence_absolute_errors.extend(
                np.abs(np.asarray(actuals) - np.asarray(persistence_predictions)).tolist()
            )

        output["rolling_origin"][column] = target_output

    output["aggregate_mae_across_series_and_horizons"] = {
        "test_cases": len(current_absolute_errors),
        "current_runtime": rounded(np.mean(current_absolute_errors)),
        "improved_runtime": rounded(np.mean(improved_absolute_errors)),
        "persistence_baseline": rounded(np.mean(persistence_absolute_errors)),
        "improvement_percent_vs_current": rounded(
            100
            * (np.mean(current_absolute_errors) - np.mean(improved_absolute_errors))
            / np.mean(current_absolute_errors)
        ),
    }
    return output


def main() -> None:
    global CURRENT_BACKEND, IMPROVED_BACKEND, current, improved

    parser = argparse.ArgumentParser()
    parser.add_argument("--current-backend", type=Path, default=CURRENT_BACKEND)
    parser.add_argument(
        "--improved-backend",
        type=Path,
        default=None,
        help="Optional historical comparison backend; defaults to the current backend.",
    )
    args = parser.parse_args()

    CURRENT_BACKEND = args.current_backend.resolve()
    IMPROVED_BACKEND = (
        args.improved_backend.resolve()
        if args.improved_backend is not None and args.improved_backend.exists()
        else CURRENT_BACKEND
    )
    current = load_prediction_module("housing_ml_current", CURRENT_BACKEND)
    improved = load_prediction_module("housing_ml_improved", IMPROVED_BACKEND)

    report = {
        "evaluation_policy": {
            "buyer_and_delay": "5-fold stratified CV plus untouched fixed hold-out matching stored artifacts",
            "economic": "chronological rolling-origin backtest at 1, 3, 6 and 12 months",
            "provenance_warning": (
                "Buyer-risk and project-delay scores are synthetic-scenario consistency metrics, "
                "not verified real-world accuracy."
            ),
            "runtime_comparison": (
                "The default evaluation measures the canonical runtime once. "
                "A separate comparison backend is optional for historical experiments."
            ),
        },
        "buyer_risk": evaluate_buyer(),
        "project_delay": evaluate_delay(),
        "economic_forecast": evaluate_economic(),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
