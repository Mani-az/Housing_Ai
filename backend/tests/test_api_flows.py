"""High-value API flow tests using a SQLite database instead of SQL Server."""

from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

# Settings are imported by the real routers. Keep a real backend/.env
# authoritative when present, but make the documented test runners work in an
# unconfigured clone without attempting a SQL Server connection.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if not (BACKEND_DIR / ".env").exists():
    os.environ.setdefault("APP_NAME", "Housing AI API")
    os.environ.setdefault("APP_VERSION", "1.0.0")
    os.environ.setdefault("DATABASE_SERVER", "localhost")
    os.environ.setdefault("DATABASE_NAME", "HousingAI")
    os.environ.setdefault("DATABASE_DRIVER", "ODBC Driver 18 for SQL Server")
    os.environ.setdefault("DATABASE_TRUSTED_CONNECTION", "yes")

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.database import get_db
from app.models import (  # noqa: F401
    auth_account,
    economic_indicator,
    expense,
    membership_request,
    payment,
    payment_plan,
    project,
    project_owner,
    project_participant,
    property_listing,
    risk_data,
    user,
)
from app.models.auth_account import DemoAuthAccount
from app.models.payment import Payment
from app.models.project import Project
from app.models.project_owner import ProjectOwnerAssignment
from app.models.project_participant import ProjectParticipant
from app.models.user import User
from app.routes.membership_request_routes import router as membership_request_router
from app.routes.project_owner_routes import router as project_owner_router
from app.routes.project_participant_routes import router as participant_router
from app.routes.project_routes import router as project_router


class TestAPIFlows(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.db = self.session_factory()

        self.project = Project(
            name="Niavaran API Test",
            location="Tehran",
            neighborhood_english="Niavaran",
            total_units=5,
            average_unit_area=100,
            estimated_total_cost=1000,
            start_date=date(2026, 1, 1),
            expected_end_date=date(2027, 1, 1),
            status="planning",
        )
        self.other_project = Project(
            name="Saadat API Test",
            location="Tehran",
            neighborhood_english="Saadat Abad",
            total_units=5,
            average_unit_area=100,
            estimated_total_cost=1000,
            status="active",
        )
        self.owner = User(
            full_name="Armin Owner",
            email="armin.api@example.com",
            role="project_owner",
        )
        self.other_owner = User(
            full_name="Sara Owner",
            email="sara.api@example.com",
            role="project_owner",
        )
        self.member = User(
            full_name="Member Applicant",
            email="member.api@example.com",
            role="MEMBER",
        )
        self.db.add_all([
            self.project,
            self.other_project,
            self.owner,
            self.other_owner,
            self.member,
        ])
        self.db.flush()
        self.db.add_all([
            ProjectOwnerAssignment(
                project_id=self.project.id,
                owner_user_id=self.owner.id,
            ),
            ProjectOwnerAssignment(
                project_id=self.other_project.id,
                owner_user_id=self.other_owner.id,
            ),
        ])
        self.db.commit()

        self.app = FastAPI()
        self.app.include_router(project_router)
        self.app.include_router(participant_router)
        self.app.include_router(project_owner_router)
        self.app.include_router(membership_request_router)

        def override_get_db():
            db = self.session_factory()
            try:
                yield db
            finally:
                db.close()

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()

    def _apply(self, project_id: int | None = None, member_id: int | None = None):
        return self.client.post(
            "/membership-requests/",
            json={
                "project_id": project_id or self.project.id,
                "member_id": member_id or self.member.id,
            },
        )

    def test_membership_lifecycle_creates_participant_only_on_approval(self):
        applied = self._apply()
        self.assertEqual(applied.status_code, 201)
        self.assertEqual(applied.json()["status"], "PENDING")
        self.assertEqual(self.db.query(ProjectParticipant).count(), 0)

        duplicate = self._apply()
        self.assertEqual(duplicate.status_code, 400)

        request_id = applied.json()["id"]
        approved = self.client.put(
            f"/membership-requests/{request_id}/review",
            json={"status": "APPROVED", "reviewed_by": self.owner.id},
        )
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.json()["status"], "APPROVED")

        participants = self.db.query(ProjectParticipant).all()
        self.assertEqual(len(participants), 1)
        self.assertEqual(participants[0].project_id, self.project.id)
        self.assertEqual(participants[0].user_id, self.member.id)

    def test_membership_review_rejects_non_owner_and_creates_no_participant(self):
        applied = self._apply()
        request_id = applied.json()["id"]

        other_owner = self.client.put(
            f"/membership-requests/{request_id}/review",
            json={"status": "APPROVED", "reviewed_by": self.other_owner.id},
        )
        self.assertEqual(other_owner.status_code, 403)

        member_reviewer = self.client.put(
            f"/membership-requests/{request_id}/review",
            json={"status": "APPROVED", "reviewed_by": self.member.id},
        )
        self.assertEqual(member_reviewer.status_code, 403)

        missing_reviewer = self.client.put(
            f"/membership-requests/{request_id}/review",
            json={"status": "APPROVED"},
        )
        self.assertEqual(missing_reviewer.status_code, 403)

        rejected = self.client.put(
            f"/membership-requests/{request_id}/review",
            json={
                "status": "REJECTED",
                "reviewed_by": self.owner.id,
                "rejection_reason": "Not selected for this demonstration.",
            },
        )
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(rejected.json()["status"], "REJECTED")
        self.assertEqual(self.db.query(ProjectParticipant).count(), 0)

    def test_login_contract_and_1234_fallback_only_without_credential_row(self):
        """The legacy 1234 path is limited to users with no credential row."""
        self.db.add_all([
            DemoAuthAccount(
                user_id=self.member.id,
                username="member-test",
                password="secret",
                role="member",
            ),
            DemoAuthAccount(
                user_id=self.other_owner.id,
                username="sara",
                password="real-password",
                role="project_owner",
            ),
        ])
        self.db.commit()

        correct = self.client.post(
            "/project-owners/login",
            json={"username": "member-test", "password": "secret"},
        )
        self.assertEqual(correct.status_code, 200)
        self.assertEqual(correct.json()["role"], "MEMBER")
        self.assertEqual(correct.json()["user_id"], self.member.id)

        self.assertEqual(
            self.client.post(
                "/project-owners/login",
                json={"username": "member-test", "password": "wrong"},
            ).status_code,
            401,
        )
        self.assertEqual(
            self.client.post(
                "/project-owners/login",
                json={"username": "unknown", "password": "secret"},
            ).status_code,
            401,
        )

        admin = self.client.post(
            "/project-owners/login",
            json={"username": "admin", "password": "admin"},
        )
        self.assertEqual(admin.status_code, 200)
        self.assertEqual(admin.json()["role"], "admin")

        seeded_owner_without_credentials = self.client.post(
            "/project-owners/login",
            json={"username": "armin", "password": "1234"},
        )
        self.assertEqual(seeded_owner_without_credentials.status_code, 200)
        self.assertEqual(
            seeded_owner_without_credentials.json()["user_id"], self.owner.id
        )

        credential_owner_wrong_fallback = self.client.post(
            "/project-owners/login",
            json={"username": "sara", "password": "1234"},
        )
        self.assertEqual(credential_owner_wrong_fallback.status_code, 401)

        credential_owner_correct = self.client.post(
            "/project-owners/login",
            json={"username": "sara", "password": "real-password"},
        )
        self.assertEqual(credential_owner_correct.status_code, 200)
        self.assertEqual(credential_owner_correct.json()["user_id"], self.other_owner.id)

    def test_projects_derive_payment_progress_without_penalties_and_available_units(self):
        today = date.today()
        self.db.add_all([
            ProjectParticipant(
                project_id=self.project.id,
                user_id=self.member.id,
                role="member",
                reserved_units=2,
                share_percent=40,
                paid_amount=0,
            ),
            ProjectParticipant(
                project_id=self.project.id,
                user_id=self.other_owner.id,
                role="member",
                reserved_units=1,
                share_percent=20,
                paid_amount=0,
            ),
            Payment(
                project_id=self.project.id,
                user_id=self.member.id,
                amount=600,
                due_date=today,
                paid_date=today,
                status="paid",
                payment_type="installment",
            ),
            Payment(
                project_id=self.project.id,
                user_id=self.member.id,
                amount=400,
                due_date=today + timedelta(days=30),
                paid_date=None,
                status="unpaid",
                payment_type="installment",
            ),
            Payment(
                project_id=self.project.id,
                user_id=self.member.id,
                amount=50,
                due_date=today,
                paid_date=today,
                status="paid",
                payment_type="penalty",
            ),
        ])
        self.db.commit()

        response = self.client.get("/projects/")
        self.assertEqual(response.status_code, 200)
        project = next(item for item in response.json() if item["id"] == self.project.id)
        self.assertEqual(project["payment_progress"], 60.0)
        self.assertEqual(project["available_units"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
