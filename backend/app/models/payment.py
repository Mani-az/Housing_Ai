from datetime import date

from sqlalchemy import CheckConstraint, Column, Float, Date, DateTime, ForeignKey, Index, Integer, Unicode, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.core.business_rules import (
    MONTHLY_LATE_PENALTY_RATE,
    calculate_simple_late_penalty,
    overdue_calendar_months,
)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        # A round obligation is unique per member.  Penalty and prepayment
        # rows intentionally remain outside these filtered indexes because
        # multiple fee/credit events may occur on the same paid date.
        Index(
            "uq_payment_installment_round_per_member",
            "project_id",
            "user_id",
            "due_date",
            unique=True,
            sqlite_where=text("payment_type = 'installment'"),
            mssql_where=text("payment_type = 'installment'"),
        ),
        Index(
            "uq_payment_cost_share_round_per_member",
            "project_id",
            "user_id",
            "due_date",
            unique=True,
            sqlite_where=text("payment_type = 'cost_share'"),
            mssql_where=text("payment_type = 'cost_share'"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    amount = Column(Float, nullable=False)

    due_date = Column(Date, nullable=False)
    paid_date = Column(Date, nullable=True)

    status = Column(Unicode(30), default="unpaid", nullable=False)
    delay_days = Column(Integer, default=0, nullable=False)

    payment_type = Column(Unicode(50), default="installment", nullable=False)
    description = Column(Unicode(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="payments")
    user = relationship("User")

    @property
    def overdue_months(self) -> int:
        if (
            self.payment_type != "installment"
            or self.paid_date is not None
            or not self.due_date
            or date.today() <= self.due_date
        ):
            return 0
        return overdue_calendar_months(self.due_date, date.today())

    @property
    def accrued_penalty_amount(self) -> float:
        if self.overdue_months <= 0:
            return 0.0
        return calculate_simple_late_penalty(
            principal=float(self.amount or 0),
            due_date=self.due_date,
            as_of_date=date.today(),
            monthly_rate=MONTHLY_LATE_PENALTY_RATE,
        )
