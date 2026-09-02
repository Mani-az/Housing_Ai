from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.project_owner import (
    DemoAccountResponse,
    DemoLoginRequest,
    OwnerProjectSummary,
    ProjectOwnerAssignRequest,
    ProjectOwnerAssignmentResponse,
    ProjectOwnerCreateAccountRequest,
    ProjectOwnerSummary,
)
from app.services.project_owner_service import (
    assign_owner_to_project,
    create_owner_account,
    get_demo_accounts,
    get_owner_assignments,
    get_owner_projects,
    get_project_owners,
    login_demo_account,
    remove_owner_from_project,
)

router = APIRouter(
    prefix="/project-owners",
    tags=["Project Owners"],
)


@router.post("/login", response_model=DemoAccountResponse)
def login_project_owner(
    login_data: DemoLoginRequest,
    db: Session = Depends(get_db),
):
    return login_demo_account(db=db, login_data=login_data)


@router.post(
    "/create-account",
    response_model=DemoAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project_owner_account(
    account_data: ProjectOwnerCreateAccountRequest,
    db: Session = Depends(get_db),
):
    return create_owner_account(db=db, account_data=account_data)


@router.post("/assign", response_model=ProjectOwnerAssignmentResponse)
def assign_project_owner(
    assignment_data: ProjectOwnerAssignRequest,
    db: Session = Depends(get_db),
):
    return assign_owner_to_project(db=db, assignment_data=assignment_data)


@router.get("/assignments", response_model=list[ProjectOwnerAssignmentResponse])
def read_owner_assignments(db: Session = Depends(get_db)):
    return get_owner_assignments(db=db)


@router.get("/project/{project_id}", response_model=list[ProjectOwnerSummary])
def read_project_owners(
    project_id: int,
    db: Session = Depends(get_db),
):
    return get_project_owners(db=db, project_id=project_id)


@router.get("/owner/{owner_user_id}/projects", response_model=list[OwnerProjectSummary])
def read_owner_projects(
    owner_user_id: int,
    db: Session = Depends(get_db),
):
    return get_owner_projects(db=db, owner_user_id=owner_user_id)


@router.delete("/project/{project_id}/owner/{owner_user_id}")
def delete_project_owner_assignment(
    project_id: int,
    owner_user_id: int,
    db: Session = Depends(get_db),
):
    return remove_owner_from_project(
        db=db,
        project_id=project_id,
        owner_user_id=owner_user_id,
    )


@router.get("/demo-accounts", response_model=list[DemoAccountResponse])
def read_demo_accounts(db: Session = Depends(get_db)):
    return get_demo_accounts(db=db)
