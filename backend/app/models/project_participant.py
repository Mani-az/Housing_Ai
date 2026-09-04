from sqlalchemy import CheckConstraint, Column, Integer, Float, DateTime, ForeignKey, Unicode, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class ProjectParticipant(Base):
    __tablename__ = "project_participants"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "user_id",
            name="uq_project_participant_project_user",
        ),
        CheckConstraint(
            "reserved_units > 0",
            name="ck_project_participants_reserved_units_positive",
        ),
        CheckConstraint(
            "share_percent IS NULL OR (share_percent > 0 AND share_percent <= 100)",
            name="ck_project_participants_share_percent_valid",
        ),
        CheckConstraint(
            "paid_amount >= 0",
            name="ck_project_participants_paid_amount_nonnegative",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    role = Column(Unicode(50), default="buyer", nullable=False)

    share_percent = Column(Float, nullable=True)
    reserved_units = Column(Float, default=1, nullable=False)

    paid_amount = Column(Float, default=0, nullable=False)

    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
    user = relationship("User")
