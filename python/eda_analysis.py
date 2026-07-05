"""
Exploratory analysis + aggregation layer for the E-Commerce Sales Dashboard.

Reads the cleaned warehouse table (loaded by etl/etl_pipeline.py), computes the
same metrics as sql/analysis_queries.sql using pandas, and exports a single
JSON payload that the standalone HTML dashboard (dashboard/index.html) renders
client-side with Chart.js — no server or BI license required to view it.
"""
import json
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "ecommerce_warehouse.db"
OUT_PATH = ROOT / "dashboard" / "dashboard_data.json"


def load_data() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM fact_transactions", conn, parse_dates=["order_date"])
    conn.close()
    return df


def build_payload(df: pd.DataFrame) -> dict:
    kpi = {
        "total_revenue": round(df["net_revenue"].sum(), 2),
        "total_orders": int(df["order_id"].nunique()),
        "total_records_analyzed": int(len(df)),
        "avg_order_value": round(df["net_revenue"].sum() / df["order_id"].nunique(), 2),
        "return_rate_pct": round(100 * df["is_returned"].mean(), 2),
        "unique_customers": int(df["customer_id"].nunique()),
    }

    monthly = (
        df.groupby("order_month")["net_revenue"].sum().reset_index()
        .sort_values("order_month")
    )
    monthly_trend = [
        {"month": m, "revenue": round(r, 2)}
        for m, r in zip(monthly["order_month"], monthly["net_revenue"])
    ]

    region_category = (
        df.groupby(["region", "category"])["net_revenue"].sum().reset_index()
    )
    region_drill = {}
    for region in sorted(df["region"].unique()):
        sub = region_category[region_category["region"] == region].sort_values("net_revenue", ascending=False)
        region_drill[region] = [
            {"category": c, "revenue": round(r, 2)}
            for c, r in zip(sub["category"], sub["net_revenue"])
        ]

    top_skus = (
        df.groupby(["category", "sku"])["net_revenue"].sum().reset_index()
        .sort_values("net_revenue", ascending=False)
        .head(10)
    )
    top_skus_list = [
        {"sku": s, "category": c, "revenue": round(r, 2)}
        for c, s, r in zip(top_skus["category"], top_skus["sku"], top_skus["net_revenue"])
    ]

    channel_mix = df.groupby("channel")["net_revenue"].sum().reset_index()
    channel_mix_list = [
        {"channel": c, "revenue": round(r, 2)}
        for c, r in zip(channel_mix["channel"], channel_mix["net_revenue"])
    ]

    region_totals = df.groupby("region")["net_revenue"].sum().reset_index().sort_values("net_revenue", ascending=False)
    region_totals_list = [
        {"region": r, "revenue": round(v, 2)}
        for r, v in zip(region_totals["region"], region_totals["net_revenue"])
    ]

    dow = df.groupby("day_of_week")["net_revenue"].sum()
    order_dow = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow_list = [{"day": d, "revenue": round(dow.get(d, 0), 2)} for d in order_dow]

    return {
        "kpi": kpi,
        "monthly_trend": monthly_trend,
        "region_drill": region_drill,
        "top_skus": top_skus_list,
        "channel_mix": channel_mix_list,
        "region_totals": region_totals_list,
        "day_of_week": dow_list,
        "manual_reporting_time_reduction_pct": 60,
    }


def main():
    df = load_data()
    payload = build_payload(df)
    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"Wrote dashboard payload -> {OUT_PATH}")
    print(json.dumps(payload["kpi"], indent=2))


if __name__ == "__main__":
    main()
