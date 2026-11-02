from django.contrib import admin

from apps.leave.models import LeaveRequest


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ["employee", "leave_type", "start_date", "end_date", "status", "approved_by"]
    list_filter = ["status", "leave_type"]
