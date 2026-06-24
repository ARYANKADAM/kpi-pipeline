"""
send_to_slack.py
Uploads the generated KPI Excel report to a Slack channel,
with a short summary message including key metrics.
"""

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from compute_kpis import main as compute_kpis_main
from generate_report import generate_excel_report

# ---- CONFIG ----
import os
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "")


def build_summary_message(report):
    this_week = report["this_week_kpis"]
    wow = report["wow_change"]

    def fmt_pct(p):
        if p is None:
            return "N/A"
        symbol = "📈" if p >= 0 else "📉"
        return f"{symbol} {p}%"

    message = (
        f"*📊 Weekly KPI Report* — {report['window']['this_week'][0]} to {report['window']['this_week'][1]}\n\n"
        f"• *Total Revenue:* ${this_week['total_revenue']:,.2f} ({fmt_pct(wow['revenue_pct'])} WoW)\n"
        f"• *Total Orders:* {this_week['total_orders']} ({fmt_pct(wow['orders_pct'])} WoW)\n"
        f"• *Avg Order Value:* ${this_week['avg_order_value']:,.2f} ({fmt_pct(wow['avg_order_value_pct'])} WoW)\n"
        f"• *Top Category:* {this_week['top_category']}\n\n"
        f"Full breakdown attached below 👇"
    )
    return message


def send_to_slack(filepath, message):
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL:
        print("⚠️ Slack token/channel not set. Skipping Slack delivery.")
        return False

    client = WebClient(token=SLACK_BOT_TOKEN)
    try:
        # Post the summary message first
        client.chat_postMessage(channel=SLACK_CHANNEL, text=message)

        # Upload the Excel file
        client.files_upload_v2(
            channel=SLACK_CHANNEL,
            file=filepath,
            title="Weekly KPI Report",
        )
        print(f"✅ Report sent to Slack channel {SLACK_CHANNEL}")
        return True

    except SlackApiError as e:
        error_code = e.response.get("error", "unknown_error")
        print(f"❌ Slack API error: {error_code}")
        if error_code in {"invalid_auth", "not_authed"}:
            print("⚠️ Slack authentication failed. Continuing without failing the pipeline.")
            return False
        raise


def main():
    report = compute_kpis_main()
    filepath = generate_excel_report(report)
    message = build_summary_message(report)
    send_to_slack(filepath, message)


if __name__ == "__main__":
    main()
