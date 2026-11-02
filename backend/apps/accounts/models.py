from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.managers import UserManager


class User(AbstractUser):
    class Role(models.TextChoices):
        EMPLOYEE = "employee", "Employee"
        MANAGER = "manager", "Manager"

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    # Self-referential: an employee's current manager. A manager may itself
    # have no manager (null=True). Queryset-level scoping (see
    # apps/leave/views.py and apps/attendance/views.py) uses
    # User.objects.filter(manager=request.user) to find direct reports only
    # - the same pattern used by the sibling perf-okr-platform app.
    manager = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="direct_reports",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER
