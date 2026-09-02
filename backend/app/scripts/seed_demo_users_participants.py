from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from random import Random

from sqlalchemy import func

from app.database.database import SessionLocal
from app.models.payment import Payment
from app.models.payment_plan import PaymentPlan
from app.core.business_rules import DEFAULT_INSTALLMENT_COUNT, MONTHLY_LATE_PENALTY_RATE
from app.models.project import Project
from app.models.project_participant import ProjectParticipant
from app.models.user import User


OLD_DEMO_EMAILS = [
    "ali.ahmadi@example.com",
    "sara.mohammadi@example.com",
    "reza.karimi@example.com",
    "neda.hosseini@example.com",
    "m.ebrahimi@example.com",
    "leila.rahimi@example.com",
]


DEMO_USERS = [
    {"full_name": "Amir Hosseini", "email": "amir.hosseini.demo@example.com", "phone_number": "09121000001", "national_id": "0090000001", "role": "buyer"},
    {"full_name": "Mina Karimi", "email": "mina.karimi.demo@example.com", "phone_number": "09121000002", "national_id": "0090000002", "role": "buyer"},
    {"full_name": "Pouya Rahimi", "email": "pouya.rahimi.demo@example.com", "phone_number": "09121000003", "national_id": "0090000003", "role": "buyer"},
    {"full_name": "Shirin Ahmadi", "email": "shirin.ahmadi.demo@example.com", "phone_number": "09121000004", "national_id": "0090000004", "role": "buyer"},
    {"full_name": "Kian Moradi", "email": "kian.moradi.demo@example.com", "phone_number": "09121000005", "national_id": "0090000005", "role": "buyer"},
    {"full_name": "Niloofar Jafari", "email": "niloofar.jafari.demo@example.com", "phone_number": "09121000006", "national_id": "0090000006", "role": "buyer"},
    {"full_name": "Saeed Rezaei", "email": "saeed.rezaei.demo@example.com", "phone_number": "09121000007", "national_id": "0090000007", "role": "buyer"},
    {"full_name": "Hanieh Mohammadi", "email": "hanieh.mohammadi.demo@example.com", "phone_number": "09121000008", "national_id": "0090000008", "role": "buyer"},
    {"full_name": "Arman Sadeghi", "email": "arman.sadeghi.demo@example.com", "phone_number": "09121000009", "national_id": "0090000009", "role": "buyer"},
    {"full_name": "Maryam Ghasemi", "email": "maryam.ghasemi.demo@example.com", "phone_number": "09121000010", "national_id": "0090000010", "role": "buyer"},
    {"full_name": "Farid Nazari", "email": "farid.nazari.demo@example.com", "phone_number": "09121000011", "national_id": "0090000011", "role": "buyer"},
    {"full_name": "Setareh Ebrahimi", "email": "setareh.ebrahimi.demo@example.com", "phone_number": "09121000012", "national_id": "0090000012", "role": "buyer"},
    {"full_name": "Navid Tavakoli", "email": "navid.tavakoli.demo@example.com", "phone_number": "09121000013", "national_id": "0090000013", "role": "buyer"},
    {"full_name": "Parisa Maleki", "email": "parisa.maleki.demo@example.com", "phone_number": "09121000014", "national_id": "0090000014", "role": "buyer"},
    {"full_name": "Mehdi Akbari", "email": "mehdi.akbari.demo@example.com", "phone_number": "09121000015", "national_id": "0090000015", "role": "buyer"},
    {"full_name": "Atena Shariati", "email": "atena.shariati.demo@example.com", "phone_number": "09121000016", "national_id": "0090000016", "role": "buyer"},
    {"full_name": "Babak Heidari", "email": "babak.heidari.demo@example.com", "phone_number": "09121000017", "national_id": "0090000017", "role": "buyer"},
    {"full_name": "Roya Kazemi", "email": "roya.kazemi.demo@example.com", "phone_number": "09121000018", "national_id": "0090000018", "role": "buyer"},
    {"full_name": "Ehsan Fathi", "email": "ehsan.fathi.demo@example.com", "phone_number": "09121000019", "national_id": "0090000019", "role": "buyer"},
    {"full_name": "Dorsa Amini", "email": "dorsa.amini.demo@example.com", "phone_number": "09121000020", "national_id": "0090000020", "role": "buyer"},
]


@dataclass(frozen=True)
class PaymentBehavior:
    name: str
    on_time_probability: float
    mild_late_probability: float
    severe_late_probability: float
    overdue_probability: float
    max_late_days: int
    amount_multiplier_min: float = 0.96
    amount_multiplier_max: float = 1.05


BEHAVIORS: dict[str, PaymentBehavior] = {
    # Probability fields are kept for readability/extension, but the demo seed
    # now uses deterministic round templates below so the sample portfolio is
    # balanced and reproducible.
    "prepayer": PaymentBehavior("prepayer", 0.94, 0.05, 0.01, 0.00, 4, 1.00, 1.00),
    "excellent": PaymentBehavior("excellent", 0.86, 0.12, 0.02, 0.00, 6, 0.98, 1.06),
    "good": PaymentBehavior("good", 0.70, 0.24, 0.04, 0.02, 12, 0.97, 1.06),
    "slightly_late": PaymentBehavior("slightly_late", 0.50, 0.38, 0.08, 0.04, 22, 0.96, 1.05),
    "mixed": PaymentBehavior("mixed", 0.34, 0.28, 0.16, 0.22, 38, 0.94, 1.03),
    "stretched": PaymentBehavior("stretched", 0.22, 0.24, 0.18, 0.36, 58, 0.92, 1.02),
    "high_risk": PaymentBehavior("high_risk", 0.10, 0.18, 0.22, 0.50, 84, 0.90, 1.00),
    "critical": PaymentBehavior("critical", 0.04, 0.10, 0.18, 0.68, 115, 0.88, 0.98),
}


# Project-specific mixes. These intentionally create a visible demo spread:
# - Shahrak Omid should look financially healthy.
# - Niavaran should be mostly healthy, with one weaker member.
# - Mehr should be mid-risk.
# - Saadat Abad should remain the risky/critical demo project.
PROJECT_BEHAVIOR_MIX_BY_NAME: dict[str, list[str]] = {
    "Niavaran Sapphire Residences": ["excellent", "good", "slightly_late", "mixed", "stretched"],
    "Saadat Abad Negin Tower": ["mixed", "stretched", "high_risk", "high_risk", "critical"],
    "Mehr Housing Tower Phase 3": ["good", "slightly_late", "mixed", "mixed", "stretched"],
    "Shahrak Omid Apartment": ["prepayer", "excellent", "good", "good", "slightly_late"],
}

PROJECT_INSTALLMENT_COUNTS: dict[str, int] = {
    "Niavaran Sapphire Residences": 12,
    "Saadat Abad Negin Tower": 10,
    "Mehr Housing Tower Phase 3": 16,
    "Shahrak Omid Apartment": 8,
}


DEFAULT_BEHAVIOR_MIX = ["excellent", "good", "slightly_late", "mixed", "stretched"]


# Eight payment rounds roughly every two months: seven historical rounds and
# one near-future installment.
ROUND_OFFSETS_DAYS = [-420, -360, -300, -240, -180, -120, -60, 45]

# Deterministic payment templates by buyer behavior. The final item is the
# near-future round and should stay unpaid/upcoming, not overdue.
BEHAVIOR_ROUND_STATUS: dict[str, list[str]] = {
    "prepayer": ["paid", "paid", "paid", "paid", "paid", "paid", "paid", "prepaid"],
    "excellent": ["paid", "paid", "paid", "paid", "paid", "paid_late_mild", "paid", "future_unpaid"],
    "good": ["paid", "paid", "paid_late_mild", "paid", "paid", "paid_late_mild", "paid", "future_unpaid"],
    "slightly_late": ["paid", "paid_late_mild", "paid", "paid_late_mild", "paid", "paid_late_severe", "paid", "future_unpaid"],
    "mixed": ["paid", "paid_late_mild", "overdue", "paid", "paid_late_severe", "overdue", "paid", "future_unpaid"],
    "stretched": ["paid", "overdue", "paid_late_mild", "overdue", "paid", "paid_late_severe", "overdue", "future_unpaid"],
    "high_risk": ["paid_late_mild", "overdue", "overdue", "paid", "paid_late_severe", "overdue", "overdue", "future_unpaid"],
    "critical": ["overdue", "paid_late_severe", "overdue", "overdue", "paid_late_severe", "overdue", "overdue", "future_unpaid"],
}


def calculate_payment_status(due_date: date, paid_date: date | None = None):
    today = date.today()

    if paid_date:
        delay_days = max((paid_date - due_date).days, 0)
        if delay_days > 0:
            return "paid_late", delay_days
        return "paid", 0

    if today > due_date:
        delay_days = (today - due_date).days
        return "overdue", delay_days

    return "unpaid", 0


def get_or_create_user(db, user_data):
    existing_user = db.query(User).filter(User.email == user_data["email"]).first()
    if existing_user:
        print(f"User already exists: {existing_user.full_name}")
        return existing_user

    user = User(
        full_name=user_data["full_name"],
        email=user_data["email"],
        phone_number=user_data["phone_number"],
        national_id=user_data["national_id"],
        role=user_data["role"],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Created user: {user.full_name}")
    return user


def get_demo_users_from_db(db):
    demo_emails = OLD_DEMO_EMAILS + [user["email"] for user in DEMO_USERS]
    return db.query(User).filter(User.email.in_(demo_emails)).all()


def remove_previous_demo_data(db):
    demo_users = get_demo_users_from_db(db)
    demo_user_ids = [user.id for user in demo_users]

    if not demo_user_ids:
        print("No previous demo data found.")
        return

    deleted_payments = (
        db.query(Payment)
        .filter(Payment.user_id.in_(demo_user_ids))
        .delete(synchronize_session=False)
    )
    deleted_participants = (
        db.query(ProjectParticipant)
        .filter(ProjectParticipant.user_id.in_(demo_user_ids))
        .delete(synchronize_session=False)
    )
    db.commit()

    print(f"Removed previous demo payments: {deleted_payments}")
    print(f"Removed previous demo participants: {deleted_participants}")


def get_reserved_units(db, project_id):
    reserved_units = (
        db.query(func.sum(ProjectParticipant.reserved_units))
        .filter(ProjectParticipant.project_id == project_id)
        .scalar()
    )
    return reserved_units or 0


def create_participant(db, user, project):
    current_reserved_units = get_reserved_units(db=db, project_id=project.id)
    if current_reserved_units + 1 > project.total_units:
        print(f"Skipped {user.full_name}: {project.name} has no available units.")
        return None

    share_percent = (1 / project.total_units) * 100
    participant = ProjectParticipant(
        project_id=project.id,
        user_id=user.id,
        role="buyer",
        share_percent=share_percent,
        reserved_units=1,
        paid_amount=0,
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)

    print(f"Assigned {user.full_name} -> {project.name} (project_id={project.id}, user_id={user.id})")
    return participant


def ensure_payment_plan(db, project):
    # Demo plans intentionally use different owner-selected installment counts.
    # New projects created in the UI have no forced default; the owner chooses the count
    # when generating the first payment round.
    installment_count = PROJECT_INSTALLMENT_COUNTS.get(project.name, DEFAULT_INSTALLMENT_COUNT)
    plan = db.query(PaymentPlan).filter(PaymentPlan.project_id == project.id).first()
    if not plan:
        plan = PaymentPlan(
            project_id=project.id,
            installment_count=installment_count,
            payment_interval_months=1,
            monthly_late_penalty_rate=MONTHLY_LATE_PENALTY_RATE,
        )
        db.add(plan)
    else:
        plan.installment_count = installment_count
        plan.payment_interval_months = 1
        plan.monthly_late_penalty_rate = MONTHLY_LATE_PENALTY_RATE
    db.commit()
    return plan


def get_installment_amount(project, installment_count):
    unit_price = float(project.estimated_total_cost or 0) / max(float(project.total_units or 1), 1.0)
    return round(unit_price / max(int(installment_count), 1), 2)


def create_payment(db, project_id, user_id, amount, due_date, paid_date, description):
    status, delay_days = calculate_payment_status(due_date=due_date, paid_date=paid_date)
    payment = Payment(
        project_id=project_id,
        user_id=user_id,
        amount=amount,
        due_date=due_date,
        paid_date=paid_date,
        status=status,
        delay_days=delay_days,
        payment_type="installment",
        description=description,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def decide_paid_date(
    due_date: date,
    behavior: PaymentBehavior,
    round_index: int,
    rng: Random,
) -> date | None:
    status_template = BEHAVIOR_ROUND_STATUS.get(behavior.name, BEHAVIOR_ROUND_STATUS["mixed"])[round_index]

    if status_template in {"future_unpaid", "overdue"}:
        return None

    if status_template == "prepaid":
        return due_date - timedelta(days=35)

    if status_template == "paid_late_severe":
        late_days = rng.randint(max(14, behavior.max_late_days // 3), behavior.max_late_days)
        return due_date + timedelta(days=late_days)

    if status_template == "paid_late_mild":
        late_days = rng.randint(3, max(7, min(18, behavior.max_late_days)))
        return due_date + timedelta(days=late_days)

    # Paid on time or a few days early.
    early_days = rng.randint(0, 3)
    return due_date - timedelta(days=early_days)


def create_demo_payments_for_participant(db, user, project, participant_index: int, behavior_name: str):
    today = date.today()
    rng = Random(f"housing-ai-realistic-{project.id}-{user.id}-{behavior_name}")
    behavior = BEHAVIORS[behavior_name]
    plan = ensure_payment_plan(db, project)
    base_amount = get_installment_amount(project, plan.installment_count)

    created_payments = []
    for round_index, offset_days in enumerate(ROUND_OFFSETS_DAYS, start=1):
        due_date = today + timedelta(days=offset_days)
        paid_date = decide_paid_date(due_date, behavior, round_index - 1, rng)
        # Base installment principal is fixed by the project payment plan.
        # Behavior diversity comes from timing/status, not arbitrary amount variation.
        amount = base_amount

        description = f"Round {round_index:02d} installment | behavior={behavior.name}"
        payment = create_payment(
            db=db,
            project_id=project.id,
            user_id=user.id,
            amount=amount,
            due_date=due_date,
            paid_date=paid_date,
            description=description,
        )
        created_payments.append(payment)

    total_paid = sum(payment.amount for payment in created_payments if payment.paid_date is not None)
    participant = (
        db.query(ProjectParticipant)
        .filter(ProjectParticipant.project_id == project.id, ProjectParticipant.user_id == user.id)
        .first()
    )
    if participant:
        participant.paid_amount = total_paid
        db.commit()

    status_counts = {}
    for payment in created_payments:
        status_counts[payment.status] = status_counts.get(payment.status, 0) + 1

    print(
        f"Created {len(created_payments)} payments for {user.full_name} | "
        f"project={project.name} | behavior={behavior.name} | statuses={status_counts}"
    )


def get_behavior_for_project_member(project: Project, member_index: int) -> str:
    mix = PROJECT_BEHAVIOR_MIX_BY_NAME.get(project.name, DEFAULT_BEHAVIOR_MIX)
    return mix[member_index % len(mix)]


def create_demo_participants_and_payments(db, users, projects):
    if not projects:
        print("No projects found.")
        return

    # Keep owner/project scoping simple: distribute users evenly across projects,
    # but track member_index inside each project so behavior is mixed inside the
    # project instead of being accidentally uniform.
    member_index_by_project: dict[int, int] = {project.id: 0 for project in projects}
    created_participants = 0

    for index, user in enumerate(users):
        project = projects[index % len(projects)]
        participant = create_participant(db=db, user=user, project=project)
        if not participant:
            continue

        member_index = member_index_by_project[project.id]
        behavior_name = get_behavior_for_project_member(project, member_index)
        member_index_by_project[project.id] += 1

        create_demo_payments_for_participant(
            db=db,
            user=user,
            project=project,
            participant_index=member_index,
            behavior_name=behavior_name,
        )
        created_participants += 1

    print(f"Created participant rows: {created_participants}")


def check_demo_users_have_only_one_project(db):
    demo_emails = [user["email"] for user in DEMO_USERS]
    rows = (
        db.query(
            User.full_name,
            User.email,
            func.count(ProjectParticipant.project_id).label("project_count"),
        )
        .join(ProjectParticipant, ProjectParticipant.user_id == User.id)
        .filter(User.email.in_(demo_emails))
        .group_by(User.full_name, User.email)
        .having(func.count(ProjectParticipant.project_id) > 1)
        .all()
    )

    if not rows:
        print("Check passed: no demo user is assigned to more than one project.")
        return

    print("Warning: some demo users are assigned to more than one project:")
    for row in rows:
        print(f"- {row.full_name} | {row.email} | projects={row.project_count}")


def print_project_payment_summary(db):
    print("\nProject payment summaries:")
    projects = db.query(Project).order_by(Project.id.asc()).all()
    for project in projects:
        payments = db.query(Payment).filter(Payment.project_id == project.id).all()
        if not payments:
            print(f"- {project.name}: no payments")
            continue

        total_amount = sum(float(payment.amount or 0) for payment in payments)
        paid_amount = sum(float(payment.amount or 0) for payment in payments if payment.paid_date is not None)
        overdue_count = sum(1 for payment in payments if payment.status == "overdue")
        paid_late_count = sum(1 for payment in payments if payment.status == "paid_late")
        rounds = sorted({payment.due_date for payment in payments})
        completion = paid_amount / total_amount if total_amount else 0

        print(
            f"- {project.name}: rounds={len(rounds)}, "
            f"completion={completion:.2%}, overdue={overdue_count}, paid_late={paid_late_count}, "
            f"first_due={rounds[0]}, last_due={rounds[-1]}"
        )


def print_summary(db):
    total_users = db.query(User).count()
    total_participants = db.query(ProjectParticipant).count()
    total_payments = db.query(Payment).count()

    print("\nDone.")
    print(f"Total users: {total_users}")
    print(f"Total participants: {total_participants}")
    print(f"Total payments: {total_payments}")


def main():
    db = SessionLocal()
    try:
        print("Seeding realistic demo users, participants, and payments...")
        print("Rule: each demo user is assigned to only one project.")
        print("Payment behavior is intentionally mixed inside each project.")

        projects = db.query(Project).order_by(Project.id.asc()).all()
        if not projects:
            print("No projects found in database.")
            return

        print("\nProjects:")
        for project in projects:
            print(f"- {project.id}: {project.name} | total_units={project.total_units}")

        print("\nCreating demo users if needed...")
        users = [get_or_create_user(db=db, user_data=user_data) for user_data in DEMO_USERS]

        print("\nRemoving previous demo participants and payments...")
        remove_previous_demo_data(db=db)

        print("\nCreating fresh realistic participants and payments...")
        create_demo_participants_and_payments(db=db, users=users, projects=projects)

        print("\nFinal checks:")
        check_demo_users_have_only_one_project(db=db)
        print_project_payment_summary(db=db)
        print_summary(db=db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
