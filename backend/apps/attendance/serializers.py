from rest_framework import serializers

from apps.accounts.serializers import UserBriefSerializer
from apps.attendance.models import AttendanceRecord


class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee = UserBriefSerializer(read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = ["id", "employee", "date", "check_in_time", "check_out_time", "status"]
        read_only_fields = fields
