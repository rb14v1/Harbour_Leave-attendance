"""Confirms the demo-data seed migration (accounts.0002_seed_demo_data)
produced the expected rows. Since migrations already ran once before the
test DB was built for this run, this checks the state as left by `migrate`
rather than re-invoking RunPython (which is also exercised directly by
`manage.py migrate` in the verification steps)."""
from django.test import TestCase

from apps.accounts.models import User
from apps.attendance.models import AttendanceRecord
from apps.leave.models import LeaveRequest


class SeedDataTests(TestCase):
    def test_demo_users_created_with_correct_roles_and_manager(self):
        manager = User.objects.get(email="manager@example.com")
        employee1 = User.objects.get(email="employee1@example.com")
        employee2 = User.objects.get(email="employee2@example.com")

        self.assertEqual(manager.role, "manager")
        self.assertEqual(employee1.role, "employee")
        self.assertEqual(employee2.role, "employee")
        self.assertEqual(employee1.manager_id, manager.id)
        self.assertEqual(employee2.manager_id, manager.id)
        self.assertTrue(manager.check_password("demo12345"))

    def test_demo_leave_requests_cover_all_statuses(self):
        statuses = set(
            LeaveRequest.objects.filter(
                employee__email__in=["employee1@example.com", "employee2@example.com"]
            ).values_list("status", flat=True)
        )
        self.assertEqual(statuses, {"pending", "approved", "rejected"})

    def test_demo_attendance_history_seeded_for_both_employees(self):
        for email in ["employee1@example.com", "employee2@example.com"]:
            employee = User.objects.get(email=email)
            count = AttendanceRecord.objects.filter(employee=employee).count()
            self.assertGreater(count, 0, f"expected seeded attendance rows for {email}")
