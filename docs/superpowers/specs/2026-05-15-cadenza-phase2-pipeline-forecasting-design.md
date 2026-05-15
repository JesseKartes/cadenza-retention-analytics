# Cadenza Pipeline & Forecasting — Phase 2 Design

**Status:** Approved (design phase). Ready for implementation plan.
**Date:** 2026-05-15
**Owner:** Jesse Kartes
**Purpose:** Portfolio Phase 2 — extend Cadenza (a fictional B2B sales engagement SaaS) with pipeline and forecasting analytics, demonstrating SaaS RevOps fluency for SaaS Sales/Revenue Ops job applications.

---

## 1. Project pitch

A pipeline-and-forecasting analytics extension to the Cadenza Retention Analytics application. Adds opportunity-level data — new business, renewals, and expansions — plus quarterly forecast snapshots, and surfaces canonical RevOps metrics: pipeline coverage, weighted pipeline, win rate, sales cycle length, stage velocity, stage-to-stage conversion, forecast accuracy, and commit/best-case/pipeline buckets. The dataset deliberately encodes a second hidden insight: **Mid-Market deals stall in Proof of Concept ~2× longer than SMB or Enterprise, with markedly worse POC→Negotiation conversion**, suggesting the POC motion is built for SMB and Enterprise but leaves Mid-Market in a gap.

**One-sentence resume framing:**
> Extended Cadenza Retention Analytics (Python, Streamlit, pandas) with pipeline and forecasting analytics — opportunity lifecycle, weighted pipeline, win-rate, sales-cycle, stage-velocity, and forecast-accuracy-by-quarter — modeling ~3,200 opportunities across new-business, renewal, and expansion motions to surface a segment-level POC stall masked by healthy headline coverage.

## 2. Hiring narrative — why Phase 2 exists

Phase 1 (Retention Analytics, shipped 2026-05-15 at https://cadenza-retention-analytics.streamlit.app) proved the SaaS-retention vocabulary: ARR, NRR, GRR, logo churn, cohort retention. Phase 2 proves the **pipeline-to-forecast** vocabulary that most SaaS RevOps job descriptions list as a core responsibility: pipeline coverage, weighted pipeline, win rate, sales cycle, forecast accuracy, commit/best-case/pipeline buckets. Together they cover the two halves of the SaaS revenue motion (booking new revenue, retaining/expanding existing revenue).

The second hidden insight is deliberately segment-shaped, not channel-shaped (Phase 1's was channel-shaped). This shows analytical range — different cuts of data, different recommendations.

Phase 3 (Quota & Rep Performance) remains explicitly deferred.

## 3. Scope

**In scope (Phase 2):**
- Synthetic opportunity / stage-history / pipeline-snapshot data, extending Phase 1's generator.
- Three opportunity types modeled distinctly: **new_business**, **renewal**, **expansion**.
- Two new Streamlit pages: **Pipeline** and **Forecasting**.
- Pipeline metrics with documented formulas: total pipeline, weighted pipeline, pipeline coverage ratio, win rate, average sales cycle days, average days in stage, stage-to-stage conversion, aging deals.
- Forecasting metrics with documented formulas: forecast buckets (commit / best case / pipeline), forecast accuracy (snapshot vs. actual), forecast accuracy trend across 8 quarterly snapshots, forecast bias by segment.
- Stage Velocity Heatmap (segment × stage) as the hero visualization that surfaces the Mid-Market POC stall.
- Test suite verifying metric formulas against hand-built fixtures, plus an insight-protection test and a Phase 1 byte-identical invariant test.
- Updated About page and CHANGELOG / README.

**Out of scope (explicit):**
- Rep-level analytics, AE leaderboards, quota attainment (Phase 3). `owner_rep_id` is captured on opportunities but never surfaced on any Phase 2 page.
- Marketing funnel / MQL → SQL conversion (Cadenza's data starts at opportunity creation).
- Activity tracking (calls / emails / meetings per deal).
- Real-time pipeline updates, Salesforce / HubSpot sync.
- Deal-level commentary, next-step notes.
- ML-based deal scoring / win probability beyond the stage-based probability.
- Named-account drilldowns.
- Cohort-to-pipeline cross-linking (e.g., clicking a cohort to filter pipeline). Possible Phase 3 polish.

## 4. Tech stack and architecture

No new dependencies. Same stack as Phase 1: Python 3.12, pandas, Plotly, Streamlit, pytest. Deployment continues via Streamlit Community Cloud, auto-redeploying on `git push origin main`.

**Architecture (extends Phase 1 additively):**

```
src/data_generator.py (extended, Phase 1 logic untouched)
  ↓
data/generated/
  customers.csv               ← Phase 1, byte-identical
  subscriptions.csv           ← Phase 1, byte-identical
  events.csv                  ← Phase 1, byte-identical
  opportunities.csv           ← NEW
  opportunity_stage_history.csv  ← NEW
  pipeline_snapshots.csv      ← NEW
  ↓
src/metrics.py, src/cohorts.py (Phase 1, untouched)
src/pipeline.py               ← NEW (pure functions)
src/forecast.py               ← NEW (pure functions)
  ↓
src/viz.py (extended; Phase 1 builders untouched)
  ↓
Overview.py, pages/2_Cohort_Analysis.py, pages/3_Segment_Drilldown.py
  (Phase 1, untouched)
pages/5_Pipeline.py           ← NEW
pages/6_Forecasting.py        ← NEW
pages/7_About.py              ← renamed from 4_About.py, content extended
```

All Phase 2 modules in `src/` are **pure functions** (no IO, no Streamlit imports, no global state) — matching the Phase 1 convention. Each Streamlit page has its own `@st.cache_data load_data()`. No shared session state across pages.

## 5. Synthetic data model

### 5.1 Opportunity types and their semantics

| Type | Created when | Closes when | Amount (ACV) | Stage flow |
|---|---|---|---|---|
| `new_business` | ~6–14 weeks before a non-Self-Serve Phase 1 customer's `signup_date`; or for currently-open / closed-lost deals, generated independently | On signup_date (won), in stage (lost), or remains open | `initial_mrr × 12` | Discovery → Qualification → POC → Negotiation → Closed Won / Closed Lost |
| `renewal` | ~60 days before a customer's annual signup anniversary | Won (close_date = anniversary) if customer was active 30+ days after anniversary; Lost (close_date ≈ Phase 1 churn event date) if customer churned within ±30 days of anniversary | Customer's MRR at opp creation × 12 | Renewal Discussion → Negotiation → Closed Won / Closed Lost |
| `expansion` | 30–60 days before each Phase 1 `upgrade` event | On the upgrade event date, always Closed Won | `event.mrr_delta × 12` | Expansion Discussion → Closed Won |

**Why this design:**
- Self-Serve Promo customers don't get new_business opportunities because self-serve has no sales motion (this is a real-world semantic, not a shortcut).
- Renewal-lost opps are linked to specific Phase 1 churn events by date proximity, so the data is internally consistent — a customer doesn't churn in Phase 1 with no renewal-lost opp explaining why, and vice versa.
- Lost expansions are not modeled — they add noise without insight.

### 5.2 Stage definitions

| Opp type | Stage | Win probability (used for weighted pipeline) |
|---|---|---|
| new_business | Discovery | 0.10 |
| new_business | Qualification | 0.20 |
| new_business | Proof of Concept | 0.40 |
| new_business | Negotiation | 0.65 |
| new_business | Closed Won / Closed Lost | 1.0 / 0.0 |
| renewal | Renewal Discussion | 0.75 |
| renewal | Negotiation | 0.90 |
| renewal | Closed Won / Closed Lost | 1.0 / 0.0 |
| expansion | Expansion Discussion | 0.80 |
| expansion | Closed Won | 1.0 |

**Forecast category mapping** (industry-standard, applies primarily to new_business but used across all open opps):

| Stage | Forecast category |
|---|---|
| Negotiation (any opp type) | Commit |
| Proof of Concept, Renewal Discussion, Expansion Discussion | Best Case |
| Discovery, Qualification | Pipeline |

### 5.3 Tables

**`opportunities.csv`** — one row per deal:

| Column | Type | Notes |
|---|---|---|
| opportunity_id | string | `OPP-NNNN` |
| customer_id | string | FK to `customers.customer_id`. Populated for: all Closed-Won new_business opps; all renewal opps (won or lost); all expansion opps. NULL for open or Closed-Lost new_business opps that never became a Phase 1 customer. |
| account_name | string | Same as `customers.company_name` when `customer_id` is set; otherwise a generated fake company name. |
| segment | string | SMB / Mid-Market / Enterprise. Matches Phase 1 segment for FK'd opps. |
| acquisition_channel | string | Phase 1 channels minus Self-Serve Promo. |
| owner_rep_id | string | `REP-01`...`REP-12`. Captured but not surfaced in Phase 2 pages. |
| opportunity_type | string | `new_business` / `renewal` / `expansion` |
| created_date | date | When the opp was created. |
| close_date | date | Actual close date if closed; expected close date if open. |
| amount | float | ACV (annualized) — formula varies by opp_type, see §5.1. |
| current_stage | string | One of the stages from §5.2. |
| status | string | `open` / `closed_won` / `closed_lost` |

**`opportunity_stage_history.csv`** — one row per (opp × stage entered):

| Column | Type | Notes |
|---|---|---|
| opportunity_id | string | FK |
| stage | string | The stage entered |
| entered_date | date | When the deal entered this stage |
| exited_date | date | When it left, or NULL if it's currently in this stage |
| days_in_stage | int | `exited_date − entered_date` (or `today − entered_date` if NULL) |

**`pipeline_snapshots.csv`** — one row per (snapshot_date × open opp at that date):

| Column | Type | Notes |
|---|---|---|
| snapshot_date | date | First of each quarter, Q1 2024 → Q4 2025 (8 snapshots) |
| opportunity_id | string | FK |
| stage_at_snapshot | string | The stage the deal was in on snapshot_date, reconstructed from `opportunity_stage_history` |
| amount | float | ACV as of snapshot |
| forecast_category | string | Commit / Best Case / Pipeline (derived from stage_at_snapshot) |
| expected_close_date | date | The deal's expected close as of that snapshot |

### 5.4 Volume estimates

| Table | Rows (approx) |
|---|---|
| opportunities | ~3,200 (660 NB-won + 150 NB-open + 80 NB-lost + ~1,500 renewals + ~800 expansions) |
| opportunity_stage_history | ~8,000 |
| pipeline_snapshots | ~1,200 (~150 open deals × 8 quarters) |

Well within "fast to load" territory. All CSVs committed to the repo (Streamlit Cloud doesn't run the generator).

## 6. The engineered hidden insight

**Mid-Market POC stall.** Mid-Market deals dwell in Proof of Concept ~2× longer than SMB or Enterprise, and convert POC→Negotiation at roughly half the rate. Encoded in the generator as:

```python
STAGE_DWELL_DAYS = {
    "Discovery":         {"SMB": 7,  "Mid-Market": 10, "Enterprise": 14},
    "Qualification":     {"SMB": 10, "Mid-Market": 14, "Enterprise": 20},
    "Proof of Concept":  {"SMB": 15, "Mid-Market": 45, "Enterprise": 25},  # ← the gap
    "Negotiation":       {"SMB": 10, "Mid-Market": 18, "Enterprise": 25},
}

STAGE_ADVANCE_PROB = {
    "Discovery":        {"SMB": 0.85, "Mid-Market": 0.80, "Enterprise": 0.90},
    "Qualification":    {"SMB": 0.75, "Mid-Market": 0.70, "Enterprise": 0.85},
    "Proof of Concept": {"SMB": 0.70, "Mid-Market": 0.40, "Enterprise": 0.75},  # ← the gap
    "Negotiation":      {"SMB": 0.80, "Mid-Market": 0.75, "Enterprise": 0.85},
}
```

Dwell days sampled from a gamma distribution around these means (positive skew — real dwell times have a long tail).

**Narrative for the case study:** "The POC motion is built for SMB (fast, mostly self-guided) and Enterprise (custom, white-glove). Mid-Market falls in the middle — too complex for the SMB POC playbook, too small to justify the Enterprise one. Either invest in a Mid-Market-specific POC playbook, or change qualification criteria to filter out Mid-Market deals that aren't ready to evaluate."

## 7. Metrics

All metrics live in `src/pipeline.py` and `src/forecast.py` as pure functions. They take pandas DataFrames matching the schemas in §5.3 and return scalars or aggregated DataFrames. Formulas surface in docstrings and in the About page metric table (must stay in sync — same Phase 1 convention).

### 7.1 `src/pipeline.py`

| Function | Returns | Formula |
|---|---|---|
| `total_pipeline(opps, as_of_date)` | float | sum of `amount` for `status='open'` and `created_date ≤ as_of_date` |
| `weighted_pipeline(opps, as_of_date)` | float | sum of `amount × stage_probability` for open opps |
| `pipeline_coverage(opps, target, as_of_date)` | float | `total_pipeline / target` |
| `win_rate(opps, start, end)` | float | `closed_won / (closed_won + closed_lost)` for deals with `close_date` in window |
| `avg_sales_cycle_days(opps, start, end)` | float | mean `(close_date − created_date)` for `status='closed_won'` deals in window |
| `avg_days_in_stage(history, stage, start, end)` | float | mean `days_in_stage` over rows where `stage == stage` and `entered_date` in window |
| `stage_conversion(history, from_stage, to_stage, start, end)` | float | of deals entering `from_stage` in window, fraction that ever reached `to_stage` |
| `aging_deals(opps, history, as_of_date, threshold_days=60)` | DataFrame | open deals where `days_in_current_stage > threshold` |

Pure functional API: the caller pre-filters opps by opp_type / segment / channel before calling. Matches Phase 1's `_active()` pattern.

### 7.2 `src/forecast.py`

| Function | Returns | Formula |
|---|---|---|
| `forecast_buckets(snapshots, snapshot_date)` | dict | `{commit, best_case, pipeline}` summed from snapshot rows |
| `forecast_accuracy(snapshots, opps, snapshot_date)` | float | weighted pipeline at snapshot ÷ actual closed-won in [snapshot_date, snapshot_date + 3 months) |
| `forecast_accuracy_trend(snapshots, opps)` | DataFrame | row per snapshot_date with forecast, actual, accuracy |
| `forecast_bias_by_segment(snapshots, opps, snapshot_date)` | DataFrame | forecast vs. actual per segment for the snapshot's quarter |

## 8. Pages

### 8.1 `pages/5_Pipeline.py`

**Sidebar filters:** reporting "as-of" month (default = `2025-12-01`, last month of data), segment, channel, opportunity type.

**Layout (matches Phase 1's 4-tile + hero-viz + supporting-tables structure):**
- **KPI tile row (4 tiles):** Total Pipeline · Weighted Pipeline · Coverage Ratio (vs. editable target, default calibrated to ~1.2× expected close-won for the quarter — exact value set during implementation against generator output) · Win Rate (TTM)
- **Stage Funnel** — Plotly funnel chart of $ by stage (new_business only by default; renewal/expansion shown as a companion stat row "Pipeline mix: $X new · $Y renewal · $Z expansion")
- **Stage Velocity Heatmap (hero)** — rows = segments, columns = stages, cell value = avg days in stage. Cadenza palette: fast = green, slow = red. **This is where the Mid-Market POC stall is visible without further drilling.**
- **Stage Conversion Table** — styled `st.dataframe` of segment × stage transitions, using `highlight_min/max` (reuses page-3 styling pattern)
- **Aging Deals Table** — open deals with `days_in_current_stage > 60`, sortable

### 8.2 `pages/6_Forecasting.py`

**Sidebar filters:** snapshot quarter (default = `2025-10-01`, the most recent snapshot), segment.

**Layout:**
- **KPI tile row (4 tiles):** Commit · Best Case · Pipeline (total weighted at snapshot) · Forecast Accuracy (last completed quarter)
- **Forecast Buckets Chart** — horizontal stacked bar (Commit / Best Case / Pipeline) vs. the quarter target reference line
- **Forecast Accuracy Trend** — line chart across 8 quarterly snapshots, weighted forecast vs. actual closed-won that quarter, with a 100% reference line (reuses Phase 1's `trend_figure`)
- **Forecast Bias by Segment** — grouped bar showing per-segment forecast vs. actual

### 8.3 `pages/7_About.py` (renamed from `4_About.py`)

- Content rename only; file rename is for sidebar ordering. Existing Phase 1 metric definitions remain unchanged.
- Append a "Phase 2: Pipeline & Forecasting" narrative subsection.
- Extend the metric definitions table with all Phase 2 metrics from §7.1 and §7.2.

## 9. Generator mechanics

In `src/data_generator.py`, new functions appended (Phase 1 functions and their RNG seeding remain unchanged):

1. **Run Phase 1's existing generator** (`generate_customers`, `generate_subscriptions_and_events`) — unchanged. Output remains deterministic with `seed=42`.
2. **Generate closed-won new_business opportunities** by walking each non-Self-Serve Phase 1 customer backward from their `signup_date`: sample stage dwell times from segment-conditional gammas, walk through Discovery → Qualification → POC → Negotiation, set `created_date = signup_date − total_dwell`. Populate `customer_id` FK.
3. **Generate currently-open new_business opportunities** (~150): created on dates spread across 2024–2025, currently sitting in a stage based on probabilistic advancement. Expected close dates in Q1–Q2 2026.
4. **Generate closed-lost new_business opportunities** (~80): walked through stages, dropped out at some point.
5. **Generate renewal opportunities:** for each customer × each annual signup anniversary in the data window, create a renewal opp. Lookup the customer's churn event (if any); if `|anniversary − churn_date| ≤ 30 days`, the renewal opp is Closed-Lost with `close_date ≈ churn_date`; otherwise Closed-Won at `close_date = anniversary`.
6. **Generate expansion opportunities:** one per Phase 1 `upgrade` event. `close_date = upgrade.event_date` (Closed-Won), `created_date = close_date − sampled_lead_time` (30–60 days), `amount = upgrade.mrr_delta × 12`.
7. **Take quarterly snapshots:** on the 1st of each quarter Q1 2024 – Q4 2025, for each opportunity, look up its stage at that date from `opportunity_stage_history`. Record the row if the deal was open on that date.

**Determinism:** new RNG instance seeded `RNG_SEED + 2` (Phase 1 uses `seed` and `seed + 1`). Re-running the full generator is a no-op as long as code doesn't change.

## 10. Testing

**Hand-built fixtures** (extend `tests/conftest.py`):
- **`tiny_opportunities`** — ~8 hand-crafted deals spanning all 3 opp_types, all stages, all segments, both win/loss outcomes. Comments document hand-calculated expected values for total pipeline, weighted pipeline, win rate, sales cycle.
- **`tiny_stage_history`** — stage transitions for those deals with deliberate dwell times so `avg_days_in_stage('POC')` and `stage_conversion('POC' → 'Negotiation')` have hand-verifiable answers.
- **`tiny_snapshots`** — 2 snapshot dates × ~4 open deals each, hand-mapped to forecast categories so `forecast_buckets()` and `forecast_accuracy()` are testable against known answers.

**New test files:**
- **`tests/test_pipeline.py`** — one test per function in `src/pipeline.py`, asserting against `tiny_*` fixtures.
- **`tests/test_forecast.py`** — one test per function in `src/forecast.py`.

**Extensions to `tests/test_data_generator.py`** (two new tests):
1. **Insight protection:** assert `avg_days_in_stage('Proof of Concept', segment='Mid-Market') >= 2 × avg_days_in_stage('Proof of Concept', segment='SMB')`, with the threshold in the assertion message so a future weakening fails informatively.
2. **Phase 1 byte-identical invariant:** after running the full generator, assert `customers.csv`, `subscriptions.csv`, and `events.csv` are byte-identical to their committed Phase 1 versions. Guards against Phase 2 generator code accidentally perturbing Phase 1 RNG.

**Target:** 20 Phase 1 tests + ~15–20 Phase 2 tests, all green. Phase 1 tests stay untouched.

## 11. Phase 1 touchpoints — full inventory

Every Phase 2 change to a Phase 1 file is enumerated here. All are either additive or cosmetic. No Phase 1 logic, metric formula, data file, or shipped UX changes.

**Renames (1 file):**
- `pages/4_About.py` → `pages/7_About.py` — for sidebar ordering (About should be last, not in the middle between retention and pipeline pages).

**Append-only changes (Phase 1 contents preserved):**
- `src/data_generator.py` — new generator functions appended; Phase 1 functions and seeds untouched.
- `src/viz.py` — new figure builders (stage funnel, velocity heatmap, forecast trend, etc.) appended; Phase 1 builders untouched; Cadenza brand palette constants unchanged.
- `pages/7_About.py` (formerly `4_About.py`) — metric table extended with Phase 2 entries; Phase 2 narrative subsection added. Phase 1 content unchanged.
- `tests/conftest.py` — new fixtures appended; Phase 1 fixtures untouched.
- `tests/test_data_generator.py` — two new tests appended; existing tests unchanged.
- `README.md` — Phase 2 pages added to the list.
- `CLAUDE.md` — architecture diagram updated, Phase 2 status flipped.
- `CHANGELOG.md` — Phase 2 entry on ship.

**Untouched (firm — flag immediately if Phase 2 forces a change):**
- `data/generated/customers.csv`, `subscriptions.csv`, `events.csv` — byte-identical (enforced by the invariant test in §10).
- `src/metrics.py`, `src/cohorts.py` — zero changes.
- `Overview.py`, `pages/2_Cohort_Analysis.py`, `pages/3_Segment_Drilldown.py` — zero changes.
- All 20 existing Phase 1 tests — stay green, untouched.
- Cadenza brand palette constants in `src/viz.py` — unchanged.
- `.streamlit/config.toml`, `requirements.txt`, deployment configuration — unchanged (no new dependencies).

## 12. Conventions carried from Phase 1

- `from __future__ import annotations` at the top of every new Python module.
- Pure functions in `src/`: no IO, no global state, no Streamlit imports.
- Streamlit pages are presentation only — they call into `src/*` modules.
- Each Streamlit page has its own `@st.cache_data load_data()`.
- TDD with hand-built fixtures whose comments document hand-calculated expected values.
- Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `style:`, `polish:`, `ops:`).
- Metric formulas in both docstrings and the About page table — kept in sync.
- Cadenza brand palette only. No new colors.
- Percentages on charts use `yaxis_tickformat=".0%"`.
- Streamlit Cloud, Python 3.12 pinned in deploy UI (not via `runtime.txt`).
