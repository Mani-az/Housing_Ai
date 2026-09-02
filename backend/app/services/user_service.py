from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.auth_account import DemoAuthAccount
from app.models.payment import Payment
from app.models.project_participant import ProjectParticipant
from app.models.project_owner import ProjectOwnerAssignment
from app.models.risk_data import RiskPredictionData
from app.models.membership_request import MembershipRequest
from app.schemas.user import UserCreate


def create_user(db: Session, user_data: UserCreate) -> User:
    existing_user = db.query(User).filter(User.email == user_data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        phone_number=user_data.phone_number,
        national_id=user_data.national_id,
        role=("project_owner" if user_data.role == "OWNER" else "MEMBER" if user_data.role == "MEMBER" else user_data.role),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def get_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.id.desc()).all()


def get_user_by_id(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return user


def delete_member(db: Session, user_id: int) -> None:
    """Permanently remove a Member and every record owned by that Member.

    Dependents are removed first because the existing SQL Server schema uses
    foreign keys without database-level cascades. Owners and administrators
    are deliberately protected from this Admin member-deletion action.
    """
    user = get_user_by_id(db=db, user_id=user_id)
    role = str(user.role or "").strip().lower()
    if role not in {"member", "buyer"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only MEMBER accounts can be deleted from this panel.",
        )

    try:
        # Keep historical request rows for other members valid if this user
        # was ever recorded as a reviewer, while deleting their own requests.
        db.query(MembershipRequest).filter(
            MembershipRequest.reviewed_by == user_id,
        ).update({MembershipRequest.reviewed_by: None}, synchronize_session=False)
        for model, column in (
            (DemoAuthAccount, DemoAuthAccount.user_id),
            (Payment, Payment.user_id),
            (ProjectParticipant, ProjectParticipant.user_id),
            (ProjectOwnerAssignment, ProjectOwnerAssignment.owner_user_id),
            (RiskPredictionData, RiskPredictionData.user_id),
            (MembershipRequest, MembershipRequest.member_id),
        ):
            db.query(model).filter(column == user_id).delete(synchronize_session=False)

        db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
        raise
