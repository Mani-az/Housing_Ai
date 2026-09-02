from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class ProjectOwnerAssignment(Base):
    __tablename__ = "project_owner_assignments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
    owner = relationship("User")

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "owner_user_id",
            name="uq_project_owner_assignment",
        ),
    )
