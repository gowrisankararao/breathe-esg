"""
SAP Concur Expense File Export-style CSV parser.

Pipe or comma delimited; expense type drives category (flight/hotel/ground).
Distances may be missing — airport codes used for suspicion flags.
"""
from decimal import Decimal

from .common import normalize_row_keys, parse_date, parse_decimal, read_csv_rows, sniff_delimiter

TRAVEL_FIELD_MAP = {
    "report_id": "report_id",
    "employee": "employee",
    "employee_name": "employee",
    "expense_type": "expense_type",
    "expense_type_name": "expense_type",
    "transaction_date": "transaction_date",
    "expense_date": "transaction_date",
    "posted_amount": "amount",
    "amount": "amount",
    "transaction_amount": "amount",
    "currency": "currency",
    "payment_currency": "currency",
    "from_location": "origin",
    "departure_city": "origin",
    "departure_airport": "origin",
    "to_location": "destination",
    "arrival_city": "destination",
    "arrival_airport": "destination",
    "distance": "distance",
    "mileage": "distance",
    "distance_km": "distance",
    "business_purpose": "purpose",
    "org_unit_1": "cost_center",
    "cost_center": "cost_center",
}


def _map_fields(row: dict) -> dict:
    mapped = {}
    for key, val in row.items():
        canonical = TRAVEL_FIELD_MAP.get(key, key)
        if canonical not in mapped or not mapped[canonical]:
            mapped[canonical] = val
    return mapped


def _infer_travel_category(expense_type: str) -> str:
    t = expense_type.lower()
    if any(k in t for k in ("air", "flight", "airfare", "air fare")):
        return "flight"
    if any(k in t for k in ("hotel", "lodging", "accommodation", "room")):
        return "hotel"
    if any(k in t for k in ("mileage", "taxi", "uber", "lyft", "rail", "train", "car rental", "ground")):
        return "ground"
    return "other"


def parse_travel_row(row: dict) -> dict:
    mapped = _map_fields(normalize_row_keys(row))
    expense_type = mapped.get("expense_type", "")
    category = _infer_travel_category(expense_type)
    activity_date = parse_date(mapped.get("transaction_date", ""))
    amount = parse_decimal(mapped.get("amount", ""))
    distance = parse_decimal(mapped.get("distance", ""))
    origin = mapped.get("origin", "")
    destination = mapped.get("destination", "")

    warnings = []
    suspicious = []

    if not activity_date:
        warnings.append("missing_date")
    if category == "flight" and not origin and not destination:
        suspicious.append("flight_missing_route")
    if category == "flight" and not distance:
        suspicious.append("flight_missing_distance")
    if category == "ground" and "mileage" in expense_type.lower() and not distance:
        suspicious.append("mileage_missing_distance")
    if amount and amount > Decimal("50000"):
        suspicious.append("unusually_high_spend")

    return {
        "category": category,
        "scope": "scope3",
        "activity_date": activity_date,
        "description": expense_type or mapped.get("purpose", ""),
        "quantity": distance,
        "unit_original": "km" if distance else "",
        "amount": amount,
        "currency": (mapped.get("currency", "") or "USD")[:3],
        "origin": origin,
        "destination": destination,
        "distance_km": distance,
        "source_reference": mapped.get("report_id", ""),
        "parse_warnings": warnings,
        "suspicion_reasons": suspicious,
        "is_suspicious": len(suspicious) > 0,
        "raw_mapped": mapped,
    }


def parse_travel_file(text: str) -> list[dict]:
    delimiter = sniff_delimiter(text, ("|", ",", "\t"))
    rows = read_csv_rows(text, delimiter)
    results = []
    for i, row in enumerate(rows, start=1):
        if not any(v.strip() for v in row.values() if v):
            continue
        try:
            parsed = parse_travel_row(row)
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
