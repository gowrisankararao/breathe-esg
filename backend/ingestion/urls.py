from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ActivityViewSet, DashboardView, IngestionRunViewSet, UploadView

router = DefaultRouter()
router.register("activities", ActivityViewSet, basename="activities")
router.register("runs", IngestionRunViewSet, basename="runs")

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("upload/", UploadView.as_view(), name="upload"),
    path("", include(router.urls)),
]
