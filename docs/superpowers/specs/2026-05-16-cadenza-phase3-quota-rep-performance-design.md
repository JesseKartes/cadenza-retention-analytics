# Cadenza Quota Attainment & Rep Performance — Phase 3 Design

**Status:** Approved (design phase). Ready for implementation plan.
**Date:** 2026-05-16
**Owner:** Jesse Kartes
**Purpose:** Portfolio Phase 3 — extend Cadenza (a fictional B2B sales engagement SaaS) with rep-level performance analytics, demonstrating SaaS RevOps fluency for SaaS Sales/Revenue Ops job applications.

---

## 1. Project pitch

A rep-performance analytics extension to the Cadenza application. Adds a `reps` table (12 quota-carrying AEs with hire dates, segment specialties, territories, and tiered quotas) and surfaces the canonical RevOps rep metrics: quarterly quota attainment, attainment distribution, win rate per rep, average deal size, average sales cycle, territory balance, and a longitudinal ramp curve. The dataset deliberately encodes a third hidden insight: **the team's actual ramp curve hits full productivity at ~9 months, not the industry-assumed 6**, meaning recent hires are being mistakenly tagged as underperformers when the underlying issue is a ramp-expectation miscalibration.

**One-sentence resume framing:**
> Extended Cadenza with rep-performance analytics (Python, Streamlit, pandas) — quarterly quota attainment, attainment distribution, win-rate and cycle-time per rep, ramp-curve-by-tenure, and territory balance — modeling 12 AEs with staggered hire dates and tiered segment-aligned quotas to surface a 3-month ramp gap masked by aggregate team attainment.

## 2. Hiring narrative — why Phase 3 exists

Phase 1 (Retention) proved the SaaS-retention vocabulary; Phase 2 (Pipeline & Forecasting) proved the deal-motion vocabulary. Phase 3 proves the **people-management** vocabulary that every SaaS RevOps job description lists alongside the other two: quota attainment, ramp, territory balance, rep scorecards, concentration risk.

The three hidden insights span three different cuts of the data — channel (Phase 1: Self-Serve Promo churn), stage (Phase 2: Mid-Market POC stall), and **tenure** (Phase 3: ramp longer than assumed). That spread shows analytical range across the dimensions a RevOps analyst is expected to interrogate.

## 3. Scope

**In scope (Phase 3):**
- Synthetic `reps.csv` (12 quota-carrying AEs) with hire date, segment specialty, territory, and tiered quarterly quota.
- One new Streamlit page: **Quota** (single page, four sections + rep scorecard table).
- Quota metrics with documented formulas: quarterly attainment per rep, attainment distribution, team-level attainment summary, win rate per rep, average deal size per rep, average sales cycle per rep.
- Ramp metrics: longitudinal ramp curve (rolling-3mo attainment % by tenure month), tenure-bucket median attainment.
- Territory balance metric: closed-won $ by territory × segment for the selected quarter.
- Generator extension: new `generate_reps()` and a tenure-aware win-rate adjustment in `_generate_new_business_opps` to inject the ramp pattern, with a compensating boost on tenured reps so the team-level win rate stays in band (21-25%).
- Test suite for all new metric functions, plus insight-protection and calibration-protection guardrails.
- Updated About page and CHANGELOG / README.

**Out of scope (explicit):**
- Renewal and expansion quota credit. Quota is new-business only — matches how most SaaS orgs separate AE comp from CSM/AM comp. Stated explicitly on the About page.
- Per-period (ramped) quota schedules. Quota is flat per rep; the ramp curve is a chart-level pattern, not a quota-model feature.
- Rep activity tracking (calls, emails, meetings).
- Compensation modeling, OTE, commission rates.
- Manager/team hierarchies. The 12 reps are a flat team.
- Real-time quota progression, live CRM sync.
- ML-based attainment forecasting or quota-setting recommendations.

## 4. Tech stack and architecture

No new dependencies. Same stack as Phase 1/2: Python 3.12, pandas, Plotly, Streamlit, pytest. Deployment continues via Streamlit Community Cloud, auto-redeploying on `git push origin main`.

**Architecture (extends Phase 1/2 additively):**

```
src/data_generator.py (extended; Phase 1 logic untouched, _generate_new_business_opps modified for tenure-aware win-rate)
  ↓
data/generated/
  customers.csv               ← Phase 1, byte-identical
  subscriptions.csv           ← Phase 1, byte-identical
  events.csv                  ← Phase 1, byte-identical
  opportunities.csv           ← regenerated (per-rep win rates shift; team-level win rate held in 21-25%)
  opportunity_stage_history.csv  ← regenerated
  pipeline_snapshots.csv      ← regenerated
  reps.csv                    ← NEW
  ↓
src/metrics.py, src/cohorts.py     (Phase 1, untouched)
src/pipeline.py, src/forecast.py   (Phase 2, untouched)
src/quota.py                       ← NEW (pure functions)
  ↓
src/viz.py (extended; Phase 1/2 builders untouched)
  ↓
Overview.py, pages/2_Cohort_Analysis.py, pages/3_Segment_Drilldown.py,
pages/5_Pipeline.py, pages/6_Forecasting.py   (Phase 1/2, untouched)
pages/7_Quota.py                   ← NEW
pages/8_About.py                   ← renamed from 7_About.py, content extended
```

All Phase 3 modules in `src/` are **pure functions** (no IO, no Streamlit imports, no global state) — matching the Phase 1/2 convention. The Quota page has its own `@st.cache_data load_data()`. No shared session state.

## 5. Synthetic data model

### 5.1 `reps.csv`

One row per rep. 12 rows.

| Column | Type | Notes |
|---|---|---|
| `rep_id` | string | `REP-01`...`REP-12`. Already used as FK on `opportunities.owner_rep_id`. |
| `name` | string | Human first/last name (e.g., "Alex Morgan"). Selected without replacement from a fixed 24-name pool, deterministic via `RNG_SEED+3`. |
| `hire_date` | date | Staggered across the dataset: 4 reps in 2021-01 to 2022-12 (always tenured), 4 in 2023-01 to 2024-06 (transition mid-dataset), 4 in 2024-07 to 2025-06 (still ramping at dataset end). |
| `segment_specialty` | enum | `SMB` / `Mid-Market` / `Enterprise`. **Derived** in a two-pass step: opportunities are generated first with uniform-random `owner_rep_id`, then each rep's modal closed-won segment is computed and written back. This makes specialty honest to the underlying data. |
| `territory` | enum | `North` / `South` / `East` / `West`. Round-robin assigned so each territory has exactly 3 reps. |
| `quarterly_quota` | float | Tiered by specialty: SMB $150,000, Mid-Market $500,000, Enterprise $1,500,000. |

### 5.2 Hire date cohorts

| Cohort | Hire window | Count | Role in ramp narrative |
|---|---|---|---|
| Veteran | 2021-01 to 2022-12 | 4 | At full productivity for the entire dataset (Jan 2023 – Dec 2025). Anchor for the "tenured" tenure bucket. |
| Mid-tenure | 2023-01 to 2024-06 | 4 | Ramping in 2023 / early 2024; tenured by mid-2024 onward. Bridges tenure buckets. |
| New hires | 2024-07 to 2025-06 | 4 | Still ramping at dataset end. Populates the 0-3, 3-6, and 6-12 month tenure buckets at the most recent reporting quarters. |

### 5.3 Quota tiers — rationale

Tiered quotas are necessary for attainment % to be comparable across reps. With a flat quota, an Enterprise rep closing one $1M deal would show 700% attainment while an SMB rep closing $120K in deals would show 80%, even though both are healthy outcomes for their book. Tiering normalizes to a 0-200% range where "near 100%" means "on plan."

Tiers calibrated against the existing Phase 2 deal-size distributions:
- SMB ACVs average ~$8K. ~5-6 closed-won SMB deals per quarter clears $150K.
- Mid-Market ACVs average ~$50K. ~10 closed-won deals per quarter clears $500K.
- Enterprise ACVs average ~$800K. ~2 closed-won deals per quarter clears $1.5M.

If empirical calibration during implementation shows these miss the mark, the tier values may shift; the test suite enforces that the team-level median attainment lands in the 75-110% band so individual quotas aren't pathologically too easy or too hard.

## 6. The engineered hidden insight

**Ramp curve longer than the assumed 6 months.** The team's actual time-to-full-productivity is approximately 9 months, not the 6 months that most SaaS sales orgs use as their baseline ramp assumption. Surfaced via:

1. **Longitudinal ramp curve** — line chart of rolling-3-month attainment % per rep, plotted against `(close_date − hire_date)` in months. Two vertical dashed reference lines: month 6 (annotated "Industry-assumed ramp") and month 9 (annotated "Actual full productivity"). The curve hits 100% near month 9, with a visible plateau before that.
2. **Tenure-bucket bar chart** — median attainment by tenure bucket (0-3, 3-6, 6-12, 12+ months), adjacent to the longitudinal curve. Same data, simpler summary view.

**Encoded in the generator** via a tenure-aware win-rate multiplier in `_generate_new_business_opps`. For each opportunity, the existing closed-won vs. closed-lost decision is adjusted by a multiplier derived from the owning rep's tenure at `close_date`:

```python
def ramp_multiplier(tenure_months: float) -> float:
    if tenure_months < 0:
        return 0.55                    # safety: rep not yet hired
    if tenure_months < 9:
        return 0.55 + 0.05 * tenure_months  # 0.55 → 1.0 across 9 months
    return 1.0 + TENURED_BOOST              # ~1.05, calibrated empirically
```

`TENURED_BOOST` is hand-calibrated so the team-level new-business win rate stays in the 21-25% band (Phase 2's calibrated number is ~23%). The boost compensates for the ramp drag on new reps. Calibration happens during implementation by running the generator and adjusting the constant until the band test passes.

**Narrative for the case study:** "Eight of our twelve reps are at or above 90% attainment, but four are below 70%. The four are not underperforming — they're our four most recent hires, and they're tracking the same productivity curve our previous new hires followed. Our plan assumes new hires are at full productivity by month 6; the data says month 9. Adjust hiring lead time, ramped quota schedules, and pipeline-coverage targets accordingly, or you'll keep paying severance to people who would have been productive in 12 weeks."

## 7. Metrics

All metrics live in `src/quota.py` as pure functions. They take pandas DataFrames matching the schemas in §5 and Phase 2's opportunities/stage_history, and return scalars or aggregated DataFrames. Formulas surface in docstrings and in the About page metric table (must stay in sync — same Phase 1/2 convention).

### 7.1 `src/quota.py`

| Function | Returns | Formula |
|---|---|---|
| `load_quota_data(reps_path, opps_path)` | `(reps_df, opps_df)` | IO boundary; the only impure function. Returns `reps` plus `opps` filtered to `opportunity_type == "new_business"` and `status in {closed_won, closed_lost}`. |
| `quarterly_attainment(closed_won, reps, quarter)` | DataFrame | One row per rep: `closed_amount = sum(amount where close_date in quarter)`; `attainment_pct = closed_amount / quarterly_quota`; `status` ∈ {`At/Above` (≥100%), `On Track` (70-100%), `At Risk` (<70%)}. |
| `attainment_distribution(closed_won, reps, quarter)` | DataFrame | Per-rep attainment sorted descending; powers the bar chart in §1 of the page. |
| `ramp_curve(closed_won, reps)` | DataFrame | Long-form: for each (rep × month-of-data), compute `tenure_months = (month - hire_date) / 30.44` and the rolling-3-month attainment ratio. Numerator = sum of `closed_won.amount` for that rep over a 3-month trailing window ending in this month; denominator = the rep's `quarterly_quota` (already a 3-month figure). Result is a per-rep, per-month attainment % aligned to a 3-month window. Used for the longitudinal ramp chart. |
| `ramp_bucket_attainment(closed_won, reps)` | DataFrame | Tenure buckets (0-3, 3-6, 6-12, 12+ months) × median attainment %. Adjacent summary view next to the longitudinal curve. |
| `rep_scorecard(closed_won, closed_lost, reps, opps_all, quarter)` | DataFrame | One row per rep: `name, segment_specialty, territory, tenure_months, quarterly_quota, closed_amount, attainment_pct, win_rate, avg_deal_size, avg_cycle_days`. |
| `territory_balance(closed_won, reps, quarter)` | DataFrame | Closed-won $ by territory × segment for the quarter. Powers the stacked bar chart in §3. |
| `team_kpis(closed_won, reps, quarter)` | dict | `{team_attainment_pct, reps_at_or_above, median_attainment, at_risk_count}`. |

**Definitions reused from Phase 2** (re-stated, not imported, to keep `quota.py` pure and independently testable):
- Win rate: `closed_won_count / (closed_won_count + closed_lost_count)` over the window.
- Cycle time: `(close_date − created_date).days`, averaged across the rep's closed-won deals in the window.

**Tenure handling:**
- `tenure_months = (reference_date − hire_date).days / 30.44` (average month length).
- A rep's tenure at the time of their own deal is computed using `close_date` as `reference_date`.
- A rep's tenure for the scorecard table uses the quarter-end date.

## 8. Pages

### 8.1 `pages/7_Quota.py`

**Sidebar / filter row:**
- Quarter selector (default = most recent full quarter in data, 2025-Q4).
- Segment filter (All / SMB / Mid-Market / Enterprise) — applies to §1, §3, §4. Does NOT apply to §2 (ramp curve is longitudinal).
- Territory filter (All / North / South / East / West) — applies to §1, §3, §4. Does NOT apply to §2.

**KPI tile row (4 tiles):**
- **Team Attainment** — total closed-won $ for the quarter ÷ total quota across all reps. Δ vs. prior quarter shown when prior quarter is within the dataset; caption explains hidden delta otherwise (same UX pattern as Phase 1 Overview).
- **Reps At/Above Quota** — count of reps with attainment ≥ 100%, displayed as `N / 12`. No Δ (small integer).
- **Median Attainment** — median attainment % across all reps. Δ vs. prior quarter.
- **At-Risk Count** — count of reps with attainment < 70%. No Δ.

**§1 — Attainment Distribution.** Horizontal bar chart, one row per rep, sorted descending by attainment %. Color-banded using the Cadenza palette: `CADENZA_GOOD` for ≥100%, `CADENZA_NEUTRAL` for 70-100%, `CADENZA_BAD` for <70%. Reference line at 100%. Caption: "Quarterly attainment by rep — {quarter}."

**§2 — Ramp Curve (longitudinal; NOT filtered by quarter).** Two side-by-side charts:
- Left: line chart of mean rolling-3mo attainment % vs. tenure months (x-axis: 0 to 30 months). Two vertical dashed reference lines at month 6 (annotated "Industry-assumed ramp", `CADENZA_NEUTRAL`) and month 9 (annotated "Actual full productivity", `CADENZA_ACCENT`). 100% horizontal reference line.
- Right: horizontal bar of median attainment by tenure bucket (0-3, 3-6, 6-12, 12+ months).
- Caption explains: "Computed across all reps and all months in the dataset, aggregated by months-since-hire. The team reaches full productivity around month 9 — three months later than the industry-standard 6-month ramp assumption."

**§3 — Territory & Segment Balance.** Stacked horizontal bar: 4 territories on the y-axis, closed-won $ on the x-axis, stacked by segment (Enterprise / Mid-Market / SMB) using the Cadenza palette. Caption: "{quarter} closed-won by territory and segment. 3 reps per territory."

**§4 — Rep Scorecard.** Styled `pd.DataFrame` via `st.dataframe`, one row per rep:

| Name | Specialty | Territory | Tenure (mo) | Quota | Closed Won | Att % | Win Rate | Avg Deal | Cycle (days) |

Styling: `highlight_max` (green tint) on Att % and Win Rate; `highlight_min` (green tint) on Cycle (days). At-Risk reps get a red text color on the Att % column. Same styled-DataFrame pattern as Phase 1 page 3.

### 8.2 `pages/8_About.py` (renamed from `7_About.py`)

- Content rename only; file rename is for sidebar ordering (About should stay last).
- Append a "Phase 3: Quota Attainment & Rep Performance" narrative subsection.
- Extend the metric definitions table with all Phase 3 metrics from §7.1.
- Extend "Scope & Deferrals" with the new-business-only quota call.
- Add a "Hidden insight #3" bullet describing the ramp curve.

## 9. Generator mechanics

Changes to `src/data_generator.py` (Phase 1 logic and seeds untouched):

1. **New function `generate_reps(rng)`** — returns the `reps` DataFrame per §5.1. Uses an RNG seeded `RNG_SEED + 3`.
2. **Two-pass specialty backfit:**
   - First pass: generate opportunities with existing uniform-random `owner_rep_id` (unchanged).
   - Second pass: compute each rep's modal segment from their closed-won opps and write it to the reps table as `segment_specialty`.
   - This ensures specialty is honest to the data.
3. **Modified `_generate_new_business_opps`:** the existing closed-won vs. closed-lost decision gains a tenure-aware multiplier. Pseudocode:
   ```python
   tenure_months = (close_date - hire_date_lookup[owner_rep_id]).days / 30.44
   base_win_prob = (existing logic, unchanged structure)
   adjusted = base_win_prob * ramp_multiplier(tenure_months)
   is_won = rng.random() < adjusted
   ```
   `ramp_multiplier` is the function defined in §6. `TENURED_BOOST` is calibrated to hold the team-level win rate in [0.21, 0.25].
4. **Generator-wide:** Phase 1 customer / subscription / event generation unchanged. Renewal and expansion generation unchanged. Snapshot generation unchanged. Only new-business closed-won/lost mechanics change.

**Determinism:** new RNG instances seeded `RNG_SEED + 3` (reps) — Phase 1 uses `seed` and `seed + 1`, Phase 2 uses `seed + 2`. Re-running the full generator is a no-op as long as code doesn't change.

## 10. Testing

**Hand-built fixtures** (extend `tests/conftest.py`):

- **`sample_reps`** — 6 reps spanning the tenure cohorts and all 3 specialties / 4 territories. Comments document hand-calculated tenure-month values for the dataset's quarter ends.
- **`sample_opps_for_quota`** — ~30 hand-built new-business opportunities across Q4 2025 plus surrounding quarters. Comments document hand-calculated per-rep `closed_amount`, `attainment_pct`, `win_rate`, `avg_deal_size`, and `avg_cycle_days` for Q4 2025, designed to exercise:
  - At least one rep with >100% attainment
  - At least one rep with 70-100% attainment
  - At least one rep at <70% attainment
  - At least one rep in each tenure bucket
  - At least one rep with deals in multiple months (for rolling-3mo correctness)

**New test file `tests/test_quota.py`** — one test per public function in `src/quota.py`:

| Test | Asserts |
|---|---|
| `test_quarterly_attainment_per_rep` | Each rep's attainment % matches hand-calc from fixture (e.g., REP-A = 1.20). |
| `test_attainment_status_buckets` | Status assigned correctly: ≥100% "At/Above", 70-100% "On Track", <70% "At Risk". |
| `test_attainment_distribution_sorted` | Returns descending by attainment %. |
| `test_ramp_curve_long_form` | Returns one row per (rep, tenure_month); rolling-3mo applied correctly across month boundaries. |
| `test_ramp_curve_handles_no_close_month` | A rep with zero closes in a month has 0% attainment for that month, not NaN. |
| `test_ramp_bucket_attainment_orders_correctly` | Median attainment for 0-3 mo bucket < 12+ mo bucket on the fixture. |
| `test_rep_scorecard_columns_present` | All required columns present with expected dtypes. |
| `test_rep_scorecard_win_rate` | Win rate = closed_won / (closed_won + closed_lost), hand-verified per rep. |
| `test_rep_scorecard_cycle_time` | Cycle = mean `(close_date - created_date).days` across rep's closed-won. |
| `test_territory_balance_sum_equals_total` | Sum of all stacked-bar values equals total closed-won $ for the quarter. |
| `test_team_kpis_keys_and_values` | Four return-dict keys present, values match hand-calc. |
| `test_quota_segment_filter` | Filtering by segment narrows scorecard correctly. |
| `test_quota_territory_filter` | Filtering by territory narrows scorecard correctly. |

**Extensions to `tests/test_data_generator.py`** (new guardrails):

| Test | Asserts |
|---|---|
| `test_reps_csv_has_12_rows` | 12 reps, exactly 3 per territory, exactly 4 in each hire cohort. |
| `test_reps_csv_specialty_matches_historical_mix` | Each rep's `segment_specialty` equals their modal closed-won segment (validates the two-pass backfit). |
| `test_team_win_rate_stays_in_band` | TTM new-business win rate is in [0.21, 0.25] (ramp injection didn't break Phase 2 calibration). |
| `test_midmarket_poc_stall_still_2x` | Re-runs Phase 2 guardrail — POC stall ratio ≥ 2.0×. |
| `test_ramp_curve_visible_in_data` | Median attainment for reps with <6 months tenure is ≥20pp lower than reps with 12+ months tenure (asserts hidden insight #3 survives future generator tweaks). |
| `test_phase1_csvs_unchanged_after_phase3` | Customers/subscriptions/events CSVs byte-identical after Phase 3 generator runs. Mirrors Phase 2's invariant. |

**Target:** Phase 1+2 = 44 tests (unchanged) + 19 Phase 3 tests (13 in `tests/test_quota.py`, 6 added to `tests/test_data_generator.py`) = 63 total, all green. No screenshot/visual regression tests; charts are tested by asserting their input data is correct via the `quota.py` function tests.

## 11. Phase 1/2 touchpoints — full inventory

Every Phase 3 change to a Phase 1 or Phase 2 file is enumerated here.

**Renames (1 file):**
- `pages/7_About.py` → `pages/8_About.py` — for sidebar ordering (About should stay last, after the new Quota page).

**Modified (non-additive):**
- `src/data_generator.py` — `_generate_new_business_opps` gains the tenure-aware win-rate multiplier from §9. The structure of the function is preserved; only the win/loss coin flip is adjusted. Phase 1 generator functions, Phase 2 renewal/expansion/snapshot generators, and all RNG seeds remain unchanged.
- `data/generated/opportunities.csv`, `opportunity_stage_history.csv`, `pipeline_snapshots.csv` — regenerated. Per-rep win rates shift; the team-level win rate is held in [0.21, 0.25] by the guardrail. Mid-Market POC stall ratio is held ≥ 2.0× by the existing guardrail. These CSVs are **not** under the byte-identical lock — only Phase 1 CSVs are.

**Append-only changes (Phase 1/2 contents preserved):**
- `src/data_generator.py` — `generate_reps()` and the two-pass specialty backfit are appended.
- `src/viz.py` — new figure builders (`attainment_distribution_figure`, `ramp_curve_figure`, `territory_balance_figure`, `rep_scorecard_table_styler`) appended. Phase 1/2 builders untouched. Cadenza brand palette constants unchanged.
- `pages/8_About.py` (formerly `7_About.py`) — metric table extended; Phase 3 narrative subsection added. Phase 1/2 content unchanged.
- `tests/conftest.py` — new `sample_reps` and `sample_opps_for_quota` fixtures appended; existing fixtures untouched.
- `tests/test_data_generator.py` — new guardrail tests appended; existing tests unchanged.
- `README.md` — Phase 3 page added to the page list; Phase 3 status flipped.
- `CLAUDE.md` — architecture diagram updated, Phase 3 status flipped.
- `CHANGELOG.md` — Phase 3 entry on ship.

**Untouched (firm — flag immediately if Phase 3 forces a change):**
- `data/generated/customers.csv`, `subscriptions.csv`, `events.csv` — byte-identical (enforced by the invariant test).
- `src/metrics.py`, `src/cohorts.py`, `src/pipeline.py`, `src/forecast.py` — zero changes.
- `Overview.py`, `pages/2_Cohort_Analysis.py`, `pages/3_Segment_Drilldown.py`, `pages/5_Pipeline.py`, `pages/6_Forecasting.py` — zero changes.
- All 44 existing Phase 1+2 tests stay green, untouched (the Mid-Market POC stall test re-asserts against the regenerated opportunities CSV).
- Cadenza brand palette constants in `src/viz.py` — unchanged.
- `.streamlit/config.toml`, `requirements.txt`, deployment configuration — unchanged (no new dependencies).

## 12. Conventions carried from Phase 1/2

- `from __future__ import annotations` at the top of every new Python module.
- Pure functions in `src/`: no IO, no global state, no Streamlit imports (`load_quota_data` is the explicit IO boundary).
- Streamlit pages are presentation only — they call into `src/*` modules.
- Each Streamlit page has its own `@st.cache_data load_data()`.
- TDD with hand-built fixtures whose comments document hand-calculated expected values.
- Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `polish:`, `ops:`).
- Metric formulas in both docstrings and the About page table — kept in sync.
- Cadenza brand palette only. No new colors.
- Percentages on charts use `yaxis_tickformat=".0%"`. Dollar metrics use `f"${v:,.0f}"`.
- Streamlit Cloud, Python 3.12 pinned in deploy UI (not via `runtime.txt`).
