from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.property_listing import (
    PropertyListingResponse,
    PropertySummaryResponse,
    NeighborhoodStatsResponse,
)
from app.services.property_service import (
    get_property_listings,
    get_property_listing_by_id,
    get_property_summary,
    get_neighborhood_stats,
)


router = APIRouter(
    prefix="/properties",
    tags=["Property Listings"],
)


@router.get("/", response_model=list[PropertyListingResponse])
def read_property_listings(
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    neighborhood: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return get_property_listings(
        db=db,
        skip=skip,
        limit=limit,
        neighborhood=neighborhood,
    )


@router.get("/stats/summary", response_model=PropertySummaryResponse)
def read_property_summary(
    db: Session = Depends(get_db),
):
    return get_property_summary(db=db)


@router.get("/stats/by-neighborhood", response_model=list[NeighborhoodStatsResponse])
def read_neighborhood_stats(
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    return get_neighborhood_stats(db=db, limit=limit)


@router.get("/{property_id}", response_model=PropertyListingResponse)
def read_property_listing(
    property_id: int,
    db: Session = Depends(get_db),
):
    return get_property_listing_by_id(db=db, property_id=property_id)