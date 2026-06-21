"""
kpi_pipeline_dag.py
Orchestrates the weekly KPI pipeline:
  1. Compute KPIs from Postgres
  2. Generate Excel report
  3. Send report + summary to Slack

Runs every Monday at 8:00 AM.
"""

import sys
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# Make the mounted scripts folder importable
sys.path.insert(0, "/opt/airflow/kpi_scripts")

from airflow.models import Variable

# Pull config from Airflow Variables (set via Admin > Variables in the UI)
# This keeps the DAG file itself free of any secrets, safe to commit to git.
os.environ["KPI_DB_HOST"] = Variable.get("kpi_db_host", default_var="host.docker.internal")
os.environ["KPI_DB_PORT"] = Variable.get("kpi_db_port", default_var="5433")
os.environ["KPI_DB_USER"] = Variable.get("kpi_db_user", default_var="postgres")
os.environ["KPI_DB_PASSWORD"] = Variable.get("kpi_db_password", default_var="")
os.environ["KPI_DB_NAME"] = Variable.get("kpi_db_name", default_var="kpi_db")
os.environ["SLACK_BOT_TOKEN"] = Variable.get("slack_bot_token", default_var="")
os.environ["SLACK_CHANNEL"] = Variable.get("slack_channel", default_var="")


def task_compute_kpis(**context):
    from compute_kpis import main as compute_kpis_main
    report = compute_kpis_main()
    return report  # stored automatically in XCom


def task_generate_report(**context):
    from generate_report import generate_excel_report
    report = context["ti"].xcom_pull(task_ids="compute_kpis")
    filepath = generate_excel_report(report, output_dir="/opt/airflow/kpi_reports")
    return filepath


def task_send_to_slack(**context):
    from send_to_slack import build_summary_message, send_to_slack
    report = context["ti"].xcom_pull(task_ids="compute_kpis")
    filepath = context["ti"].xcom_pull(task_ids="generate_report")
    message = build_summary_message(report)
    send_to_slack(filepath, message)


default_args = {
    "owner": "aryan",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="weekly_kpi_pipeline",
    description="Pulls sales data, computes weekly KPIs, generates Excel report, sends to Slack",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="0 8 * * MON",   # every Monday at 8:00 AM
    catchup=False,
    tags=["kpi", "reporting", "slack"],
) as dag:

    compute_kpis = PythonOperator(
        task_id="compute_kpis",
        python_callable=task_compute_kpis,
    )

    generate_report = PythonOperator(
        task_id="generate_report",
        python_callable=task_generate_report,
    )

    send_to_slack_task = PythonOperator(
        task_id="send_to_slack",
        python_callable=task_send_to_slack,
    )

    compute_kpis >> generate_report >> send_to_slack_task
