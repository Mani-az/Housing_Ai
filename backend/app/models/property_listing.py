from sqlalchemy import Column, Integer, Float, DateTime, Unicode
from sqlalchemy.sql import func

from app.database.base import Base


class PropertyListing(Base):
    __tablename__ = "property_listings"

    id = Column(Integer, primary_key=True, index=True)

    source_listing_id = Column(Unicode(100), nullable=True)
    source = Column(Unicode(50), default="tehran_excel_dataset", nullable=False)

    submission_date = Column(Unicode(50), nullable=True)

    exact_location = Column(Unicode(255), nullable=True)
    neighborhood_name = Column(Unicode(150), nullable=True)
    neighborhood_english = Column(Unicode(150), nullable=True)

    base_area = Column(Float, nullable=True)
    floor_level = Column(Integer, nullable=True)
    building_age = Column(Integer, nullable=True)

    price_per_square_meter = Column(Float, nullable=True)
    total_price = Column(Float, nullable=True)

    listing_year = Column(Integer, nullable=True)

    inflation_factor = Column(Float, default=1.0, nullable=False)
    adjusted_price_per_square_meter = Column(Float, nullable=True)
    adjusted_total_price = Column(Float, nullable=True)

    imported_at = Column(DateTime(timezone=True), server_default=func.now())