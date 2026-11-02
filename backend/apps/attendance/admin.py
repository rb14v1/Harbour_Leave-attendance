from django.contrib import admin

from apps.attendance.models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ["employee", "date", "status", "check_in_time", "check_out_time"]
    list_filter = ["status"]
