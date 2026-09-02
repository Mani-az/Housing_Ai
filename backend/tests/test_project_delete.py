import unittest
from datetime import date

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
# Import mapped models so every relationship is registered before create_all.
from app.models import (  # noqa: F401
    auth_account,
    economic_indicator,
    expense,
    payment,
    payment_plan,
    project,
    project_owner,
    project_participant,
    property_listing,
    risk_data,
    user,
)
from app.models.expense import Expense
from app.models.payment import Payment
from app.models.payment_plan import PaymentPlan
from app.models.project import Project
from app.models.project_owner import ProjectOwnerAssignment
from app.models.project_participant import ProjectParticipant
from app.models.risk_data import RiskPredictionData
from app.models.user import User
from app.services.project_service import delete_project


class TestProjectDeletion(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        session_factory = sessionmaker(bind=self.engine)
        self.db = session_factory()

        self.project = Project(
            name="Delete Me",
            location="Tehran",
            neighborhood_english="Vanak",
            total_units=10,
            average_unit_area=90,
            estimated_total_cost=1000000,
            start_date=date(2026, 1, 1),
            expected_end_date=date(2027, 1, 1),
            status="planning",
        )
        self.user = User(
            full_name="Delete Test User",
            email="delete-test@example.com",
            role="buyer",
        )
        self.db.add_all([self.project, self.user])
        self.db.flush()

        self.db.add_all(
            [
                Payment(
                    project_id=self.project.id,
                    user_id=self.user.id,
                    amount=1000,
                    due_date=date(2026, 2, 1),
                    payment_type="installment",
                ),
                Expense(
                    project_id=self.project.id,
                    title="Permit",
                    category="legal",
                    amount=250,
                    expense_date=date(2026, 1, 15),
                ),
                ProjectParticipant(
                    project_id=self.project.id,
                    user_id=self.user.id,
                    reserved_units=1,
                    share_percent=10,
                    paid_amount=0,
                ),
                ProjectOwnerAssignment(
                    project_id=self.project.id,
                    owner_user_id=self.user.id,
                ),
                PaymentPlan(
                    project_id=self.project.id,
                    installment_count=10,
                    payment_interval_months=1,
                ),
                RiskPredictionData(
                    project_id=self.project.id,
                    user_id=self.user.id,
                    total_due_amount=1000,
                    total_paid_amount=0,
                    unpaid_amount=1000,
                ),
            ]
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_delete_project_removes_dependent_records(self):
        project_id = self.project.id

        delete_project(self.db, project_id)

        self.assertIsNone(self.db.query(Project).filter(Project.id == project_id).first())
        self.assertEqual(self.db.query(Payment).filter(Payment.project_id == project_id).count(), 0)
        self.assertEqual(self.db.query(Expense).filter(Expense.project_id == project_id).count(), 0)
        self.assertEqual(
            self.db.query(ProjectParticipant)
            .filter(ProjectParticipant.project_id == project_id)
            .count(),
            0,
        )
        self.assertEqual(
            self.db.query(ProjectOwnerAssignment)
            .filter(ProjectOwnerAssignment.project_id == project_id)
            .count(),
            0,
        )
        self.assertEqual(
            self.db.query(PaymentPlan).filter(PaymentPlan.project_id == project_id).count(),
            0,
        )
        self.assertEqual(
            self.db.query(RiskPredictionData)
            .filter(RiskPredictionData.project_id == project_id)
            .count(),
            0,
        )

    def test_delete_project_returns_not_found_for_unknown_id(self):
        with self.assertRaises(HTTPException) as raised:
            delete_project(self.db, 999999)

        self.assertEqual(raised.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
