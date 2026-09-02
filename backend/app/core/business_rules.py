from __future__ import annotations

from datetime import date


MONTHLY_LATE_PENALTY_RATE = 0.02
# Installment payments are intentionally exact at the two-decimal money
# boundary.  A one-unit tolerance silently accepted underpayments (for
# example, 99 for a required 100) and also made arbitrary overpayments pass.
# Values are rounded by the payment service before comparison, so no further
# tolerance is needed here.
INSTALLMENT_AMOUNT_TOLERANCE = 0.0
DEFAULT_INSTALLMENT_COUNT = 24


def overdue_calendar_months(due_date: date, as_of_date: date) -> int:
    """Return billable overdue months using calendar-month buckets.

    Business rule:
    - any payment after the due date incurs at least one monthly fee;
    - every new calendar month after the due month adds another monthly fee;
    - the fee is simple, not compounded.

    Example: an August installment still unpaid in October is two months late,
    so its fee is 4% of the original installment principal.
    """
    if as_of_date <= due_date:
        return 0

    month_distance = (
        (as_of_date.year - due_date.year) * 12
        + (as_of_date.month - due_date.month)
    )
    return max(month_distance, 1)


def calculate_simple_late_penalty(
    principal: float,
    due_date: date,
    as_of_date: date,
    monthly_rate: float = MONTHLY_LATE_PENALTY_RATE,
) -> float:
    months = overdue_calendar_months(due_date, as_of_date)
    if months <= 0 or principal <= 0:
        return 0.0
    return round(float(principal) * float(monthly_rate) * months, 2)
