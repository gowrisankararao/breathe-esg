from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ActivityRecord, IngestionRun, ReviewStatus
from .serializers import (
    ActivityListSerializer,
    ActivityRecordSerializer,
    DashboardStatsSerializer,
    IngestionRunSerializer,
)
from .services import edit_activity, process_upload, review_activity


def _get_org(request):
    profile = getattr(request.user, "profile", None)
    if not profile:
        return None
    return profile.organization


class DashboardView(APIView):
    def get(self, request):
        org = _get_org(request)
        if not org:
            return Response({"detail": "No organization"}, status=403)

        qs = ActivityRecord.objects.filter(organization=org)
        by_source = dict(
            qs.values("source_type")
            .annotate(count=Count("id"))
            .values_list("source_type", "count")
        )
        by_scope = dict(
            qs.values("scope").annotate(count=Count("id")).values_list("scope", "count")
        )
        recent_runs = IngestionRun.objects.filter(organization=org)[:5]

        data = {
            "total_activities": qs.count(),
            "pending_review": qs.filter(review_status=ReviewStatus.PENDING).count(),
            "approved": qs.filter(review_status=ReviewStatus.APPROVED).count(),
            "rejected": qs.filter(review_status=ReviewStatus.REJECTED).count(),
            "locked": qs.filter(review_status=ReviewStatus.LOCKED).count(),
            "suspicious": qs.filter(is_suspicious=True).count(),
            "failed_ingestions": IngestionRun.objects.filter(
                organization=org, rows_failed__gt=0
            ).count(),
            "by_source": by_source,
            "by_scope": by_scope,
            "recent_runs": IngestionRunSerializer(recent_runs, many=True).data,
        }
        return Response(data)


class UploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        org = _get_org(request)
        if not org:
            return Response({"detail": "No organization"}, status=403)

        source_type = request.data.get("source_type")
        file = request.FILES.get("file")
        if not source_type or source_type not in ("sap", "utility", "travel"):
            return Response(
                {"detail": "source_type must be sap, utility, or travel"},
                status=400,
            )
        if not file:
            return Response({"detail": "file is required"}, status=400)

        run = process_upload(
            org, source_type, file.read(), file.name, request.user
        )
        return Response(
            IngestionRunSerializer(run).data,
            status=status.HTTP_201_CREATED,
        )


class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    filterset_fields = [
        "source_type",
        "scope",
        "category",
        "review_status",
        "is_suspicious",
    ]
    search_fields = ["description", "site_name", "source_reference"]
    ordering_fields = ["activity_date", "created_at", "amount"]
    ordering = ["-activity_date", "-created_at"]

    def get_queryset(self):
        org = _get_org(self.request)
        if not org:
            return ActivityRecord.objects.none()
        return ActivityRecord.objects.filter(organization=org).prefetch_related(
            "audit_logs__performed_by"
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ActivityListSerializer
        return ActivityRecordSerializer

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        activity = self.get_object()
        action_name = request.data.get("action")
        notes = request.data.get("notes", "")
        try:
            review_activity(activity, request.user, action_name, notes)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(ActivityRecordSerializer(activity).data)

    @action(detail=True, methods=["patch"])
    def edit(self, request, pk=None):
        activity = self.get_object()
        try:
            edit_activity(activity, request.user, request.data)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(ActivityRecordSerializer(activity).data)

    @action(detail=False, methods=["post"])
    def bulk_review(self, request):
        ids = request.data.get("ids", [])
        action_name = request.data.get("action")
        notes = request.data.get("notes", "")
        org = _get_org(request)
        updated = 0
        for activity in ActivityRecord.objects.filter(
            organization=org, id__in=ids
        ):
            try:
                review_activity(activity, request.user, action_name, notes)
                updated += 1
            except ValueError:
                pass
        return Response({"updated": updated})


class IngestionRunViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngestionRunSerializer
    ordering = ["-started_at"]

    def get_queryset(self):
        org = _get_org(self.request)
        if not org:
            return IngestionRun.objects.none()
        return IngestionRun.objects.filter(organization=org)
