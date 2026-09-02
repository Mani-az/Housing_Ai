# Housing AI Backend

Housing AI is an academic/demo cooperative and pre-sale construction management system. It combines project/member/payment management with prototype ML modules for economic forecasting, member payment risk, and project delay risk.

## Core backend responsibilities

- Projects, members/participants, project owners and payment records
- Owner-defined installment plans and payment rounds
- Monthly late-fee calculation
- Exact installment-payment validation and whole-installment prepayment
- Project/member financial summaries derived from payment records
- Economic Forecast, Member Risk and Project Delay prediction endpoints

## Role and membership lifecycle

The academic demo uses three actors: `ADMIN`, `OWNER` (`project_owner`) and
`MEMBER`. Registration accepts a role and never accepts a project assignment.
Members apply through `MembershipRequest`; the Owner assigned to that project
reviews it and approval creates the `ProjectParticipant` record.

Relevant endpoints:

- `POST /project-owners/create-account` (`role=OWNER|MEMBER`)
- `POST /membership-requests/`, `GET /membership-requests/` (use
  `owner_user_id` to scope requests to an Owner's projects)
- `PUT /membership-requests/{request_id}/review`
- `GET /participants/user/{user_id}` and `GET /payments/user/{user_id}`
- `DELETE /users/{user_id}` permanently removes a MEMBER and its dependent
  auth, request, participant, payment and risk records.

The request stores a transparent risk snapshot (previous projects, late and
overdue counts, score, level and reasons) for the owning Owner's approval screen.

## Payment plan business rules

### Owner-defined installment count

There is **no forced live default installment count** for a new project.

When the first payment round is created, the project owner chooses any positive total installment count (for example 8, 10, 12, 18, etc.). That value is stored in `payment_plans` and becomes the financial basis for that project.

After the plan starts, the count is intentionally locked. Changing it mid-plan would retroactively change the calculated installment amount and invalidate existing obligations.

The demo seed uses different installment counts for different projects to demonstrate this behavior; those are seed choices, not system-wide rules.

### Payment rounds

- Each installment round is identified by its installment due date.
- A new round must have a due date later than the previous round.
- The system will not generate more rounds than the owner-selected installment count.
- Generating an already existing due date is idempotent; duplicate installment obligations are not created.
- Old overdue principal is shown in the amount currently payable, but it is **not copied into the principal of a new installment record**. This prevents double counting.

### Base installment

For a participant:

```text
member contract share = estimated project cost / total units * reserved units
base installment      = member contract share / owner-selected installment count
```

### Late fee

Late fee is fixed at **2% of the original unpaid installment principal per overdue calendar month**, simple and non-compounding.

Example:

```text
August installment:    100,000,000
Two overdue months:    4% = 4,000,000

September installment: 100,000,000
One overdue month:      2% = 2,000,000
```

Each overdue installment is calculated independently.

### Underpayment and overpayment

Partial installment payment is intentionally outside this MVP.

- Paying less than the complete amount currently due is rejected.
- Arbitrary overpayment is rejected.
- Extra money is accepted only when it equals one or more **whole future base installments**.

Example with a 100M base installment and no penalty:

```text
100M -> current installment
120M -> rejected
200M -> current installment + 1 prepaid installment
300M -> current installment + 2 prepaid installments
```

If a late fee is due, it must also be paid, so a 100M installment with a 4M fee requires 104M for the current obligation and 204M to also prepay one future 100M installment.

A member cannot prepay beyond the number of installments remaining in the owner-defined plan.

Amounts are compared after rounding to two decimal places and are exact at
that boundary. A one-unit tolerance is intentionally not used because it could
accept an underpayment (for example, 99 for a required 100).

### Prepayment lifecycle

A prepayment is stored as system-managed credit for one complete future base installment. When the next round is generated, the oldest unused prepayment is converted into that round's installment while preserving the original early `paid_date`.

This ensures:

- cash is counted only once;
- the future installment is not requested again;
- early payment can be used as a positive signal in Member Risk.

`installment`, `penalty`, and `prepayment` records are system-managed. They cannot be manually created through the generic payment endpoint. Installments also cannot bypass the rules through the legacy `mark-paid` path; they must use the installment-payment service.

## Important payment endpoints

```text
GET  /payments/project/{project_id}/plan
POST /payments/next-round/preview
POST /payments/next-round/generate
POST /payments/next-due/member
POST /payments/installment-payment
GET  /payments/project/{project_id}/member/{user_id}/summary
```

## ML modules

### Economic Forecast

Forecasts macro indicators used as project context. The current dataset is limited, so evaluation uses rolling-origin / walk-forward methodology and compares the model with a persistence baseline.

### Member Risk

Uses payment behavior and financial-pressure features. The runtime also treats verified whole-installment prepayment as a positive business-context signal. Prepayment can lower risk, but it does not erase significant overdue history.

### Project Delay

Uses project, payment-behavior and economic-pressure features. Penalty records are excluded from installment-round behavior so late-fee accounting does not artificially inflate payment-delay features.

## ML limitations

Buyer/member-risk and project-delay training data are synthetic demo datasets. Reported accuracy therefore measures consistency with those synthetic scenarios and must **not** be presented as verified real-world financial accuracy.

The ML outputs are decision-support prototypes, not deterministic financial decisions.

## Setup

### 1. Python environment

```bash
python -m venv .venv
# activate the environment
pip install -r requirements.txt
```

### 2. Environment variables

Copy `.env.example` to `.env` and set the SQL Server values.

### 3. Run API

```bash
uvicorn app.main:app --reload
```

Default frontend configuration expects:

```text
http://127.0.0.1:8000
```

## Tests

Run all backend business-logic and ML quality-gate tests:

```bash
python -m unittest discover -s tests -v
```

The current release gate also passes with:

```bash
python -m pytest -q
```

This runs 21 payment/business tests plus 3 subtests and the ML quality gates.

The payment test suite covers, among other cases:

- owner-selected installment count;
- no silent default for a new project;
- installment-count locking after plan start;
- maximum-round enforcement;
- due-date ordering;
- no overdue-principal double counting;
- simple 2% monthly late fee;
- rejection of arbitrary overpayment;
- whole-installment prepayment;
- maximum prepayment based on remaining installments;
- legacy installment `mark-paid` bypass prevention;
- system-managed payment-type protection.

## Demo / security note

Admin and Owner panels are intentionally separated for the academic demonstration, and Owner UI data is scoped to the owner's projects. This package is **not presented as production authentication/authorization infrastructure**.

For a real production financial platform, server-side authentication/RBAC, audit logs, migrations, NUMERIC/DECIMAL money storage, concurrency controls, monitoring and real-world model validation would still be required.
