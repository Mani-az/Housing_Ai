"""Create demo admin + one unique owner for each demo project.

Run from the backend folder:
    python -m app.scripts.seed_project_owners

The script is idempotent. It also removes old demo owner assignments before
creating the new one-owner-per-project mapping, so it is safe to run after the
previous shared-owner seed.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.database import SessionLocal, engine

# Import models so SQLAlchemy knows every table before create_all.
from app.models import (  # noqa: F401
    auth_account,
    economic_indicator,
    expense,
    payment,
    project,
    project_owner,
    project_participant,
    property_listing,
    risk_data,
    user,
)
from app.models.auth_account import DemoAuthAccount
from app.models.project import Project
from app.models.project_owner import ProjectOwnerAssignment
from app.models.user import User


@dataclass(frozen=True)
class DemoOwner:
    full_name: str
    email: str
    phone_number: str
    national_id: str


DEMO_ADMIN = {
    "full_name": "Admin Demo",
    "email": "admin@housing-ai.demo",
    "phone_number": "09000000000",
    "national_id": "9000000000",
    "role": "admin",
}

DEMO_MEMBER = {
    "full_name": "Member Demo",
    "email": "member@housing-ai.demo",
    "phone_number": "09120000000",
    "national_id": "9000000099",
    "role": "member",
}

# One unique owner per current seeded project.
PROJECT_OWNER_BY_PROJECT_NAME: dict[str, DemoOwner] = {
    "Niavaran Sapphire Residences": DemoOwner(
        full_name="Armin Rostami",
        email="armin.rostami.owner@housing-ai.demo",
        phone_number="09000000001",
        national_id="9000000001",
    ),
    "Saadat Abad Negin Tower": DemoOwner(
        full_name="Sara Mehrabi",
        email="sara.mehrabi.owner@housing-ai.demo",
        phone_number="09000000002",
        national_id="9000000002",
    ),
    "Mehr Housing Tower Phase 3": DemoOwner(
        full_name="Kaveh Moradi",
        email="kaveh.moradi.owner@housing-ai.demo",
        phone_number="09000000003",
        national_id="9000000003",
    ),
    "Shahrak Omid Apartment": DemoOwner(
        full_name="Neda Farhadi",
        email="neda.farhadi.owner@housing-ai.demo",
        phone_number="09000000004",
        national_id="9000000004",
    ),
}

# Extra owner names for future projects if you add more demo projects later.
FALLBACK_OWNERS: list[DemoOwner] = [
    DemoOwner("Omid Farzan", "omid.farzan.owner@housing-ai.demo", "09000000005", "9000000005"),
    DemoOwner("Leila Sadeghi", "leila.sadeghi.owner@housing-ai.demo", "09000000006", "9000000006"),
    DemoOwner("Babak Nouri", "babak.nouri.owner@housing-ai.demo", "09000000007", "9000000007"),
    DemoOwner("Mina Rahimi", "mina.rahimi.owner@housing-ai.demo", "09000000008", "9000000008"),
]

DEMO_OWNER_EMAILS = {
    owner.email for owner in PROJECT_OWNER_BY_PROJECT_NAME.values()
} | {owner.email for owner in FALLBACK_OWNERS}


DEMO_CREDENTIALS_BY_EMAIL = {
    DEMO_ADMIN["email"]: ("admin", "admin"),
    "armin.rostami.owner@housing-ai.demo": ("armin", "1234"),
    "sara.mehrabi.owner@housing-ai.demo": ("sara", "1234"),
    "kaveh.moradi.owner@housing-ai.demo": ("kaveh", "1234"),
    "neda.farhadi.owner@housing-ai.demo": ("neda", "1234"),
}


def upsert_credential(
    db: Session,
    *,
    user: User | None,
    username: str,
    password: str,
    role: str,
) -> DemoAuthAccount:
    existing = (
        db.query(DemoAuthAccount)
        .filter(DemoAuthAccount.username == username)
        .first()
    )

    if existing:
        existing.user_id = user.id if user else None
        existing.password = password
        existing.role = role
        db.commit()
        db.refresh(existing)
        return existing

    credential = DemoAuthAccount(
        user_id=user.id if user else None,
        username=username,
        password=password,
        role=role,
    )
    db.add(credential)
    db.commit()
    db.refresh(credential)
    return credential


def upsert_user(
    db: Session,
    *,
    full_name: str,
    email: str,
    phone_number: str,
    national_id: str,
    role: str,
) -> User:
    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        existing_user.full_name = full_name
        existing_user.phone_number = phone_number
        existing_user.national_id = national_id
        existing_user.role = role
        db.commit()
        db.refresh(existing_user)
        return existing_user

    new_user = User(
        full_name=full_name,
        email=email,
        phone_number=phone_number,
        national_id=national_id,
        role=role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def remove_previous_demo_owner_assignments(db: Session) -> int:
    demo_owner_ids = [
        user_id
        for (user_id,) in db.query(User.id)
        .filter(User.email.in_(DEMO_OWNER_EMAILS))
        .all()
    ]

    if not demo_owner_ids:
        return 0

    deleted_count = (
        db.query(ProjectOwnerAssignment)
        .filter(ProjectOwnerAssignment.owner_user_id.in_(demo_owner_ids))
        .delete(synchronize_session=False)
    )
    db.commit()
    return int(deleted_count or 0)


def create_assignment(db: Session, project_id: int, owner_user_id: int) -> bool:
    existing_assignment = (
        db.query(ProjectOwnerAssignment)
        .filter(
            ProjectOwnerAssignment.project_id == project_id,
            ProjectOwnerAssignment.owner_user_id == owner_user_id,
        )
        .first()
    )

    if existing_assignment:
        return False

    assignment = ProjectOwnerAssignment(
        project_id=project_id,
        owner_user_id=owner_user_id,
    )
    db.add(assignment)
    db.commit()
    return True


def get_owner_for_project(project: Project, fallback_index: int) -> DemoOwner:
    explicit_owner = PROJECT_OWNER_BY_PROJECT_NAME.get(project.name)

    if explicit_owner:
        return explicit_owner

    if fallback_index < len(FALLBACK_OWNERS):
        return FALLBACK_OWNERS[fallback_index]

    owner_number = fallback_index + 1
    return DemoOwner(
        full_name=f"Project Owner {owner_number}",
        email=f"project.owner.{owner_number}@housing-ai.demo",
        phone_number=f"091{owner_number:08d}"[:11],
        national_id=f"91{owner_number:08d}"[:10],
    )


def seed_demo_project_owners() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin = upsert_user(db=db, **DEMO_ADMIN)
        admin_username, admin_password = DEMO_CREDENTIALS_BY_EMAIL[DEMO_ADMIN["email"]]
        upsert_credential(
            db=db,
            user=admin,
            username=admin_username,
            password=admin_password,
            role="admin",
        )
        member = upsert_user(db=db, **DEMO_MEMBER)
        upsert_credential(db=db, user=member, username="member", password="1234", role="member")
        removed_count = remove_previous_demo_owner_assignments(db)

        projects = db.query(Project).order_by(Project.id.asc()).all()
        created_count = 0
        assignment_rows: list[str] = []

        fallback_index = 0
        for target_project in projects:
            owner_seed = get_owner_for_project(target_project, fallback_index)

            if target_project.name not in PROJECT_OWNER_BY_PROJECT_NAME:
                fallback_index += 1

            owner = upsert_user(
                db=db,
                full_name=owner_seed.full_name,
                email=owner_seed.email,
                phone_number=owner_seed.phone_number,
                national_id=owner_seed.national_id,
                role="project_owner",
            )

            username, password = DEMO_CREDENTIALS_BY_EMAIL.get(
                owner.email,
                (owner.full_name.split()[0].lower(), "1234"),
            )
            upsert_credential(
                db=db,
                user=owner,
                username=username,
                password=password,
                role="project_owner",
            )

            created = create_assignment(
                db=db,
                project_id=target_project.id,
                owner_user_id=owner.id,
            )
            created_count += int(created)
            assignment_rows.append(f"- {target_project.name} -> {owner.full_name}")

        print("Demo admin created/updated:")
        print(f"- {admin.full_name} | {admin.email} | role={admin.role}")

        print(f"\nOld demo owner assignments removed: {removed_count}")
        print("\nOne-owner-per-project assignments:")
        for row in assignment_rows:
            print(row)

        print(f"\nNew assignments inserted: {created_count}")
        print("\nDemo credentials:")
        print("- admin / admin")
        print("- member / 1234")
        print("- armin / 1234")
        print("- sara / 1234")
        print("- kaveh / 1234")
        print("- neda / 1234")
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_project_owners()
