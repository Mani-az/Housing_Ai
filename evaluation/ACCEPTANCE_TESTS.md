# Housing AI Member Flow — Acceptance Checklist

These are the five professor/demo checks for the updated release. The API is the source of truth for role, membership and payment validation.

| # | Scenario | Expected result |
|---:|---|---|
| 1 | Create Account → Owner → Login | Account is stored as `project_owner`/`OWNER`; the existing Owner Dashboard opens. |
| 2 | Create Account → Member → Login | Account is stored as `MEMBER`; only the independent Member Dashboard opens. |
| 3 | Member → Available Projects → Apply | A `PENDING` `MembershipRequest` is created; the Member is not yet a participant. |
| 4 | Project Owner → Membership Requests → Accept | Only the owner of that project sees the request; risk snapshot is visible; approval creates one `ProjectParticipant`. Admin has no review panel. |
| 5 | Member → My Payments | Approved project and server-generated installment, extra-cost-share, penalty and status rows are visible. |
| 6 | Admin → Users → Delete member | Confirmation appears; the member login and all dependent membership, participant, payment and risk records are removed without SSMS. |

## Validation checks

- Registration has no project selector.
- `09123456789` and `+989123456789` are accepted; a 10-digit value is rejected in both UI and API.
- Duplicate pending/approved applications are rejected.
- Owners can view their project members but have no member-create or manual-assignment controls.
- Only Admin can trigger permanent Member deletion; Owner accounts and project-owner rows are protected.
- Project cards show the same backend-derived payment progress as the Owner/Admin project table (for example, 73% means collected principal divided by collected plus outstanding principal).
- Existing installment, paid, paid_late, overdue, unpaid, penalty and extra-cost-share logic remains server-side.

## Demo credentials

The seed script creates `admin / admin`, `member / 1234`, and one owner account per demo project (for example `armin / 1234`).
