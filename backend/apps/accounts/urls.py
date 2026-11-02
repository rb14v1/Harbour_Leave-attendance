from django.urls import path

from apps.accounts.views import DirectReportsView, LogoutView, MeView, RegisterView

urlpatterns = [
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("direct-reports/", DirectReportsView.as_view(), name="direct-reports"),
]
