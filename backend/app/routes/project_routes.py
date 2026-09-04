from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectMarketEstimateResponse,
    ProjectFutureEstimateResponse,
    AnnualCostSplitResponse,
    NextYearCostSplitResponse,
)
from app.services.project_service import (
    create_project,
    get_projects,
    get_project_by_id,
    get_project_market_estimate,
    get_project_future_estimate,
    calculate_annual_cost_split,
    calculate_next_year_cost_split,
    delete_project,
)


router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.post("/", response_model=ProjectResponse)
def create_new_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
):
    return create_project(db=db, project_data=project_data)


@router.get("/", response_model=list[ProjectResponse])
def read_projects(
    db: Session = Depends(get_db),
):
    return get_projects(db=db)


@router.get("/{project_id}/market-estimate", response_model=ProjectMarketEstimateResponse)
def read_project_market_estimate(
    project_id: int,
    db: Session = Depends(get_db),
):
    return get_project_market_estimate(db=db, project_id=project_id)

@router.get(
    "/{project_id}/future-estimate",
    response_model=ProjectFutureEstimateResponse,
)
def read_project_future_estimate(
    project_id: int,
    years: int = 2,
    db: Session = Depends(get_db),
):
    return get_project_future_estimate(
        db=db,
        project_id=project_id,
        years=years,
    )

@router.get(
    "/{project_id}/annual-cost-split",
    response_model=AnnualCostSplitResponse,
)
def read_annual_cost_split(
    project_id: int,
    year: int,
    annual_cost: float,
    db: Session = Depends(get_db),
):
    return calculate_annual_cost_split(
        db=db,
        project_id=project_id,
        year=year,
        annual_cost=annual_cost,
    )

@router.get(
    "/{project_id}/next-year-cost-split",
    response_model=NextYearCostSplitResponse,
)
def read_next_year_cost_split(
    project_id: int,
    db: Session = Depends(get_db),
):
    return calculate_next_year_cost_split(
        db=db,
        project_id=project_id,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Delete a project and its related records (admin UI action)."""
    delete_project(db=db, project_id=project_id)
    return None


@router.get("/{project_id}", response_model=ProjectResponse)
def read_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    return get_project_by_id(db=db, project_id=project_id)
