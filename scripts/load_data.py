"""
load_data.py
Loads Sample-Superstore CSV into the Postgres 'sales' table.
Run this whenever you want to (re)load the dataset.
"""

import pandas as pd
from sqlalchemy import create_engine

# ---- CONFIG ----
CSV_PATH = "../data/Sample-Superstore_csv.csv"   # update path if needed
DB_USER = "postgres"
DB_PASSWORD = "yourpassword"             # match what you used in `docker run`
DB_HOST = "localhost"
DB_PORT = "5433"                         # we mapped kpi-postgres to 5433
DB_NAME = "kpi_db"

def main():
    # 1. Read CSV
    df = pd.read_csv(CSV_PATH, encoding="latin1")

    # 2. Clean column names: lowercase, spaces -> underscores, remove hyphens
    df.columns = [
        c.strip().lower().replace(" ", "_").replace("-", "_")
        for c in df.columns
    ]

    # 3. Parse dates explicitly (dayfirst=True since format is DD/MM/YYYY)
    df["order_date"] = pd.to_datetime(df["order_date"], dayfirst=True)
    df["ship_date"] = pd.to_datetime(df["ship_date"], dayfirst=True)

    # 4. Connect to Postgres
    engine = create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # 5. Push to DB (replace table each time for a clean reload)
    df.to_sql("sales", engine, if_exists="replace", index=False)

    print(f"✅ Loaded {len(df)} rows into 'sales' table.")
    print(f"   Date range: {df['order_date'].min().date()} to {df['order_date'].max().date()}")

if __name__ == "__main__":
    main()