"""
Runtime prediction helpers for Housing AI ML v2.

Backend integration idea:
- Import these functions inside your existing prediction service files.
- Keep current API response fields stable.
- Add optional fields: confidence, reasons, model_version, top_level_note.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


MODEL_VERSION = "ml_v2_2026_07_accuracy_calibrated"
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"


@lru_cache(maxsize=8)
def _load_artifact_cached(path_value: str):
    """Load a model artifact once per process instead of once per prediction request."""
    return joblib.load(path_value)


def _load_artifact(model_path: str | Path | None, default_path: Path):
    resolved = Path(model_path or default_path).resolve()
    return _load_artifact_cached(str(resolved))


def _safe_div(a: Any, b: Any) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return np.where(b != 0, a / b, 0.0)


def _as_frame(payload: dict[str, Any] | list[dict[str, Any]]) -> pd.DataFrame:
    if isinstance(payload, dict):
        return pd.DataFrame([payload])
    return pd.DataFrame(payload)


def _fill_missing_model_features(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    d = df.copy()
    for col in features:
        if col not in d.columns:
            d[col] = 0.0
    return d[features].replace([np.inf, -np.inf], 0).fillna(0)


def add_buyer_features(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    if {"total_paid_amount", "total_scheduled_amount"}.issubset(d.columns):
        if "payment_completion_ratio" in d.columns:
            d["payment_completion_ratio_calc"] = np.clip(d["payment_completion_ratio"].astype(float), 0, 1)
        else:
            d["payment_completion_ratio_calc"] = _safe_div(d["total_paid_amount"], d["total_scheduled_amount"])

        if "unpaid_amount" in d.columns:
            d["unpaid_amount_calc"] = d["unpaid_amount"].astype(float)
        else:
            d["unpaid_amount_calc"] = d["total_scheduled_amount"] - d["total_paid_amount"]
        d["unpaid_amount_ratio_calc"] = _safe_div(d["unpaid_amount_calc"], d["total_scheduled_amount"])

    if "due_payment_completion_ratio" in d.columns:
        d["due_payment_completion_ratio_calc"] = np.clip(
            d["due_payment_completion_ratio"].astype(float), 0, 1
        )
    elif {"total_paid_amount", "total_due_amount"}.issubset(d.columns):
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


def buyer_label_from_score(score: float) -> str:
    if score < 35:
        return "low"
    if score < 65:
        return "medium"
    return "high"


def _buyer_score_consistent_with_label(score: float, label: str) -> float:
    """Keep the regressor score while aligning it with the classifier band.

    The stored artifact contains separately validated regression and classification
    models. The smallest possible boundary adjustment prevents contradictory API
    output such as a medium classifier label paired with a low-band score.
    """
    numeric = float(np.clip(score, 0, 100))

    if label == "low":
        return float(np.clip(numeric, 0, 34.99))
    if label == "medium":
        return float(np.clip(numeric, 35.0, 64.99))
    return float(np.clip(numeric, 65.0, 100.0))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
        if np.isfinite(numeric):
            return numeric
    except Exception:
        pass
    return default


def _clip01(value: Any) -> float:
    return float(np.clip(_safe_float(value), 0.0, 1.0))


def _normalize_percent(value: Any, baseline: float, ceiling: float) -> float:
    """Normalize a percent-like macro value relative to an Iran-context baseline."""
    numeric = _safe_float(value)

    if ceiling <= baseline:
        return 0.0

    return float(np.clip((numeric - baseline) / (ceiling - baseline), 0.0, 1.0))


def calculate_contextual_buyer_score(
    row: pd.Series,
    ml_score: float,
) -> dict[str, Any]:
    """Blend synthetic-ML output with observable member payment behavior.

    Macro conditions are structural in Iran, so they remain modifiers. Overdue
    payments, due-payment completion, repeated lateness, and delay severity drive
    the final member label.
    """
    total_payments = max(int(_safe_float(row.get("total_payments", 0))), 1)
    paid_late_count = max(int(_safe_float(row.get("paid_late_count", 0))), 0)
    overdue_count = max(int(_safe_float(row.get("overdue_count", 0))), 0)

    due_completion = _clip01(
        row.get(
            "due_payment_completion_ratio_calc",
            row.get("due_payment_completion_ratio", 0),
        )
    )
    due_unpaid_ratio = _clip01(
        row.get(
            "due_unpaid_amount_ratio_calc",
            row.get("due_unpaid_amount_ratio", 0),
        )
    )
    unpaid_ratio = _clip01(
        row.get(
            "unpaid_amount_ratio_calc",
            row.get("unpaid_amount_ratio", 0),
        )
    )

    late_ratio = _clip01(paid_late_count / total_payments)
    overdue_ratio = _clip01(overdue_count / total_payments)
    average_delay_days = _safe_float(row.get("average_delay_days", 0))
    max_delay_days = _safe_float(row.get("max_delay_days", 0))
    average_delay_pressure = float(np.clip(average_delay_days / 45.0, 0.0, 1.0))
    max_delay_pressure = float(np.clip(max_delay_days / 90.0, 0.0, 1.0))
    prepaid_installment_count = max(int(_safe_float(row.get("prepaid_installment_count", 0))), 0)
    prepaid_amount = max(_safe_float(row.get("prepaid_amount", 0)), 0.0)

    payment_behavior_pressure = (
        0.28 * (1.0 - due_completion)
        + 0.22 * due_unpaid_ratio
        + 0.17 * overdue_ratio
        + 0.13 * late_ratio
        + 0.12 * average_delay_pressure
        + 0.08 * max_delay_pressure
    )

    required_amount = max(_safe_float(row.get("required_next_year_amount", 0)), 0.0)
    scheduled_amount = max(_safe_float(row.get("total_scheduled_amount", 0)), 0.0)
    paid_amount = max(_safe_float(row.get("total_paid_amount", 0)), 0.0)

    prepayment_ratio = float(np.clip(prepaid_amount / max(scheduled_amount, 1.0), 0.0, 1.0))
    prepayment_bonus_points = min(25.0, prepaid_installment_count * 6.0 + prepayment_ratio * 20.0)

    required_to_schedule_ratio = required_amount / max(scheduled_amount, 1.0)
    future_obligation_pressure = float(
        np.clip((required_to_schedule_ratio - 0.75) / 1.25, 0.0, 1.0)
    )
    historical_shortfall_pressure = float(
        np.clip((required_amount - paid_amount) / max(required_amount, 1.0), 0.0, 1.0)
    )
    future_pressure = (
        0.55 * future_obligation_pressure
        + 0.25 * historical_shortfall_pressure
        + 0.20 * unpaid_ratio
    )

    construction_pressure = _normalize_percent(
        row.get("construction_cost_growth", 0), baseline=45, ceiling=95
    )
    inflation_pressure = _normalize_percent(
        row.get("general_inflation_rate", 0), baseline=40, ceiling=85
    )
    usd_pressure = _normalize_percent(
        row.get("usd_growth", 0), baseline=90, ceiling=180
    )
    macro_pressure = (
        0.50 * construction_pressure
        + 0.20 * inflation_pressure
        + 0.30 * usd_pressure
    )

    contextual_score = 100.0 * (
        0.75 * payment_behavior_pressure
        + 0.15 * future_pressure
        + 0.10 * macro_pressure
    )
    final_score = 0.35 * float(np.clip(ml_score, 0, 100)) + 0.65 * contextual_score

    high_operational_risk = (
        due_completion < 0.55
        or due_unpaid_ratio >= 0.35
        or (
            overdue_count >= 2
            and (due_unpaid_ratio >= 0.18 or average_delay_pressure >= 0.45)
        )
        or (overdue_count >= 1 and average_delay_days >= 35)
    )
    medium_operational_risk = (
        overdue_count >= 1
        or due_completion < 0.90
        or due_unpaid_ratio >= 0.10
        or (
            paid_late_count >= 2
            and (late_ratio >= 0.25 or average_delay_days >= 7)
        )
    )
    clean_payment_record = (
        overdue_count == 0
        and due_completion >= 0.98
        and due_unpaid_ratio == 0
        and paid_late_count <= 1
        and average_delay_days <= 5
    )

    if high_operational_risk:
        final_score = max(final_score, 65.0)
        # Prepayment is a positive signal, but it must never erase active serious arrears.
        final_score = max(65.0, final_score - prepayment_bonus_points * 0.15)
    elif medium_operational_risk:
        final_score = max(final_score, 35.0)
        final_score = max(35.0, final_score - prepayment_bonus_points * 0.35)
    elif clean_payment_record:
        # Strong payment behavior cannot become medium/high solely because the
        # economy is inflationary. Advance installments are an explicit positive signal.
        final_score = min(final_score - prepayment_bonus_points, 34.0)
        if prepaid_installment_count >= 1:
            final_score = min(final_score, 20.0)
        if prepaid_installment_count >= 2:
            final_score = min(final_score, 12.0)
    else:
        final_score = max(final_score - prepayment_bonus_points * 0.5, 0.0)

    final_score = float(np.clip(final_score, 0, 100))
    if clean_payment_record and prepaid_installment_count > 0:
        # Prepayment is a strong positive signal, not proof of zero future risk.
        final_score = max(final_score, 5.0)

    return {
        "score": round(final_score, 2),
        "payment_behavior_pressure": round(float(payment_behavior_pressure), 4),
        "future_pressure": round(float(future_pressure), 4),
        "macro_pressure": round(float(macro_pressure), 4),
        "ml_score": round(float(np.clip(ml_score, 0, 100)), 2),
        "high_operational_risk": high_operational_risk,
        "medium_operational_risk": medium_operational_risk,
        "clean_payment_record": clean_payment_record,
        "prepaid_installment_count": prepaid_installment_count,
        "prepayment_ratio": round(prepayment_ratio, 4),
        "prepayment_bonus_points": round(float(prepayment_bonus_points), 2),
        "weights": {
            "payment_behavior": 0.75,
            "future_obligation": 0.15,
            "macro_modifier": 0.10,
        },
    }

def delay_label_from_context(score: float, row: pd.Series) -> str:
    """Assign project risk using payment/cash-flow context before macro pressure.

    Iran's macro indicators are often structurally high. A project with healthy
    payment inflow should not become high/critical only because USD or inflation
    pressure is high. Critical risk is therefore gated by operational weakness.
    """
    cash_flow = _clip01(row.get("cash_flow_pressure_ratio", 0))
    completion = _clip01(row.get("project_payment_completion_ratio", 0))
    overdue = _clip01(row.get("overdue_payment_ratio", 0))
    high_member = _clip01(row.get("high_risk_member_ratio", 0))
    construction = float(row.get("predicted_construction_cost_growth", 0) or 0)

    late = _clip01(row.get("paid_late_payment_ratio", 0))
    medium_member = _clip01(row.get("medium_risk_member_ratio", 0))

    # Only genuinely clean projects should be protected as low-risk. This keeps
    # Shahrak Omid low when cash-flow is healthy, but lets projects with overdue
    # history or weak members move to medium/high.
    pristine_payment_context = (
        cash_flow < 0.14
        and completion >= 0.82
        and overdue == 0
        and late <= 0.35
        and high_member < 0.10
    )

    healthy_payment_context = (
        cash_flow < 0.20
        and completion >= 0.78
        and overdue <= 0.05
        and high_member < 0.15
    )

    # Critical requires operational weakness. Macro pressure alone cannot make
    # a project critical in the Iranian market context.
    if (
        score >= 55
        and cash_flow >= 0.40
        and (
            overdue >= 0.30
            or high_member >= 0.35
            or completion < 0.50
        )
    ):
        return "critical"

    # Truly clean projects stay low unless construction-cost pressure is extreme
    # and the contextual score also agrees.
    if pristine_payment_context:
        if construction >= 92 and score >= 34:
            return "medium"
        return "low" if score >= 10 else "acceptable_delay"

    # Healthy-but-not-perfect projects can become medium, but not high/critical,
    # unless operational weakness appears.
    if healthy_payment_context:
        if score >= 31 or construction >= 88 or late >= 0.50:
            return "medium"
        return "low" if score >= 16 else "acceptable_delay"

    if score >= 56:
        return "high"
    if score >= 30:
        return "medium"

    # Repeated late payments plus high build-cost pressure should not stay low.
    if construction >= 65 and score >= 26 and (late >= 0.35 or medium_member >= 0.70):
        return "medium"

    if score >= 16:
        return "low"

    return "acceptable_delay"


def _delay_months_from_context(score: float, label: str, ml_months: float) -> float:
    """Blend the ML month estimate with weighted contextual score.

    The synthetic regressor remains useful for scenario shape, but final months
    are dampened when operational payment health is strong.
    """
    score_based_months = float(np.clip((score / 100.0) * 72.0, 0.0, 90.0))
    blended = 0.25 * float(ml_months) + 0.75 * score_based_months

    if label == "acceptable_delay":
        return float(np.clip(blended, 0.0, 6.0))
    if label == "low":
        return float(np.clip(blended, 6.1, 12.0))
    if label == "medium":
        return float(np.clip(blended, 12.1, 24.0))
    if label == "high":
        return float(np.clip(blended, 24.1, 60.0))
    return float(np.clip(blended, 60.1, 120.0))


def _cap_delay_label_for_healthy_operations(
    classifier_label: str,
    row: pd.Series,
    contextual_score: float,
) -> str:
    """Apply only the existing healthy-project safeguards to the ML label.

    The earlier runtime replaced the classifier decision with a separate manual
    score, which substantially reduced held-out consistency. This keeps the
    validated classifier as the primary decision while retaining conservative
    caps for genuinely pristine or healthy payment operations.
    """
    order = {
        "acceptable_delay": 0,
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4,
    }
    label = classifier_label if classifier_label in order else "medium"
    cash_flow = _clip01(row.get("cash_flow_pressure_ratio", 0))
    completion = _clip01(row.get("project_payment_completion_ratio", 0))
    overdue = _clip01(row.get("overdue_payment_ratio", 0))
    late = _clip01(row.get("paid_late_payment_ratio", 0))
    high_member = _clip01(row.get("high_risk_member_ratio", 0))
    construction = _safe_float(row.get("predicted_construction_cost_growth", 0))

    pristine = (
        cash_flow < 0.14
        and completion >= 0.82
        and overdue == 0
        and late <= 0.35
        and high_member < 0.10
    )
    healthy = (
        cash_flow < 0.20
        and completion >= 0.78
        and overdue <= 0.05
        and high_member < 0.15
    )

    if pristine:
        maximum = "medium" if construction >= 92 and contextual_score >= 34 else "low"
        if order[label] > order[maximum]:
            return maximum
    elif healthy and order[label] > order["medium"]:
        return "medium"

    return label


def _delay_months_consistent_with_label(months: float, label: str) -> float:
    numeric = float(np.clip(months, 0, 120))

    if label == "acceptable_delay":
        return float(np.clip(numeric, 0.0, 6.0))
    if label == "low":
        return float(np.clip(numeric, 6.01, 12.0))
    if label == "medium":
        return float(np.clip(numeric, 12.01, 24.0))
    if label == "high":
        return float(np.clip(numeric, 24.01, 60.0))
    return float(np.clip(numeric, 60.01, 120.0))


def calculate_contextual_delay_score(row: pd.Series) -> dict[str, Any]:
    """Weighted risk score tuned for Iranian cooperative-housing projects.

    Weights:
    - cash-flow / payment behavior: 65%
    - member risk concentration: 15%
    - construction cost growth: 15%
    - broader macro pressure: 5%
    """
    cash_flow = _clip01(row.get("cash_flow_pressure_ratio", 0))
    payment_incompletion = 1.0 - _clip01(row.get("project_payment_completion_ratio", 0))
    overdue = _clip01(row.get("overdue_payment_ratio", 0))
    late = _clip01(row.get("paid_late_payment_ratio", 0))

    member_pressure = (
        _clip01(row.get("low_risk_member_ratio", 0)) * 0.10
        + _clip01(row.get("medium_risk_member_ratio", 0)) * 0.45
        + _clip01(row.get("high_risk_member_ratio", 0)) * 1.00
    )

    # Iran-context baselines. Values below these baselines should not dominate
    # the label because high inflation / FX volatility is a structural condition.
    construction_pressure = _normalize_percent(
        row.get("predicted_construction_cost_growth", 0), baseline=45, ceiling=95
    )
    inflation_pressure = _normalize_percent(
        row.get("predicted_general_inflation_rate", 0), baseline=40, ceiling=85
    )
    usd_pressure = _normalize_percent(
        row.get("predicted_usd_growth", 0), baseline=90, ceiling=180
    )
    macro_pressure = 0.35 * inflation_pressure + 0.65 * usd_pressure

    payment_pressure = (
        0.45 * cash_flow
        + 0.25 * payment_incompletion
        + 0.20 * overdue
        + 0.10 * late
    )

    score = 100.0 * (
        0.65 * payment_pressure
        + 0.15 * member_pressure
        + 0.15 * construction_pressure
        + 0.05 * macro_pressure
    )

    return {
        "score": round(float(np.clip(score, 0, 100)), 2),
        "payment_pressure": round(float(payment_pressure), 4),
        "member_pressure": round(float(member_pressure), 4),
        "construction_pressure": round(float(construction_pressure), 4),
        "macro_pressure": round(float(macro_pressure), 4),
        "weights": {
            "payment_and_cash_flow": 0.65,
            "member_risk": 0.15,
            "construction_cost_growth": 0.15,
            "macro_pressure": 0.05,
        },
    }


def delay_label_from_months(months: float) -> str:
    if months <= 6:
        return "acceptable_delay"
    if months <= 12:
        return "low"
    if months <= 24:
        return "medium"
    if months <= 60:
        return "high"
    return "critical"


def buyer_reasons(row: pd.Series) -> list[str]:
    reasons: list[str] = []

    due_completion = _clip01(
        row.get(
            "due_payment_completion_ratio_calc",
            row.get("due_payment_completion_ratio", 0),
        )
    )
    due_unpaid_ratio = _clip01(
        row.get(
            "due_unpaid_amount_ratio_calc",
            row.get("due_unpaid_amount_ratio", 0),
        )
    )
    overdue_count = int(_safe_float(row.get("overdue_count", 0)))
    late_count = int(_safe_float(row.get("paid_late_count", 0)))
    average_delay = _safe_float(row.get("average_delay_days", 0))
    prepaid_count = max(int(_safe_float(row.get("prepaid_installment_count", 0))), 0)

    if prepaid_count >= 2:
        reasons.append(f"{prepaid_count} future installments were paid in advance")
    elif prepaid_count == 1:
        reasons.append("One future installment was paid in advance")

    if overdue_count >= 2:
        reasons.append("Multiple overdue payments")
    elif overdue_count == 1:
        reasons.append("One overdue payment")

    if due_unpaid_ratio >= 0.35:
        reasons.append("A large share of due payments is still unpaid")
    elif due_unpaid_ratio >= 0.10:
        reasons.append("Some due payment amount remains unpaid")

    if due_completion < 0.70:
        reasons.append("Due-payment completion is weak")
    elif due_completion < 0.90:
        reasons.append("Due-payment completion is below target")

    if late_count >= 2:
        reasons.append("Repeated late payments")
    if average_delay >= 20:
        reasons.append("Average payment delay is high")

    if not reasons:
        if due_completion >= 0.98 and overdue_count == 0:
            reasons.append("Due payments are complete with no overdue balance")
        else:
            reasons.append("Payment behavior is currently stable")

    if len(reasons) < 4 and row.get("construction_cost_growth", 0) >= 70:
        reasons.append("Construction-cost pressure increases future obligations")

    return reasons[:4]

def delay_reasons(row: pd.Series, context: dict[str, Any] | None = None) -> list[str]:
    reasons: list[str] = []
    context = context or {}

    if row.get("cash_flow_pressure_ratio", 0) >= 0.40:
        reasons.append("Cash-flow pressure is elevated")
    elif row.get("project_payment_completion_ratio", 0) >= 0.70 and row.get("overdue_payment_ratio", 0) == 0:
        reasons.append("Payment completion is healthy and there are no overdue payments")

    if row.get("high_risk_member_ratio", 0) >= 0.30:
        reasons.append("High-risk member ratio is significant")
    if row.get("overdue_payment_ratio", 0) >= 0.25:
        reasons.append("Overdue payment ratio is high")
    if row.get("project_payment_completion_ratio", 1) < 0.60:
        reasons.append("Project payment completion is weak")
    if row.get("predicted_construction_cost_growth", 0) >= 65:
        reasons.append("Construction cost growth is high")
    if context.get("macro_pressure", 0) >= 0.70:
        reasons.append("Macro pressure is high but treated as a modifier, not the main driver")

    return reasons[:4] or ["No single dominant delay driver detected"]


def predict_buyer_risk(payload: dict[str, Any], model_path: str | Path | None = None) -> dict[str, Any]:
    artifact = _load_artifact(model_path, MODEL_DIR / "buyer_risk_v2.joblib")
    raw = _as_frame(payload)
    enriched = add_buyer_features(raw)
    x = _fill_missing_model_features(enriched, artifact["features"])

    raw_ml_score = float(np.clip(artifact["regressor"].predict(x)[0], 0, 100))
    probabilities = {}
    classifier_label = buyer_label_from_score(raw_ml_score)
    if "classifier" in artifact:
        clf = artifact["classifier"]
        proba = clf.predict_proba(x)[0]
        probabilities = {str(cls): float(p) for cls, p in zip(clf.classes_, proba)}
        classifier_label = str(clf.predict(x)[0])

    row = enriched.iloc[0]
    context = calculate_contextual_buyer_score(row, raw_ml_score)
    score = _buyer_score_consistent_with_label(raw_ml_score, classifier_label)

    # The stored v2 model predates the new prepayment feature. Keep its validated
    # behavior for legacy rows, but apply the explicit business-context bonus when
    # real prepayment evidence is present. This avoids pretending the old model was
    # trained on a feature it never saw.
    if int(_safe_float(row.get("prepaid_installment_count", 0))) > 0:
        score = min(score, float(context["score"]))

    label = buyer_label_from_score(score)

    raw_label = buyer_label_from_score(raw_ml_score)
    probability_peak = max(probabilities.values() or [0])
    confidence = (
        "high"
        if probability_peak >= 0.70 and raw_label == classifier_label
        else "medium"
    )

    return {
        "risk_score": round(score, 2),
        "raw_ml_risk_score": round(raw_ml_score, 2),
        "risk_label": label,
        "label_probabilities": probabilities,
        "confidence": confidence,
        "reasons": buyer_reasons(row),
        "contextual_components": context,
        "model_version": MODEL_VERSION,
    }

def predict_project_delay(payload: dict[str, Any], model_path: str | Path | None = None) -> dict[str, Any]:
    artifact = _load_artifact(model_path, MODEL_DIR / "project_delay_v2.joblib")
    raw = _as_frame(payload)
    enriched = add_delay_features(raw)
    x = _fill_missing_model_features(enriched, artifact["features"])

    ml_months = float(np.clip(artifact["regressor"].predict(x)[0], 0, 120))
    row = enriched.iloc[0]
    context = calculate_contextual_delay_score(row)
    contextual_score = float(context["score"])

    probabilities = {}
    classifier_label = delay_label_from_months(ml_months)
    if "classifier" in artifact:
        clf = artifact["classifier"]
        proba = clf.predict_proba(x)[0]
        probabilities = {str(cls): float(p) for cls, p in zip(clf.classes_, proba)}
        classifier_label = str(clf.predict(x)[0])

    label = _cap_delay_label_for_healthy_operations(
        classifier_label,
        row,
        contextual_score,
    )
    months = _delay_months_consistent_with_label(ml_months, label)

    confidence = (
        "high"
        if max(probabilities.values() or [0]) >= 0.70 and label == classifier_label
        else "medium"
    )

    return {
        "predicted_delay_months": round(months, 2),
        "raw_ml_predicted_delay_months": round(ml_months, 2),
        "delay_risk_level": label,
        "contextual_delay_score": round(contextual_score, 2),
        "contextual_components": context,
        "label_probabilities": probabilities,
        "confidence": confidence,
        "reasons": delay_reasons(row, context),
        "model_version": MODEL_VERSION,
    }


def _hybrid_forecast_series(series: pd.Series, clip_min: float, clip_max: float, horizon_months: int) -> tuple[float, str, dict[str, Any]]:
    """Return a persistence-anchored, horizon-aware macro forecast.

    Rolling-origin backtesting showed that the earlier hybrid was too responsive
    to short, noisy rate movements. A 90% persistence anchor with a 10% bounded
    horizon component reduced aggregate historical MAE while different project
    horizons still affect the returned pressure estimate.
    """
    s = series.dropna().astype(float)
    if s.empty:
        return 0.0, "low", {"reason": "no usable observations"}

    horizon_months = int(max(1, min(horizon_months, 60)))

    last = float(s.iloc[-1])
    roll3 = float(s.tail(3).mean())
    roll6 = float(s.tail(6).mean()) if len(s) >= 6 else roll3
    roll12 = float(s.tail(12).mean()) if len(s) >= 12 else roll6

    recent_diffs = s.diff().dropna().tail(6)
    monthly_trend = float(recent_diffs.mean()) if not recent_diffs.empty else 0.0

    # Horizon-aware but bounded: longer projects carry more macro exposure, but
    # the adjustment is clipped so a noisy recent month cannot dominate output.
    trend_adjustment = np.clip(monthly_trend * horizon_months * 0.12, -18, 18)

    # Longer horizons lean slightly more on the 12-month average to avoid simply
    # repeating the last observed value for every project.
    horizon_weight = min(horizon_months / 60, 1.0)
    short_term_component = 0.55 * last + 0.30 * roll3 + 0.15 * roll6
    long_term_component = 0.35 * last + 0.25 * roll6 + 0.40 * roll12
    horizon_candidate = (
        (1 - horizon_weight) * short_term_component
        + horizon_weight * long_term_component
        + trend_adjustment
    )
    forecast = 0.90 * last + 0.10 * horizon_candidate
    forecast = float(np.clip(forecast, clip_min, clip_max))

    confidence = "medium" if len(s) >= 24 else "low"
    return forecast, confidence, {
        "last_value": last,
        "rolling_3": roll3,
        "rolling_6": roll6,
        "rolling_12": roll12,
        "monthly_trend": monthly_trend,
        "trend_adjustment": float(trend_adjustment),
        "horizon_candidate": float(horizon_candidate),
        "persistence_weight": 0.90,
        "horizon_component_weight": 0.10,
        "horizon_months": horizon_months,
        "observations": int(len(s)),
    }


def forecast_economic_indicators(
    model_path: str | Path | None = None,
    horizon_months: int = 12,
) -> dict[str, Any]:
    artifact = _load_artifact(model_path, MODEL_DIR / "economic_forecaster_v2.joblib")
    df = pd.DataFrame(artifact["history"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    result: dict[str, Any] = {
        "horizon_months": horizon_months,
        "model_version": MODEL_VERSION,
        "method": "persistence_anchored_horizon_blend_with_staleness_confidence",
        "forecasts": {},
    }

    for col, config in artifact["targets"].items():
        low, high = config["clip"]
        forecast, confidence, details = _hybrid_forecast_series(df[col], low, high, horizon_months)

        valid = df.dropna(subset=[col])
        last_date = str(valid["date"].max().date()) if not valid.empty else None
        # Confidence is downgraded if the latest usable macro point is stale.
        if valid.shape[0] > 0:
            months_stale = (df["date"].max().year - valid["date"].max().year) * 12 + (df["date"].max().month - valid["date"].max().month)
            details["months_stale"] = int(months_stale)
            if months_stale >= 6:
                confidence = "low"

        result["forecasts"][col] = {
            "value": round(forecast, 2),
            "confidence": confidence,
            "last_observed_date": last_date,
            "details": details,
        }

    return result
