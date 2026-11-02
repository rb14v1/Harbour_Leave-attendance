from rest_framework.routers import DefaultRouter

from apps.leave.views import LeaveRequestViewSet

router = DefaultRouter()
router.register("leave-requests", LeaveRequestViewSet, basename="leave-request")

urlpatterns = router.urls
