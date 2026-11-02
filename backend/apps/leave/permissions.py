from rest_framework import permissions


class IsRequestOwnerOrTheirManager(permissions.BasePermission):
    """Read: the owning employee or their direct manager.
    Write (approve/reject): the owning employee's direct manager only."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if obj.employee_id == user.id:
            return request.method in permissions.SAFE_METHODS
        return obj.employee.manager_id == user.id
