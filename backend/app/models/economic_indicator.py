from sqlalchemy import Column, Integer, Float, DateTime, Unicode, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.database.base import Base


class EconomicIndicator(Base):
    __tablename__ = "economic_indicators"

    id = Column(Integer, primary_key=True, index=True)

    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    general_inflation_rate = Column(Float, nullable=True)

    cpi_index = Column(Float, nullable=True)
    cpi_yoy_growth_from_index = Column(Float, nullable=True)

    housing_cpi_index = Column(Float, nullable=True)
    housing_cpi_growth = Column(Float, nullable=True)

    producer_price_index = Column(Float, nullable=True)
    producer_price_yoy_growth = Column(Float, nullable=True)

    construction_cost_growth = Column(Float, nullable=True)

    interest_rate = Column(Float, nullable=True)

    usd_rate_toman = Column(Float, nullable=True)
    usd_rate_irr = Column(Float, nullable=True)
    usd_growth = Column(Float, nullable=True)

    transaction_volume = Column(Float, nullable=True)
    transaction_volume_growth = Column(Float, nullable=True)

    avg_price_per_sqm_million_irr = Column(Float, nullable=True)
    housing_growth_rate = Column(Float, nullable=True)

    source = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_economic_indicator_year_month"),
    )