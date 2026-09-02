from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class RiskPredictionData(Base):
    __tablename__ = "risk_prediction_data"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    total_due_amount = Column(Float, nullable=False)
    total_paid_amount = Column(Float, nullable=False)
    unpaid_amount = Column(Float, nullable=False)

    average_delay_days = Column(Float, default=0.0, nullable=False)
    number_of_late_payments = Column(Integer, default=0, nullable=False)

    inflation_rate = Column(Float, default=0.0, nullable=False)
    project_progress_percent = Column(Float, default=0.0, nullable=False)

    risk_label = Column(String(20), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="risk_records")
    project = relationship("Project", back_populates="risk_records")