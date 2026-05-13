# Cadenza Retention Analytics — Phase 1 Design

**Status:** Approved (design phase). Ready for implementation plan.
**Date:** 2026-05-13
**Owner:** Jesse Kartes
**Purpose:** Portfolio project demonstrating SaaS RevOps fluency for SaaS Sales/Revenue Ops job applications.

---

## 1. Project pitch

A SaaS retention analytics application (Python / Streamlit) that ingests synthetic subscription data for a fictional sales engagement company ("Cadenza") and surfaces the canonical SaaS retention metrics — ARR, NRR, GRR, Logo Churn, Gross Revenue Churn, and cohort retention. The application deliberately encodes a hidden churn pattern in a specific acquisition-channel cohort; the dashboard's job is to surface that insight and recommend an intervention.

**One-sentence resume framing:**
> Built Cadenza Retention Analytics, a SaaS retention analytics application (Python, Streamlit, pandas) modeling 600 customers over 36 months — calculating ARR, NRR, GRR, logo churn, and cohort retention — to surface a hidden acquisition-channel churn pattern masked by healthy headline metrics, with a recommended CSM intervention plan.

## 2. Hiring narrative — why this project exists

Jesse is transitioning from industrial/manufacturing (railcar leasing at Trinity Industries) to SaaS RevOps/Sales Ops. The existing resume demonstrates strong analytics skills (Tableau, SQL, Salesforce, $250M forecasting, $5M MRR renewals reporting) but a SaaS hiring manager has to mentally translate "railcar lease renewal" into "subscription retention." This project closes that translation gap by speaking SaaS vocabulary fluently and demonstrating actionable-insight thinking.

Phase 1 (this project) covers Renewals & Retention. Phases 2 (Pipeline & Forecasting) and 3 (Quota & Rep Performance) are explicitly deferred to their own design cycles.

## 3. Scope

**In scope (Phase 1):**
- Synthetic data generator producing a realistic Cadenza customer/subscription/event dataset.
- Streamlit web application with 4 pages (Overview, Cohort Analysis, Segment & Channel Deep-Dive, About / Methodology).
- The five core retention metrics with documented formulas: ARR, NRR, GRR, Logo Churn, Gross Revenue Churn.
- Cohort retention heatmap as the hero visualization.
- MRR Waterfall chart (New + Expansion − Contraction − Churn).
- A test suite that proves metric formulas against hand-built fixtures.
- A case-study README and Streamlit Cloud deployment.

**Out of scope (explicitly):**
- Pipeline / forecasting analytics (Phase 2).
- Quota attainment / rep performance (Phase 3).
- Marketing funnel analytics.
- Machine-learning-based at-risk scoring. (User chose "Core 5 + cohort," not "+ at-risk model.")
- Real Salesforce/HubSpot integration.
- Authentication, multi-tenancy, write-back, or any production-app concerns.

## 4. Tech stack and architecture

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.11+ | Familiar to user; single language across data gen, transforms, app. |
| App framework | Streamlit | Free public hosting via Streamlit Community Cloud; right tool for analytics portfolio; interactive without frontend overhead. |
| Data manipulation | pandas | Industry standard, transparent for readers. |
| Visualization | Plotly | Interactive charts; good cohort heatmap support; renders inside Streamlit cleanly. |
| Testing | pytest | Standard. Used to verify metric math against fixtures. |
| Storage | Flat CSV files | Three tables; simple; readable by anyone with SQL or Excel; no DB to set up. |
| Deployment | Streamlit Community Cloud | Free; one-click from GitHub; public URL shareable on resume. |
| Source control | GitHub (public repo) | Pinned on Jesse's profile for hiring visibility. |

**Architecture:**

```
data_generator.py  →  data/generated/*.csv  →  metrics.py + cohorts.py  →  streamlit_app.py + pages/*.py
```

A pure data pipeline: generator produces CSVs once, metric/cohort modules compute aggregates, Streamlit reads CSVs and renders. No database, no caching infrastructure beyond Streamlit's built-in `@st.cache_data`.

## 5. Synthetic data model

**Company persona:** Cadenza is a B2B sales engagement platform (Outreach/Salesloft tier), seat-based pricing, sold to RevOps and Sales leaders.

**Three tables:**

| Table | Grain | Key fields |
|---|---|---|
| `customers` | One row per customer | customer_id, company_name, segment (SMB / Mid-Market / Enterprise), industry, signup_date, signup_cohort (YYYY-MM), acquisition_channel, plan_tier_initial |
| `subscriptions` | One row per customer per month they're active | customer_id, month, mrr, seats, plan_tier, status (new / active / expansion / contraction / churned) |
| `events` | One row per lifecycle event | customer_id, event_date, event_type (signup / upgrade / downgrade / churn / renewal), mrr_delta, reason |

**Dimensions:**
- **Time horizon:** 36 months, Jan 2023 → Dec 2025.
- **Customer count:** ~600 customers active across the period (varies by month due to new acquisitions and churn).
- **Segment mix:** ~70% SMB, ~25% Mid-Market, ~5% Enterprise.
- **Plan tiers:** Starter ($50/seat), Growth ($120/seat), Scale ($250/seat).
- **Acquisition channels:** Outbound Sales, Inbound Marketing, Partner Referral, Self-Serve Promo, Event/Conference.

**MRR mechanics encoded by generator:**
- New: customer's first month, signup_MRR = seats × plan price.
- Expansion: seat increases and plan upgrades over time.
- Contraction: seat decreases and downgrades.
- Churn: full cancellation, MRR drops to zero.
- Realistic seasonality (slight Q4 expansion bias, Q1 churn bias).

## 6. The engineered insight (the punchline)

The generator deliberately encodes one hidden pattern:

> Customers acquired through the **Self-Serve Promo** channel during **Q3 2024** (the result of a discount-driven acquisition push) churn at roughly **2× the rate** of customers from other channels. This cohort is large enough that it visibly drags retention but small enough that company-wide headline metrics still look healthy.

**Target company-wide headline numbers** (the dashboard's "front page"):
- NRR (TTM): ~108% (looks healthy)
- GRR (TTM): ~91% (looks healthy)
- Logo Churn: ~1.2%/month (looks normal)

**Target self-serve-promo cohort numbers** (revealed by drilling in):
- GRR: ~71% (clearly bad)
- M12 logo retention: ~55% (vs. ~80% for other channels)

The dashboard's Page 2 cohort heatmap and Page 3 channel breakdown are designed to make this gap visible. The Page 4 About section explicitly narrates the discovery and recommends a CSM intervention plan as the "what I'd do at a real company" close.

## 7. Metric definitions

All formulas are documented in code, in `metrics.py`, and surfaced in dashboard tooltips. Headline values shown trailing-twelve-month (TTM); trend charts show monthly.

| Metric | Formula | Notes |
|---|---|---|
| ARR | MRR × 12 | Point-in-time; run-rate, not booked. |
| Logo Churn | customers_churned_in_period ÷ customers_active_at_start_of_period | Counts customers, not revenue. |
| Gross Revenue Churn | (churn_MRR + contraction_MRR) ÷ MRR_at_start_of_period | Excludes expansion. |
| GRR | 1 − Gross Revenue Churn, capped at 100% | "Floor" retention; can't exceed 100%. |
| NRR | (starting_MRR − churn_MRR − contraction_MRR + expansion_MRR) ÷ starting_MRR | Includes expansion; can exceed 100%. |

**Cohort retention:**
- Rows: signup-month cohort.
- Columns: months since signup (M0, M3, M6, M9, M12, M15, ...).
- Cell value: % of original cohort MRR retained at that month-of-life. Toggle to view logo retention instead.
- Color scale: green ≥ 100%, yellow ~90%, red < 80%.

## 8. Dashboard structure

Four-page Streamlit app. Global sidebar filters (date range, segment, acquisition channel) apply across pages.

**Page 1 — Overview**
- 5 KPI tiles: ARR, NRR (TTM), GRR (TTM), Logo Churn (TTM), Gross Revenue Churn (TTM). Each shows current value, prior-period delta, and a 12-month sparkline.
- MRR Waterfall chart: Starting MRR → + New + Expansion − Contraction − Churn = Ending MRR for the selected period.
- NRR and GRR monthly trend lines with horizontal reference at 100%.

**Page 2 — Cohort Analysis (the hero)**
- Cohort retention heatmap with toggle (logo retention vs. revenue retention).
- Acquisition-channel filter — flipping to "Self-Serve Promo" makes the underperforming cohort visually pop.
- Secondary chart: each cohort's M12 retention, sorted, with the underperforming cohort highlighted.

**Page 3 — Segment & Channel Deep-Dive**
- NRR / GRR / Logo Churn split by segment (SMB / MM / ENT) side-by-side.
- NRR / GRR / Logo Churn split by acquisition channel — this is where the insight is quantified.
- Account table below: filterable list of customers showing signup_date, cohort, segment, channel, current MRR, lifecycle status.

**Page 4 — About / Methodology**
- The story in plain English: "This is a portfolio project. The data is synthetic and deliberately encodes [insight]. Here's how I'd act on it if this were a real RevOps role."
- Metric definitions with exact formulas.
- Link to GitHub, the data generator file, and Jesse's LinkedIn.
- "What I'd do next at a real company" close: proposes a CSM playbook for self-serve promo cohorts and a channel-quality scoring partnership with marketing.

## 9. Repo structure

```
cadenza-retention-analytics/
├── README.md                  # Case-study format (story-first, not docs-first)
├── requirements.txt
├── streamlit_app.py           # Entry point + Overview page
├── pages/
│   ├── 2_Cohort_Analysis.py
│   ├── 3_Segment_Drilldown.py
│   └── 4_About.py
├── src/
│   ├── __init__.py
│   ├── data_generator.py      # Synthetic data generator
│   ├── metrics.py             # ARR, NRR, GRR, churn formulas
│   ├── cohorts.py             # Cohort triangle logic
│   └── viz.py                 # Reusable Plotly chart helpers
├── data/
│   └── generated/             # customers.csv, subscriptions.csv, events.csv
├── tests/
│   ├── __init__.py
│   ├── test_metrics.py        # Hand-built fixtures proving NRR/GRR math
│   └── test_cohorts.py
└── .streamlit/
    └── config.toml            # Cadenza brand theme
```

## 10. Deliverables

1. **Public Streamlit URL** — one shareable link opening to the Overview page.
2. **Public GitHub repo** — pinned on Jesse's profile.
3. **Case-study README** — story-first (problem → method → findings → recommendation), not docs-first.
4. **Refined resume bullet** (drafted in section 1).
5. **LinkedIn announcement post draft** — produced at ship time.

## 11. Build effort estimate

~6–10 hours of Claude implementation work, broken roughly as:
- Data generator: ~2–3 hours
- Metrics + cohort modules + tests: ~2 hours
- Streamlit app (4 pages): ~2–3 hours
- README, polish, Cadenza theming: ~1–2 hours

User effort: create GitHub repo, deploy to Streamlit Cloud (~10 min one-time), review README voice.

## 12. Decisions deferred to later phases

- Pipeline velocity, stage conversion, forecast-vs-actual (Phase 2).
- Quota attainment, rep scorecards, ramp analysis (Phase 3).
- A Tableau Public companion of the headline view (optional bonus after Phase 1 ships; ~1–2 hours of user time).

## 13. Open items before implementation plan

- Confirm whether the local working directory `/Users/jesse/Documents/Projects/revops_portfolio_claude` should be initialized as the `cadenza-retention-analytics` repo, or whether to scaffold elsewhere.
- Confirm Jesse will create the GitHub repo before deploy step, or wants Claude to scaffold locally first and push later.
