from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User
from app.models.project_participant import ProjectParticipant
from app.schemas.project_participant import ProjectParticipantCreate


def create_project_participant(
    db: Session,
    participant_data: ProjectParticipantCreate,
) -> ProjectParticipant:
    project = (
        db.query(Project)
        .filter(Project.id == participant_data.project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    user = (
        db.query(User)
        .filter(User.id == participant_data.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if str(user.role or "").upper() not in {"MEMBER", "BUYER", "INVESTOR", "PARTNER"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only a registered member can participate in a project.",
        )

    existing_participant = (
        db.query(ProjectParticipant)
        .filter(
            ProjectParticipant.project_id == participant_data.project_id,
            ProjectParticipant.user_id == participant_data.user_id,
        )
        .first()
    )

    if existing_participant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user is already a participant in this project.",
        )

    if participant_data.reserved_units < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="reserved_units must be at least 1 for apartment pre-sale.",
        )

    reserved_units_so_far = (
        db.query(ProjectParticipant)
        .filter(ProjectParticipant.project_id == participant_data.project_id)
        .with_entities(ProjectParticipant.reserved_units)
        .all()
    )

    total_reserved_units = sum(row.reserved_units for row in reserved_units_so_far)

    if total_reserved_units + participant_data.reserved_units > project.total_units:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reserved units exceed total available project units.",
        )

    calculated_share_percent = (
        participant_data.reserved_units / project.total_units
    ) * 100

    new_participant = ProjectParticipant(
        project_id=participant_data.project_id,
        user_id=participant_data.user_id,
        role=participant_data.role,
        share_percent=calculated_share_percent,
        reserved_units=participant_data.reserved_units,
        # paid_amount is derived from persisted payment records.  Never allow a
        # client-provided value to make a newly assigned member appear paid.
        paid_amount=0,
    )

    db.add(new_participant)
    db.commit()
    db.refresh(new_participant)

    return new_participant

def get_project_participants(db: Session) -> list[ProjectParticipant]:
    return (
        db.query(ProjectParticipant)
        .order_by(ProjectParticipant.id.desc())
        .all()
    )


def get_participants_by_project(
    db: Session,
    project_id: int,
) -> list[ProjectParticipant]:
    return (
        db.query(ProjectParticipant)
        .filter(ProjectParticipant.project_id == project_id)
        .order_by(ProjectParticipant.id.desc())
        .all()
    )


def get_participants_by_user(
    db: Session,
    user_id: int,
) -> list[ProjectParticipant]:
    return (
        db.query(ProjectParticipant)
        .filter(ProjectParticipant.user_id == user_id)
        .order_by(ProjectParticipant.id.desc())
        .all()
    )
