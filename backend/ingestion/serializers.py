from rest_framework import serializers

from .models import ActivityRecord, AuditLog, IngestionRun, Organization, PlantLookup


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "slug"]


class IngestionRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestionRun
        fields = [
            "id",
            "source_type",
            "filename",
            "status",
            "rows_total",
            "rows_parsed",
            "rows_failed",
            "rows_suspicious",
            "error_summary",
            "started_at",
            "completed_at",
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "action",
            "performed_by_name",
            "field_changes",
            "note",
            "created_at",
        ]

    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return obj.performed_by.get_full_name() or obj.performed_by.username
        return "System"


class ActivityRecordSerializer(serializers.ModelSerializer):
    audit_logs = AuditLogSerializer(many=True, read_only=True)
    ingestion_run_id = serializers.IntegerField(source="ingestion_run_id", read_only=True)

    class Meta:
        model = ActivityRecord
        fields = [
            "id",
            "source_type",
            "scope",
            "category",
            "activity_date",
            "period_start",
            "period_end",
            "site_name",
            "plant_code",
            "description",
            "quantity",
            "unit_original",
            "unit_normalized",
            "quantity_normalized",
            "currency",
            "amount",
            "origin",
            "destination",
            "distance_km",
            "is_suspicious",
            "suspicion_reasons",
            "parse_warnings",
            "review_status",
            "reviewed_at",
            "review_notes",
            "source_reference",
            "ingestion_run_id",
            "created_at",
            "updated_at",
            "audit_logs",
        ]


class ActivityListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityRecord
        fields = [
            "id",
            "source_type",
            "scope",
            "category",
            "activity_date",
            "site_name",
            "description",
            "quantity",
            "unit_normalized",
            "amount",
            "currency",
            "is_suspicious",
            "suspicion_reasons",
            "review_status",
            "created_at",
        ]


class DashboardStatsSerializer(serializers.Serializer):
    total_activities = serializers.IntegerField()
    pending_review = serializers.IntegerField()
    approved = serializers.IntegerField()
    rejected = serializers.IntegerField()
    locked = serializers.IntegerField()
    suspicious = serializers.IntegerField()
    failed_ingestions = serializers.IntegerField()
    by_source = serializers.DictField()
    by_scope = serializers.DictField()
    recent_runs = IngestionRunSerializer(many=True)


class PlantLookupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantLookup
        fields = ["id", "plant_code", "site_name", "country"]
