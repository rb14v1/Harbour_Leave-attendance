from datetime import date

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.attendance.models import AttendanceRecord


class CheckInOutTests(APITestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            email="emp@co.com", password="pw12345678", role=User.Role.EMPLOYEE
        )
        self.client.force_authenticate(self.employee)

    def test_check_in_creates_todays_record(self):
        resp = self.client.post(reverse("attendance-check-in"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        record = AttendanceRecord.objects.get(employee=self.employee, date=timezone.localdate())
        self.assertIsNotNone(record.check_in_time)
        self.assertEqual(record.status, "present")

    def test_double_check_in_rejected(self):
        self.client.post(reverse("attendance-check-in"))
        resp = self.client.post(reverse("attendance-check-in"))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_check_out_sets_time_on_existing_record(self):
        self.client.post(reverse("attendance-check-in"))
        resp = self.client.post(reverse("attendance-check-out"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        record = AttendanceRecord.objects.get(employee=self.employee, date=timezone.localdate())
        self.assertIsNotNone(record.check_out_time)

    def test_check_out_without_prior_check_in_creates_record(self):
        resp = self.client.post(reverse("attendance-check-out"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        record = AttendanceRecord.objects.get(employee=self.employee, date=timezone.localdate())
        self.assertIsNotNone(record.check_out_time)
        self.assertIsNone(record.check_in_time)


class AttendanceSummaryTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            email="mgr@co.com", password="pw12345678", role=User.Role.MANAGER
        )
        self.employee = User.objects.create_user(
            email="emp@co.com", password="pw12345678", role=User.Role.EMPLOYEE, manager=self.manager
        )
        self.other_manager = User.objects.create_user(
            email="mgr2@co.com", password="pw12345678", role=User.Role.MANAGER
        )
        today = date.today()
        self.month = f"{today.year:04d}-{today.month:02d}"
        # Days 1/2/3 of the current month are valid in every month and are
        # guaranteed distinct, regardless of what day "today" actually is.
        AttendanceRecord.objects.create(employee=self.employee, date=today.replace(day=1), status="present")
        AttendanceRecord.objects.create(employee=self.employee, date=today.replace(day=2), status="absent")
        AttendanceRecord.objects.create(employee=self.employee, date=today.replace(day=3), status="half_day")

    def test_employee_sees_own_summary(self):
        self.client.force_authenticate(self.employee)
        resp = self.client.get(reverse("attendance-summary"), {"month": self.month})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["present"], 1)
        self.assertEqual(resp.data["absent"], 1)
        self.assertEqual(resp.data["half_day"], 1)

    def test_manager_can_view_direct_reports_summary(self):
        self.client.force_authenticate(self.manager)
        resp = self.client.get(
            reverse("attendance-summary"), {"month": self.month, "employee": self.employee.id}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["present"], 1)

    def test_manager_cannot_view_non_report_summary(self):
        self.client.force_authenticate(self.other_manager)
        resp = self.client.get(
            reverse("attendance-summary"), {"month": self.month, "employee": self.employee.id}
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_employee_cannot_view_anothers_summary(self):
        self.client.force_authenticate(self.employee)
        resp = self.client.get(
            reverse("attendance-summary"), {"month": self.month, "employee": self.manager.id}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class AttendanceScopingTests(APITestCase):
    def setUp(self):
        self.manager_a = User.objects.create_user(
            email="mgr-a@co.com", password="pw12345678", role=User.Role.MANAGER
        )
        self.manager_b = User.objects.create_user(
            email="mgr-b@co.com", password="pw12345678", role=User.Role.MANAGER
        )
        self.report_a = User.objects.create_user(
            email="ra@co.com", password="pw12345678", role=User.Role.EMPLOYEE, manager=self.manager_a
        )
        self.report_b = User.objects.create_user(
            email="rb@co.com", password="pw12345678", role=User.Role.EMPLOYEE, manager=self.manager_b
        )
        self.record_a = AttendanceRecord.objects.create(
            employee=self.report_a, date=date.today(), status="present"
        )
        self.record_b = AttendanceRecord.objects.create(
            employee=self.report_b, date=date.today(), status="present"
        )

    def test_cross_manager_isolation(self):
        self.client.force_authenticate(self.manager_a)
        resp = self.client.get(reverse("attendance-list"))
        ids = {row["id"] for row in resp.data}
        self.assertIn(self.record_a.id, ids)
        self.assertNotIn(self.record_b.id, ids)
