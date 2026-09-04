from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.valuation import (
    ProjectValuationRequest,
    ProjectValuationResponse,
    PropertyValuationRequest,
    PropertyValuationResponse,
)
from app.services.valuation_service import estimate_project_value, estimate_single_property


router = APIRouter(
    prefix="/ml/valuation",
    tags=["Property Estimation"],
)


@router.post("/property", response_model=PropertyValuationResponse)
def read_single_property_valuation(
    payload: PropertyValuationRequest,
    db: Session = Depends(get_db),
):
    """Estimate one property's market value for the Admin/Owner Projects tool."""
    return estimate_single_property(db=db, payload=payload)


@router.post("/project", response_model=ProjectValuationResponse)
def read_project_valuation(
    payload: ProjectValuationRequest,
    db: Session = Depends(get_db),
):
    """Estimate a construction project's market value for the Admin/Owner tool."""
    return estimate_project_value(db=db, payload=payload)
