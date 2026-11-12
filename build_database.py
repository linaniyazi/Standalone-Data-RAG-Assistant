"""Build superstore.db from data/Superstore.csv (reproducible, from scratch).

python build_database.py                      -> writes superstore.db
python build_database.py --out test.db        -> writes a different file
python build_database.py --csv other.csv
"""
import argparse
import os
import sqlite3

import pandas as pd

CATEGORY_GROUP = [
    ("Technology", "High Margin"),
    ("Office Supplies", "High Margin"),
    ("Furniture", "Low Margin"),
]

VIEWS = {
    "category_summary": """
CREATE VIEW category_summary AS
SELECT
    Category,
    SUM(Sales) AS total_sales,
    SUM(Profit) AS total_profit,
    ROUND(SUM(Profit) * 1.0 / SUM(Sales), 4) AS overall_profit_margin
FROM orders
GROUP BY Category
""",
    "subcategory_summary": """
CREATE VIEW subcategory_summary AS
SELECT
    "Sub-Category",
    SUM(Sales) AS total_sales,
    SUM(Profit) AS total_profit,
    ROUND(SUM(Profit) * 1.0 / SUM(Sales), 4) AS overall_profit_margin
FROM orders
GROUP BY "Sub-Category"
""",
    "region_summary": """
CREATE VIEW region_summary AS
SELECT
    Region,
    SUM(Sales) AS total_sales,
    SUM(Profit) AS total_profit,
    ROUND(SUM(Profit) * 1.0 / SUM(Sales), 4) AS overall_profit_margin
FROM orders
GROUP BY Region
""",
}


def build(csv_path: str, db_path: str) -> None:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path, encoding="latin1")
    print(f"Read {len(df)} rows, {len(df.columns)} columns from {csv_path}")

    # نفس معالجة التاريخ تبع الأسبوع 6: M/D/YYYY -> datetime + order_date_fixed
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
    df["order_date_fixed"] = df["Order Date"].dt.strftime("%Y-%m-%d")

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    try:
        df.to_sql("orders", conn, if_exists="replace", index=False)

        conn.execute("""
            CREATE TABLE category_group (
                Category TEXT PRIMARY KEY,
                business_line TEXT
            )""")
        conn.executemany("INSERT INTO category_group VALUES (?, ?)", CATEGORY_GROUP)

        for sql in VIEWS.values():
            conn.execute(sql)
        conn.commit()
        print(f"Built {db_path}: table orders, table category_group, "
              f"views {', '.join(VIEWS)}")
        verify(conn)
    finally:
        conn.close()


def verify(conn) -> None:
    n = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    lo, hi = conn.execute(
        "SELECT MIN(order_date_fixed), MAX(order_date_fixed) FROM orders").fetchone()
    print(f"Check: {n} rows, dates {lo} to {hi}")

    if n != 9994:
        print("Known-value checks skipped (not the full Superstore dataset).")
        return

    expected_sales = {"West": 725457.8245, "East": 678781.24,
                      "Central": 501239.8908, "South": 391721.905}
    expected_profit = {"West": 108418.4489, "East": 91522.78,
                       "South": 46749.4303, "Central": 39706.3625}
    ok = True
    for region, sales, profit in conn.execute(
            "SELECT Region, total_sales, total_profit FROM region_summary"):
        good = (abs(sales - expected_sales[region]) < 0.01
                and abs(profit - expected_profit[region]) < 0.01)
        ok &= good
        print(f"  {'OK  ' if good else 'FAIL'} {region}: sales={sales:.2f} profit={profit:.2f}")
    tables = conn.execute(
        'SELECT total_profit FROM subcategory_summary WHERE "Sub-Category"=\'Tables\''
    ).fetchone()[0]
    good = abs(tables - (-17725.4811)) < 0.01
    ok &= good
    print(f"  {'OK  ' if good else 'FAIL'} Tables total profit = {tables:.2f}")
    ok &= (lo == "2014-01-03" and hi == "2017-12-30")
    print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default="data/Superstore.csv")
    p.add_argument("--out", default="superstore.db")
    args = p.parse_args()
    build(args.csv, args.out)