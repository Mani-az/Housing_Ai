"""Market valuation service built on the existing property-listing dataset.

The project currently has no persisted property-price model artifact.  This
service therefore trains a small, deterministic Random Forest at request time
from the existing imported listings, with lightweight synthetic perturbations
to improve scenario coverage.  It never changes financial/project records.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from fastapi import HTTPException, status
from sklearn.ensemble import RandomForestRegressor
from sqlalchemy.orm import Session

from app.models.economic_indicator import EconomicIndicator
from app.models.property_listing import PropertyListing
from app.schemas.valuation import ProjectValuationRequest, PropertyValuationRequest


MODEL_NAME = "property_market_random_forest_v1"
DEFAULT_PRICE_PER_SQM = 75_000_000.0
# The imported listing workbook is historical.  This transparent calibration
# maps its inflation-adjusted values to the current Tehran demo-market level
# (Jordan is approximately 600–700 million Toman/m²), while preserving the
# ML-estimated relative effects of area, age and floor.
CURRENT_MARKET_CALIBRATION_FACTOR = 5.2
# The 5.2 calibration is anchored to the latest usable housing-CPI point in
# the supplied macro dataset (September 2025).  If the economic-indicator
# import is refreshed with a newer Housing CPI value, valuations move with it
# instead of remaining permanently tied to a hard-coded "today" value.
HOUSING_CPI_REFERENCE = 343.4
GENERAL_CPI_REFERENCE = 384.6
CONDITION_MULTIPLIERS = {
    "new": 1.06,
    "excellent": 1.06,
    "renovated": 1.08,
    "good": 1.0,
    "standard": 1.0,
    "needs_renovation": 0.91,
    "old": 0.88,
}
BUILDING_TYPE_MULTIPLIERS = {
    "luxury": 1.12,
    "modern": 1.07,
    "standard": 1.0,
    "apartment": 1.0,
    "villa": 1.08,
    "commercial": 1.04,
}


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def _load_listing_rows(db: Session, neighborhood: str) -> tuple[pd.DataFrame, int, bool]:
    matching = (
        db.query(PropertyListing)
        .filter(PropertyListing.neighborhood_english.ilike(f"%{neighborhood}%"))
        .limit(5000)
        .all()
    )
    exact_match_count = len(matching)
    uses_citywide_fallback = exact_match_count < 8
    rows = matching
    if uses_citywide_fallback:
        rows = (
            db.query(PropertyListing)
            .filter(PropertyListing.base_area.isnot(None))
            .limit(5000)
            .all()
        )

    records = []
    for item in rows:
        area = _safe_float(item.base_area)
        price = _safe_float(item.adjusted_price_per_square_meter)
        if price is None:
            raw_price = _safe_float(item.price_per_square_meter)
            factor = _safe_float(item.inflation_factor) or 1.0
            price = raw_price * factor if raw_price is not None else None
        if area is None or area <= 0 or price is None or price <= 0:
            continue
        records.append(
            {
                "area": area,
                "age": max(0.0, _safe_float(item.building_age) or 0.0),
                "floor": _safe_float(item.floor_level),
                "price": price,
            }
        )

    frame = pd.DataFrame(records)
    if frame.empty:
        return frame, exact_match_count, uses_citywide_fallback
    frame["floor"] = frame["floor"].fillna(frame["floor"].median()).fillna(2.0)
    return frame, exact_match_count, uses_citywide_fallback


def _economic_market_adjustment(db: Session) -> tuple[float, str]:
    """Return a current-market multiplier from imported economic indicators.

    The property listings are from 2013 and the macro file begins much later,
    so the historical import factor remains the bridge to the source period.
    This function then keeps the current-market calibration responsive to the
    most recent available housing-CPI value.  General CPI is a clearly marked
    backup when Housing CPI has not been imported.
    """
    index_sources = (
        ("housing_cpi_index", HOUSING_CPI_REFERENCE, "Housing CPI"),
        ("cpi_index", GENERAL_CPI_REFERENCE, "General CPI"),
    )
    for field_name, reference_value, label in index_sources:
        field = getattr(EconomicIndicator, field_name)
        row = (
            db.query(EconomicIndicator)
            .filter(field.isnot(None))
            .order_by(EconomicIndicator.year.desc(), EconomicIndicator.month.desc())
            .first()
        )
        index_value = _safe_float(getattr(row, field_name, None)) if row else None
        if index_value is not None and index_value > 0:
            # Prevent a malformed or partial macro import from distorting a
            # property estimate by several orders of magnitude.
            multiplier = float(np.clip(index_value / reference_value, 0.65, 1.50))
            return multiplier, f"{label} {row.year}-{row.month:02d}"
    return 1.0, "economic index unavailable (reference calibration retained)"


def _augment_training_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Add deterministic synthetic scenarios without altering stored listings."""
    if frame.empty:
        return frame
    rng = np.random.default_rng(42)
    augmented = [frame]
    for _ in range(2):
        copy = frame.copy()
        copy["area"] = (copy["area"] * rng.normal(1.0, 0.04, len(copy))).clip(lower=20)
        copy["age"] = (copy["age"] + rng.integers(-1, 2, len(copy))).clip(lower=0)
        copy["price"] = (copy["price"] * rng.normal(1.0, 0.025, len(copy))).clip(lower=1)
        augmented.append(copy)
    return pd.concat(augmented, ignore_index=True)


def _fit_price_model(
    frame: pd.DataFrame,
    area: float,
    building_age: int,
    floor: int | None,
) -> tuple[float, float, str]:
    """Return price prediction, confidence and model label."""
    if len(frame) < 12:
        return float(frame["price"].median()) if not frame.empty else DEFAULT_PRICE_PER_SQM, 45.0, "neighborhood_median_fallback"

    training = _augment_training_data(frame)
    features = ["area", "age", "floor"]
    split = max(8, int(len(training) * 0.8))
    model = RandomForestRegressor(
        n_estimators=80,
        max_depth=10,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(training[features].iloc[:split], training["price"].iloc[:split])
    validation = model.predict(training[features].iloc[split:])
    actual = training["price"].iloc[split:].to_numpy()
    relative_error = float(np.mean(np.abs(validation - actual) / np.maximum(actual, 1.0)))
    model.fit(training[features], training["price"])
    query = pd.DataFrame([{
        "area": area,
        "age": building_age,
        "floor": floor if floor is not None else float(frame["floor"].median()),
    }])
    confidence = 58.0 + min(len(frame), 400) / 12.0
    confidence += 10.0 if relative_error <= 0.15 else 4.0 if relative_error <= 0.25 else 0.0
    return float(model.predict(query[features])[0]), min(confidence, 94.0), MODEL_NAME


def _confidence_label(value: float) -> str:
    if value >= 80:
        return "High"
    if value >= 60:
        return "Medium"
    return "Low"


def _estimate_price_per_sqm(
    db: Session,
    neighborhood: str,
    area: float,
    building_age: int,
    floor: int | None,
    rooms: int | None,
    elevator: bool,
    parking: bool,
    storage: bool,
    condition: str,
) -> dict[str, Any]:
    frame, matching_count, uses_citywide_fallback = _load_listing_rows(db, neighborhood)
    if frame.empty:
        base = DEFAULT_PRICE_PER_SQM
        confidence = 35.0
        model_name = "market_baseline_fallback"
        sample_count = 0
    else:
        base, confidence, model_name = _fit_price_model(
            frame,
            area=area,
            building_age=building_age,
            floor=floor,
        )
        # This number deliberately reports direct neighborhood evidence, not
        # the much larger Tehran-wide data used only when that evidence is
        # absent.  It makes an unknown neighborhood visibly lower-confidence.
        sample_count = matching_count

    if uses_citywide_fallback:
        confidence = min(confidence, 45.0)
        model_name = f"{model_name}_citywide_fallback"

    factors = []
    amenities_multiplier = 1.0
    if rooms is not None:
        room_adjustment = 1.0 + max(-0.03, min(0.045, (rooms - 2) * 0.015))
        amenities_multiplier *= room_adjustment
        factors.append(f"{rooms} rooms considered")
    if elevator:
        amenities_multiplier *= 1.03
        factors.append("elevator premium")
    if parking:
        amenities_multiplier *= 1.04
        factors.append("parking premium")
    if storage:
        amenities_multiplier *= 1.015
        factors.append("storage premium")
    normalized_condition = condition.strip().lower().replace(" ", "_")
    condition_multiplier = CONDITION_MULTIPLIERS.get(normalized_condition, 1.0)
    if condition_multiplier != 1.0:
        factors.append(f"{normalized_condition.replace('_', ' ')} condition adjustment")
    if building_age:
        factors.append(f"building age: {building_age} years")

    if uses_citywide_fallback:
        factors.append("no reliable neighborhood samples; Tehran-wide fallback used")
    else:
        factors.append(f"{sample_count} neighborhood market samples")

    economic_multiplier, economic_source = _economic_market_adjustment(db)
    factors.append(f"{economic_source} adjustment: {economic_multiplier:.2f}x")

    adjusted = max(
        1.0,
        base
        * amenities_multiplier
        * condition_multiplier
        * CURRENT_MARKET_CALIBRATION_FACTOR
        * economic_multiplier,
    )
    spread = 0.12 if sample_count >= 20 and not uses_citywide_fallback else 0.20
    return {
        "price_per_sqm": adjusted,
        "range_min_per_sqm": adjusted * (1 - spread),
        "range_max_per_sqm": adjusted * (1 + spread),
        "confidence": round(confidence, 1),
        "confidence_label": _confidence_label(confidence),
        "market_samples_used": sample_count,
        "model_name": model_name,
        "factors": factors or ["neighborhood market baseline", "area and building age"],
    }


def estimate_single_property(db: Session, payload: PropertyValuationRequest) -> dict[str, Any]:
    if payload.city.strip().lower() not in {"tehran", "تهران"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The current property dataset supports Tehran only.",
        )
    result = _estimate_price_per_sqm(
        db=db,
        neighborhood=payload.neighborhood,
        area=payload.area,
        building_age=payload.building_age,
        floor=payload.floor,
        rooms=payload.rooms,
        elevator=payload.elevator,
        parking=payload.parking,
        storage=payload.storage,
        condition=payload.property_condition,
    )
    total = result["price_per_sqm"] * payload.area
    factors = result["factors"]
    return {
        "estimation_type": "single_property",
        "city": payload.city,
        "neighborhood": payload.neighborhood,
        "area": payload.area,
        "estimated_total_price": round(total, 2),
        "estimated_price_per_sqm": round(result["price_per_sqm"], 2),
        "price_range_min": round(result["range_min_per_sqm"] * payload.area, 2),
        "price_range_max": round(result["range_max_per_sqm"] * payload.area, 2),
        "confidence": result["confidence"],
        "confidence_label": result["confidence_label"],
        "market_samples_used": result["market_samples_used"],
        "model_name": result["model_name"],
        "influential_factors": factors,
        "explanation": "The estimate combines neighborhood market evidence with area, building age and available property features.",
        "model_note": "Market estimate only: trained from historical real listings, adjusted through the imported inflation factor and latest available economic index, then augmented with deterministic synthetic scenarios; it is not a guaranteed sale price.",
    }


def estimate_project_value(db: Session, payload: ProjectValuationRequest) -> dict[str, Any]:
    if payload.city.strip().lower() not in {"tehran", "تهران"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The current property dataset supports Tehran only.",
        )
    total_area = payload.total_area or payload.total_units * payload.average_unit_area
    result = _estimate_price_per_sqm(
        db=db,
        neighborhood=payload.neighborhood,
        area=payload.average_unit_area,
        building_age=0,
        floor=None,
        rooms=None,
        elevator=False,
        parking=False,
        storage=False,
        condition="standard",
    )
    type_key = payload.building_type.strip().lower().replace(" ", "_")
    type_multiplier = BUILDING_TYPE_MULTIPLIERS.get(type_key, 1.0)
    price_per_sqm = result["price_per_sqm"] * type_multiplier
    total = price_per_sqm * total_area
    factors = result["factors"] + [f"{type_key.replace('_', ' ')} building type"]
    return {
        "estimation_type": "construction_project",
        "city": payload.city,
        "neighborhood": payload.neighborhood,
        "total_units": payload.total_units,
        "average_unit_area": payload.average_unit_area,
        "total_area": total_area,
        "estimated_total_project_value": round(total, 2),
        "estimated_value_per_unit": round(total / payload.total_units, 2),
        "estimated_price_per_sqm": round(price_per_sqm, 2),
        "price_range_min": round(result["range_min_per_sqm"] * type_multiplier * total_area, 2),
        "price_range_max": round(result["range_max_per_sqm"] * type_multiplier * total_area, 2),
        "confidence": result["confidence"],
        "confidence_label": result["confidence_label"],
        "market_samples_used": result["market_samples_used"],
        "model_name": result["model_name"],
        "influential_factors": factors,
        "explanation": "Total project value is calculated as total area multiplied by the predicted market price per square metre.",
        "model_note": "Market estimate only: historical real listings are adjusted through the imported inflation factor and latest available economic index, then combined with deterministic synthetic scenarios; construction cost, land title and final sale price are not guaranteed.",
    }
