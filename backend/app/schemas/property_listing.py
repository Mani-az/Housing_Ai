from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PropertyListingResponse(BaseModel):
    id: int

    source_listing_id: Optional[str] = None
    source: str

    submission_date: Optional[str] = None

    exact_location: Optional[str] = None
    neighborhood_name: Optional[str] = None
    neighborhood_english: Optional[str] = None

    base_area: Optional[float] = None
    floor_level: Optional[int] = None
    building_age: Optional[int] = None

    price_per_square_meter: Optional[float] = None
    total_price: Optional[float] = None

    listing_year: Optional[int] = None

    inflation_factor: float
    adjusted_price_per_square_meter: Optional[float] = None
    adjusted_total_price: Optional[float] = None

    imported_at: datetime

    class Config:
        from_attributes = True


class PropertySummaryResponse(BaseModel):
    total_listings: int
    average_price_per_meter: Optional[float] = None
    average_adjusted_price_per_meter: Optional[float] = None
    average_total_price: Optional[float] = None
    average_adjusted_total_price: Optional[float] = None
    min_area: Optional[float] = None
    max_area: Optional[float] = None


class NeighborhoodStatsResponse(BaseModel):
    neighborhood_english: Optional[str] = None
    neighborhood_name: Optional[str] = None
    total_listings: int
    average_area: Optional[float] = None
    average_price_per_meter: Optional[float] = None
    average_adjusted_price_per_meter: Optional[float] = None