# Changelog

All notable changes to this project will be documented here.

## v0.1.0-phase1 — 2026-05-15

Phase 1 of the Cadenza Retention Analytics portfolio: SaaS retention metrics + cohort analysis built on a deliberately-engineered synthetic dataset.

### Shipped

**Data**
- Synthetic data generator producing 786 customers, 12,055 subscription rows, and 1,460 lifecycle events over 36 months (Jan 2023 – Dec 2025).
- Three CSV outputs: `customers.csv`, `subscriptions.csv`, `events.csv`.
- Engineered insight: customers acquired via the **Self-Serve Promo** channel in Q3 2024 churn at roughly **2× the rate** of customers from other channels.

**Metrics** (`src/metrics.py`, pure pandas)
- ARR, NRR, GRR, Logo Churn, Gross Revenue Churn
- MRR Waterfall (starting + new + expansion − contraction − churn = ending)
- All formulas use a cohort-based definition with TTM as the default reporting window.

**Cohorts** (`src/cohorts.py`)
- Logo retention matrix (customer-count-weighted)
- Revenue retention matrix (MRR-weighted)
- Both correctly distinguish "cohort hasn't reached this age yet" (NaN, blank in heatmap) from "cohort reached this age with 0% retention" (red).

**Application** (`Overview.py` + `pages/*.py`)
- Page 1 — Overview: 4 KPI tiles with year-over-year deltas (inverse color on Logo Churn), MRR Waterfall, NRR/GRR trailing-12-month trend.
- Page 2 — Cohort Analysis: heatmap with Logo/Revenue toggle, channel and segment filters, M12 retention bar chart with the engineered Q3 2024 promo cohort highlighted.
- Page 3 — Segment & Channel Deep-Dive: NRR/GRR/Logo Churn split by segment and channel, dynamic red highlighting on the worst-performing row, account explorer table.
- Page 4 — About: methodology, metric formulas, links, and the "what I'd do at a real company" recommendation (CSM intervention playbook, channel-quality scoring, tighter promo gating).

**Tests**
- 20 pytest tests passing. Hand-built fixtures with hand-calculated expected values verify every metric formula. Data-generator sanity tests lock in the engineered insight so future changes can't accidentally erase it.

**Deployment**
- Live at https://cadenza-retention-analytics.streamlit.app
- Streamlit Cloud, public, Python 3.12 (pinned via deploy UI settings)

### Deferred to later phases

- **Phase 2** — Pipeline & Forecasting (pipeline velocity, stage conversion, forecast-vs-actual, weighted pipeline coverage)
- **Phase 3** — Quota Attainment & Rep Performance (rep scorecards, attainment distribution, ramp analysis, territory balance)
- Machine-learning at-risk scoring (explicitly out of scope for portfolio)
- Real Salesforce/HubSpot connectors
- Auth, multi-tenancy, write-back
