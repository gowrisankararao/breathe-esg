from django.contrib import admin

from .models import (
    ActivityRecord,
    AuditLog,
    IngestionRun,
    Organization,
    PlantLookup,
    RawRecord,
    UserProfile,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "organization"]


@admin.register(PlantLookup)
class PlantLookupAdmin(admin.ModelAdmin):
    list_display = ["organization", "plant_code", "site_name", "country"]
    list_filter = ["organization"]


class RawRecordInline(admin.TabularInline):
    model = RawRecord
    extra = 0
    readonly_fields = ["row_number", "raw_payload", "parse_error"]


@admin.register(IngestionRun)
class IngestionRunAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "organization",
        "source_type",
        "status",
        "rows_parsed",
        "rows_failed",
        "started_at",
    ]
    list_filter = ["source_type", "status", "organization"]
    inlines = [RawRecordInline]


class AuditLogInline(admin.TabularInline):
    model = AuditLog
    extra = 0
    readonly_fields = ["action", "performed_by", "field_changes", "note", "created_at"]


@admin.register(ActivityRecord)
class ActivityRecordAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "organization",
        "source_type",
        "category",
        "scope",
        "activity_date",
        "review_status",
        "is_suspicious",
    ]
    list_filter = [
        "organization",
        "source_type",
        "scope",
        "review_status",
        "is_suspicious",
    ]
    inlines = [AuditLogInline]
