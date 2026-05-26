# Data Model

## Design goal

The hard part of ESG ingestion is not carbon math — it is reconciling heterogeneous client data into a **single reviewable, auditable activity ledger** per tenant. The model optimizes for:

1. **Multi-tenancy** — strict org isolation
2. **Scope 1 / 2 / 3** — assigned at normalization time from category rules
3. **Source-of-truth** — every activity row links to ingestion run + raw staging row
4. **Unit normalization** — original units preserved; normalized quantity stored separately
5. **Audit trail** — immutable log of create, edit, approve, reject, lock

## Entity relationship (conceptual)

```
Organization
  ├── UserProfile → User (analyst)
  ├── PlantLookup (SAP plant code → site name)
  ├── IngestionRun
  │     └── RawRecord (staging JSON per source row)
  └── ActivityRecord (normalized, reviewable)
        └── AuditLog (immutable events)
```

## Core entities

### Organization

Tenant boundary. Every query filters by `organization_id` via the authenticated user's `UserProfile`. No cross-tenant data access at the API layer.

### PlantLookup

SAP exports ship opaque plant codes (`Werk` / `1000`). Real deployments maintain a client-specific mapping table. The parser resolves `plant_code → site_name` at ingest time; unresolved codes keep the raw code and flag `parse_warnings`.

### IngestionRun

One upload attempt from one source. Tracks operational metrics analysts care about:

- `rows_total`, `rows_parsed`, `rows_failed`, `rows_suspicious`
- `source_type`: `sap` | `utility` | `travel`
- `filename`, `uploaded_by`, timestamps

This is the **provenance anchor**: "this file arrived at this time."

### RawRecord

Staging layer. Stores the verbatim parsed row as JSON plus `parse_error` if the row could not be normalized. Preserved even when normalization succeeds so auditors can diff "what SAP said" vs "what we stored."

### ActivityRecord

The normalized unit of work. One row ≈ one emissions-relevant activity (fuel purchase, electricity bill period, flight leg).

| Field group | Purpose |
|-------------|---------|
| `scope`, `category` | GHG classification (`scope1`/`fuel`, `scope2`/`electricity`, `scope3`/`procurement`/`flight`/…) |
| `activity_date`, `period_start`, `period_end` | Temporal — utility uses billing period; SAP uses posting date |
| `quantity`, `unit_original`, `quantity_normalized`, `unit_normalized` | Dual storage: never lose source units |
| `is_suspicious`, `suspicion_reasons`, `parse_warnings` | Analyst triage without blocking ingest |
| `review_status` | `pending` → `approved` → `locked` (or `rejected`) |
| `ingestion_run`, `raw_record` | Lineage back to source file and row |

**Scope assignment rules (prototype):**

| Source | Category | Scope |
|--------|----------|-------|
| SAP | fuel (keyword match) | Scope 1 |
| SAP | procurement | Scope 3 |
| Utility | electricity | Scope 2 |
| Travel | flight, hotel, ground | Scope 3 |

Production would externalize these rules per client methodology (GHG Protocol, location vs market-based Scope 2, etc.).

### AuditLog

Append-only event log per activity:

- `created` — ingested from file
- `edited` — analyst corrected quantity/description before approval
- `approved` / `rejected` / `locked` — review workflow

`field_changes` stores `{field: [old, new]}` for defensibility.

## Multi-tenancy enforcement

- `UserProfile.organization` is the sole tenant key on the user
- All ViewSets filter `queryset` by `request.user.profile.organization`
- No organization ID in URLs (prevents IDOR if an analyst guesses another org's PK)

## What we deliberately did not model (yet)

- Emission factors and tCO₂e calculation (downstream of approved activities)
- Client hierarchy (subsidiaries, joint ventures)
- Versioned methodology / recalculation runs
- Duplicate detection across runs (same PO line ingested twice)

See [TRADEOFFS.md](TRADEOFFS.md).
