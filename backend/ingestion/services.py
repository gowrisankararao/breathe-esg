from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import (
    ActivityRecord,
    AuditLog,
    IngestionRun,
    PlantLookup,
    RawRecord,
    ReviewStatus,
)
from .parsers import PARSERS
from .parsers.common import decode_content, normalize_unit


def _resolve_plant_name(organization, plant_code: str) -> str:
    if not plant_code:
        return ""
    lookup = PlantLookup.objects.filter(
        organization=organization, plant_code=plant_code
    ).first()
    return lookup.site_name if lookup else ""


def _apply_unit_normalization(parsed: dict) -> dict:
    unit = parsed.get("unit_original", "")
    qty = parsed.get("quantity")
    if not unit or qty is None:
        parsed["unit_normalized"] = ""
        parsed["quantity_normalized"] = qty
        return parsed
    base_unit, multiplier = normalize_unit(unit)
    parsed["unit_normalized"] = base_unit
    if multiplier:
        parsed["quantity_normalized"] = qty * multiplier
    else:
        parsed["quantity_normalized"] = qty
    return parsed


@transaction.atomic
def process_upload(organization, source_type: str, file_bytes: bytes, filename: str, user):
    run = IngestionRun.objects.create(
        organization=organization,
        source_type=source_type,
        filename=filename,
        uploaded_by=user,
        status=IngestionRun.Status.PROCESSING,
    )

    text = decode_content(file_bytes)
    parser = PARSERS.get(source_type)
    if not parser:
        run.status = IngestionRun.Status.FAILED
        run.error_summary = f"Unknown source type: {source_type}"
        run.completed_at = timezone.now()
        run.save()
        return run

    parsed_rows = parser(text)
    run.rows_total = len(parsed_rows)

    failed = 0
    suspicious = 0
    created = 0

    for item in parsed_rows:
        row_num = item.get("row_number", 0)
        raw = RawRecord.objects.create(
            ingestion_run=run,
            row_number=row_num,
            raw_payload=item.get("raw_payload", item),
            parse_error=item.get("parse_error", ""),
        )

        if item.get("parse_error"):
            failed += 1
            continue

        item = _apply_unit_normalization(item)
        plant_code = item.get("plant_code", "")
        site_name = item.get("site_name", "") or _resolve_plant_name(
            organization, plant_code
        )

        if item.get("is_suspicious"):
            suspicious += 1

        activity = ActivityRecord.objects.create(
            organization=organization,
            ingestion_run=run,
            raw_record=raw,
            source_type=source_type,
            scope=item["scope"],
            category=item["category"],
            activity_date=item.get("activity_date"),
            period_start=item.get("period_start"),
            period_end=item.get("period_end"),
            site_name=site_name,
            plant_code=plant_code,
            description=item.get("description", ""),
            quantity=item.get("quantity"),
            unit_original=item.get("unit_original", ""),
            unit_normalized=item.get("unit_normalized", ""),
            quantity_normalized=item.get("quantity_normalized"),
            currency=item.get("currency", ""),
            amount=item.get("amount"),
            origin=item.get("origin", ""),
            destination=item.get("destination", ""),
            distance_km=item.get("distance_km"),
            is_suspicious=item.get("is_suspicious", False),
            suspicion_reasons=item.get("suspicion_reasons", []),
            parse_warnings=item.get("parse_warnings", []),
            source_reference=item.get("source_reference", ""),
        )
        AuditLog.objects.create(
            activity=activity,
            action=AuditLog.Action.CREATED,
            performed_by=user,
            note=f"Ingested from {source_type} file {filename}",
        )
        created += 1

    run.rows_parsed = created
    run.rows_failed = failed
    run.rows_suspicious = suspicious
    run.status = IngestionRun.Status.COMPLETED
    run.completed_at = timezone.now()
    run.save()
    return run


def review_activity(activity, user, action: str, notes: str = "", field_changes: dict | None = None):
    if activity.review_status == ReviewStatus.LOCKED:
        raise ValueError("Record is locked for audit")

    old_status = activity.review_status
    if action == "approve":
        activity.review_status = ReviewStatus.APPROVED
        audit_action = AuditLog.Action.APPROVED
    elif action == "reject":
        activity.review_status = ReviewStatus.REJECTED
        audit_action = AuditLog.Action.REJECTED
    elif action == "lock":
        activity.review_status = ReviewStatus.LOCKED
        audit_action = AuditLog.Action.LOCKED
    else:
        raise ValueError(f"Unknown action: {action}")

    activity.reviewed_by = user
    activity.reviewed_at = timezone.now()
    activity.review_notes = notes
    activity.save()

    AuditLog.objects.create(
        activity=activity,
        action=audit_action,
        performed_by=user,
        field_changes=field_changes or {"review_status": [old_status, activity.review_status]},
        note=notes,
    )
    return activity


def edit_activity(activity, user, updates: dict):
    if activity.review_status == ReviewStatus.LOCKED:
        raise ValueError("Record is locked for audit")

    changes = {}
    allowed = {
        "description",
        "quantity",
        "unit_original",
        "site_name",
        "activity_date",
        "amount",
    }
    for field, value in updates.items():
        if field not in allowed:
            continue
        old = getattr(activity, field)
        if str(old) != str(value):
            changes[field] = [str(old) if old is not None else None, str(value)]
            setattr(activity, field, value)

    if "quantity" in updates:
        activity.quantity_normalized = Decimal(str(updates["quantity"]))
        if activity.unit_original:
            base, mult = normalize_unit(activity.unit_original)
            activity.unit_normalized = base
            if mult:
                activity.quantity_normalized = activity.quantity * mult

    activity.save()
    if changes:
        AuditLog.objects.create(
            activity=activity,
            action=AuditLog.Action.EDITED,
            performed_by=user,
            field_changes=changes,
            note="Analyst correction before approval",
        )
    return activity
