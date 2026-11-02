from rest_framework import serializers

from apps.accounts.serializers import UserBriefSerializer
from apps.leave.models import LeaveRequest


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee = UserBriefSerializer(read_only=True)
    approved_by = UserBriefSerializer(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            "id",
            "employee",
            "start_date",
            "end_date",
            "leave_type",
            "status",
            "reason",
            "approved_by",
            "decided_at",
            "created_at",
        ]
        read_only_fields = ["id", "status", "approved_by", "decided_at", "created_at"]

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "end_date must be on or after start_date."}
            )

        employee = self.context["request"].user
        if start_date and end_date:
            overlap_qs = LeaveRequest.objects.filter(
                employee=employee,
                status=LeaveRequest.Status.APPROVED,
                start_date__lte=end_date,
                end_date__gte=start_date,
            )
            if self.instance is not None:
                overlap_qs = overlap_qs.exclude(pk=self.instance.pk)
            if overlap_qs.exists():
                raise serializers.ValidationError(
                    "This date range overlaps an already-approved leave request for this employee."
                )
        return attrs

    def create(self, validated_data):
        validated_data["employee"] = self.context["request"].user
        return super().create(validated_data)
