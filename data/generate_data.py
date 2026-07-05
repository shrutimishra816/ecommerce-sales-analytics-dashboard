"""
Synthetic e-commerce transaction data generator.
Produces 120,000 realistic transaction records with seasonal trends,
regional patterns, and product-category dynamics for the Sales Dashboard project.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

rng = np.random.default_rng(42)

N = 120_000

regions = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East & Africa"]
region_weights = [0.34, 0.28, 0.22, 0.10, 0.06]

categories = {
    "Electronics": ["Wireless Earbuds", "4K Smart TV", "Laptop Sleeve", "Bluetooth Speaker", "Gaming Mouse", "Power Bank"],
    "Apparel": ["Denim Jacket", "Running Shoes", "Cotton T-Shirt", "Wool Sweater", "Yoga Pants", "Rain Jacket"],
    "Home & Kitchen": ["Air Fryer", "Coffee Maker", "Bedsheet Set", "LED Desk Lamp", "Vacuum Cleaner", "Cutlery Set"],
    "Beauty & Personal Care": ["Face Serum", "Hair Dryer", "Electric Toothbrush", "Perfume", "Skincare Kit"],
    "Sporting Goods": ["Yoga Mat", "Dumbbell Set", "Cycling Helmet", "Camping Tent", "Water Bottle"],
    "Toys & Games": ["Building Blocks", "Board Game", "RC Car", "Puzzle Set", "Action Figure"],
}
category_names = list(categories.keys())
category_weights = [0.27, 0.22, 0.18, 0.13, 0.11, 0.09]

channels = ["Website", "Mobile App", "Marketplace"]
channel_weights = [0.45, 0.40, 0.15]

payment_methods = ["Credit Card", "Debit Card", "Digital Wallet", "Cash on Delivery", "Buy Now Pay Later"]
payment_weights = [0.38, 0.20, 0.24, 0.10, 0.08]

start_date = datetime(2023, 1, 1)
end_date = datetime(2025, 12, 31)
total_days = (end_date - start_date).days

# Base price ranges per category (min, max) and a per-SKU price anchor
category_price_range = {
    "Electronics": (15, 650),
    "Apparel": (10, 180),
    "Home & Kitchen": (12, 320),
    "Beauty & Personal Care": (5, 120),
    "Sporting Goods": (8, 260),
    "Toys & Games": (6, 90),
}

def seasonal_multiplier(day_of_year):
    # Holiday season (Nov-Dec) and mid-year sale (June) bumps
    if day_of_year >= 320 or day_of_year <= 5:
        return 1.55
    if 150 <= day_of_year <= 175:
        return 1.25
    return 1.0

rows = []
cat_choices = rng.choice(category_names, size=N, p=category_weights)
region_choices = rng.choice(regions, size=N, p=region_weights)
channel_choices = rng.choice(channels, size=N, p=channel_weights)
payment_choices = rng.choice(payment_methods, size=N, p=payment_weights)
day_offsets = rng.integers(0, total_days, size=N)

customer_pool_size = 28_000
customer_ids = rng.integers(100000, 100000 + customer_pool_size, size=N)

for i in range(N):
    cat = cat_choices[i]
    sku = rng.choice(categories[cat])
    lo, hi = category_price_range[cat]
    base_price = rng.uniform(lo, hi)
    date = start_date + timedelta(days=int(day_offsets[i]))
    mult = seasonal_multiplier(date.timetuple().tm_yday)
    qty = rng.choice([1, 1, 1, 2, 2, 3, 4], p=[0.42, 0.2, 0.1, 0.14, 0.06, 0.05, 0.03])
    discount_pct = rng.choice([0, 0, 5, 10, 15, 20, 30], p=[0.35, 0.15, 0.15, 0.15, 0.1, 0.07, 0.03])
    unit_price = round(base_price * mult, 2)
    gross_revenue = round(unit_price * qty, 2)
    discount_amt = round(gross_revenue * discount_pct / 100, 2)
    net_revenue = round(gross_revenue - discount_amt, 2)
    # ~2.5% return rate, higher for apparel
    return_prob = 0.045 if cat == "Apparel" else 0.02
    is_returned = rng.random() < return_prob

    rows.append((
        200000 + i,
        int(customer_ids[i]),
        date.strftime("%Y-%m-%d"),
        region_choices[i],
        cat,
        sku,
        channel_choices[i],
        payment_choices[i],
        int(qty),
        unit_price,
        discount_pct,
        gross_revenue,
        discount_amt,
        net_revenue,
        int(is_returned),
    ))

df = pd.DataFrame(rows, columns=[
    "order_id", "customer_id", "order_date", "region", "category", "sku",
    "channel", "payment_method", "quantity", "unit_price", "discount_pct",
    "gross_revenue", "discount_amount", "net_revenue", "is_returned"
])

# Inject a small number of data-quality issues on purpose, then the ETL script fixes them
dirty_idx = rng.choice(df.index, size=600, replace=False)
df.loc[dirty_idx[:200], "unit_price"] = -1  # invalid negative prices
df.loc[dirty_idx[200:400], "quantity"] = 0   # invalid zero quantity
df.loc[dirty_idx[400:], "region"] = None     # missing region

# Duplicate ~300 rows to simulate real-world dupes for the ETL to catch
dupes = df.sample(300, random_state=1)
df = pd.concat([df, dupes], ignore_index=True)

df.to_csv("/home/claude/ecommerce/data/raw_transactions.csv", index=False)
print(f"Generated {len(df):,} rows -> raw_transactions.csv")
print(df.head())
