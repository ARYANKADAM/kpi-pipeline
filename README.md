# Automated KPI Reporting Pipeline

An end-to-end data pipeline that pulls sales data from PostgreSQL, computes weekly KPIs with week-over-week comparisons, generates a formatted Excel report, and automatically delivers it to Slack.

The pipeline runs in **two modes**:
- **Local orchestration** via Apache Airflow (Docker Compose) — demonstrates DAG-based orchestration, task dependencies, and XCom data passing.
- **Cloud automation** via GitHub Actions + Neon (serverless Postgres) — runs the same pipeline on a real schedule, fully independent of any local machine being on.

## Live Proof of Automation

This pipeline runs automatically **every Monday at 8:00 AM UTC** via GitHub Actions — no local infrastructure required.

🔗 **[View live run history →](https://github.com/ARYANKADAM/kpi-pipeline/actions)**

Every run there is real: triggered by GitHub's own scheduler, not manually, with full logs and timestamps as proof.

## Why this project

Manual weekly reporting is a common time-sink for analysts. This project automates the full workflow: **data → analysis → report → delivery**, with zero manual intervention once scheduled — and proves it by actually running unattended in production, not just locally on a demo machine.

## Architecture

### Local / Development (Airflow)
```
PostgreSQL (Docker)
        │
        ▼
Apache Airflow DAG (scheduled: every Monday, 8:00 AM)
        │
        ├── Task 1: compute_kpis      → queries DB, calculates KPIs + WoW change
        ├── Task 2: generate_report   → builds formatted Excel report
        └── Task 3: send_to_slack     → posts summary + file to Slack channel
```
Data flows between tasks via Airflow XCom (no intermediate files needed).

### Production / Always-On (GitHub Actions + Neon)
```
GitHub Actions (cron: "0 8 * * 1")
        │
        ▼
Neon (serverless Postgres, cloud-hosted)
        │
        ▼
Python script chain: compute_kpis → generate_report → send_to_slack
        │
        ▼
Slack channel (report delivered)
```
Runs on GitHub's infrastructure — works even if every local machine involved is powered off.

## Tech Stack

- **Database:** PostgreSQL — Dockerized locally, Neon (serverless) in production
- **Orchestration:** Apache Airflow 2.9 (local, Docker Compose, LocalExecutor) + GitHub Actions (cloud scheduler)
- **Data processing:** Python, Pandas, SQLAlchemy
- **Report generation:** openpyxl
- **Delivery:** Slack SDK (slack_sdk)
- **Secrets management:** python-dotenv (local), Airflow Variables (local orchestrated runs), GitHub Encrypted Secrets (cloud runs)

## Features

- **Automated weekly KPI computation:** total revenue, order count, average order value, regional breakdown, top category
- **Week-over-week comparison:** automatically compares current period against the prior period, with visual ▲/▼ indicators in the report
- **Formatted Excel reports:** color-coded growth/decline, auto-sized columns, multi-sheet breakdown
- **Slack delivery:** posts a readable summary message plus the full Excel file directly into a channel
- **Dual scheduling setup:** local Airflow DAG for orchestration demonstration, GitHub Actions for genuine always-on automation
- **Secrets kept out of code everywhere:** `.env` (gitignored) locally, Airflow Variables for local orchestrated runs, GitHub encrypted Secrets for cloud runs — no credential type ever touches version control

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
├── .github/
│   └── workflows/
│       └── weekly-kpi-pipeline.yml   # GitHub Actions cloud schedule
├── airflow/
│   ├── docker-compose.yaml           # Airflow services (webserver, scheduler, metadata DB)
│   └── dags/
│       └── kpi_pipeline_dag.py       # DAG definition (local orchestration)
├── scripts/
│   ├── load_data.py                  # Loads raw CSV data into Postgres
│   ├── compute_kpis.py               # KPI calculation logic
│   ├── generate_report.py            # Excel report generation
│   ├── send_to_slack.py              # Slack delivery
│   └── requirements.txt
├── data/
│   └── Sample-Superstore_csv.csv
├── reports/                          # Generated reports land here (local runs)
├── .env.example                      # Template for required environment variables
├── .gitignore
└── README.md
```

## Setup

### Prerequisites
- Docker Desktop (for local Airflow mode)
- Python 3.11+
- A free [Neon](https://neon.tech) Postgres database (for cloud mode)
- A Slack workspace + bot token

### 1. Clone and configure secrets
```bash
git clone https://github.com/ARYANKADAM/kpi-pipeline.git
cd kpi-pipeline
cp .env.example .env
# Fill in your actual DB credentials, Slack bot token, and channel ID
```

### 2. Load data into your database
```bash
cd scripts
pip install -r requirements.txt
python load_data.py
```

### 3. Run locally (without orchestration)
```bash
python compute_kpis.py      # console output only
python generate_report.py   # + generates Excel file
python send_to_slack.py     # + sends to Slack
```

### 4. Run via local Airflow (orchestration demo)
```bash
cd airflow
docker-compose up airflow-init
docker-compose up -d
```
Open `http://localhost:8080`, log in, add the required Airflow Variables (`kpi_db_host`, `kpi_db_password`, `slack_bot_token`, etc.)

### 5. Enable cloud automation (GitHub Actions)
1. Push this repo to your own GitHub account
2. Go to **Settings → Secrets and variables → Actions**
3. Add these repository secrets: `KPI_DB_HOST`, `KPI_DB_USER`, `KPI_DB_PASSWORD`, `KPI_DB_PORT`, `KPI_DB_NAME`, `SLACK_BOT_TOKEN`, `SLACK_CHANNEL`
4. Go to **Actions** tab → "Weekly KPI Pipeline" → "Run workflow" to test manually
5. From then on, it runs automatically every Monday at 8:00 AM UTC — no further action needed

## Key Engineering Decisions

- **LocalExecutor over CeleryExecutor:** appropriate for a single-machine deployment; avoids unnecessary Redis/Celery complexity for this scale.
- **`host.docker.internal` networking (local Airflow):** Airflow containers run on a separate Docker network from the Postgres container; this resolves the host machine's loopback to reach it cleanly without merging networks.
- **XCom for inter-task data (local Airflow):** avoids writing intermediate files to disk between tasks, keeping the pipeline stateless between runs.
- **GitHub Actions + Neon for true 24/7 automation:** rather than paying for or maintaining an always-on VM, this pipeline uses two genuinely free, zero-maintenance services to achieve the same outcome — a real-world cost/complexity tradeoff a working analyst or engineer regularly has to make.
- **Layered secrets management:** `.env` for local dev, Airflow Variables for local orchestrated runs, GitHub encrypted Secrets for cloud runs — no credential type ever touches version control, and each environment uses the storage mechanism appropriate to it.

## Possible Extensions
- Add data quality checks (null checks, schema validation) before KPI computation
- Add Slack alerting on pipeline failure
- Parameterize the reporting window (daily/weekly/monthly)
- Add a lightweight Streamlit dashboard for historical KPI trends

## Further Reading
See [`EXPLANATION.md`](./EXPLANATION.md) for a deeper walkthrough of the project's purpose, design reasoning, and real-world relevance.
