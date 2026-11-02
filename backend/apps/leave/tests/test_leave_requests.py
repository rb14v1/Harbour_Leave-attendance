from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.leave.models import LeaveRequest


class LeaveRequestValidationTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            email="mgr@co.com", password="pw12345678", role=User.Role.MANAGER
        )
        self.employee = User.objects.create_user(
            email="emp@co.com", password="pw12345678", role=User.Role.EMPLOYEE, manager=self.manager
        )
        self.client.force_authenticate(self.employee)
        self.list_url = reverse("leave-request-list")

    def test_end_date_before_start_date_rejected(self):
        today = date.today()
        resp = self.client.post(
            self.list_url,
            {
                "start_date": str(today),
                "end_date": str(today - timedelta(days=1)),
                "leave_type": "vacation",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_date", resp.data)

    def test_overlap_with_approved_request_rejected(self):
        today = date.today()
        LeaveRequest.objects.create(
            employee=self.employee,
            start_date=today,
            end_date=today + timedelta(days=5),
            leave_type="vacation",
            status=LeaveRequest.Status.APPROVED,
        )
        resp = self.client.post(
            self.list_url,
            {
                "start_date": str(today + timedelta(days=2)),
                "end_date": str(today + timedelta(days=3)),
                "leave_type": "sick",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_overlap_with_pending_request_is_allowed(self):
        """Only APPROVED requests block new ones - pending/rejected do not."""
        today = date.today()
        LeaveRequest.objects.create(
            employee=self.employee,
            start_date=today,
            end_date=today + timedelta(days=5),
            leave_type="vacation",
            status=LeaveRequest.Status.PENDING,
        )
        resp = self.client.post(
            self.list_url,
            {
                "start_date": str(today + timedelta(days=2)),
                "end_date": str(today + timedelta(days=3)),
                "leave_type": "sick",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_non_overlapping_request_created(self):
        today = date.today()
        resp = self.client.post(
            self.list_url,
            {
                "start_date": str(today + timedelta(days=1)),
                "end_date": str(today + timedelta(days=2)),
                "leave_type": "vacation",
                "reason": "Trip",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], "pending")
        self.assertEqual(resp.data["employee"]["email"], "emp@co.com")


class LeaveApprovalWorkflowTests(APITestCase):
    def setUp(self):
        self.manager_a = User.objects.create_user(
            email="mgr-a@co.com", password="pw12345678", role=User.Role.MANAGER
        )
        self.manager_b = User.objects.create_user(
            email="mgr-b@co.com", password="pw12345678", role=User.Role.MANAGER
        )
        self.employee_a = User.objects.create_user(
            email="a@co.com", password="pw12345678", role=User.Role.EMPLOYEE, manager=self.manager_a
        )
        self.leave_request = LeaveRequest.objects.create(
            employee=self.employee_a,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            leave_type="vacation",
        )

    def test_direct_manager_can_approve(self):
        self.client.force_authenticate(self.manager_a)
        resp = self.client.post(
            reverse("leave-request-approve", args=[self.leave_request.id])
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.leave_request.refresh_from_db()
        self.assertEqual(self.leave_request.status, "approved")
        self.assertEqual(self.leave_request.approved_by_id, self.manager_a.id)
        self.assertIsNotNone(self.leave_request.decided_at)

    def test_non_direct_manager_cannot_approve(self):
        """A manager who is not this employee's direct manager must not be
        able to approve the request - the queryset scoping means it's not
        even visible to them, so this should come back as 404."""
        self.client.force_authenticate(self.manager_b)
        resp = self.client.post(
            reverse("leave-request-approve", args=[self.leave_request.id])
        )
        self.assertIn(resp.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))
        self.leave_request.refresh_from_db()
        self.assertEqual(self.leave_request.status, "pending")

    def test_employee_cannot_approve_own_request(self):
        self.client.force_authenticate(self.employee_a)
        resp = self.client.post(
            reverse("leave-request-approve", args=[self.leave_request.id])
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_reject_sets_status_and_decider(self):
        self.client.force_authenticate(self.manager_a)
        resp = self.client.post(
            reverse("leave-request-reject", args=[self.leave_request.id])
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.leave_request.refresh_from_db()
        self.assertEqual(self.leave_request.status, "rejected")
        self.assertEqual(self.leave_request.approved_by_id, self.manager_a.id)

    def test_cannot_decide_already_decided_request(self):
        self.client.force_authenticate(self.manager_a)
        self.client.post(reverse("leave-request-approve", args=[self.leave_request.id]))
        resp = self.client.post(reverse("leave-request-reject", args=[self.leave_request.id]))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_employee_can_cancel_own_pending_request(self):
        self.client.force_authenticate(self.employee_a)
        resp = self.client.post(reverse("leave-request-cancel", args=[self.leave_request.id]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LeaveRequest.objects.filter(id=self.leave_request.id).exists())

    def test_cannot_cancel_approved_request(self):
        self.leave_request.status = LeaveRequest.Status.APPROVED
        self.leave_request.save()
        self.client.force_authenticate(self.employee_a)
        resp = self.client.post(reverse("leave-request-cancel", args=[self.leave_request.id]))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class LeaveRequestScopingTests(APITestCase):
    """Employees see only their own requests; managers additionally see
    (read-only) their direct reports' requests; a manager must never see
    another manager's reports' data."""

    def setUp(self):
        self.manager_a = User.objects.create_user(
            email="mgr-a2@co.com", password="pw12345678", role=User.Role.MANAGER
        )
        self.manager_b = User.objects.create_user(
            email="mgr-b2@co.com", password="pw12345678", role=User.Role.MANAGER
        )
        self.report_a = User.objects.create_user(
            email="ra@co.com", password="pw12345678", role=User.Role.EMPLOYEE, manager=self.manager_a
        )
        self.report_b = User.objects.create_user(
            email="rb@co.com", password="pw12345678", role=User.Role.EMPLOYEE, manager=self.manager_b
        )
        self.leave_a = LeaveRequest.objects.create(
            employee=self.report_a,
            start_date=date.today(),
            end_date=date.today(),
            leave_type="vacation",
        )
        self.leave_b = LeaveRequest.objects.create(
            employee=self.report_b,
            start_date=date.today(),
            end_date=date.today(),
            leave_type="sick",
        )

    def test_manager_sees_own_reports_requests_only(self):
        self.client.force_authenticate(self.manager_a)
        resp = self.client.get(reverse("leave-request-list"))
        ids = {row["id"] for row in resp.data}
        self.assertIn(self.leave_a.id, ids)
        self.assertNotIn(self.leave_b.id, ids)

    def test_employee_sees_only_own_requests(self):
        self.client.force_authenticate(self.report_a)
        resp = self.client.get(reverse("leave-request-list"))
        ids = {row["id"] for row in resp.data}
        self.assertEqual(ids, {self.leave_a.id})

    def test_manager_cannot_retrieve_other_managers_report_request(self):
        self.client.force_authenticate(self.manager_a)
        resp = self.client.get(reverse("leave-request-detail", args=[self.leave_b.id]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
