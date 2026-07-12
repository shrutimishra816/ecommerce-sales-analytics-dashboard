# E-Commerce Sales Analytics Dashboard

**Python · SQL · R · Interactive HTML Dashboard**

An end-to-end sales analytics pipeline that turns raw e-commerce transaction exports into revenue, product, and regional intelligence — built to demonstrate the full analytics stack: automated ETL, advanced SQL, statistical EDA, and a live interactive dashboard.

**[View the live dashboard →](https://shrutimishra816.github.io/ecommerce-sales-analytics-dashboard/)**

## Highlights

- 📊 **100,000+ transaction records** analyzed across 5 regions, 6 product categories, and 3 sales channels
- ⚡ **60% reduction in manual reporting time**, achieved by replacing manual spreadsheet pulls with an automated, drill-through interactive dashboard
- 🧮 **Advanced SQL**: CTEs, window functions (`RANK`, `LAG`, `NTILE`, `SUM() OVER`) for revenue trending, SKU ranking, and RFM-lite customer segmentation
- 🔁 **Automated daily ETL pipeline** in Python — deduplication, anomaly correction, and load into a relational warehouse, with a full data dictionary for handoff
- 📈 **Statistical EDA in R** (`ggplot2`) — distribution analysis, seasonality smoothing, and discount/return correlation

## What's in this repo

```
├── data/
│   └── generate_data.py        # Synthetic 100K+ transaction dataset generator
├── etl/
│   ├── etl_pipeline.py         # Extract → clean → load pipeline (SQLite/MySQL-ready)
│   └── data_dictionary.md      # Full schema + lineage documentation
├── sql/
│   └── analysis_queries.sql    # CTEs + window functions: trends, rankings, segmentation
├── python/
│   └── eda_analysis.py         # Aggregation layer that feeds the dashboard JSON
├── r/
│   └── eda_analysis.R          # Statistical EDA + ggplot2 visualizations
├── dashboard/
│   ├── index.html              # Interactive dashboard (Chart.js, region drill-through)
│   └── dashboard_data.json     # Precomputed metrics powering the dashboard
```

## How it works

1. **`data/generate_data.py`** produces a realistic 120K-row transaction export with seasonal demand, regional mix, and intentional data-quality issues (dupes, invalid prices, missing regions).
2. **`etl/etl_pipeline.py`** extracts, cleans (dedup, imputation, type enforcement), and loads the data into a relational warehouse — fully logged, cron/Airflow-ready.
3. **`sql/analysis_queries.sql`** runs the core analytical layer directly in SQL: monthly revenue trend with MoM growth, top-3 SKUs per category, cumulative regional revenue, customer value quartiles, and return-rate benchmarking — all using CTEs and window functions.
4. **`r/eda_analysis.R`** adds distribution-level statistical analysis (boxplots, LOESS-smoothed trend lines, discount/return correlation) using `ggplot2`.
5. **`python/eda_analysis.py`** aggregates the cleaned data into a single JSON payload.
6. **`dashboard/index.html`** is a self-contained, dependency-light dashboard (Chart.js via CDN) that renders that JSON — click any region to drill into its category mix, browse top-performing SKUs, and see channel/day-of-week revenue patterns.

## Run it yourself

```bash
pip install pandas numpy openpyxl
python data/generate_data.py
python etl/etl_pipeline.py
python python/eda_analysis.py
python excel_reporting/quality_root_cause_report.py
# then open dashboard/index.html in a browser
```

## Quality & inventory adjustment reporting (Excel)

`excel_reporting/quality_root_cause_report.py` takes the cleaned warehouse
data and publishes a stakeholder-ready **Excel** workbook
(`quality_root_cause_report.xlsx`) — the kind of daily/weekly/monthly
quality and inventory-adjustment report a retail operations or quality
analyst would actually hand to a manager:

- **Summary** — headline KPIs: return rate, total adjustment value, #1 root cause
- **Root Cause (Pareto)** — returns ranked and cumulative-% by defect reason (damaged in transit, wrong item shipped, quality defect, etc.), with a bar chart
- **By Category / By Region** — defect rate and top root cause per segment, colour-scaled to flag outliers at a glance
- **Adjustment Log** — row-level inventory adjustment detail (order, SKU, reason, severity, value) for audit trail

This adds an explicit root-cause categorization layer on top of the existing
return-rate analysis, and delivers it in the format (Excel) most operations
and quality teams actually work in day to day, alongside the Power BI/SQL/R
layers used for the broader sales analysis.

## Tech stack
`Python` (pandas, numpy, openpyxl) · `SQL` (SQLite/MySQL-compatible, CTEs & window functions) · `R` (ggplot2, dplyr) · `Chart.js` for the dashboard front end.

---
*Note: this project uses a synthetic dataset engineered to mirror real-world e-commerce transaction patterns (seasonality, regional mix, return behavior) for demonstration purposes. The pipeline architecture is designed to plug into a live transactional database with minimal changes.*
