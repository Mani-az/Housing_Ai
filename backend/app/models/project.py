from sqlalchemy import CheckConstraint, Column, Integer, Float, Date, DateTime, Unicode
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("total_units > 0", name="ck_projects_total_units_positive"),
        CheckConstraint(
            "estimated_total_cost > 0",
            name="ck_projects_estimated_cost_positive",
        ),
        CheckConstraint(
            "average_unit_area IS NULL OR average_unit_area > 0",
            name="ck_projects_average_area_positive",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    name = Column(Unicode(150), nullable=False)
    location = Column(Unicode(200), nullable=True)

    neighborhood_english = Column(Unicode(150), nullable=True)

    total_units = Column(Integer, nullable=False)
    average_unit_area = Column(Float, nullable=True)

    estimated_total_cost = Column(Float, nullable=False)

    start_date = Column(Date, nullable=True)
    expected_end_date = Column(Date, nullable=True)

    status = Column(Unicode(30), default="planning", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    payments = relationship("Payment", back_populates="project")
    expenses = relationship("Expense", back_populates="project")
    risk_records = relationship("RiskPredictionData", back_populates="project")
