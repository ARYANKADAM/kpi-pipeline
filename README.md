# Automated KPI Reporting Pipeline

An end-to-end data pipeline that pulls sales data from PostgreSQL, computes weekly KPIs with week-over-week comparisons, generates a formatted Excel report, and automatically delivers it to Slack — orchestrated by Apache Airflow on a weekly schedule.

## Why this project

Manual weekly reporting is a common time-sink for analysts. This project automates the full workflow: **data → analysis → report → delivery**, with zero manual intervention once scheduled.

## Architecture

```
PostgreSQL (sales data)
        │
        ▼
Apache Airflow DAG (scheduled: every Monday, 8:00 AM)
        │
        ├── Task 1: compute_kpis      → queries DB, calculates KPIs + WoW change
        ├── Task 2: generate_report   → builds formatted Excel report
        └── Task 3: send_to_slack     → posts summary + file to Slack channel
```

Data flows between tasks via Airflow XCom (no intermediate files needed).

## Tech Stack

- **Database:** PostgreSQL (Dockerized)
- **Orchestration:** Apache Airflow 2.9 (Docker Compose, LocalExecutor)
- **Data processing:** Python, Pandas, SQLAlchemy
- **Report generation:** openpyxl
- **Delivery:** Slack SDK (slack_sdk)
- **Secrets management:** python-dotenv (local), Airflow Variables (orchestrated runs)

## Features

- **Automated weekly KPI computation:** total revenue, order count, average order value, regional breakdown, top category
- **Week-over-week comparison:** automatically compares current period against the prior period, with visual ▲/▼ indicators in the report
- **Formatted Excel reports:** color-coded growth/decline, auto-sized columns, multi-sheet breakdown
- **Slack delivery:** posts a readable summary message plus the full Excel file directly into a channel
- **Fully scheduled:** runs automatically via Airflow — no manual execution needed
- **Secrets kept out of code:** local `.env` file + Airflow Variables, both gitignored/encrypted

## Sample Output

**Slack delivery:**

> 📊 Weekly KPI Report — 2018-12-24 to 2018-12-30
> • Total Revenue: $15,210.89 (📉 -21.82% WoW)
> • Total Orders: 46 (📉 -8.0% WoW)
> • Avg Order Value: $330.67 (📉 -15.03% WoW)
> • Top Category: Office Supplies
>
> *Full Excel report attached*

**Excel report:** includes a summary sheet with WoW comparisons and a separate regional revenue breakdown sheet.

## Project Structure

```
kpi-pipeline/
├── airflow/
│   ├── docker-compose.yaml      # Airflow services (webserver, scheduler, metadata DB)
│   └── dags/
│       └── kpi_pipeline_dag.py  # DAG definition
├── scripts/
│   ├── load_data.py             # Loads raw CSV data into Postgres
│   ├── compute_kpis.py          # KPI calculation logic
│   ├── generate_report.py       # Excel report generation
│   └── send_to_slack.py         # Slack delivery
├── data/
│   └── Sample-Superstore_csv.csv
├── reports/                     # Generated reports land here
├── .env.example                 # Template for required environment variables
└── README.md
```

## Setup

### Prerequisites
- Docker Desktop
- Python 3.11+

### 1. Database setup
```bash
docker run --name kpi-postgres -e POSTGRES_PASSWORD=<your_password> -e POSTGRES_DB=kpi_db -p 5433:5432 -d postgres
cd scripts
pip install -r requirements.txt
python load_data.py
```

### 2. Configure secrets
```bash
cp .env.example .env
# Fill in your actual DB password, Slack bot token, and channel ID
```

### 3. Run locally (without Airflow)
```bash
python compute_kpis.py      # console output only
python generate_report.py   # + generates Excel file
python send_to_slack.py     # + sends to Slack
```

### 4. Run via Airflow (scheduled automation)
```bash
cd airflow
docker-compose up airflow-init
docker-compose up -d
```
Then open `http://localhost:8080`, log in, and add the required Airflow Variables (see `.env.example` for the full list of keys needed — `kpi_db_host`, `kpi_db_password`, `slack_bot_token`, etc.)

## Key Engineering Decisions

- **LocalExecutor over CeleryExecutor:** appropriate for a single-machine deployment; avoids unnecessary Redis/Celery complexity for this scale.
- **`host.docker.internal` networking:** Airflow containers run on a separate Docker network from the Postgres container; this resolves the host machine's loopback to reach it cleanly without merging networks.
- **XCom for inter-task data:** avoids writing intermediate files to disk between tasks, keeping the pipeline stateless between runs.
- **Two-layer secrets management:** `.env` for local development, Airflow Variables for orchestrated runs — neither secret type ever touches version control.

## Possible Extensions
- Add data quality checks (null checks, schema validation) before KPI computation
- Add Slack alerting on pipeline failure
- Parameterize the reporting window (daily/weekly/monthly)
- Add a lightweight Streamlit dashboard for historical KPI trends