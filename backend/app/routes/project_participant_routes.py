from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.project_participant import (
    ProjectParticipantCreate,
    ProjectParticipantResponse,
)
from app.services.project_participant_service import (
    create_project_participant,
    get_project_participants,
    get_participants_by_project,
    get_participants_by_user,
)


router = APIRouter(
    prefix="/participants",
    tags=["Project Participants"],
)


@router.post("/", response_model=ProjectParticipantResponse)
def create_new_project_participant(
    participant_data: ProjectParticipantCreate,
    db: Session = Depends(get_db),
):
    return create_project_participant(
        db=db,
        participant_data=participant_data,
    )


@router.get("/", response_model=list[ProjectParticipantResponse])
def read_project_participants(
    db: Session = Depends(get_db),
):
    return get_project_participants(db=db)


@router.get("/project/{project_id}", response_model=list[ProjectParticipantResponse])
def read_participants_by_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    return get_participants_by_project(
        db=db,
        project_id=project_id,
    )


@router.get("/user/{user_id}", response_model=list[ProjectParticipantResponse])
def read_participants_by_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    return get_participants_by_user(
        db=db,
        user_id=user_id,
    )