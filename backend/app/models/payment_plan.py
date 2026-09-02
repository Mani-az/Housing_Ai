from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.sql import func

from app.database.base import Base
from app.core.business_rules import MONTHLY_LATE_PENALTY_RATE


class PaymentPlan(Base):
    __tablename__ = "payment_plans"
    __table_args__ = (
        UniqueConstraint("project_id", name="uq_payment_plan_project"),
        CheckConstraint(
            "installment_count > 0",
            name="ck_payment_plans_installment_count_positive",
        ),
        CheckConstraint(
            "payment_interval_months > 0",
            name="ck_payment_plans_interval_positive",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    installment_count = Column(Integer, nullable=False)
    payment_interval_months = Column(Integer, default=1, nullable=False)
    monthly_late_penalty_rate = Column(Float, default=MONTHLY_LATE_PENALTY_RATE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
