import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.membership_request import MembershipRequest
from app.models.payment import Payment
from app.models.project import Project
from app.models.project_participant import ProjectParticipant
from app.models.user import User
from app.models.project_owner import ProjectOwnerAssignment
from app.schemas.membership_request import MembershipRequestCreate, MembershipRequestReview, MembershipRequestResponse
from app.schemas.project_participant import ProjectParticipantCreate
from app.services.project_participant_service import create_project_participant

router = APIRouter(prefix="/membership-requests", tags=["Membership Requests"])


def _risk_for_member(db: Session, member_id: int) -> dict:
    payments = db.query(Payment).filter(Payment.user_id == member_id).all()
    participants = db.query(ProjectParticipant).filter(ProjectParticipant.user_id == member_id).all()
    installments = [p for p in payments if p.payment_type == "installment"]
    if not payments and not participants:
        return {"has_history": False, "previous_projects": 0, "late_payments": 0, "overdue_payments": 0,
                "risk_score": 0, "risk_level": "NEW", "reasons": ["No previous history available"]}
    late = sum(1 for p in installments if p.status == "paid_late" or (p.paid_date and p.paid_date > p.due_date))
    overdue = sum(1 for p in installments if p.paid_date is None and p.status == "overdue")
    total = max(len(installments), 1)
    score = min(100, int(round(late * 6 + overdue * 12 + (overdue / total) * 40)))
    level = "HIGH" if score >= 60 else "MEDIUM" if score >= 30 else "LOW"
    reasons = (["Late payment history"] if late else []) + (["High overdue ratio"] if overdue else [])
    if score >= 60:
        reasons.append("Payment pressure")
    return {"has_history": True, "previous_projects": len(participants), "late_payments": late,
            "overdue_payments": overdue, "risk_score": score, "risk_level": level,
            "reasons": reasons or ["On-time payment history"]}


def _serialize(req: MembershipRequest, db: Session) -> dict:
    try:
        risk = json.loads(req.risk_details or "{}")
    except (TypeError, ValueError):
        risk = {}
    member = db.query(User).filter(User.id == req.member_id).first()
    project = db.query(Project).filter(Project.id == req.project_id).first()
    return {"id": req.id, "member_id": req.member_id, "project_id": req.project_id, "status": req.status,
            "risk_snapshot": req.risk_snapshot, "risk_details": req.risk_details,
            "member_name": member.full_name if member else None, "member_email": member.email if member else None,
            "project_name": project.name if project else None, "reviewed_by": req.reviewed_by,
            "created_at": req.created_at, "reviewed_at": req.reviewed_at, **risk}


@router.post("/", response_model=MembershipRequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(data: MembershipRequestCreate, db: Session = Depends(get_db)):
    member = db.query(User).filter(User.id == data.member_id).first()
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not member or not project:
        raise HTTPException(status_code=404, detail="Member or project not found.")
    if str(member.role or "").upper() not in {"MEMBER", "BUYER"}:
        raise HTTPException(status_code=400, detail="Only a MEMBER account can apply to projects.")
    existing = db.query(MembershipRequest).filter(MembershipRequest.member_id == data.member_id,
        MembershipRequest.project_id == data.project_id, MembershipRequest.status.in_(["PENDING", "APPROVED"])).first()
    if existing:
        raise HTTPException(status_code=400, detail="An active request already exists for this project.")
    reserved = sum(float(row.reserved_units or 0) for row in db.query(ProjectParticipant).filter(ProjectParticipant.project_id == data.project_id).all())
    if reserved >= project.total_units:
        raise HTTPException(status_code=400, detail="No available units remain in this project.")
    risk = _risk_for_member(db, data.member_id)
    req = MembershipRequest(member_id=data.member_id, project_id=data.project_id, status="PENDING",
                            risk_snapshot=risk["risk_level"], risk_details=json.dumps(risk, ensure_ascii=False))
    db.add(req); db.commit(); db.refresh(req)
    return _serialize(req, db)


@router.get("/", response_model=list[MembershipRequestResponse])
def list_requests(member_id: int | None = Query(default=None), project_id: int | None = Query(default=None),
                  owner_user_id: int | None = Query(default=None),
                  request_status: str | None = Query(default=None, alias="status"), db: Session = Depends(get_db)):
    query = db.query(MembershipRequest)
    if member_id is not None: query = query.filter(MembershipRequest.member_id == member_id)
    if project_id is not None: query = query.filter(MembershipRequest.project_id == project_id)
    if owner_user_id is not None:
        query = query.join(
            ProjectOwnerAssignment,
            ProjectOwnerAssignment.project_id == MembershipRequest.project_id,
        ).filter(ProjectOwnerAssignment.owner_user_id == owner_user_id)
    if request_status: query = query.filter(MembershipRequest.status == request_status.upper())
    return [_serialize(req, db) for req in query.order_by(MembershipRequest.created_at.desc()).all()]


@router.put("/{request_id}/review", response_model=MembershipRequestResponse)
def review_request(request_id: int, data: MembershipRequestReview, db: Session = Depends(get_db)):
    req = db.query(MembershipRequest).filter(MembershipRequest.id == request_id).first()
    if not req: raise HTTPException(status_code=404, detail="Membership request not found.")
    next_status = str(data.status).upper()
    if next_status not in {"APPROVED", "REJECTED", "PENDING"}:
        raise HTTPException(status_code=400, detail="Status must be APPROVED or REJECTED.")
    if data.reviewed_by is None:
        raise HTTPException(status_code=403, detail="The project owner must review this request.")
    owner_assignment = db.query(ProjectOwnerAssignment).filter(
        ProjectOwnerAssignment.project_id == req.project_id,
        ProjectOwnerAssignment.owner_user_id == data.reviewed_by,
    ).first()
    reviewer = db.query(User).filter(User.id == data.reviewed_by).first()
    if not owner_assignment or not reviewer or str(reviewer.role or "").lower() not in {"owner", "project_owner"}:
        raise HTTPException(status_code=403, detail="Only the owner of this project can review the request.")
    if next_status == "APPROVED" and req.status != "APPROVED":
        project = db.query(Project).filter(Project.id == req.project_id).first()
        reserved = sum(float(row.reserved_units or 0) for row in db.query(ProjectParticipant).filter(ProjectParticipant.project_id == req.project_id).all())
        if not project or reserved >= project.total_units:
            raise HTTPException(status_code=400, detail="No available units remain in this project.")
        create_project_participant(db, ProjectParticipantCreate(project_id=req.project_id, user_id=req.member_id, role="member", reserved_units=1, paid_amount=0))
    req.status = next_status
    req.rejection_reason = data.rejection_reason if next_status == "REJECTED" else None
    req.reviewed_by = data.reviewed_by
    req.reviewed_at = datetime.utcnow()
    db.commit(); db.refresh(req)
    return _serialize(req, db)
