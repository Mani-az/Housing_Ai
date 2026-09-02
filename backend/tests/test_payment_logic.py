import unittest
from datetime import date

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
# Register all mapped tables/relationships used by the project before create_all.
from app.models import user, project, payment, expense, risk_data, property_listing, economic_indicator, project_owner, auth_account, payment_plan  # noqa: F401
from app.models import project_participant  # noqa: F401
from app.models.payment import Payment
from app.models.project import Project
from app.models.project_participant import ProjectParticipant
from app.models.user import User
from app.core.business_rules import calculate_simple_late_penalty
from app.schemas.payment import PaymentCreate
from app.schemas.project import ProjectCreate
from app.services.payment_service import (
    create_payment,
    generate_next_payment_round,
    get_payment_plan_summary,
    mark_payment_as_paid,
    record_installment_payment,
)


class TestPaymentBusinessLogic(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()

        self.project = Project(
            name="Test Housing",
            location="Tehran",
            neighborhood_english="Test",
            total_units=1,
            average_unit_area=100,
            estimated_total_cost=800.0,
            start_date=date(2026, 1, 1),
            expected_end_date=date(2027, 1, 1),
            status="construction",
        )
        self.user = User(
            full_name="Test Member",
            email="member@example.com",
            role="buyer",
        )
        self.db.add_all([self.project, self.user])
        self.db.flush()
        self.participant = ProjectParticipant(
            project_id=self.project.id,
            user_id=self.user.id,
            reserved_units=1,
            share_percent=100,
            paid_amount=0,
        )
        self.db.add(self.participant)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_monthly_penalty_is_simple_not_compounded(self):
        august_penalty = calculate_simple_late_penalty(
            100.0, date(2026, 8, 1), date(2026, 10, 1)
        )
        september_penalty = calculate_simple_late_penalty(
            100.0, date(2026, 9, 1), date(2026, 10, 1)
        )
        self.assertEqual(august_penalty, 4.0)
        self.assertEqual(september_penalty, 2.0)
        self.assertEqual(august_penalty + september_penalty, 6.0)

    def test_generated_round_does_not_copy_old_overdue_principal(self):
        old = Payment(
            project_id=self.project.id,
            user_id=self.user.id,
            amount=100.0,
            due_date=date(2026, 5, 1),
            paid_date=None,
            status="overdue",
            delay_days=30,
            payment_type="installment",
        )
        self.db.add(old)
        self.db.commit()

        result = generate_next_payment_round(
            self.db,
            project_id=self.project.id,
            due_date=date(2026, 7, 1),
            installment_count=8,
        )

        july = (
            self.db.query(Payment)
            .filter(
                Payment.project_id == self.project.id,
                Payment.user_id == self.user.id,
                Payment.due_date == date(2026, 7, 1),
                Payment.payment_type == "installment",
            )
            .one()
        )
        self.assertEqual(july.amount, 100.0)
        self.assertEqual(result["members"][0]["previous_overdue_amount"], 100.0)
        self.assertEqual(result["members"][0]["late_penalty_amount"], 4.0)
        self.assertEqual(result["members"][0]["total_due_amount"], 204.0)

    def test_exact_multiple_overpayment_becomes_prepayment_and_is_consumed(self):
        generate_next_payment_round(
            self.db,
            project_id=self.project.id,
            due_date=date(2026, 8, 20),
            installment_count=8,
        )
        result = record_installment_payment(
            self.db,
            project_id=self.project.id,
            user_id=self.user.id,
            amount=200.0,
            due_date=date(2026, 8, 20),
            paid_date=date(2026, 8, 20),
            installment_count=8,
        )
        self.assertEqual(result["prepaid_installments_count"], 1)
        self.assertEqual(result["prepaid_amount"], 100.0)

        credits = self.db.query(Payment).filter(Payment.payment_type == "prepayment").all()
        self.assertEqual(len(credits), 1)
        self.assertEqual(credits[0].amount, 100.0)

        generate_next_payment_round(
            self.db,
            project_id=self.project.id,
            due_date=date(2026, 9, 20),
            installment_count=8,
        )

        credits_after = self.db.query(Payment).filter(Payment.payment_type == "prepayment").all()
        self.assertEqual(len(credits_after), 0)

        september = (
            self.db.query(Payment)
            .filter(
                Payment.payment_type == "installment",
                Payment.due_date == date(2026, 9, 20),
            )
            .one()
        )
        self.assertEqual(september.amount, 100.0)
        self.assertEqual(september.paid_date, date(2026, 8, 20))
        self.assertEqual(september.status, "paid")

        paid_contract_cash = sum(
            float(p.amount or 0)
            for p in self.db.query(Payment).all()
            if p.paid_date is not None and p.payment_type != "penalty"
        )
        self.assertEqual(paid_contract_cash, 200.0)

    def test_arbitrary_overpayment_is_rejected(self):
        generate_next_payment_round(
            self.db,
            project_id=self.project.id,
            due_date=date(2026, 8, 20),
            installment_count=8,
        )
        with self.assertRaises(HTTPException) as raised:
            record_installment_payment(
                self.db,
                project_id=self.project.id,
                user_id=self.user.id,
                amount=120.0,
                due_date=date(2026, 8, 20),
                paid_date=date(2026, 8, 20),
                installment_count=8,
            )
        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("Arbitrary overpayment", raised.exception.detail)

    def test_installment_amount_must_be_exact(self):
        generate_next_payment_round(
            self.db,
            project_id=self.project.id,
            due_date=date(2026, 8, 20),
            installment_count=8,
        )

        with self.assertRaises(HTTPException):
            record_installment_payment(
                self.db,
                project_id=self.project.id,
                user_id=self.user.id,
                amount=99.99,
                due_date=date(2026, 8, 20),
                paid_date=date(2026, 8, 20),
                installment_count=8,
            )

        with self.assertRaises(HTTPException):
            record_installment_payment(
                self.db,
                project_id=self.project.id,
                user_id=self.user.id,
                amount=100.01,
                due_date=date(2026, 8, 20),
                paid_date=date(2026, 8, 20),
                installment_count=8,
            )

        accepted = record_installment_payment(
            self.db,
            project_id=self.project.id,
            user_id=self.user.id,
            amount=100.0,
            due_date=date(2026, 8, 20),
            paid_date=date(2026, 8, 20),
            installment_count=8,
        )
        self.assertEqual(accepted["principal_settled_amount"], 100.0)

    def test_generated_past_due_round_is_immediately_overdue(self):
        generate_next_payment_round(
            self.db,
            project_id=self.project.id,
            due_date=date(2026, 7, 1),
            installment_count=8,
        )
        installment = (
            self.db.query(Payment)
            .filter(Payment.payment_type == "installment")
            .one()
        )
        self.assertEqual(installment.status, "overdue")
        self.assertGreater(installment.delay_days, 0)

    def test_project_schema_rejects_invalid_financial_values(self):
        with self.assertRaises(ValueError):
            ProjectCreate(
                name="Invalid",
                total_units=0,
                estimated_total_cost=100,
            )

        with self.assertRaises(ValueError):
            ProjectCreate(
                name="Invalid dates",
                total_units=1,
                estimated_total_cost=100,
                start_date=date(2027, 1, 1),
                expected_end_date=date(2026, 1, 1),
            )

    def test_multiple_overdue_installments_get_individual_monthly_penalties(self):
        self.db.add_all([
            Payment(
                project_id=self.project.id,
                user_id=self.user.id,
                amount=100.0,
                due_date=date(2026, 5, 1),
                paid_date=None,
                status="overdue",
                delay_days=1,
                payment_type="installment",
            ),
            Payment(
                project_id=self.project.id,
                user_id=self.user.id,
                amount=100.0,
                due_date=date(2026, 6, 1),
                paid_date=None,
                status="overdue",
                delay_days=1,
                payment_type="installment",
            ),
        ])
        self.db.commit()

        # Owner starts an 8-installment plan and generates July as the current round.
        generate_next_payment_round(
            self.db,
            project_id=self.project.id,
            due_date=date(2026, 7, 1),
            installment_count=8,
        )
        # Current July installment adds 100 principal. Penalties are 4 + 2.
        result = record_installment_payment(
            self.db,
            project_id=self.project.id,
            user_id=self.user.id,
            amount=306.0,
            due_date=date(2026, 7, 1),
            paid_date=date(2026, 7, 1),
            installment_count=8,
        )
        self.assertEqual(result["principal_settled_amount"], 300.0)
        self.assertEqual(result["penalty_paid_amount"], 6.0)
        penalties = self.db.query(Payment).filter(Payment.payment_type == "penalty").all()
        self.assertEqual(len(penalties), 1)
        self.assertEqual(penalties[0].amount, 6.0)

    def test_installment_count_is_locked_after_plan_creation(self):
        generate_next_payment_round(
            self.db,
            project_id=self.project.id,
            due_date=date(2026, 8, 1),
            installment_count=8,
        )
        with self.assertRaises(HTTPException) as raised:
            generate_next_payment_round(
                self.db,
                project_id=self.project.id,
                due_date=date(2026, 9, 1),
                installment_count=24,
            )
        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("already uses 8 installments", raised.exception.detail)


    def test_first_round_requires_owner_selected_installment_count(self):
        with self.assertRaises(HTTPException) as raised:
            generate_next_payment_round(
                self.db,
                project_id=self.project.id,
                due_date=date(2026, 8, 1),
                installment_count=None,
            )
        self.assertIn("owner must choose the total installment count", raised.exception.detail.lower())

    def test_owner_can_choose_any_positive_installment_count(self):
        result = generate_next_payment_round(
            self.db,
            project_id=self.project.id,
            due_date=date(2026, 8, 1),
            installment_count=5,
        )
        self.assertEqual(result["installment_count"], 5)
        self.assertEqual(result["members"][0]["base_installment"], 160.0)
        plan = get_payment_plan_summary(self.db, self.project.id)
        self.assertTrue(plan["exists"])
        self.assertEqual(plan["installment_count"], 5)

    def test_cannot_generate_more_rounds_than_owner_plan(self):
        due_dates = [
            date(2026, 1, 1),
            date(2026, 2, 1),
            date(2026, 3, 1),
        ]
        for due in due_dates:
            generate_next_payment_round(
                self.db,
                project_id=self.project.id,
                due_date=due,
                installment_count=3,
            )
        with self.assertRaises(HTTPException) as raised:
            generate_next_payment_round(
                self.db,
                project_id=self.project.id,
                due_date=date(2026, 4, 1),
                installment_count=3,
            )
        self.assertIn("All 3 installment rounds", raised.exception.detail)

    def test_new_round_due_date_must_move_forward(self):
        generate_next_payment_round(
            self.db,
            project_id=self.project.id,
            due_date=date(2026, 8, 1),
            installment_count=4,
        )
        with self.assertRaises(HTTPException) as raised:
            generate_next_payment_round(
                self.db,
                project_id=self.project.id,
                due_date=date(2026, 7, 1),
                installment_count=4,
            )
        self.assertIn("must be later than the previous round", raised.exception.detail)

    def test_prepayment_cannot_exceed_remaining_installments(self):
        generate_next_payment_round(
            self.db,
            project_id=self.project.id,
            due_date=date(2026, 8, 1),
            installment_count=2,
        )
        # Base installment is 400. Current 400 + two future installments would exceed the one slot left.
        with self.assertRaises(HTTPException) as raised:
            record_installment_payment(
                self.db,
                project_id=self.project.id,
                user_id=self.user.id,
                amount=1200.0,
                due_date=date(2026, 8, 1),
                paid_date=date(2026, 8, 1),
                installment_count=2,
            )
        self.assertIn("can prepay at most 1 more installment", raised.exception.detail)

    def test_installment_mark_paid_bypass_is_blocked(self):
        generate_next_payment_round(
            self.db,
            project_id=self.project.id,
            due_date=date(2026, 8, 1),
            installment_count=4,
        )
        installment = self.db.query(Payment).filter(Payment.payment_type == "installment").one()
        with self.assertRaises(HTTPException) as raised:
            mark_payment_as_paid(self.db, installment.id, paid_date=date(2026, 8, 1))
        self.assertIn("cannot be marked paid directly", raised.exception.detail)

    def test_system_payment_types_cannot_be_created_manually(self):
        for payment_type in ("installment", "penalty", "prepayment"):
            with self.subTest(payment_type=payment_type):
                with self.assertRaises(HTTPException) as raised:
                    create_payment(
                        self.db,
                        PaymentCreate(
                            project_id=self.project.id,
                            user_id=self.user.id,
                            amount=100.0,
                            due_date=date(2026, 8, 1),
                            paid_date=None,
                            payment_type=payment_type,
                        ),
                    )
                self.assertIn("system-managed", raised.exception.detail)



if __name__ == "__main__":
    unittest.main(verbosity=2)
