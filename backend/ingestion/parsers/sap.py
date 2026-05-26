"""
SAP MM procurement / fuel flat-file parser.

Handles semicolon-delimited exports from custom SAP reports (ME2M-style)
with German or English headers — the most common mid-market path without PI/OData.
"""
from decimal import Decimal

from .common import (
    normalize_row_keys,
    parse_date,
    parse_decimal,
    read_csv_rows,
    sniff_delimiter,
)

# Header aliases seen in real SAP custom exports
SAP_FIELD_MAP = {
    "material": "material",
    "matnr": "material",
    "material_number": "material",
    "beschreibung": "description",
    "description": "description",
    "short_text": "description",
    "werk": "plant",
    "plant": "plant",
    "werks": "plant",
    "menge": "quantity",
    "quantity": "quantity",
    "qty": "quantity",
    "einheit": "unit",
    "unit": "unit",
    "uom": "unit",
    "netwr": "amount",
    "net_value": "amount",
    "amount": "amount",
    "waers": "currency",
    "currency": "currency",
    "budat": "posting_date",
    "posting_date": "posting_date",
    "bldat": "document_date",
    "document_date": "document_date",
    "ebeln": "po_number",
    "po_number": "po_number",
    "lifnr": "vendor",
    "vendor": "vendor",
    "mtart": "material_type",
    "material_type": "material_type",
}

FUEL_KEYWORDS = (
    "diesel",
    "gasoline",
    "petrol",
    "fuel",
    "heating oil",
    "heizöl",
    "kerosene",
    "lpg",
    "natural gas",
    "erdgas",
)


def _map_fields(row: dict) -> dict:
    mapped = {}
    for key, val in row.items():
        canonical = SAP_FIELD_MAP.get(key, key)
        if canonical not in mapped or not mapped[canonical]:
            mapped[canonical] = val
    return mapped


def _infer_category(description: str, material_type: str) -> str:
    text = f"{description} {material_type}".lower()
    if any(k in text for k in FUEL_KEYWORDS):
        return "fuel"
    return "procurement"


def parse_sap_row(row: dict) -> dict:
    """Parse one normalized SAP row into activity fields."""
    mapped = _map_fields(normalize_row_keys(row))
    description = mapped.get("description", "")
    material_type = mapped.get("material_type", "")
    category = _infer_category(description, material_type)

    qty = parse_decimal(mapped.get("quantity", ""))
    unit = mapped.get("unit", "")
    posting_date = parse_date(mapped.get("posting_date", "")) or parse_date(
        mapped.get("document_date", "")
    )

    warnings = []
    if not qty:
        warnings.append("missing_quantity")
    if not unit:
        warnings.append("missing_unit")
    if not posting_date:
        warnings.append("missing_date")

    suspicious = []
    if qty and qty > Decimal("100000"):
        suspicious.append("unusually_high_quantity")
    if unit and unit.upper() in ("ST", "EA") and category == "fuel":
        suspicious.append("fuel_in_count_units")

    return {
        "category": category,
        "scope": "scope1" if category == "fuel" else "scope3",
        "activity_date": posting_date,
        "plant_code": mapped.get("plant", ""),
        "description": description or mapped.get("material", ""),
        "quantity": qty,
        "unit_original": unit,
        "currency": mapped.get("currency", "")[:3],
        "amount": parse_decimal(mapped.get("amount", "")),
        "source_reference": mapped.get("po_number", "") or mapped.get("material", ""),
        "parse_warnings": warnings,
        "suspicion_reasons": suspicious,
        "is_suspicious": len(suspicious) > 0,
        "raw_mapped": mapped,
    }


def parse_sap_file(text: str) -> list[dict]:
    delimiter = sniff_delimiter(text, (";", ",", "\t"))
    rows = read_csv_rows(text, delimiter)
    results = []
    for i, row in enumerate(rows, start=1):
        if not any(v.strip() for v in row.values() if v):
            continue
        try:
            parsed = parse_sap_row(row)
            parsed["row_number"] = i
            parsed["raw_payload"] = row
            if parsed["parse_warnings"]:
                parsed["is_suspicious"] = True
                parsed["suspicion_reasons"] = list(
                    set(parsed.get("suspicion_reasons", []) + ["incomplete_row"])
                )
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
