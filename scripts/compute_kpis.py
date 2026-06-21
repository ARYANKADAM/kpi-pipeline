"""
compute_kpis.py
Pulls last 7 days of sales data (relative to max date in table),
computes KPIs, and compares against the prior 7-day window.
"""

import pandas as pd
from sqlalchemy import create_engine

# ---- CONFIG (same as load_data.py) ----
import os
from dotenv import load_dotenv

load_dotenv()  # loads variables from .env into os.environ when running locally

DB_USER = os.environ.get("KPI_DB_USER", "postgres")
DB_PASSWORD = os.environ.get("KPI_DB_PASSWORD", "")
DB_HOST = os.environ.get("KPI_DB_HOST", "localhost")
DB_PORT = os.environ.get("KPI_DB_PORT", "5433")
DB_NAME = os.environ.get("KPI_DB_NAME", "kpi_db")


def get_engine():
    return create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
    )


def fetch_window(engine, start_date, end_date):
    """Fetch rows where order_date is within [start_date, end_date)."""
    query = """
        SELECT * FROM sales
        WHERE order_date >= %(start)s AND order_date < %(end)s
    """
    df = pd.read_sql(query, engine, params={"start": start_date, "end": end_date})
    return df


def compute_kpis(df):
    if df.empty:
        return {
            "total_revenue": 0,
            "total_orders": 0,
            "avg_order_value": 0,
            "revenue_by_region": {},
            "top_category": None,
        }

    total_revenue = df["sales"].sum()
    total_orders = df["order_id"].nunique()
    avg_order_value = total_revenue / total_orders if total_orders else 0
    revenue_by_region = df.groupby("region")["sales"].sum().round(2).to_dict()
    top_category = df.groupby("category")["sales"].sum().idxmax()

    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "avg_order_value": round(avg_order_value, 2),
        "revenue_by_region": revenue_by_region,
        "top_category": top_category,
    }


def pct_change(current, previous):
    if previous == 0:
        return None  # avoid division by zero
    return round(((current - previous) / previous) * 100, 2)


def main():
    engine = get_engine()

    # Find the most recent date in the dataset
    max_date = pd.read_sql("SELECT MAX(order_date) AS max_date FROM sales", engine)["max_date"][0]
    max_date = pd.Timestamp(max_date)

    # Define this week and last week windows
    this_week_start = max_date - pd.Timedelta(days=6)   # 7-day window including max_date
    this_week_end = max_date + pd.Timedelta(days=1)      # exclusive upper bound

    last_week_start = this_week_start - pd.Timedelta(days=7)
    last_week_end = this_week_start

    # Fetch both windows
    this_week_df = fetch_window(engine, this_week_start, this_week_end)
    last_week_df = fetch_window(engine, last_week_start, last_week_end)

    # Compute KPIs
    this_week_kpis = compute_kpis(this_week_df)
    last_week_kpis = compute_kpis(last_week_df)

    # Week-over-week changes
    revenue_change = pct_change(this_week_kpis["total_revenue"], last_week_kpis["total_revenue"])
    orders_change = pct_change(this_week_kpis["total_orders"], last_week_kpis["total_orders"])
    aov_change = pct_change(this_week_kpis["avg_order_value"], last_week_kpis["avg_order_value"])

    report = {
        "window": {
            "this_week": (str(this_week_start.date()), str(max_date.date())),
            "last_week": (str(last_week_start.date()), str((last_week_end - pd.Timedelta(days=1)).date())),
        },
        "this_week_kpis": this_week_kpis,
        "last_week_kpis": last_week_kpis,
        "wow_change": {
            "revenue_pct": revenue_change,
            "orders_pct": orders_change,
            "avg_order_value_pct": aov_change,
        },
    }

    # Print summary to console for now (Phase 3 will turn this into a report file)
    print("\n📊 WEEKLY KPI REPORT")
    print(f"This week: {report['window']['this_week'][0]} to {report['window']['this_week'][1]}")
    print(f"Last week: {report['window']['last_week'][0]} to {report['window']['last_week'][1]}\n")

    print(f"Total Revenue: ${this_week_kpis['total_revenue']:,.2f} "
          f"({'+' if revenue_change and revenue_change >= 0 else ''}{revenue_change}% WoW)")
    print(f"Total Orders: {this_week_kpis['total_orders']} "
          f"({'+' if orders_change and orders_change >= 0 else ''}{orders_change}% WoW)")
    print(f"Avg Order Value: ${this_week_kpis['avg_order_value']:,.2f} "
          f"({'+' if aov_change and aov_change >= 0 else ''}{aov_change}% WoW)")
    print(f"Top Category: {this_week_kpis['top_category']}")
    print(f"Revenue by Region: {this_week_kpis['revenue_by_region']}")

    return report


if __name__ == "__main__":
    main()
