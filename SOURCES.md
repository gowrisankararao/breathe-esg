# Sources — research, sample data, production risks

## 1. SAP — fuel & procurement

### Real-world format researched

- SAP custom reports (`BBP_ES_CUSTOMIZINGDATA_EXT_CSV`, ME2M/PO history exports) producing **semicolon-delimited CSV**
- LSMW/direct-input conventions: SAP technical field names, space or semicolon delimiters
- German localized headers (`Werk`, `Menge`, `Einheit`, `Budat`) in EU deployments
- European decimal notation (`12500,5`)

### What we learned

- There is no single "SAP export format" — each client configures custom reports
- Plant codes are meaningless without a lookup table
- Fuel lines may appear as material types `ROH` with descriptions containing "Diesel", not as a dedicated fuel module
- Units vary (L, KWH for natural gas, ST for miscategorized lines)

### Sample data (`sample_data/sap_procurement_fuel.csv`)

| Row | Why it's there |
|-----|----------------|
| Diesel at plants 1000/2000 | Typical fleet fuel with German dates and comma decimals |
| Natural gas in KWH | Heating fuel, Scope 1 boundary case |
| Office paper in ST at US plant | Scope 3 procurement, US date format |
| Heizöl | German fuel type name |
| Laptop docks | Non-fuel procurement |
| Gasoline 999999 L | **Suspicious** — triggers `unusually_high_quantity` |

### What breaks in production

- Different delimiter (tab vs semicolon) — mitigated by sniffer
- Column names not in alias map — needs client onboarding mapping UI
- Multiple company codes in one file — need split by `BUKRS`
- Encrypted/archived exports from SAP secure folder workflow

---

## 2. Utility — electricity

### Real-world format researched

- **Green Button "Download My Data"** CSV: Meter, TYPE, START DATE, END DATE, UNITS (Oracle docs)
- **EnergyCAP** flat file pattern: `account,meter,commodity,uom,start,end,use,cost`
- Billing periods that don't align to calendar months
- Portal data may not match bill totals exactly (estimates vs billed reads)

### What we learned

- Enterprise clients export **billing period** summaries, not 15-min AMI, for Scope 2 reporting
- "Multiple" meter field when one account has many service points
- Negative usage appears on rebills/credits

### Sample data (`sample_data/utility_electricity.csv`)

| Row | Why it's there |
|-----|----------------|
| Berlin/Munich/Chicago meters | Multi-site, non-aligned periods (Dec 18–Jan 17 vs Jan 5–Feb 4) |
| Chicago negative 150 kWh | **Suspicious** `negative_usage` |
| High volume Chicago row | Normal large facility baseline |

### What breaks in production

- 50+ utilities × 50+ CSV schemas — needs schema registry or vendor aggregator (Arcadia/Urjanet)
- Missing facility name — only account number; requires meter→site master data
- Unit confusion (MWh labeled as kWh)

---

## 3. Corporate travel — Concur-style

### Real-world format researched

- **SAP Concur Expense File Export** — customizable CSV/pipe-delimited detail extract
- **Standard Accounting Extract (SAE) v3** — pipe-delimited, multi-segment; overkill for prototype
- Expense types are custom per client ("Airfare" vs "Air Fare - International")
- Flights often lack distance — only airport codes

### What we learned

- Category for GHG must be inferred from expense type string, not a clean ISO code
- Mileage reports include distance; flights may not
- Finance extracts include non-travel lines — need filtering

### Sample data (`sample_data/concur_travel_export.csv`)

| Row | Why it's there |
|-----|----------------|
| JFK→LHR flight + London hotel | Typical trip pattern |
| Car mileage with 82 km | Ground transport with distance |
| Flight with empty route | **Suspicious** `flight_missing_route` |
| Taxi SFO | Ground without distance |
| $52,000 airfare ORD→DFW | **Suspicious** `unusually_high_spend` |

### What breaks in production

- Pipe vs comma vs tab delimiter changes per Concur admin config
- Custom fields (cost center, project) not in standard extract — need mapping
- Round-trip vs one-way line splitting
- Need Great Circle distance service when only IATA codes exist
