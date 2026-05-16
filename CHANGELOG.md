# Changelog

All notable changes to this project will be documented here.

## Phase 3 — Quota Attainment & Rep Performance (2026-05-16)

### Added
- `reps.csv` table (12 AEs with hire_date, segment_specialty, territory, quarterly_quota).
- `src/quota.py` — pure-function metrics: `quarterly_attainment`, `attainment_distribution`, `ramp_curve`, `ramp_bucket_attainment`, `rep_scorecard`, `territory_balance`, `team_kpis`, `load_quota_data`.
- `pages/7_Quota.py` — Quota Attainment & Rep Performance page (KPI tiles, attainment distribution, ramp curve, territory balance, rep scorecard).
- 5 new figure builders in `src/viz.py` — `attainment_distribution_figure`, `ramp_curve_figure`, `ramp_bucket_attainment_figure`, `territory_balance_figure`, plus `rep_scorecard_styler`.
- 25 new tests (13 in `tests/test_quota.py`, 12 generator guardrails in `tests/test_data_generator.py`); total suite 69 tests, all green.
- Engineered insight #3: team's actual ramp curve hits full productivity at ~9 months, not the industry-assumed 6.

### Changed
- `_generate_new_business_opps` — owner-assignment is now tenure-weighted in the closed-won and closed-lost loops (uniform random was Phase 2). Team-level new-business win rate is preserved exactly; only per-rep distribution shifts.
- `pages/7_About.py` renamed to `pages/8_About.py` for sidebar ordering.
- `pages/8_About.py` content extended with Phase 3 narrative, metric table rows, and Scope & Deferrals additions.
- `data/generated/opportunities.csv`, `opportunity_stage_history.csv`, `pipeline_snapshots.csv` regenerated (per-rep owner shifts).

### Preserved
- Phase 1 CSVs (`customers.csv`, `subscriptions.csv`, `events.csv`) — byte-identical (enforced by `test_phase1_csvs_unchanged_after_phase3`).
- Phase 2 Mid-Market POC stall ratio ≥ 2.0× (enforced by `test_midmarket_poc_stall_still_2x`).
- Phase 2 team TTM new-business win rate in 21-25% band (enforced by `test_team_win_rate_stays_in_band`).

### Calibrated (post-merge polish)
- Quota tiers lowered from \$150K/\$500K/\$1.5M to \$80K/\$150K/\$500K. Original tiers were aspirational; calibrated tiers match the dataset's per-rep deal volume so attainment lands in a realistic 30-150% range. Specialty assignment and routing logic unchanged.
- Specialty assignment moved from modal-backfit to cohort-aligned pre-assignment with segment-aware deal routing (5:1 specialty match weight). Veterans → Enterprise, mid-tenure → Mid-Market, new hires → SMB. Resolves the §1-vs-§2 dashboard narrative conflict where new reps could appear as top performers.
- Pre-hire reps excluded from owner selection pool (was a generator bug; pre-hire owner assignments were causing the ramp line chart to show 174% at month 0).
- Specialty routing tightened from 5:1 to 19:1 (~90% specialty concentration). At 5:1 (~70%), occasional Enterprise deals leaked to SMB reps, producing 1000%+ attainment outliers on the distribution chart. 19:1 caps spillover at ~5% per non-specialty rep while keeping enough variety that the chart doesn't look programmatically perfect.

---

## Phase 2 — Pipeline & Forecasting

**Date:** 2026-05-15

- Generator extended with opportunities, opportunity_stage_history, pipeline_snapshots tables (~3,451 opportunities, ~8,570 stage history rows, ~1,591 snapshots across 8 quarters)
- New-business closed-lost population sized so TTM Win Rate lands around 23% — matching the SaaS-industry benchmark of 25-35% (previously, won deals were seeded 1:1 with Phase 1 customers, inflating Win Rate to ~83% with only 80 lost deals as a counterweight)
- Three opportunity types modeled distinctly: new_business, renewal, expansion — linked to Phase 1 customers via customer_id FK
- Self-Serve Promo customers have no opportunity (self-serve is no-touch)
- Two new Streamlit pages:
  - **Pipeline** — new-business pipeline only (KPIs, pipeline-by-stage bar, stage velocity heatmap, conversion table, aging deals)
  - **Forecasting** — aggregates all three motions (commit/best-case/pipeline buckets, accuracy trend, per-segment bias)
- New pure-function modules: `src/pipeline.py`, `src/forecast.py`
- New figure builders in `src/viz.py`: `pipeline_by_stage_figure`, `stage_velocity_heatmap`, `forecast_buckets_figure`, `forecast_bias_bar`
- Engineered insight: **Mid-Market POC stall** — Mid-Market deals dwell in Proof of Concept ~2.9× longer than SMB, with POC→Negotiation conversion at ~half the rate. Surfaces in the Stage Velocity Heatmap.
- Phase 1 invariants enforced via test: customers.csv / subscriptions.csv / events.csv remain byte-identical after Phase 2 generator runs
- Insight-protection test: Mid-Market POC dwell must remain ≥ 2× SMB; fails informatively if future tuning weakens the engineered pattern
- `pages/4_About.py` renamed to `pages/7_About.py` for sidebar ordering (About now appears last, after Pipeline and Forecasting)
- About page extended with Phase 2 metric definitions, narrative, and a Scope & deferrals section
- ~24 new pytest tests (15 metric tests + 7 forecast tests + 2 guardrail tests); total suite 44 tests, all green
- No new dependencies; Python 3.12 unchanged

### Scope and deferrals

The Pipeline page is intentionally scoped to **net-new acquisition only** — the funnel, stage velocity, and conversion analyses assume the new-business five-stage cycle. Renewal and expansion data exist in the model and feed the Forecasting page's commit/best-case/pipeline buckets (a real forecast call blends all three motions), but **dedicated renewal-management and expansion-pipeline analytics — at-risk renewals, gross renewal rate trend, expansion attainment, cross-sell mix — are deferred to a future phase (Phase 2.5+)**. In a real RevOps stack those workflows typically live in a separate tool surface (e.g., Gainsight for renewals) owned by CSM/AM teams; they deserve their own page rather than being grafted onto a new-business funnel.

---

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
