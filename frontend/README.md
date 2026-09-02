# Housing AI — presentation frontend

This folder is a presentation-ready visual redesign of the existing React frontend. The original `frontend` folder, backend services, API contracts and ML logic are unchanged.

## Existing application inventory

| Area | Preserved behavior |
| --- | --- |
| Authentication | Login, fallback demo access and Owner/Member account creation |
| Access control | System Administrator overview, owner-scoped work and an independent Member dashboard |
| Dashboard | Portfolio/project counts, financial summaries, payment health and backend status |
| Projects | Project creation, standardized city/neighborhood selection, financial progress and owner assignment |
| Users / Members | Owner review of membership requests for owned projects; owners cannot create or manually assign members |
| Payments | Filters, statuses, schedule analysis, next-round preview/generation and auto-calculated installments |
| Predictions | Project selection, SSE progress, economic forecast, project delay and member financial risk results |

## Preserved product behavior

- Login and project-owner account creation
- Role selection at registration with required Iranian phone validation; project assignment is never part of registration
- Member marketplace cards, working project details, pending applications, Owner approval/rejection and Member payment schedule
- Admin access across all projects
- Project-owner-specific access
- Admin-only permanent Member deletion from the Users panel, with confirmation
- Dashboard financial summaries
- Project, member and payment management
- Paid, paid late, overdue and upcoming payment states
- Economic forecast, project delay and member financial risk streams
- Existing CRUD forms, validation, filters and API endpoints

The prediction run still uses the original server-sent event endpoints. Its progress modal now presents the existing run as a clear step-by-step timeline while retaining the live backend message and overall percentage.

Member prediction results show the current payment round as `Round X of Y`, future rounds remaining, amount remaining, overdue payments and late payments. Future rounds use `max(total recorded rounds - current round, 0)`, so historical unpaid rounds are not counted as future rounds.

## Visual system

- Full-screen architectural login hero with a professional dark overlay
- Concrete-gray canvas with crisp white financial surfaces
- Charcoal navigation with steel-blue and muted brass accents
- Clear typographic hierarchy and tabular financial values
- 11–18px industrial surface radius, precise borders and restrained layered shadows
- Consistent Lucide navigation icons
- Distinct selected, hover, loading, empty, error and success states
- Desktop-first layout

## Run

The frontend uses `http://127.0.0.1:8000` as its existing API base URL.

```bash
npm ci
npm run lint
npm run build
```

For local development:

```bash
npm run dev
```

Vite serves the frontend at `http://localhost:5173` by default. Production build:

```bash
npm run build
```
