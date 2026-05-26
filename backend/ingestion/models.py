from django.conf import settings
from django.db import models


class Organization(models.Model):
    """Tenant boundary — all activity data is scoped to one organization."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="users",
    )

    def __str__(self):
        return f"{self.user.username} @ {self.organization.slug}"


class PlantLookup(models.Model):
    """Client-specific SAP plant code → human-readable site."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="plants",
    )
    plant_code = models.CharField(max_length=20)
    site_name = models.CharField(max_length=255)
    country = models.CharField(max_length=2, blank=True)

    class Meta:
        unique_together = [("organization", "plant_code")]

    def __str__(self):
        return f"{self.plant_code} → {self.site_name}"


class SourceType(models.TextChoices):
    SAP = "sap", "SAP (fuel & procurement)"
    UTILITY = "utility", "Utility portal (electricity)"
    TRAVEL = "travel", "Corporate travel (Concur-style)"


class IngestionRun(models.Model):
    """One upload or pull attempt from a single source."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="ingestion_runs",
    )
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    filename = models.CharField(max_length=512, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    rows_total = models.PositiveIntegerField(default=0)
    rows_parsed = models.PositiveIntegerField(default=0)
    rows_failed = models.PositiveIntegerField(default=0)
    rows_suspicious = models.PositiveIntegerField(default=0)
    error_summary = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.source_type} run #{self.pk}"


class RawRecord(models.Model):
    """Staging row — preserves source payload before normalization."""

    ingestion_run = models.ForeignKey(
        IngestionRun,
        on_delete=models.CASCADE,
        related_name="raw_records",
    )
    row_number = models.PositiveIntegerField()
    raw_payload = models.JSONField()
    parse_error = models.TextField(blank=True)

    class Meta:
        ordering = ["row_number"]
        unique_together = [("ingestion_run", "row_number")]


class ScopeCategory(models.TextChoices):
    SCOPE1 = "scope1", "Scope 1 — direct"
    SCOPE2 = "scope2", "Scope 2 — purchased energy"
    SCOPE3 = "scope3", "Scope 3 — value chain"


class ActivityCategory(models.TextChoices):
    FUEL = "fuel", "Stationary/mobile fuel"
    PROCUREMENT = "procurement", "Purchased goods & services"
    ELECTRICITY = "electricity", "Purchased electricity"
    FLIGHT = "flight", "Business air travel"
    HOTEL = "hotel", "Business lodging"
    GROUND = "ground", "Ground transport"
    OTHER = "other", "Other"


class ReviewStatus(models.TextChoices):
    PENDING = "pending", "Pending review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    LOCKED = "locked", "Locked for audit"


class ActivityRecord(models.Model):
    """
    Normalized activity row — the unit analysts review and auditors consume.
  Source-of-truth: which ingestion run + raw row produced this; edits tracked in AuditLog.
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    ingestion_run = models.ForeignKey(
        IngestionRun,
        on_delete=models.SET_NULL,
        null=True,
        related_name="activities",
    )
    raw_record = models.ForeignKey(
        RawRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
    )

    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    scope = models.CharField(max_length=10, choices=ScopeCategory.choices)
    category = models.CharField(max_length=20, choices=ActivityCategory.choices)

    # Normalized dimensions
    activity_date = models.DateField(null=True, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    site_name = models.CharField(max_length=255, blank=True)
    plant_code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)

    quantity = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    unit_original = models.CharField(max_length=32, blank=True)
    unit_normalized = models.CharField(max_length=32, blank=True)
    quantity_normalized = models.DecimalField(
        max_digits=18, decimal_places=6, null=True, blank=True
    )

    currency = models.CharField(max_length=3, blank=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    # Travel-specific (nullable for other sources)
    origin = models.CharField(max_length=64, blank=True)
    destination = models.CharField(max_length=64, blank=True)
    distance_km = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    # Quality flags
    is_suspicious = models.BooleanField(default=False)
    suspicion_reasons = models.JSONField(default=list, blank=True)
    parse_warnings = models.JSONField(default=list, blank=True)

    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_activities",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    source_reference = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-activity_date", "-created_at"]
        indexes = [
            models.Index(fields=["organization", "review_status"]),
            models.Index(fields=["organization", "source_type"]),
            models.Index(fields=["organization", "is_suspicious"]),
        ]

    def __str__(self):
        return f"{self.category} @ {self.activity_date or '?'}"


class AuditLog(models.Model):
    """Immutable trail of changes for audit defensibility."""

    class Action(models.TextChoices):
        CREATED = "created", "Created"
        UPDATED = "updated", "Updated"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        LOCKED = "locked", "Locked"
        EDITED = "edited", "Edited by analyst"

    activity = models.ForeignKey(
        ActivityRecord,
        on_delete=models.CASCADE,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    field_changes = models.JSONField(default=dict, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
