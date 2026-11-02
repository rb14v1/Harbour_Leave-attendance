from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.leave.models import LeaveRequest
from apps.leave.serializers import LeaveRequestSerializer


class LeaveRequestViewSet(viewsets.ModelViewSet):
    """Queryset scoping (per spec):
    - An employee sees only their own leave requests, and can create /
      edit / delete (while pending) their own.
    - A manager additionally sees (read-only) their direct reports' leave
      requests, via User.objects.filter(manager=request.user) - expressed
      here as employee__manager=request.user.
    - Only the employee's direct manager may approve/reject a pending
      request; get_object() below is scoped so a manager who isn't the
      employee's direct manager gets a 404 rather than ever reaching the
      object.
    """

    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = LeaveRequest.objects.select_related("employee", "approved_by", "employee__manager")
        if self.action in ("update", "partial_update", "destroy"):
            # Editing/deleting is restricted to the owning employee only -
            # a manager's visibility into direct reports' requests is
            # read-only.
            return qs.filter(employee=user)
        return qs.filter(Q(employee=user) | Q(employee__manager=user))

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != LeaveRequest.Status.PENDING:
            return Response(
                {"detail": "Only a pending request can be cancelled/deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """An employee can cancel their own still-pending request."""
        instance = self.get_object()
        if instance.employee_id != request.user.id:
            return Response(
                {"detail": "You can only cancel your own leave request."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if instance.status != LeaveRequest.Status.PENDING:
            return Response(
                {"detail": "Only a pending request can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _decide(self, request, pk, new_status):
        # get_object() uses get_queryset() above, which only exposes a
        # leave request to the employee themself or to employee's direct
        # manager - anyone else gets a 404 here, never reaching the checks
        # below.
        instance = self.get_object()
        if instance.employee.manager_id != request.user.id:
            return Response(
                {"detail": "Only the employee's direct manager can decide this request."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if instance.status != LeaveRequest.Status.PENDING:
            return Response(
                {"detail": "Only a pending request can be approved or rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.status = new_status
        instance.approved_by = request.user
        instance.decided_at = timezone.now()
        instance.save(update_fields=["status", "approved_by", "decided_at"])
        return Response(LeaveRequestSerializer(instance, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._decide(request, pk, LeaveRequest.Status.APPROVED)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._decide(request, pk, LeaveRequest.Status.REJECTED)
