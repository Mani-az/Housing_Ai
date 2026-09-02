from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class DemoAuthAccount(Base):
    __tablename__ = "demo_auth_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    username = Column(String(80), unique=True, index=True, nullable=False)
    password = Column(String(120), nullable=False)
    role = Column(String(30), nullable=False, default="project_owner")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
