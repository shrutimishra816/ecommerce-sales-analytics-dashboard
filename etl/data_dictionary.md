# Data Dictionary — `fact_transactions`

| Column | Type | Description |
|---|---|---|
| order_id | INTEGER | Unique order identifier (PK) |
| customer_id | INTEGER | Unique customer identifier (FK, ~28K distinct customers) |
| order_date | DATE | Date the order was placed |
| region | TEXT | Sales region: North America, Europe, Asia Pacific, Latin America, Middle East & Africa |
| category | TEXT | Product category (6 categories) |
| sku | TEXT | Product name / SKU label |
| channel | TEXT | Sales channel: Website, Mobile App, Marketplace |
| payment_method | TEXT | Payment method used at checkout |
| quantity | INTEGER | Units purchased in the line item |
| unit_price | FLOAT | Price per unit at time of sale (local currency) |
| discount_pct | INTEGER | Discount percentage applied (0–30) |
| gross_revenue | FLOAT | unit_price × quantity |
| discount_amount | FLOAT | gross_revenue × discount_pct / 100 |
| net_revenue | FLOAT | gross_revenue − discount_amount |
| is_returned | INTEGER | 1 if the order was returned, else 0 |
| order_year | INTEGER | Derived: calendar year |
| order_month | TEXT | Derived: YYYY-MM |
| order_quarter | TEXT | Derived: YYYY-Qn |
| day_of_week | TEXT | Derived: day name |

## Source & lineage
- **Source**: daily transactional export (`raw_transactions.csv`), simulating a POS/e-commerce order system dump.
- **Grain**: one row = one product line item within an order.
- **Refresh cadence**: designed to run daily via `etl_pipeline.py` (cron / Airflow-ready).
- **Known transformations**: duplicate removal, invalid price/quantity imputation (category median / default), missing-region backfill, revenue field recomputation for consistency, time-dimension derivation.

## Data quality rules enforced by the ETL
1. `unit_price` and `quantity` must be > 0 — invalid values are imputed, never silently dropped, to preserve volume metrics.
2. `gross_revenue`, `discount_amount`, `net_revenue` are always recomputed from source fields rather than trusted as-is, to avoid propagating upstream calculation drift.
3. Duplicate line items (same order, customer, date, SKU) are removed before load.
4. `region` nulls are labeled `Unknown` rather than dropped, so denominators in aggregate reports stay accurate.
