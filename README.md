# Leave & Attendance Tracker

Deliberately basic full-stack demo app: React + Django REST Framework +
PostgreSQL. Two roles - `employee` and `manager` - covering leave request
submission/approval and daily attendance check-in/check-out.

## Stack

- Backend: Django 5 + Django REST Framework + Simple JWT, PostgreSQL in
  Docker (SQLite dev-override for local `manage.py` work without Docker).
- Frontend: React + Vite + TypeScript, plain styling.
- No Celery/Redis - out of scope for this demo's size.

## Data model

- `accounts.User` (custom, email login): `role` (`employee`/`manager`),
  self-referential `manager` FK.
- `leave.LeaveRequest`: employee, date range, `leave_type`, `status`
  (`pending`/`approved`/`rejected`), `reason`, `approved_by`, `decided_at`.
  Rejects `end_date < start_date` and any new request that date-overlaps an
  already-**approved** request for the same employee.
- `attendance.AttendanceRecord`: employee, date (unique per employee),
  `check_in_time`, `check_out_time`, `status`
  (`present`/`absent`/`half_day`).

## Demo accounts (seeded via data migration)

| Email | Password | Role |
| --- | --- | --- |
| manager@example.com | demo12345 | manager |
| employee1@example.com | demo12345 | employee (reports to manager) |
| employee2@example.com | demo12345 | employee (reports to manager) |

Seed data (manager + 2 employees, leave requests in all three statuses, two
weeks of attendance history across the current and previous month) is
created by an idempotent Django data migration
(`backend/apps/accounts/migrations/0002_seed_demo_data.py`) - it runs on
every `migrate` but only inserts once.

## API

- `POST /api/auth/login/`, `/api/auth/refresh/`, `/api/auth/logout/`,
  `/api/auth/me/`, `/api/auth/register/`
- `/api/leave-requests/` (list/create, scoped per role) +
  `/{id}/approve/`, `/{id}/reject/`, `/{id}/cancel/`
- `/api/attendance/` (list, scoped per role) + `/check-in/`, `/check-out/`,
  `/summary/?month=YYYY-MM[&employee=<id>]`
- `/api/direct-reports/` (manager's direct reports)

### Queryset scoping

An employee sees only their own leave requests/attendance records. A
manager additionally sees (read-only) their **direct** reports' records,
via `User.objects.filter(manager=request.user)` - the same pattern used by
the sibling `perf-okr-platform` app. Approve/reject is restricted to the
employee's direct manager only; the viewset's queryset makes a request
invisible (404) to anyone else before any permission check even runs.

## Running locally without Docker (backend)

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # or venv/bin/activate on macOS/Linux
pip install -r requirements.txt

export USE_SQLITE=True
export DJANGO_SETTINGS_MODULE=config.settings.dev

python manage.py makemigrations --check --dry-run
python manage.py check
python manage.py migrate
python manage.py test
python manage.py runserver
```

## Running locally without Docker (frontend)

```bash
cd frontend
npm install
npm run dev     # dev server on :5173
npm run build   # production build
```

Set `VITE_API_BASE_URL` (defaults to `http://localhost:8000/api`) if the
backend runs elsewhere.

## Running with Docker Compose (Postgres)

```bash
cp .env.example .env
docker compose up --build
```

This was not exercised in this build environment (no Docker/Postgres
available here) - see the verification report for what was and wasn't run.
