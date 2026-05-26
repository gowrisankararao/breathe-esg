import csv
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from dateutil import parser as date_parser


def decode_content(file_bytes: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="replace")


def sniff_delimiter(text: str, candidates=(";", ",", "\t", "|")) -> str:
    first_line = text.splitlines()[0] if text else ""
    counts = {d: first_line.count(d) for d in candidates}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ";"


def read_csv_rows(text: str, delimiter: str | None = None) -> list[dict[str, str]]:
    delimiter = delimiter or sniff_delimiter(text)
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    return [dict(row) for row in reader]


def normalize_header(key: str) -> str:
    return re.sub(r"\s+", "_", key.strip().lower())


def normalize_row_keys(row: dict) -> dict[str, str]:
    return {normalize_header(k): (v or "").strip() for k, v in row.items()}


def parse_decimal(value: str) -> Decimal | None:
    if not value or not str(value).strip():
        return None
    cleaned = str(value).strip().replace(" ", "")
    # European: 1.234,56 → 1234.56
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def parse_date(value: str):
    if not value or not str(value).strip():
        return None
    value = str(value).strip()
    for fmt in ("%Y%m%d", "%d.%m.%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    try:
        return date_parser.parse(value, dayfirst=True).date()
    except (ValueError, OverflowError):
        return None


UNIT_TO_BASE = {
    "l": "liters",
    "liter": "liters",
    "liters": "liters",
    "litre": "liters",
    "litres": "liters",
    "gal": "gallons_us",
    "gallon": "gallons_us",
    "gallons": "gallons_us",
    "kg": "kg",
    "kwh": "kwh",
    "mwh": "mwh",
    "km": "km",
    "mi": "miles",
    "mile": "miles",
    "miles": "miles",
    "st": "units",  # German Stück
    "stück": "units",
    "ea": "units",
    "each": "units",
}


def normalize_unit(unit: str) -> tuple[str, Decimal | None]:
    """Return (normalized_unit, multiplier to base)."""
    if not unit:
        return "", None
    u = unit.strip().lower()
    if u in UNIT_TO_BASE:
        base = UNIT_TO_BASE[u]
        if u == "mwh":
            return "kwh", Decimal("1000")
        return base, Decimal("1")
    return u, Decimal("1")
