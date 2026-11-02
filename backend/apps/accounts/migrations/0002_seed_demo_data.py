# Demo-data seed migration.
#
# Creates one demo manager and two demo employees reporting to them, plus a
# handful of LeaveRequests (one per status) and a couple of weeks of
# AttendanceRecord history (current + previous month) for each employee, so
# the app has something to look at immediately after `migrate` - no
# separate fixtures/management command needed.
#
# Idempotent: bails out immediately if the demo manager already exists, so
# running `migrate` again (or in CI) never creates duplicate rows.
from datetime import date, datetime, timedelta

from django.db import migrations
from django.utils import timezone as dj_timezone


def _aware(naive_dt):
    return dj_timezone.make_aware(naive_dt)

DEMO_PASSWORD = "demo12345"


def _add_months(year, month, delta):
    index = (year * 12 + (month - 1)) + delta
    return index // 12, index % 12 + 1


def _weekdays(start, end):
    """Inclusive list of Mon-Fri dates between start and end."""
    days = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def seed_demo_data(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    LeaveRequest = apps.get_model("leave", "LeaveRequest")
    AttendanceRecord = apps.get_model("attendance", "AttendanceRecord")

    if User.objects.filter(email="manager@example.com").exists():
        return

    # Use the real custom user manager's password hashing via set_password,
    # which is still available on the historical model because AbstractUser
    # fields (password) are plain model fields - only set_password() itself
    # comes from the concrete User class, so hash manually with Django's
    # hasher to stay migration-safe.
    from django.contrib.auth.hashers import make_password

    hashed_password = make_password(DEMO_PASSWORD)

    manager = User.objects.create(
        email="manager@example.com",
        first_name="Morgan",
        last_name="Taylor",
        role="manager",
        password=hashed_password,
        is_active=True,
    )
    employee1 = User.objects.create(
        email="employee1@example.com",
        first_name="Alex",
        last_name="Rivera",
        role="employee",
        password=hashed_password,
        is_active=True,
        manager=manager,
    )
    employee2 = User.objects.create(
        email="employee2@example.com",
        first_name="Jordan",
        last_name="Lee",
        role="employee",
        password=hashed_password,
        is_active=True,
        manager=manager,
    )

    today = date.today()

    # --- Leave requests: one of each status, for each employee ---
    LeaveRequest.objects.create(
        employee=employee1,
        start_date=today + timedelta(days=10),
        end_date=today + timedelta(days=12),
        leave_type="vacation",
        status="pending",
        reason="Family trip",
    )
    LeaveRequest.objects.create(
        employee=employee1,
        start_date=today - timedelta(days=30),
        end_date=today - timedelta(days=28),
        leave_type="personal",
        status="approved",
        reason="Personal errands",
        approved_by=manager,
        decided_at=_aware(datetime.now()),
    )
    LeaveRequest.objects.create(
        employee=employee1,
        start_date=today - timedelta(days=5),
        end_date=today - timedelta(days=5),
        leave_type="sick",
        status="rejected",
        reason="Felt unwell",
        approved_by=manager,
        decided_at=_aware(datetime.now()),
    )

    LeaveRequest.objects.create(
        employee=employee2,
        start_date=today + timedelta(days=3),
        end_date=today + timedelta(days=3),
        leave_type="sick",
        status="pending",
        reason="Doctor's appointment",
    )
    LeaveRequest.objects.create(
        employee=employee2,
        start_date=today - timedelta(days=20),
        end_date=today - timedelta(days=16),
        leave_type="vacation",
        status="approved",
        reason="Annual leave",
        approved_by=manager,
        decided_at=_aware(datetime.now()),
    )
    LeaveRequest.objects.create(
        employee=employee2,
        start_date=today + timedelta(days=1),
        end_date=today + timedelta(days=2),
        leave_type="other",
        status="rejected",
        reason="Clashes with release week",
        approved_by=manager,
        decided_at=_aware(datetime.now()),
    )

    # --- Attendance: a couple of weeks of history for current + previous month ---
    current_month_start = today.replace(day=1)
    current_month_days = _weekdays(
        max(current_month_start, today - timedelta(days=14)), today - timedelta(days=1)
    )

    prev_year, prev_month = _add_months(today.year, today.month, -1)
    prev_month_last_day = current_month_start - timedelta(days=1)
    prev_month_first_relevant = prev_month_last_day - timedelta(days=13)
    previous_month_days = _weekdays(prev_month_first_relevant, prev_month_last_day)

    all_days = current_month_days + previous_month_days

    def status_for(index):
        if index % 7 == 6:
            return "absent"
        if index % 5 == 3:
            return "half_day"
        return "present"

    for employee, offset in ((employee1, 0), (employee2, 2)):
        for i, day in enumerate(all_days):
            attendance_status = status_for(i + offset)
            check_in = None
            check_out = None
            if attendance_status in ("present", "half_day"):
                check_in = _aware(datetime.combine(day, datetime.min.time()).replace(hour=9, minute=2))
            if attendance_status == "present":
                check_out = _aware(datetime.combine(day, datetime.min.time()).replace(hour=17, minute=30))
            elif attendance_status == "half_day":
                check_out = _aware(datetime.combine(day, datetime.min.time()).replace(hour=13, minute=0))

            AttendanceRecord.objects.get_or_create(
                employee=employee,
                date=day,
                defaults={
                    "status": attendance_status,
                    "check_in_time": check_in,
                    "check_out_time": check_out,
                },
            )


def unseed_demo_data(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(
        email__in=["manager@example.com", "employee1@example.com", "employee2@example.com"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("leave", "0001_initial"),
        ("attendance", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_demo_data, unseed_demo_data),
    ]
