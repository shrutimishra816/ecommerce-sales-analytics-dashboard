"""
Daily ETL pipeline for the E-Commerce Sales Dashboard project.

Extract  -> read raw transaction export (CSV, as dropped by the source system)
Transform-> deduplicate, fix invalid/missing values, enforce types & business rules
Load     -> write to a relational database (SQLite locally / MySQL-compatible schema
            in production; connection string is the only thing that changes)

Run: python etl_pipeline.py
"""
import sqlite3
import logging
import pandas as pd
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("ecommerce_etl")

RAW_PATH = Path(__file__).parent.parent / "data" / "raw_transactions.csv"
DB_PATH = Path(__file__).parent.parent / "data" / "ecommerce_warehouse.db"


def extract() -> pd.DataFrame:
    log.info("Extracting raw transactions from %s", RAW_PATH)
    df = pd.read_csv(RAW_PATH, parse_dates=["order_date"])
    log.info("Extracted %s raw rows", f"{len(df):,}")
    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    # 1. Drop exact duplicate transactions (dupe order_id + customer_id + order_date)
    df = df.drop_duplicates(subset=["order_id", "customer_id", "order_date", "sku"])
    log.info("Removed %s duplicate rows", before - len(df))

    # 2. Fix invalid numeric values
    invalid_price = (df["unit_price"] <= 0)
    invalid_qty = (df["quantity"] <= 0)
    log.info("Fixing %s invalid unit_price rows and %s invalid quantity rows",
              invalid_price.sum(), invalid_qty.sum())
    # Impute invalid prices with the category median (robust to outliers)
    cat_median_price = df.loc[~invalid_price].groupby("category")["unit_price"].median()
    df.loc[invalid_price, "unit_price"] = df.loc[invalid_price, "category"].map(cat_median_price)
    df.loc[invalid_qty, "quantity"] = 1

    # 3. Recompute derived financial fields so they stay internally consistent
    df["gross_revenue"] = (df["unit_price"] * df["quantity"]).round(2)
    df["discount_amount"] = (df["gross_revenue"] * df["discount_pct"] / 100).round(2)
    df["net_revenue"] = (df["gross_revenue"] - df["discount_amount"]).round(2)

    # 4. Fill missing categorical values
    missing_region = df["region"].isna().sum()
    log.info("Backfilling %s missing region values with 'Unknown'", missing_region)
    df["region"] = df["region"].fillna("Unknown")

    # 5. Enforce dtypes
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["is_returned"] = df["is_returned"].astype(int)
    df["quantity"] = df["quantity"].astype(int)

    # 6. Derived time dimensions used heavily by the dashboard / SQL layer
    df["order_year"] = df["order_date"].dt.year
    df["order_month"] = df["order_date"].dt.to_period("M").astype(str)
    df["order_quarter"] = df["order_date"].dt.to_period("Q").astype(str)
    df["day_of_week"] = df["order_date"].dt.day_name()

    log.info("Transform complete: %s clean rows (from %s raw rows)", f"{len(df):,}", f"{before:,}")
    return df


def load(df: pd.DataFrame) -> None:
    log.info("Loading %s rows into warehouse at %s", f"{len(df):,}", DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("fact_transactions", conn, if_exists="replace", index=False)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_order_date ON fact_transactions(order_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_region ON fact_transactions(region)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON fact_transactions(category)")
    conn.commit()
    conn.close()
    log.info("Load complete.")


def run():
    df = extract()
    clean = transform(df)
    load(clean)
    log.info("ETL run finished successfully — %s clean records available for analysis.", f"{len(clean):,}")
    return clean


if __name__ == "__main__":
    run()
