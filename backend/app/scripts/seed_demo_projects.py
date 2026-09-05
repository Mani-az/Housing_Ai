"""Create the four projects used by the demo seed chain.

Run from the backend folder:
    python -m app.scripts.seed_demo_projects

The script is idempotent. Existing projects are reused without modification;
only missing demo projects are inserted.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.database import SessionLocal, engine

# Import every mapped model before create_all so a fresh database gets the full
# application schema even when this script is run before the API.
from app.models import (  # noqa: F401
    auth_account,
    economic_indicator,
    expense,
    membership_request,
    payment,
    payment_plan,
    project,
    project_owner,
    project_participant,
    property_listing,
    risk_data,
    user,
)
from app.models.project import Project


PROJECT_SPECS = (
    {
        "name": "Niavaran Sapphire Residences",
        "neighborhood_english": "Niavaran",
        "status": "planning",
    },
    {
        "name": "Saadat Abad Negin Tower",
        "neighborhood_english": "Saadat Abad",
        "status": "active",
    },
    {
        "name": "Mehr Housing Tower Phase 3",
        "neighborhood_english": "Narmak",
        "status": "delayed",
    },
    {
        "name": "Shahrak Omid Apartment",
        "neighborhood_english": "Yousef Abad",
        "status": "completed",
    },
)

TOTAL_UNITS = 5
AVERAGE_UNIT_AREA = 100.0
DATASET_PATH = Path("data/tehran_properties.xlsx")
FRONTEND_APP_PATH = Path("../frontend/src/AppUpdated.jsx")


def _frontend_neighborhoods(path: Path) -> set[str]:
    source = path.read_text(encoding="utf-8")
    match = re.search(
        r"const\s+TEHRAN_NEIGHBORHOOD_OPTIONS\s*=\s*\[(.*?)\];",
        source,
        flags=re.DOTALL,
    )
    if not match:
        raise RuntimeError(f"Could not locate TEHRAN_NEIGHBORHOOD_OPTIONS in {path}.")

    return set(re.findall(r'"value"\s*:\s*"([^"]+)"', match.group(1)))


def _median_unit_prices(
    dataset_path: Path,
) -> pd.Series:
    data = pd.read_excel(
        dataset_path,
        usecols=["Neighborhood (English)", "Price per Square Meter"],
    )
    data["Neighborhood (English)"] = data["Neighborhood (English)"].astype("string").str.strip()
    data["Price per Square Meter"] = pd.to_numeric(
        data["Price per Square Meter"],
        errors="coerce",
    )
    return data.dropna(
        subset=["Neighborhood (English)", "Price per Square Meter"]
    ).groupby("Neighborhood (English)")["Price per Square Meter"].median()


def _verified_median_prices() -> dict[str, float]:
    frontend_neighborhoods = _frontend_neighborhoods(FRONTEND_APP_PATH)
    median_prices = _median_unit_prices(DATASET_PATH)
    dataset_neighborhoods = {str(value) for value in median_prices.index}
    intersection = frontend_neighborhoods & dataset_neighborhoods

    invalid_neighborhoods = {
        spec["neighborhood_english"]
        for spec in PROJECT_SPECS
        if spec["neighborhood_english"] not in intersection
    }
    if invalid_neighborhoods:
        raise RuntimeError(
            "Configured demo neighborhoods are not present in both the frontend "
            f"options and the property dataset: {sorted(invalid_neighborhoods)}"
        )

    forbidden_neighborhoods = {"Mehrabad", "Omid Town"}
    if forbidden_neighborhoods & {
        spec["neighborhood_english"] for spec in PROJECT_SPECS
    }:
        raise RuntimeError("Demo projects must not use empty dataset neighborhoods.")

    print(
        "Verified neighborhood intersection: "
        f"{len(intersection)} shared options; using "
        f"{', '.join(spec['neighborhood_english'] for spec in PROJECT_SPECS)}."
    )
    return {
        spec["neighborhood_english"]: float(median_prices[spec["neighborhood_english"]])
        for spec in PROJECT_SPECS
    }


def seed_demo_projects() -> None:
    Base.metadata.create_all(bind=engine)

    median_prices = _verified_median_prices()
    db: Session = SessionLocal()
    created_count = 0
    reused_count = 0
    try:
        for spec in PROJECT_SPECS:
            existing = db.query(Project).filter(Project.name == spec["name"]).first()
            if existing:
                reused_count += 1
                if int(existing.total_units or 0) < TOTAL_UNITS:
                    print(
                        "Warning: reused project "
                        f"{existing.name!r} has total_units={existing.total_units}; "
                        f"the member seed needs at least {TOTAL_UNITS}."
                    )
                print(f"Reused existing project: {existing.name} (id={existing.id})")
                continue

            neighborhood = spec["neighborhood_english"]
            estimated_total_cost = round(
                median_prices[neighborhood] * TOTAL_UNITS * AVERAGE_UNIT_AREA,
                2,
            )
            new_project = Project(
                name=spec["name"],
                location="Tehran",
                neighborhood_english=neighborhood,
                total_units=TOTAL_UNITS,
                average_unit_area=AVERAGE_UNIT_AREA,
                estimated_total_cost=estimated_total_cost,
                status=spec["status"],
            )
            db.add(new_project)
            db.commit()
            db.refresh(new_project)
            created_count += 1
            print(
                f"Created project: {new_project.name} (id={new_project.id}, "
                f"neighborhood={neighborhood}, median_unit_price={median_prices[neighborhood]:.2f}, "
                f"estimated_total_cost={estimated_total_cost:.2f})"
            )

        print(
            f"Done. Created projects: {created_count}; "
            f"reused projects: {reused_count}."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_projects()
