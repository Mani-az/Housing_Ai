from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.property_listing import PropertyListing


def get_property_listings(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    neighborhood: Optional[str] = None,
):
    query = db.query(PropertyListing)

    if neighborhood:
        query = query.filter(
            PropertyListing.neighborhood_english.ilike(f"%{neighborhood}%")
        )

    return (
        query
        .order_by(PropertyListing.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_property_listing_by_id(db: Session, property_id: int):
    property_listing = (
        db.query(PropertyListing)
        .filter(PropertyListing.id == property_id)
        .first()
    )

    if not property_listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property listing not found.",
        )

    return property_listing


def get_property_summary(db: Session):
    result = (
        db.query(
            func.count(PropertyListing.id).label("total_listings"),
            func.avg(PropertyListing.price_per_square_meter).label("average_price_per_meter"),
            func.avg(PropertyListing.adjusted_price_per_square_meter).label("average_adjusted_price_per_meter"),
            func.avg(PropertyListing.total_price).label("average_total_price"),
            func.avg(PropertyListing.adjusted_total_price).label("average_adjusted_total_price"),
            func.min(PropertyListing.base_area).label("min_area"),
            func.max(PropertyListing.base_area).label("max_area"),
        )
        .first()
    )

    return {
        "total_listings": result.total_listings,
        "average_price_per_meter": result.average_price_per_meter,
        "average_adjusted_price_per_meter": result.average_adjusted_price_per_meter,
        "average_total_price": result.average_total_price,
        "average_adjusted_total_price": result.average_adjusted_total_price,
        "min_area": result.min_area,
        "max_area": result.max_area,
    }


def get_neighborhood_stats(db: Session, limit: int = 20):
    results = (
        db.query(
            PropertyListing.neighborhood_english.label("neighborhood_english"),
            PropertyListing.neighborhood_name.label("neighborhood_name"),
            func.count(PropertyListing.id).label("total_listings"),
            func.avg(PropertyListing.base_area).label("average_area"),
            func.avg(PropertyListing.price_per_square_meter).label("average_price_per_meter"),
            func.avg(PropertyListing.adjusted_price_per_square_meter).label("average_adjusted_price_per_meter"),
        )
        .filter(PropertyListing.neighborhood_english.isnot(None))
        .group_by(
            PropertyListing.neighborhood_english,
            PropertyListing.neighborhood_name,
        )
        .order_by(func.count(PropertyListing.id).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "neighborhood_english": row.neighborhood_english,
            "neighborhood_name": row.neighborhood_name,
            "total_listings": row.total_listings,
            "average_area": row.average_area,
            "average_price_per_meter": row.average_price_per_meter,
            "average_adjusted_price_per_meter": row.average_adjusted_price_per_meter,
        }
        for row in results
    ]