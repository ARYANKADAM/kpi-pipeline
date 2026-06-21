# Project Explanation: Automated KPI Reporting Pipeline

## 1. The Problem This Solves

In almost every company that sells anything — retail, SaaS, e-commerce, finance — someone on the analytics or operations team is responsible for producing a **weekly business performance report**. In practice, this usually looks like:

1. Open a BI tool or write a SQL query manually
2. Pull last week's numbers
3. Compare them to the prior week by hand or with a spreadsheet formula
4. Copy results into a slide deck, email, or spreadsheet
5. Send it to stakeholders (manager, leadership, a Slack channel)

This is repetitive, time-consuming, and entirely mechanical — yet it's done manually at a huge number of companies, every single week, by actual human analysts. Industry surveys consistently find analysts spend a significant portion of their week on repetitive reporting tasks rather than actual analysis. This project automates that exact workflow end-to-end.

## 2. What the Project Actually Does

Given a sales database, the pipeline:

1. **Pulls** the most recent week of transactional data
2. **Computes** core business KPIs: total revenue, order count, average order value, revenue by region, and top-performing product category
3. **Compares** this week's numbers to the prior week automatically, producing week-over-week (WoW) percentage changes — the single most common comparison stakeholders ask for in any business review
4. **Formats** these results into a polished Excel report with color-coded growth/decline indicators
5. **Delivers** the report directly into a Slack channel, with a readable text summary attached
6. **Repeats this automatically every week**, without a human ever running a script or opening a tool

## 3. Why This Is a Realistic, Not a Toy, Project

A lot of portfolio projects stop at "I wrote a script that does X." This project intentionally goes further, in ways that mirror what actually happens in a real company's data infrastructure:

- **It's scheduled, not run by hand.** A script someone has to remember to run isn't automation — it's a chore with extra steps. This pipeline runs on a real cron schedule via two different mechanisms (Airflow locally, GitHub Actions in the cloud), matching how actual production data pipelines are operated.
- **It survives the developer being unavailable.** The cloud version (GitHub Actions + Neon) runs whether or not any laptop is on. This is the actual bar production systems have to meet — "works on my machine" is explicitly not good enough for anything a business depends on.
- **Secrets are never hardcoded.** Database passwords and API tokens live in environment variables, Airflow's encrypted variable store, or GitHub's encrypted secrets — never in source code. This isn't an academic nicety; hardcoded credentials in committed code are one of the most common real-world security incidents in small companies and early-stage startups.
- **It's debuggable.** Both Airflow and GitHub Actions provide structured logs per task/run, meaning when something breaks (and several things did break during development — see below), there's a clear, traceable path to the root cause, exactly like a real production incident.

## 4. Real Problems Encountered and Solved

This section exists because *how* problems were solved is often more informative to an interviewer than the final clean result. During development, the following genuine issues came up and were fixed:

- **Docker networking across two separate container networks.** The Airflow containers and the Postgres data container were created independently and lived on different Docker networks, so `localhost` couldn't be used to connect them. Resolved using `host.docker.internal` to bridge from inside the Airflow container back to the host machine's exposed port.
- **Port conflicts.** A pre-existing project already used Postgres's default port 5432, requiring this project's database to run on a separate port (5433) — a common real-world situation when multiple services run on a shared development machine.
- **Secrets exposure caught by GitHub's push protection.** An early commit accidentally included a hardcoded Slack token. GitHub's automated secret scanning blocked the push before any leak occurred. The fix required removing the secret from the file *and* the git history (not just the latest commit), and rotating the exposed credential — a realistic security remediation exercise, not just a "delete the line" fix.
- **Authentication and connection-string debugging across environments.** Moving from local Docker Postgres to a cloud-hosted Neon database surfaced real differences in connection requirements (SSL enforcement, hostname resolution, credential mismatches between `.env` and CI secrets) that had to be debugged one error at a time by reading actual stack traces.

## 5. Why This Matters for Hiring Managers / Interviewers

This project gives concrete, defensible talking points across multiple skill areas that are hard to fake convincingly:

- **Data engineering fundamentals:** designing a schema, writing ETL-style loading logic, structuring KPI aggregation queries
- **Orchestration:** understanding DAGs, task dependencies, and inter-task data passing (XCom) — concepts directly transferable to tools like Airflow, Prefect, or Dagster used in real data teams
- **DevOps/CI-CD literacy:** configuring GitHub Actions, managing secrets, debugging environment-specific failures — skills increasingly expected even of analysts and junior engineers, not just dedicated DevOps hires
- **Cloud service integration:** working with a managed serverless database (Neon) instead of assuming infrastructure is already provided
- **Security awareness:** recognizing and correctly remediating a credential leak rather than just hiding it

## 6. How This Maps to Real Job Functions

| Project Component | Real-World Equivalent Role Task |
|---|---|
| KPI computation logic | Analyst building a recurring business report |
| Airflow DAG | Data Engineer maintaining scheduled ETL/reporting jobs |
| GitHub Actions automation | DevOps/Platform engineer setting up CI/CD-style scheduled jobs |
| Slack delivery integration | Analytics Engineer building stakeholder-facing reporting tools |
| Secrets management across environments | Any engineering role responsible for production credential hygiene |

## 7. Honest Limitations (worth being upfront about in an interview)

- The dataset is a static historical sample (Superstore dataset), not a live transactional system — in a real company this would connect to an actual production database or data warehouse.
- There's no automated testing (unit tests for the KPI logic, integration tests for the pipeline) — a natural and valuable next step.
- Error handling sends failures to logs but doesn't yet alert anyone on failure (e.g., a Slack message saying "this week's report failed to generate") — listed as a possible extension for exactly this reason.

Being able to articulate these limitations clearly, rather than overselling the project, is itself a signal of engineering maturity worth demonstrating in an interview.