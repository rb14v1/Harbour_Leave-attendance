from calendar import monthrange
from datetime import date

from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import User
from apps.attendance.models import AttendanceRecord
from apps.attendance.serializers import AttendanceRecordSerializer


class AttendanceViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Read-only list/retrieve, plus check-in/check-out/summary actions.

    Queryset scoping (per spec): an employee sees only their own attendance
    records; a manager additionally sees (read-only) their direct reports'
    records via employee__manager=request.user.
    """

    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return AttendanceRecord.objects.select_related("employee").filter(
            Q(employee=user) | Q(employee__manager=user)
        )

    @action(detail=False, methods=["post"], url_path="check-in")
    def check_in(self, request):
        today = timezone.localdate()
        record, _ = AttendanceRecord.objects.get_or_create(
            employee=request.user, date=today, defaults={"status": AttendanceRecord.Status.PRESENT}
        )
        if record.check_in_time:
            return Response(
                {"detail": "Already checked in today."}, status=status.HTTP_400_BAD_REQUEST
            )
        record.check_in_time = timezone.now()
        record.status = AttendanceRecord.Status.PRESENT
        record.save(update_fields=["check_in_time", "status"])
        return Response(AttendanceRecordSerializer(record).data)

    @action(detail=False, methods=["post"], url_path="check-out")
    def check_out(self, request):
        today = timezone.localdate()
        record, _ = AttendanceRecord.objects.get_or_create(
            employee=request.user, date=today, defaults={"status": AttendanceRecord.Status.PRESENT}
        )
        if record.check_out_time:
            return Response(
                {"detail": "Already checked out today."}, status=status.HTTP_400_BAD_REQUEST
            )
        record.check_out_time = timezone.now()
        record.save(update_fields=["check_out_time"])
        return Response(AttendanceRecordSerializer(record).data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        month_param = request.query_params.get("month")
        if month_param:
            try:
                year, month = (int(part) for part in month_param.split("-"))
            except (ValueError, TypeError):
                return Response(
                    {"detail": "month must be formatted as YYYY-MM."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            today = timezone.localdate()
            year, month = today.year, today.month

        employee = request.user
        employee_param = request.query_params.get("employee")
        if employee_param:
            if not request.user.is_manager:
                return Response(
                    {"detail": "Only a manager can view another employee's summary."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            try:
                employee = User.objects.get(pk=employee_param, manager=request.user)
            except User.DoesNotExist:
                return Response(
                    {"detail": "Not found or not your direct report."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])

        records = AttendanceRecord.objects.filter(
            employee=employee, date__gte=first_day, date__lte=last_day
        )
        counts = {choice.value: 0 for choice in AttendanceRecord.Status}
        for row in records.values_list("status", flat=True):
            counts[row] = counts.get(row, 0) + 1

        return Response(
            {
                "employee_id": employee.id,
                "month": f"{year:04d}-{month:02d}",
                "present": counts.get(AttendanceRecord.Status.PRESENT, 0),
                "absent": counts.get(AttendanceRecord.Status.ABSENT, 0),
                "half_day": counts.get(AttendanceRecord.Status.HALF_DAY, 0),
            }
        )
