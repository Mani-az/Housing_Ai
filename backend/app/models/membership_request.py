from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base

class MembershipRequest(Base):
    __tablename__ = 'membership_requests'

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    status = Column(String(20), default='PENDING', nullable=False)
    risk_snapshot = Column(String(50), nullable=True)
    risk_details = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    member = relationship('User', foreign_keys=[member_id])
    project = relationship('Project')
    reviewer = relationship('User', foreign_keys=[reviewed_by])
