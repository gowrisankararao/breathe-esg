# Decisions

## SAP: flat file CSV (semicolon-delimited), not IDoc/OData

**Chose:** Custom SAP report export as semicolon CSV with German/English mixed headers.

**Why:** Mid-market enterprises without PI/Integration Suite most often get fuel/procurement data via scheduled reports (ME2M-style material movement or PO history), not live OData. IDocs require ABAP/PI expertise; OData MM APIs need gateway setup and auth the PM won't have in week one.

**Subset handled:**
- Fuel (diesel, gasoline, natural gas, heating oil) and non-fuel procurement lines
- Plant code, quantity, unit, amount, posting date, PO reference
- German headers (`Werk`, `Menge`, `Einheit`, `Budat`) and European number formats (`12500,5`)

**Ignored:**
- IDoc MATMAS / ORDERS05
- OData `API_PURCHASEORDER_PROCESS_SRV`
- Batch-level serial numbers, storage location, valuation class
- Multi-company code consolidation

**PM questions:**
- Which SAP module owns fuel — MM, PM, or custom Z-report?
- Do you already have a plant → site mapping spreadsheet?
- Reporting currency vs document currency rules?

**Ingestion mechanism:** File upload (analyst or IT drops export in portal). Matches how sustainability teams receive SAP data today — email attachment, not API.

---

## Utility: portal CSV billing export, not PDF OCR

**Chose:** Green Button / EnergyCAP-style billing CSV: account, meter, commodity, UOM, bill start/end, usage, cost.

**Why:** Facilities teams already export CSV from utility portals ("Download My Data", Green Button). PDF bills require OCR, are error-prone on tariff line items, and don't scale to 200 meters. API (Arcadia Plug, Urjanet) needs contracts — out of scope for 4-day prototype.

**Subset handled:**
- Electricity kWh per billing period (non-calendar-aligned dates)
- Multiple meters per site
- Negative usage flagged suspicious (credit rebill)

**Ignored:**
- 15-minute AMI interval data
- Tariff breakdown (peak/off-peak demand charges)
- Market-based vs location-based Scope 2 factors
- Gas/water commodities

**PM questions:**
- Which utility portal(s) — one CSV schema or many?
- Do billing periods map to your reporting year or fiscal calendar?
- Who owns meter-to-facility mapping when account says "Multiple"?

**Ingestion mechanism:** File upload of portal CSV export.

---

## Travel: Concur Expense File Export CSV, not live API

**Chose:** Pipe-delimited expense extract mimicking SAP Concur's customizable GL/expense export (not full SAE v3 binary spec).

**Why:** Concur API access requires admin credentials, OAuth, and client-specific field mappings. The **Expense File Export** is what finance already receives when T&E isn't integrated — pipe-delimited, configurable columns. SAE v3 is 50+ segment types; we need flight/hotel/ground line items only.

**Subset handled:**
- Expense type → category inference (airfare → flight, hotel → hotel, mileage → ground)
- Amount, date, currency, origin/destination where present
- Suspicion when flight has no route or distance

**Ignored:**
- Full SAE v3 multi-file ZIP
- Per-passenger class (economy vs business) for factor selection
- Hotel night itemization / tax lines
- Navan API real-time pull

**PM questions:**
- Concur or Navan? Who owns export field configuration?
- Do you have a distance calculation service for airport pairs?
- Policy: are personal car mileage reports in scope for Scope 3 cat 6?

**Ingestion mechanism:** File upload of monthly expense extract.

---

## Review workflow

**Chose:** `pending` → `approved` → `locked` (explicit lock step, not auto-lock on approve).

**Why:** Analysts often approve in batches then a lead locks for audit. Separating steps matches SOX-style sign-off.

**Ignored:** Multi-level approval chains, role-based permissions beyond single analyst user.

---

## Authentication

**Chose:** Token auth + demo user per org.

**Why:** Simple for SPA + Render deploy. Production would use SSO (Okta) and org-scoped RBAC.

---

## Frontend stack

**Chose:** React + Vite + Tailwind (no component library).

**Why:** Fast to build a focused analyst UI without fighting MUI theming. Dark theme reduces eye strain for long review sessions.
