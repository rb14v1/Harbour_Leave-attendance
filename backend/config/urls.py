from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.http import require_GET
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import LoginView


@require_GET
def healthz(request):
    """Unauthenticated liveness probe for orchestrators and load balancers."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("admin/", admin.site.urls),
    path("api/auth/login/", LoginView.as_view(), name="auth-login"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.leave.urls")),
    path("api/", include("apps.attendance.urls")),
]
