"""
Utility portal CSV parser (Green Button / EnergyCAP-style billing export).

Columns: account, meter, commodity, uom, bill start/end, usage, cost.
Billing periods often do not align with calendar months.
"""
from decimal import Decimal

from .common import normalize_row_keys, parse_date, parse_decimal, read_csv_rows

UTILITY_FIELD_MAP = {
    "account": "account",
    "account_number": "account",
    "meter": "meter",
    "meter_id": "meter",
    "meter_number": "meter",
    "commodity": "commodity",
    "type": "commodity",
    "units": "unit",
    "unit": "unit",
    "uom": "unit",
    "start_date": "period_start",
    "bill_start": "period_start",
    "bill_start_date": "period_start",
    "end_date": "period_end",
    "bill_end": "period_end",
    "bill_end_date": "period_end",
    "usage": "usage",
    "use": "usage",
    "consumption": "usage",
    "quantity": "usage",
    "cost": "cost",
    "total_cost": "cost",
    "amount": "cost",
    "site": "site",
    "facility": "site",
    "location": "site",
}


def _map_fields(row: dict) -> dict:
    mapped = {}
    for key, val in row.items():
        canonical = UTILITY_FIELD_MAP.get(key, key)
        if canonical not in mapped or not mapped[canonical]:
            mapped[canonical] = val
    return mapped


def parse_utility_row(row: dict) -> dict:
    mapped = _map_fields(normalize_row_keys(row))
    period_start = parse_date(mapped.get("period_start", ""))
    period_end = parse_date(mapped.get("period_end", ""))
    usage = parse_decimal(mapped.get("usage", ""))
    unit = mapped.get("unit", "kWh")
    cost = parse_decimal(mapped.get("cost", ""))

    warnings = []
    suspicious = []

    if not usage:
        warnings.append("missing_usage")
    if not period_start or not period_end:
        warnings.append("missing_billing_period")
    if period_start and period_end and period_end < period_start:
        suspicious.append("end_before_start")
    if usage and usage < 0:
        suspicious.append("negative_usage")
    if usage and usage > Decimal("5000000"):
        suspicious.append("unusually_high_kwh")

    # Activity date = period end (common ESG reporting convention)
    activity_date = period_end or period_start

    return {
        "category": "electricity",
        "scope": "scope2",
        "activity_date": activity_date,
        "period_start": period_start,
        "period_end": period_end,
        "site_name": mapped.get("site", "") or mapped.get("meter", ""),
        "description": f"Electricity — meter {mapped.get('meter', 'unknown')}",
        "quantity": usage,
        "unit_original": unit,
        "amount": cost,
        "currency": "USD",
        "source_reference": mapped.get("account", "") or mapped.get("meter", ""),
        "parse_warnings": warnings,
        "suspicion_reasons": suspicious,
        "is_suspicious": len(suspicious) > 0,
        "raw_mapped": mapped,
    }


def parse_utility_file(text: str) -> list[dict]:
    rows = read_csv_rows(text, ",")
    results = []
    for i, row in enumerate(rows, start=1):
        if not any(v.strip() for v in row.values() if v):
            continue
        try:
            parsed = parse_utility_row(row)
            parsed["row_number"] = i
            parsed["raw_payload"] = row
            if parsed["parse_warnings"]:
                parsed["is_suspicious"] = True
            results.append(parsed)
        except Exception as exc:
            results.append(
                {
                    "row_number": i,
                    "raw_payload": row,
                    "parse_error": str(exc),
                }
            )
    return results
