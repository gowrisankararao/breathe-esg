# Tradeoffs — three things we deliberately did not build

## 1. Emission factor engine / tCO₂e calculation

**What:** Applying DEFRA, EPA, or client-specific factors to normalized quantities and producing CO₂e totals.

**Why not:** The assignment states the hard part is ingestion and normalization, not carbon math. Building factors prematurely invites false precision (wrong factor for hotel nights vs room-nights, location-based Scope 2, etc.) without methodology sign-off from the client.

**What we'd need from PM:** Which factor library, reporting year, and whether Scope 2 is location- or market-based.

---

## 2. Automated duplicate detection and cross-source reconciliation

**What:** Detecting the same activity ingested twice (re-uploaded SAP file) or matching utility kWh to SAP electricity spend.

**Why not:** Requires stable business keys (PO line + material + plant + date) that vary per client SAP config. Reconciliation rules are a consulting engagement, not a 4-day prototype.

**What we'd need:** Golden-key definition per source and tolerance rules for fuzzy matches.

---

## 3. PDF utility bill parsing (OCR)

**What:** Uploading scanned utility PDFs and extracting meter reads via OCR.

**Why not:** High engineering cost, low reliability on tariff tables, and facilities teams already have CSV export paths on modern portals. PDF is a fallback in production, usually handled by a dedicated service (e.g. EnergyCAP, Urjanet), not bespoke OCR in the ingestion app.

**What we'd need:** Volume of PDF-only utilities vs CSV-capable, and budget for a document-AI vendor.
