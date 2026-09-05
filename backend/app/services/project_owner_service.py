from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.auth_account import DemoAuthAccount
from app.models.project import Project
from app.models.project_owner import ProjectOwnerAssignment
from app.models.user import User
from app.schemas.project_owner import (
    DemoLoginRequest,
    ProjectOwnerAssignRequest,
    ProjectOwnerCreateAccountRequest,
)


ADMIN_ACCOUNT = {
    "id": "admin-demo",
    "user_id": None,
    "displayName": "Admin Demo",
    "email": "admin@housing-ai.demo",
    "phone_number": None,
    "role": "admin",
    "roleLabel": "System Admin",
    "accessLabel": "Full platform access",
    "projectIds": None,
    "projectNames": [],
    "username": "admin",
}


def normalize_username(username: str) -> str:
    return str(username or "").strip().lower()


def default_owner_username(owner: User) -> str:
    first_name = str(owner.full_name or "").strip().split()[0].lower()
    if first_name:
        return first_name
    return str(owner.email or "").split("@")[0].split(".")[0].lower()


def ensure_project_owner_role(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner user not found.",
        )

    if str(user.role or "").lower() not in {"project_owner", "owner", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected user must have role 'project_owner' or 'admin'.",
        )

    return user


def ensure_project_exists(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    return project


def assign_owner_to_project(
    db: Session,
    assignment_data: ProjectOwnerAssignRequest,
) -> ProjectOwnerAssignment:
    ensure_project_exists(db, assignment_data.project_id)
    ensure_project_owner_role(db, assignment_data.owner_user_id)

    existing_assignment = (
        db.query(ProjectOwnerAssignment)
        .filter(
            ProjectOwnerAssignment.project_id == assignment_data.project_id,
            ProjectOwnerAssignment.owner_user_id == assignment_data.owner_user_id,
        )
        .first()
    )

    if existing_assignment:
        return existing_assignment

    assignment = ProjectOwnerAssignment(
        project_id=assignment_data.project_id,
        owner_user_id=assignment_data.owner_user_id,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


def get_owner_assignments(db: Session) -> list[ProjectOwnerAssignment]:
    return (
        db.query(ProjectOwnerAssignment)
        .order_by(ProjectOwnerAssignment.assigned_at.desc())
        .all()
    )


def get_project_owners(db: Session, project_id: int) -> list[User]:
    ensure_project_exists(db, project_id)

    return (
        db.query(User)
        .join(ProjectOwnerAssignment, ProjectOwnerAssignment.owner_user_id == User.id)
        .filter(ProjectOwnerAssignment.project_id == project_id)
        .order_by(User.full_name.asc())
        .all()
    )


def get_owner_projects(db: Session, owner_user_id: int) -> list[Project]:
    ensure_project_owner_role(db, owner_user_id)

    return (
        db.query(Project)
        .join(ProjectOwnerAssignment, ProjectOwnerAssignment.project_id == Project.id)
        .filter(ProjectOwnerAssignment.owner_user_id == owner_user_id)
        .order_by(Project.id.desc())
        .all()
    )


def remove_owner_from_project(
    db: Session,
    project_id: int,
    owner_user_id: int,
) -> dict:
    assignment = (
        db.query(ProjectOwnerAssignment)
        .filter(
            ProjectOwnerAssignment.project_id == project_id,
            ProjectOwnerAssignment.owner_user_id == owner_user_id,
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project owner assignment not found.",
        )

    db.delete(assignment)
    db.commit()

    return {"message": "Project owner assignment removed."}


def get_auth_account_for_user(db: Session, user_id: int) -> DemoAuthAccount | None:
    return (
        db.query(DemoAuthAccount)
        .filter(DemoAuthAccount.user_id == user_id)
        .order_by(DemoAuthAccount.id.asc())
        .first()
    )


def get_auth_account_by_username(db: Session, username: str) -> DemoAuthAccount | None:
    normalized_username = normalize_username(username)
    return (
        db.query(DemoAuthAccount)
        .filter(func.lower(DemoAuthAccount.username) == normalized_username)
        .first()
    )


def build_owner_demo_account(db: Session, owner: User) -> dict:
    projects = get_owner_projects(db=db, owner_user_id=owner.id)
    project_ids = [str(project.id) for project in projects]
    project_names = [project.name for project in projects]
    credential = get_auth_account_for_user(db=db, user_id=owner.id)

    return {
        "id": f"owner-{owner.id}",
        "user_id": owner.id,
        "displayName": owner.full_name,
        "email": owner.email,
        "phone_number": owner.phone_number,
        "role": "project_owner",
        "roleLabel": "Project Owner",
        "accessLabel": (
            f"{len(projects)} assigned project"
            if len(projects) == 1
            else f"{len(projects)} assigned projects"
        ),
        "projectIds": project_ids,
        "projectNames": project_names,
        "username": credential.username if credential else default_owner_username(owner),
    }


def build_member_demo_account(db: Session, member: User) -> dict:
    credential = get_auth_account_for_user(db=db, user_id=member.id)
    return {
        "id": f"member-{member.id}",
        "user_id": member.id,
        "displayName": member.full_name,
        "email": member.email,
        "phone_number": member.phone_number,
        "role": "MEMBER",
        "roleLabel": "Member",
        "accessLabel": "Find projects and manage your payments",
        "projectIds": [],
        "projectNames": [],
        "username": credential.username if credential else default_owner_username(member),
    }


def get_demo_accounts(db: Session) -> list[dict]:
    accounts = [ADMIN_ACCOUNT]

    owners = (
        db.query(User)
        .filter(func.lower(User.role).in_(["project_owner", "owner"]))
        .order_by(User.full_name.asc())
        .all()
    )

    for owner in owners:
        accounts.append(build_owner_demo_account(db=db, owner=owner))

    members = (
        db.query(User)
        .filter(func.lower(User.role).in_(["member", "buyer"]))
        .order_by(User.full_name.asc())
        .all()
    )
    for member in members:
        # Existing buyer rows are historical demo members; expose them as member
        # accounts without changing their payment history.
        accounts.append(build_member_demo_account(db=db, member=member))

    return accounts


def login_demo_account(db: Session, login_data: DemoLoginRequest) -> dict:
    username = normalize_username(login_data.username)
    password = str(login_data.password or "").strip()

    if username == "admin" and password == "admin":
        return ADMIN_ACCOUNT

    credential = get_auth_account_by_username(db=db, username=username)

    if credential and credential.password == password:
        if credential.role == "admin":
            return ADMIN_ACCOUNT

        if not credential.user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        account_user = db.query(User).filter(User.id == credential.user_id).first()
        if not account_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
        if str(credential.role or "").upper() == "MEMBER" or str(account_user.role or "").upper() == "MEMBER":
            return build_member_demo_account(db=db, member=account_user)
        owner = ensure_project_owner_role(db=db, user_id=credential.user_id)
        return build_owner_demo_account(db=db, owner=owner)

    # Backward-compatible fallback for already-seeded owners without credential rows.
    if credential is None and password == "1234":
        owners = db.query(User).filter(func.lower(User.role).in_(["project_owner", "owner"])).all()
        for owner in owners:
            if default_owner_username(owner) == username:
                return build_owner_demo_account(db=db, owner=owner)
        members = db.query(User).filter(func.lower(User.role).in_(["member", "buyer"])).all()
        for member in members:
            if default_owner_username(member) == username:
                return build_member_demo_account(db=db, member=member)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password.",
    )


def create_owner_account(
    db: Session,
    account_data: ProjectOwnerCreateAccountRequest,
) -> dict:
    username = normalize_username(account_data.username)
    password = str(account_data.password or "").strip()

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required.",
        )

    existing_username = get_auth_account_by_username(db=db, username=username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is already taken.",
        )

    existing_email = (
        db.query(User)
        .filter(func.lower(User.email) == str(account_data.email).lower())
        .first()
    )
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    national_id = account_data.national_id
    if not national_id:
        # Keep the demo robust on SQL Server unique nullable columns.
        timestamp = datetime.utcnow().strftime("%y%m%d%H%M%S%f")[:18]
        national_id = f"OWN{timestamp}"[:20]

    account_role = str(account_data.role or "OWNER").strip().upper()
    if account_role not in {"OWNER", "MEMBER"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role must be OWNER or MEMBER.")

    new_owner = User(
        full_name=account_data.full_name.strip(),
        email=str(account_data.email).strip().lower(),
        phone_number=account_data.phone_number,
        national_id=national_id,
        role="project_owner" if account_role == "OWNER" else "MEMBER",
    )
    db.add(new_owner)
    db.commit()
    db.refresh(new_owner)

    credential = DemoAuthAccount(
        user_id=new_owner.id,
        username=username,
        password=password,
        role="project_owner" if account_role == "OWNER" else "member",
    )
    db.add(credential)
    db.commit()

    return build_owner_demo_account(db=db, owner=new_owner) if account_role == "OWNER" else build_member_demo_account(db=db, member=new_owner)
