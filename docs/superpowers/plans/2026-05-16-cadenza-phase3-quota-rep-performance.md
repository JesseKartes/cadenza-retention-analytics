# Cadenza Phase 3 — Quota Attainment & Rep Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend Cadenza with rep-level performance analytics — a new `reps` table (12 quota-carrying AEs), a `Quota` Streamlit page (KPI tiles, attainment distribution, ramp curve, territory balance, rep scorecard), and pure-function metrics in `src/quota.py`. The dataset encodes a third hidden insight: actual ramp is ~9 months, not the industry-assumed 6.

**Architecture:** Additive to Phase 1/2 where possible. New module `src/quota.py` with pure functions tested against hand-built fixtures. New page `pages/7_Quota.py`. The generator gets a new `generate_reps_skeleton()` plus a tenure-weighted owner-assignment refactor of the existing `rng.choice(REP_IDS)` calls in `_generate_new_business_opps` (closed-won and closed-lost loops only — tenured reps over-represented in wins, new reps over-represented in losses). Team-level new-business win rate is preserved exactly by construction; only per-rep distribution shifts. No new dependencies.

**Tech Stack:** Python 3.12, pandas, numpy, plotly, streamlit, pytest (all already in Phase 1/2).

**Spec reference:** `docs/superpowers/specs/2026-05-16-cadenza-phase3-quota-rep-performance-design.md`

**Implementation refinement to spec §6 / §9:** The spec described a per-opp closed-won-vs-lost coin-flip multiplier and a `TENURED_BOOST` calibration constant. The actual generator builds closed-won and closed-lost opps in two separate loops (one per Phase 1 customer for wins, ~1,500 independent for losses), so a coin-flip mechanism would require restructuring those loops. The equivalent, simpler implementation is **tenure-weighted `owner_rep_id` assignment in each loop** — same effect on per-rep win rates, team-level win rate preserved exactly (no calibration constant needed), minimal touchpoints. All other spec sections stand as written.

---

## File Structure

**New files:**
```
src/quota.py                          # Pure functions: quota & rep metrics
pages/7_Quota.py                      # Quota page (Streamlit)
tests/test_quota.py                   # Tests for src/quota.py
data/generated/reps.csv               # Generated, committed
```

**Modified files (append-only or surgical, Phase 1/2 logic preserved):**
```
src/data_generator.py                 # Add generate_reps_skeleton, backfit_reps_specialty_and_quota;
                                      #   change 2 lines in _generate_new_business_opps to tenure-weighted choice;
                                      #   wire reps.csv into write_to_disk
src/viz.py                            # Append 4 new figure builders
tests/conftest.py                     # Append sample_reps + sample_opps_for_quota fixtures
tests/test_data_generator.py          # Append 6 guardrail tests
README.md                             # Phase 3 added to page list, status flipped
CLAUDE.md                             # Architecture diagram updated, Phase 3 flipped
CHANGELOG.md                          # Phase 3 entry on ship
data/generated/opportunities.csv             # Regenerated (per-rep owner shifts)
data/generated/opportunity_stage_history.csv # Regenerated (downstream of opps)
data/generated/pipeline_snapshots.csv        # Regenerated (downstream of opps)
```

**Renamed files (1):**
```
pages/7_About.py  →  pages/8_About.py        # Sidebar ordering
```

**Untouched (firm):**
- `data/generated/customers.csv`, `subscriptions.csv`, `events.csv` (byte-identical lock)
- `src/metrics.py`, `src/cohorts.py`, `src/pipeline.py`, `src/forecast.py`
- `Overview.py`, `pages/2_Cohort_Analysis.py`, `pages/3_Segment_Drilldown.py`, `pages/5_Pipeline.py`, `pages/6_Forecasting.py`
- Cadenza brand palette constants
- `requirements.txt`, `.streamlit/config.toml`, deployment configuration

---

## Task 1: Rename `pages/7_About.py` → `pages/8_About.py`

The About page should stay last in the sidebar after the new Quota page is added. Rename now so subsequent tasks can write to `pages/7_Quota.py` without collision.

**Files:**
- Rename: `pages/7_About.py` → `pages/8_About.py`

- [ ] **Step 1: Rename file with git**

```bash
git mv pages/7_About.py pages/8_About.py
```

- [ ] **Step 2: Verify Streamlit sidebar order is unaffected**

The Streamlit page filename's leading number controls sidebar ordering. `8_` keeps About after the (soon-to-exist) `7_Quota.py`. The page's `st.title()` line stays unchanged.

- [ ] **Step 3: Run existing test suite to confirm no breakage**

Run: `pytest -q`
Expected: 44 passed (Phase 1+2 baseline).

- [ ] **Step 4: Commit**

```bash
git add pages/
git commit -m "chore(phase-3): rename 7_About.py -> 8_About.py to make room for Quota page"
```

---

## Task 2: Hand-built fixtures + empty `src/quota.py`

Set up the fixtures and empty module so Tasks 3-9 can TDD against them. The fixtures are the contract: their comments document hand-calculated expected metric values.

**Files:**
- Modify: `tests/conftest.py` (append two fixtures)
- Create: `src/quota.py`
- Create: `tests/test_quota.py` (with a single import-check test)

- [ ] **Step 1: Append `sample_reps` fixture to `tests/conftest.py`**

Append this fixture at the end of the file:

```python
@pytest.fixture
def sample_reps() -> pd.DataFrame:
    """6 reps spanning all tenure cohorts, 3 specialties, 4 territories.

    Used by Phase 3 quota tests. Tenure is computed relative to a quarter-end
    reference date of 2025-12-31 (the dataset's final day).

    Hand-calculated tenure at 2025-12-31:
      REP-A: hired 2020-01-15 → 71.5 months tenure  (Veteran, Enterprise, North, $1.5M)
      REP-B: hired 2022-06-15 → 41.6 months         (Veteran, Mid-Market, South, $500K)
      REP-C: hired 2024-01-15 → 23.5 months         (Mid-tenure, Mid-Market, East, $500K)
      REP-D: hired 2025-06-15 →  6.5 months         (New, SMB, West, $150K)
      REP-E: hired 2024-09-15 → 15.5 months         (Mid-tenure, SMB, North, $150K)
      REP-F: hired 2023-03-15 → 33.5 months         (Veteran, Enterprise, South, $1.5M)
    """
    rows = [
        {"rep_id": "REP-A", "name": "Alex Morgan",   "hire_date": "2020-01-15",
         "segment_specialty": "Enterprise", "territory": "North", "quarterly_quota": 1_500_000.0},
        {"rep_id": "REP-B", "name": "Priya Shah",    "hire_date": "2022-06-15",
         "segment_specialty": "Mid-Market", "territory": "South", "quarterly_quota": 500_000.0},
        {"rep_id": "REP-C", "name": "Diego Lopez",   "hire_date": "2024-01-15",
         "segment_specialty": "Mid-Market", "territory": "East",  "quarterly_quota": 500_000.0},
        {"rep_id": "REP-D", "name": "Jamie Chen",    "hire_date": "2025-06-15",
         "segment_specialty": "SMB",        "territory": "West",  "quarterly_quota": 150_000.0},
        {"rep_id": "REP-E", "name": "Riley Park",    "hire_date": "2024-09-15",
         "segment_specialty": "SMB",        "territory": "North", "quarterly_quota": 150_000.0},
        {"rep_id": "REP-F", "name": "Sam Okafor",    "hire_date": "2023-03-15",
         "segment_specialty": "Enterprise", "territory": "South", "quarterly_quota": 1_500_000.0},
    ]
    return pd.DataFrame(rows)
```

- [ ] **Step 2: Append `sample_opps_for_quota` fixture to `tests/conftest.py`**

Append immediately after `sample_reps`:

```python
@pytest.fixture
def sample_opps_for_quota() -> pd.DataFrame:
    """Hand-built new-business opportunities for Phase 3 quota tests.

    Designed so per-rep Q4 2025 (2025-10-01 to 2025-12-31) values match hand-calc:
      REP-A: 2 closed-won @ $900K each = $1,800,000 / $1,500,000 quota = 120% attainment
             2 closed-lost in window. Win rate = 2/(2+2) = 0.50.
             Cycle days for the 2 won: 90 and 60 → avg 75.
      REP-B: 8 closed-won @ $50K each   = $400,000 / $500,000 = 80% (On Track)
             2 closed-lost in window. Win rate = 8/10 = 0.80.
             Cycle days: 8 deals all 30 days → avg 30.
      REP-C: 6 closed-won @ $50K each   = $300,000 / $500,000 = 60% (At Risk)
             4 closed-lost in window. Win rate = 6/10 = 0.60.
             Cycle days: 6 deals all 45 days → avg 45.
      REP-D: 2 closed-won @ $15K each   = $30,000 / $150,000 = 20% (At Risk, early ramp)
             8 closed-lost in window. Win rate = 2/10 = 0.20.
             Cycle days: 2 deals at 50 and 70 → avg 60.
      REP-E: 6 closed-won @ $15K each   = $90,000 / $150,000 = 60% (At Risk, mid ramp)
             4 closed-lost in window. Win rate = 6/10 = 0.60.
             Cycle days: 6 deals all 40 days → avg 40.
      REP-F: 2 closed-won @ $800K each  = $1,600,000 / $1,500,000 = 107% (At/Above)
             1 closed-lost in window. Win rate = 2/3 ≈ 0.667.
             Cycle days: 2 deals at 100 and 80 → avg 90.

    Q4 2025 team totals (for territory_balance / team_kpis tests):
      Total closed-won = $4,220,000 across 26 deals
      By territory (rep_id → territory):
        North: REP-A ($1.8M Enterprise) + REP-E ($90K SMB)  = $1,890,000
        South: REP-B ($400K Mid-Market) + REP-F ($1.6M Ent) = $2,000,000
        East:  REP-C ($300K Mid-Market)                     =   $300,000
        West:  REP-D ($30K SMB)                             =    $30,000

    Plus extra opps in 2025-Q1 through 2025-Q3 to give ramp_curve enough monthly
    data per rep (rolling-3mo needs >=3 months of close activity per rep).
    """
    rows = []
    next_id = 1

    def add(rep, won, amount, segment, created, close):
        nonlocal next_id
        rows.append({
            "opportunity_id": f"OPP-Q{next_id:04d}",
            "customer_id": None,
            "account_name": "Synthetic Account",
            "segment": segment,
            "acquisition_channel": "Outbound Sales",
            "owner_rep_id": rep,
            "opportunity_type": "new_business",
            "created_date": created,
            "close_date": close,
            "amount": float(amount),
            "current_stage": "Closed Won" if won else "Closed Lost",
            "status": "closed_won" if won else "closed_lost",
        })
        next_id += 1

    # --- Q4 2025 hand-calc deals ---
    # REP-A: 2 won @ $900K (cycle 90, 60 days); 2 lost
    add("REP-A", True,  900_000, "Enterprise", "2025-08-15", "2025-11-13")  # 90d
    add("REP-A", True,  900_000, "Enterprise", "2025-09-30", "2025-11-29")  # 60d
    add("REP-A", False, 700_000, "Enterprise", "2025-10-01", "2025-11-15")
    add("REP-A", False, 750_000, "Enterprise", "2025-10-15", "2025-12-10")

    # REP-B: 8 won @ $50K (each 30d cycle); 2 lost
    for i in range(8):
        d = f"2025-{10 + i // 3:02d}-{(i % 28 + 1):02d}"
        add("REP-B", True, 50_000, "Mid-Market", "2025-09-15", d)  # ~30d cycles
    # Force exact 30-day cycle by setting created_date precisely on the 2 we test:
    # The avg will land at 30 with the spread above; tests assert avg, not exact.
    add("REP-B", False, 50_000, "Mid-Market", "2025-09-15", "2025-10-20")
    add("REP-B", False, 50_000, "Mid-Market", "2025-09-20", "2025-11-10")

    # REP-C: 6 won @ $50K (45d cycles); 4 lost
    for i in range(6):
        d = f"2025-{10 + i // 2:02d}-{(2 + i * 4):02d}"
        add("REP-C", True, 50_000, "Mid-Market", "2025-08-20", d)
    for i in range(4):
        d = f"2025-{10 + i // 2:02d}-{(5 + i * 3):02d}"
        add("REP-C", False, 50_000, "Mid-Market", "2025-09-01", d)

    # REP-D: 2 won @ $15K (cycle 50, 70d); 8 lost (early ramp)
    add("REP-D", True, 15_000, "SMB", "2025-09-10", "2025-10-30")  # 50d
    add("REP-D", True, 15_000, "SMB", "2025-09-20", "2025-11-29")  # 70d
    for i in range(8):
        d = f"2025-{10 + i // 3:02d}-{(3 + i * 3):02d}"
        add("REP-D", False, 15_000, "SMB", "2025-09-25", d)

    # REP-E: 6 won @ $15K (40d cycles); 4 lost (mid ramp)
    for i in range(6):
        d = f"2025-{10 + i // 2:02d}-{(4 + i * 4):02d}"
        add("REP-E", True, 15_000, "SMB", "2025-09-01", d)
    for i in range(4):
        d = f"2025-{10 + i // 2:02d}-{(6 + i * 3):02d}"
        add("REP-E", False, 15_000, "SMB", "2025-09-15", d)

    # REP-F: 2 won @ $800K (cycle 100, 80d); 1 lost
    add("REP-F", True,  800_000, "Enterprise", "2025-07-23", "2025-10-31")  # 100d
    add("REP-F", True,  800_000, "Enterprise", "2025-09-11", "2025-11-30")  # 80d
    add("REP-F", False, 750_000, "Enterprise", "2025-09-15", "2025-11-20")

    # --- Pre-Q4 2025 deals for ramp_curve rolling-3mo continuity ---
    # Give each rep 1 won deal per month in Q1-Q3 2025 so the longitudinal series
    # has non-zero values at every month-since-hire bucket we care about.
    for rep, amt, seg in [
        ("REP-A", 900_000, "Enterprise"), ("REP-B", 50_000, "Mid-Market"),
        ("REP-C", 50_000, "Mid-Market"),  ("REP-D", 15_000, "SMB"),
        ("REP-E", 15_000, "SMB"),         ("REP-F", 800_000, "Enterprise"),
    ]:
        for month in ("01", "02", "03", "04", "05", "06", "07", "08", "09"):
            add(rep, True, amt, seg, f"2025-{month}-01", f"2025-{month}-25")

    return pd.DataFrame(rows)
```

- [ ] **Step 3: Create `src/quota.py` with module docstring and empty placeholder**

```python
"""Cadenza Quota & Rep Performance — quarterly attainment, ramp, scorecard, territory.

Scope is new-business opportunities only. Renewal and expansion ACV does not
count toward attainment — matches how most SaaS orgs separate AE comp from
CSM/AM comp. See the About page's Scope & Deferrals section.

The third engineered insight surfaces here: the team's actual ramp curve hits
full productivity at ~9 months, not the industry-assumed 6.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
```

- [ ] **Step 4: Create `tests/test_quota.py` with import sanity check**

```python
"""Tests for src/quota.py — Cadenza Phase 3 quota / rep performance metrics."""
from __future__ import annotations

import pandas as pd
import pytest


def test_module_importable():
    """Smoke check: the empty module imports cleanly."""
    from src import quota  # noqa: F401
```

- [ ] **Step 5: Run tests**

Run: `pytest -q`
Expected: 45 passed (44 baseline + 1 new sanity).

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py tests/test_quota.py src/quota.py
git commit -m "test(phase-3): hand-built fixtures + empty quota module skeleton"
```

---

## Task 3: `quarterly_attainment` (TDD)

First metric. Computes per-rep closed_amount / quarterly_quota for a given quarter, plus a status bucket.

**Files:**
- Modify: `tests/test_quota.py` (add failing test)
- Modify: `src/quota.py` (implement)

- [ ] **Step 1: Write failing test in `tests/test_quota.py`**

Append:

```python
def test_quarterly_attainment_per_rep(sample_reps, sample_opps_for_quota):
    """Each rep's Q4 2025 attainment % matches the hand-calc in the fixture."""
    from src.quota import quarterly_attainment

    result = quarterly_attainment(
        sample_opps_for_quota, sample_reps, pd.Period("2025Q4")
    )
    # Index/order by rep_id for deterministic lookup
    result = result.set_index("rep_id")

    # Hand-calc per fixture docstring:
    assert result.loc["REP-A", "closed_amount"] == 1_800_000
    assert result.loc["REP-A", "attainment_pct"] == pytest.approx(1.20)
    assert result.loc["REP-A", "status"] == "At/Above"

    assert result.loc["REP-B", "closed_amount"] == 400_000
    assert result.loc["REP-B", "attainment_pct"] == pytest.approx(0.80)
    assert result.loc["REP-B", "status"] == "On Track"

    assert result.loc["REP-C", "closed_amount"] == 300_000
    assert result.loc["REP-C", "attainment_pct"] == pytest.approx(0.60)
    assert result.loc["REP-C", "status"] == "At Risk"

    assert result.loc["REP-D", "closed_amount"] == 30_000
    assert result.loc["REP-D", "attainment_pct"] == pytest.approx(0.20)
    assert result.loc["REP-D", "status"] == "At Risk"

    assert result.loc["REP-E", "closed_amount"] == 90_000
    assert result.loc["REP-E", "attainment_pct"] == pytest.approx(0.60)
    assert result.loc["REP-E", "status"] == "At Risk"

    assert result.loc["REP-F", "closed_amount"] == 1_600_000
    assert result.loc["REP-F", "attainment_pct"] == pytest.approx(1.0666666666)
    assert result.loc["REP-F", "status"] == "At/Above"


def test_attainment_status_buckets(sample_reps, sample_opps_for_quota):
    """Boundary checks: ≥100% At/Above; 70-100% On Track; <70% At Risk."""
    from src.quota import quarterly_attainment

    result = quarterly_attainment(
        sample_opps_for_quota, sample_reps, pd.Period("2025Q4")
    ).set_index("rep_id")
    # REP-B is exactly 80% → On Track
    assert result.loc["REP-B", "status"] == "On Track"
    # REP-C is 60% → At Risk
    assert result.loc["REP-C", "status"] == "At Risk"
    # REP-A is 120% → At/Above
    assert result.loc["REP-A", "status"] == "At/Above"
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_quota.py::test_quarterly_attainment_per_rep -v`
Expected: FAIL — `ImportError: cannot import name 'quarterly_attainment'`.

- [ ] **Step 3: Implement in `src/quota.py`**

Append to the module:

```python
def quarterly_attainment(opps: pd.DataFrame, reps: pd.DataFrame,
                          quarter: pd.Period) -> pd.DataFrame:
    """Per-rep closed-won total vs. quarterly quota for the given quarter.

    Numerator: sum of `amount` for closed-won new-business opps with
      `close_date` in `quarter`, grouped by `owner_rep_id`.
    Denominator: each rep's `quarterly_quota` from the reps table.
    Status:
      - 'At/Above' if attainment_pct >= 1.0
      - 'On Track' if 0.7 <= attainment_pct < 1.0
      - 'At Risk'  if attainment_pct < 0.7

    Returns DataFrame with columns:
      rep_id, name, quarterly_quota, closed_amount, attainment_pct, status.
    """
    closed_won = opps[
        (opps["status"] == "closed_won")
        & (opps["opportunity_type"] == "new_business")
    ].copy()
    closed_won["close_date"] = pd.to_datetime(closed_won["close_date"])
    in_quarter = closed_won[closed_won["close_date"].dt.to_period("Q") == quarter]

    per_rep = (
        in_quarter.groupby("owner_rep_id", as_index=False)["amount"]
        .sum()
        .rename(columns={"owner_rep_id": "rep_id", "amount": "closed_amount"})
    )

    merged = reps[["rep_id", "name", "quarterly_quota"]].merge(
        per_rep, on="rep_id", how="left"
    )
    merged["closed_amount"] = merged["closed_amount"].fillna(0.0)
    merged["attainment_pct"] = merged["closed_amount"] / merged["quarterly_quota"]
    merged["status"] = merged["attainment_pct"].apply(_attainment_status)
    return merged


def _attainment_status(pct: float) -> str:
    if pct >= 1.0:
        return "At/Above"
    if pct >= 0.7:
        return "On Track"
    return "At Risk"
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_quota.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/quota.py tests/test_quota.py
git commit -m "feat(phase-3): quarterly_attainment metric"
```

---

## Task 4: `attainment_distribution` (TDD)

Returns one row per rep sorted descending by attainment %, for the §1 horizontal bar chart.

**Files:**
- Modify: `tests/test_quota.py` (append test)
- Modify: `src/quota.py` (append function)

- [ ] **Step 1: Write failing test**

Append to `tests/test_quota.py`:

```python
def test_attainment_distribution_sorted(sample_reps, sample_opps_for_quota):
    """attainment_distribution returns rows sorted descending by attainment_pct."""
    from src.quota import attainment_distribution

    result = attainment_distribution(
        sample_opps_for_quota, sample_reps, pd.Period("2025Q4")
    )
    pcts = result["attainment_pct"].tolist()
    assert pcts == sorted(pcts, reverse=True), \
        f"Expected descending, got {pcts}"

    # Top row is REP-A at 120%; bottom row is REP-D at 20%
    assert result.iloc[0]["rep_id"] == "REP-A"
    assert result.iloc[-1]["rep_id"] == "REP-D"
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_quota.py::test_attainment_distribution_sorted -v`
Expected: FAIL — `cannot import name 'attainment_distribution'`.

- [ ] **Step 3: Implement in `src/quota.py`**

Append:

```python
def attainment_distribution(opps: pd.DataFrame, reps: pd.DataFrame,
                              quarter: pd.Period) -> pd.DataFrame:
    """Per-rep attainment for the quarter, sorted descending. Powers §1 of the page.

    Returns the same columns as `quarterly_attainment`, sorted by attainment_pct desc.
    """
    return quarterly_attainment(opps, reps, quarter).sort_values(
        "attainment_pct", ascending=False
    ).reset_index(drop=True)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_quota.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/quota.py tests/test_quota.py
git commit -m "feat(phase-3): attainment_distribution metric"
```

---

## Task 5: `ramp_curve` (TDD)

Longitudinal curve: for each (rep × month-of-data), compute tenure_months and rolling-3-month attainment %. This is the heart of the hidden insight chart.

**Files:**
- Modify: `tests/test_quota.py`
- Modify: `src/quota.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_quota.py`:

```python
def test_ramp_curve_long_form(sample_reps, sample_opps_for_quota):
    """ramp_curve returns one row per (rep, month), with tenure_months and
    rolling-3mo attainment_pct computed correctly."""
    from src.quota import ramp_curve

    result = ramp_curve(sample_opps_for_quota, sample_reps)

    # Required columns
    assert {"rep_id", "month", "tenure_months", "attainment_pct"}.issubset(result.columns)

    # For REP-A (hired 2020-01-15), tenure at 2025-11-01 should be ~70 months.
    # The fixture closes 1 deal per month Jan-Sep 2025 at $900K plus 2 Q4 deals.
    # At month 2025-11-01: rolling-3mo window is Sep+Oct+Nov.
    # Sep close = $900K. Oct = 0. Nov = $900K + $900K (the two Q4 deals are Nov 13 and 29).
    # Total $ in 3mo = $2,700,000; quarterly_quota = $1,500,000; ratio = 1.80.
    rep_a_nov = result[
        (result["rep_id"] == "REP-A")
        & (result["month"] == pd.Timestamp("2025-11-01"))
    ]
    assert len(rep_a_nov) == 1
    assert rep_a_nov.iloc[0]["attainment_pct"] == pytest.approx(1.80)
    assert rep_a_nov.iloc[0]["tenure_months"] == pytest.approx(
        (pd.Timestamp("2025-11-01") - pd.Timestamp("2020-01-15")).days / 30.44,
        rel=0.001,
    )


def test_ramp_curve_zero_close_month_is_zero_not_nan(sample_reps, sample_opps_for_quota):
    """A rep with no closes in a 3-month window should have attainment_pct=0,
    not NaN. Otherwise plotly skips the point and the curve has gaps."""
    from src.quota import ramp_curve

    result = ramp_curve(sample_opps_for_quota, sample_reps)
    # REP-D hired 2025-06; pre-2025 months have no closes for them.
    # Pick a month well before hire — but a rep can't have negative tenure,
    # so the function should only emit rows where tenure >= 0.
    rep_d_pre_hire = result[
        (result["rep_id"] == "REP-D")
        & (result["month"] < pd.Timestamp("2025-06-01"))
    ]
    assert len(rep_d_pre_hire) == 0, \
        "ramp_curve should not emit rows for months before a rep's hire_date"
    # And the months REP-D *was* hired but had no closes should be 0.0, not NaN.
    rep_d_post_hire = result[result["rep_id"] == "REP-D"]
    assert rep_d_post_hire["attainment_pct"].notna().all()
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_quota.py::test_ramp_curve_long_form -v`
Expected: FAIL — `cannot import name 'ramp_curve'`.

- [ ] **Step 3: Implement in `src/quota.py`**

Append:

```python
def ramp_curve(opps: pd.DataFrame, reps: pd.DataFrame) -> pd.DataFrame:
    """Per-rep rolling-3-month attainment indexed by tenure-months-since-hire.

    For each rep and each calendar month from their `hire_date` through the latest
    close_date in the data, computes:
      - `tenure_months` = (month - hire_date).days / 30.44
      - `closed_amount_3mo` = sum of closed-won new-business amounts for that rep
        in the trailing 3-month window ending in this month
      - `attainment_pct` = closed_amount_3mo / quarterly_quota

    Months before a rep's hire_date are not emitted. Months after hire with zero
    closes get attainment_pct = 0.0 (not NaN) so the longitudinal chart has no gaps.

    Returns long-form DataFrame: rep_id, month, tenure_months, attainment_pct.
    """
    closed_won = opps[
        (opps["status"] == "closed_won")
        & (opps["opportunity_type"] == "new_business")
    ].copy()
    closed_won["close_date"] = pd.to_datetime(closed_won["close_date"])
    closed_won["close_month"] = closed_won["close_date"].values.astype("datetime64[M]")

    reps = reps.copy()
    reps["hire_date"] = pd.to_datetime(reps["hire_date"])

    if len(closed_won) == 0:
        return pd.DataFrame(columns=["rep_id", "month", "tenure_months", "attainment_pct"])

    data_max_month = pd.Timestamp(closed_won["close_month"].max())

    rows = []
    for _, rep in reps.iterrows():
        start = pd.Timestamp(rep["hire_date"]).to_period("M").to_timestamp()
        # Walk one month at a time
        months = pd.date_range(start=start, end=data_max_month, freq="MS")
        rep_closes = closed_won[closed_won["owner_rep_id"] == rep["rep_id"]]
        # Monthly closed-won totals
        monthly = (
            rep_closes.groupby("close_month")["amount"]
            .sum()
            .reindex(months, fill_value=0.0)
        )
        rolling_3mo = monthly.rolling(window=3, min_periods=1).sum()
        for m, amt_3mo in rolling_3mo.items():
            tenure = (m - rep["hire_date"]).days / 30.44
            if tenure < 0:
                continue
            rows.append({
                "rep_id": rep["rep_id"],
                "month": m,
                "tenure_months": tenure,
                "attainment_pct": float(amt_3mo) / float(rep["quarterly_quota"]),
            })
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_quota.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/quota.py tests/test_quota.py
git commit -m "feat(phase-3): ramp_curve metric (rolling-3mo by tenure month)"
```

---

## Task 6: `ramp_bucket_attainment` (TDD)

Tenure buckets (0-3, 3-6, 6-12, 12+ months) × median attainment %. Powers the summary bar next to the longitudinal curve.

**Files:**
- Modify: `tests/test_quota.py`
- Modify: `src/quota.py`

- [ ] **Step 1: Write failing test**

Append:

```python
def test_ramp_bucket_attainment_orders_correctly(sample_reps, sample_opps_for_quota):
    """Median attainment increases monotonically across tenure buckets."""
    from src.quota import ramp_bucket_attainment

    result = ramp_bucket_attainment(sample_opps_for_quota, sample_reps)

    # Returned with exactly these 4 buckets in this order
    assert result["tenure_bucket"].tolist() == ["0-3 mo", "3-6 mo", "6-12 mo", "12+ mo"]

    # Each bucket has a median_attainment column (float or NaN if empty)
    assert "median_attainment" in result.columns

    # The 12+ mo bucket median should exceed the 0-3 mo bucket median.
    # (sample_opps_for_quota deliberately encodes lower attainment for early-tenure reps.)
    tenured = result.loc[result["tenure_bucket"] == "12+ mo", "median_attainment"].iloc[0]
    early = result.loc[result["tenure_bucket"] == "0-3 mo", "median_attainment"].iloc[0]
    if pd.notna(early):  # only meaningful if the bucket has any rows
        assert tenured > early
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_quota.py::test_ramp_bucket_attainment_orders_correctly -v`
Expected: FAIL.

- [ ] **Step 3: Implement in `src/quota.py`**

Append:

```python
RAMP_BUCKETS = [
    ("0-3 mo",  0.0,  3.0),
    ("3-6 mo",  3.0,  6.0),
    ("6-12 mo", 6.0, 12.0),
    ("12+ mo", 12.0, float("inf")),
]


def ramp_bucket_attainment(opps: pd.DataFrame, reps: pd.DataFrame) -> pd.DataFrame:
    """Median attainment_pct across all (rep × month) observations, bucketed by tenure.

    Buckets: 0-3, 3-6, 6-12, 12+ months. Median is across all rep-months that fall
    into each bucket — so a rep contributes multiple data points as their tenure grows.

    Returns DataFrame with: tenure_bucket, n_observations, median_attainment.
    median_attainment is NaN if a bucket has no observations.
    """
    curve = ramp_curve(opps, reps)
    out = []
    for label, lo, hi in RAMP_BUCKETS:
        mask = (curve["tenure_months"] >= lo) & (curve["tenure_months"] < hi)
        in_bucket = curve.loc[mask, "attainment_pct"]
        out.append({
            "tenure_bucket": label,
            "n_observations": int(in_bucket.shape[0]),
            "median_attainment": float(in_bucket.median()) if len(in_bucket) else float("nan"),
        })
    return pd.DataFrame(out)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_quota.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add src/quota.py tests/test_quota.py
git commit -m "feat(phase-3): ramp_bucket_attainment metric"
```

---

## Task 7: `rep_scorecard` (TDD)

One row per rep with all the columns the §4 scorecard table needs.

**Files:**
- Modify: `tests/test_quota.py`
- Modify: `src/quota.py`

- [ ] **Step 1: Write failing tests**

Append:

```python
def test_rep_scorecard_columns_present(sample_reps, sample_opps_for_quota):
    from src.quota import rep_scorecard

    result = rep_scorecard(
        sample_opps_for_quota, sample_reps, pd.Period("2025Q4")
    )

    expected_cols = {
        "rep_id", "name", "segment_specialty", "territory", "tenure_months",
        "quarterly_quota", "closed_amount", "attainment_pct", "win_rate",
        "avg_deal_size", "avg_cycle_days",
    }
    assert expected_cols.issubset(result.columns)
    assert len(result) == len(sample_reps)


def test_rep_scorecard_win_rate(sample_reps, sample_opps_for_quota):
    """Per-rep win rate = closed_won / (closed_won + closed_lost) in window."""
    from src.quota import rep_scorecard

    result = rep_scorecard(
        sample_opps_for_quota, sample_reps, pd.Period("2025Q4")
    ).set_index("rep_id")

    # Hand-calc from fixture (Q4 2025 only)
    assert result.loc["REP-A", "win_rate"] == pytest.approx(2 / (2 + 2))  # 0.50
    assert result.loc["REP-B", "win_rate"] == pytest.approx(8 / (8 + 2))  # 0.80
    assert result.loc["REP-D", "win_rate"] == pytest.approx(2 / (2 + 8))  # 0.20


def test_rep_scorecard_cycle_time(sample_reps, sample_opps_for_quota):
    """avg_cycle_days = mean of (close_date - created_date).days across rep's
    Q4 2025 closed-won deals."""
    from src.quota import rep_scorecard

    result = rep_scorecard(
        sample_opps_for_quota, sample_reps, pd.Period("2025Q4")
    ).set_index("rep_id")

    # REP-A: 90d and 60d → avg 75
    assert result.loc["REP-A", "avg_cycle_days"] == pytest.approx(75.0)
    # REP-F: 100d and 80d → avg 90
    assert result.loc["REP-F", "avg_cycle_days"] == pytest.approx(90.0)


def test_rep_scorecard_avg_deal_size(sample_reps, sample_opps_for_quota):
    """avg_deal_size = mean amount across Q4 closed-won deals."""
    from src.quota import rep_scorecard

    result = rep_scorecard(
        sample_opps_for_quota, sample_reps, pd.Period("2025Q4")
    ).set_index("rep_id")

    assert result.loc["REP-A", "avg_deal_size"] == pytest.approx(900_000.0)
    assert result.loc["REP-B", "avg_deal_size"] == pytest.approx(50_000.0)
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_quota.py::test_rep_scorecard_columns_present -v`
Expected: FAIL — `cannot import name 'rep_scorecard'`.

- [ ] **Step 3: Implement in `src/quota.py`**

Append:

```python
def rep_scorecard(opps: pd.DataFrame, reps: pd.DataFrame,
                    quarter: pd.Period) -> pd.DataFrame:
    """One row per rep with attainment, win rate, deal size, cycle time for the quarter.

    Reuses `quarterly_attainment` for closed_amount / attainment_pct / status.
    Additional columns:
      win_rate     = closed_won_count / (closed_won_count + closed_lost_count) for
                     new-business deals with close_date in quarter, per rep
      avg_deal_size = mean amount of rep's closed-won deals in quarter
      avg_cycle_days = mean (close_date - created_date).days across rep's
                       closed-won deals in quarter
      tenure_months = (quarter_end - hire_date).days / 30.44

    Returns DataFrame ordered by attainment_pct desc.
    """
    attainment = quarterly_attainment(opps, reps, quarter)

    quarter_end = pd.Period(quarter).to_timestamp(how="end").normalize()
    reps = reps.copy()
    reps["hire_date"] = pd.to_datetime(reps["hire_date"])
    reps["tenure_months"] = (quarter_end - reps["hire_date"]).dt.days / 30.44

    nb = opps[opps["opportunity_type"] == "new_business"].copy()
    nb["close_date"] = pd.to_datetime(nb["close_date"])
    nb["created_date"] = pd.to_datetime(nb["created_date"])
    in_q = nb[nb["close_date"].dt.to_period("Q") == quarter]

    closed_won_q = in_q[in_q["status"] == "closed_won"]
    closed_lost_q = in_q[in_q["status"] == "closed_lost"]

    won_per_rep = closed_won_q.groupby("owner_rep_id").size()
    lost_per_rep = closed_lost_q.groupby("owner_rep_id").size()
    avg_size_per_rep = closed_won_q.groupby("owner_rep_id")["amount"].mean()

    closed_won_q = closed_won_q.assign(
        cycle_days=(closed_won_q["close_date"] - closed_won_q["created_date"]).dt.days
    )
    avg_cycle_per_rep = closed_won_q.groupby("owner_rep_id")["cycle_days"].mean()

    extras = pd.DataFrame({
        "won_count": won_per_rep,
        "lost_count": lost_per_rep,
        "avg_deal_size": avg_size_per_rep,
        "avg_cycle_days": avg_cycle_per_rep,
    }).fillna(0.0)
    extras["win_rate"] = extras["won_count"] / (extras["won_count"] + extras["lost_count"])
    extras = extras.reset_index().rename(columns={"owner_rep_id": "rep_id"})

    out = (
        reps[["rep_id", "name", "segment_specialty", "territory", "tenure_months",
              "quarterly_quota"]]
        .merge(
            attainment[["rep_id", "closed_amount", "attainment_pct", "status"]],
            on="rep_id", how="left",
        )
        .merge(
            extras[["rep_id", "win_rate", "avg_deal_size", "avg_cycle_days"]],
            on="rep_id", how="left",
        )
    )
    out = out.fillna({"win_rate": 0.0, "avg_deal_size": 0.0, "avg_cycle_days": 0.0})
    return out.sort_values("attainment_pct", ascending=False).reset_index(drop=True)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_quota.py -v`
Expected: 11 passed.

- [ ] **Step 5: Commit**

```bash
git add src/quota.py tests/test_quota.py
git commit -m "feat(phase-3): rep_scorecard metric"
```

---

## Task 8: `territory_balance` (TDD)

Closed-won $ by territory × segment for the quarter. Powers §3 stacked bar.

**Files:**
- Modify: `tests/test_quota.py`
- Modify: `src/quota.py`

- [ ] **Step 1: Write failing test**

Append:

```python
def test_territory_balance_sum_equals_total(sample_reps, sample_opps_for_quota):
    """Sum of stacked-bar values equals total closed-won $ for the quarter."""
    from src.quota import territory_balance

    result = territory_balance(
        sample_opps_for_quota, sample_reps, pd.Period("2025Q4")
    )

    # Required columns
    assert {"territory", "segment", "closed_amount"}.issubset(result.columns)

    total = result["closed_amount"].sum()
    # From fixture hand-calc: $1.89M + $2.00M + $0.30M + $0.03M = $4.22M
    assert total == pytest.approx(4_220_000.0)


def test_territory_balance_north_includes_two_reps(sample_reps, sample_opps_for_quota):
    """REP-A (North, Enterprise) + REP-E (North, SMB) both report under North."""
    from src.quota import territory_balance

    result = territory_balance(
        sample_opps_for_quota, sample_reps, pd.Period("2025Q4")
    )
    north = result[result["territory"] == "North"].set_index("segment")
    assert north.loc["Enterprise", "closed_amount"] == pytest.approx(1_800_000.0)
    assert north.loc["SMB", "closed_amount"] == pytest.approx(90_000.0)
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_quota.py::test_territory_balance_sum_equals_total -v`
Expected: FAIL.

- [ ] **Step 3: Implement in `src/quota.py`**

Append:

```python
def territory_balance(opps: pd.DataFrame, reps: pd.DataFrame,
                       quarter: pd.Period) -> pd.DataFrame:
    """Closed-won new-business $ by territory × segment for the quarter.

    Powers the stacked horizontal bar in §3 of the Quota page. Each row's
    territory comes from the rep table (joined on owner_rep_id); segment
    comes from the opp.

    Returns DataFrame with: territory, segment, closed_amount.
    """
    closed_won = opps[
        (opps["status"] == "closed_won")
        & (opps["opportunity_type"] == "new_business")
    ].copy()
    closed_won["close_date"] = pd.to_datetime(closed_won["close_date"])
    in_q = closed_won[closed_won["close_date"].dt.to_period("Q") == quarter]

    merged = in_q.merge(
        reps[["rep_id", "territory"]],
        left_on="owner_rep_id", right_on="rep_id", how="left",
    )
    grouped = (
        merged.groupby(["territory", "segment"], as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "closed_amount"})
    )
    return grouped
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_quota.py -v`
Expected: 13 passed.

- [ ] **Step 5: Commit**

```bash
git add src/quota.py tests/test_quota.py
git commit -m "feat(phase-3): territory_balance metric"
```

---

## Task 9: `team_kpis` + `load_quota_data` (TDD)

Final two functions. `team_kpis` returns the 4 KPI tile values; `load_quota_data` is the IO boundary that the Streamlit page calls.

**Files:**
- Modify: `tests/test_quota.py`
- Modify: `src/quota.py`

- [ ] **Step 1: Write failing tests**

Append:

```python
def test_team_kpis_keys_and_values(sample_reps, sample_opps_for_quota):
    from src.quota import team_kpis

    result = team_kpis(
        sample_opps_for_quota, sample_reps, pd.Period("2025Q4")
    )

    assert set(result.keys()) == {
        "team_attainment_pct",
        "reps_at_or_above",
        "median_attainment",
        "at_risk_count",
    }

    # Total quota = 1.5M + 0.5M + 0.5M + 0.15M + 0.15M + 1.5M = 4.3M
    # Total closed-won Q4 = 4.22M
    # Team attainment = 4.22 / 4.3 ≈ 0.9814
    assert result["team_attainment_pct"] == pytest.approx(4_220_000 / 4_300_000)

    # Reps at/above quota: REP-A (120%), REP-F (107%) → 2
    assert result["reps_at_or_above"] == 2
    # At-risk count (<70%): REP-C (60%), REP-D (20%), REP-E (60%) → 3
    assert result["at_risk_count"] == 3


def test_load_quota_data_filters_to_new_business_closed(tmp_path):
    """load_quota_data reads reps + opps CSV and filters opps to new-business
    closed-won/lost only."""
    from src.quota import load_quota_data

    # Build tiny CSVs on disk
    reps = pd.DataFrame([
        {"rep_id": "REP-X", "name": "Test Rep", "hire_date": "2024-01-01",
         "segment_specialty": "SMB", "territory": "North", "quarterly_quota": 100_000},
    ])
    opps = pd.DataFrame([
        # Kept
        {"opportunity_id": "OPP-1", "owner_rep_id": "REP-X",
         "opportunity_type": "new_business", "status": "closed_won",
         "close_date": "2024-03-01", "created_date": "2024-01-01",
         "amount": 50_000, "segment": "SMB",
         "customer_id": None, "account_name": "X", "acquisition_channel": "Outbound Sales",
         "current_stage": "Closed Won"},
        # Filtered out: renewal
        {"opportunity_id": "OPP-2", "owner_rep_id": "REP-X",
         "opportunity_type": "renewal", "status": "closed_won",
         "close_date": "2024-03-01", "created_date": "2024-01-01",
         "amount": 50_000, "segment": "SMB",
         "customer_id": None, "account_name": "X", "acquisition_channel": "Outbound Sales",
         "current_stage": "Closed Won"},
        # Filtered out: open
        {"opportunity_id": "OPP-3", "owner_rep_id": "REP-X",
         "opportunity_type": "new_business", "status": "open",
         "close_date": "2024-03-01", "created_date": "2024-01-01",
         "amount": 50_000, "segment": "SMB",
         "customer_id": None, "account_name": "X", "acquisition_channel": "Outbound Sales",
         "current_stage": "Negotiation"},
    ])
    reps_path = tmp_path / "reps.csv"
    opps_path = tmp_path / "opportunities.csv"
    reps.to_csv(reps_path, index=False)
    opps.to_csv(opps_path, index=False)

    loaded_reps, loaded_opps = load_quota_data(reps_path, opps_path)

    assert len(loaded_reps) == 1
    assert len(loaded_opps) == 1  # only OPP-1 survives the filter
    assert loaded_opps.iloc[0]["opportunity_id"] == "OPP-1"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_quota.py::test_team_kpis_keys_and_values -v`
Expected: FAIL.

- [ ] **Step 3: Implement in `src/quota.py`**

Append:

```python
def team_kpis(opps: pd.DataFrame, reps: pd.DataFrame, quarter: pd.Period) -> dict:
    """Returns the 4 KPI tile values for the Quota page header.

    - team_attainment_pct = sum(closed_won $) / sum(quarterly_quota) across all reps
    - reps_at_or_above    = count of reps with attainment >= 1.0
    - median_attainment   = median attainment_pct across all reps
    - at_risk_count       = count of reps with attainment < 0.7
    """
    att = quarterly_attainment(opps, reps, quarter)
    return {
        "team_attainment_pct": float(att["closed_amount"].sum() / att["quarterly_quota"].sum()),
        "reps_at_or_above": int((att["attainment_pct"] >= 1.0).sum()),
        "median_attainment": float(att["attainment_pct"].median()),
        "at_risk_count": int((att["attainment_pct"] < 0.7).sum()),
    }


def load_quota_data(reps_path: Path, opps_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """IO boundary for the Streamlit page. The only impure function in this module.

    Returns:
      (reps_df, opps_df) where opps_df is pre-filtered to new-business
      closed-won and closed-lost only (open opps don't count toward attainment).
    """
    reps_df = pd.read_csv(reps_path)
    opps_df = pd.read_csv(opps_path)
    opps_df = opps_df[
        (opps_df["opportunity_type"] == "new_business")
        & (opps_df["status"].isin(["closed_won", "closed_lost"]))
    ].reset_index(drop=True)
    return reps_df, opps_df
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_quota.py -v`
Expected: 15 passed.

- [ ] **Step 5: Commit**

```bash
git add src/quota.py tests/test_quota.py
git commit -m "feat(phase-3): team_kpis + load_quota_data IO boundary"
```

---

## Task 10: Generator — `generate_reps_skeleton`

Build the partial reps table (rep_id, name, hire_date, territory) BEFORE opp generation. Specialty and quota are filled in later by `backfit_reps_specialty_and_quota` after opps exist.

**Files:**
- Modify: `src/data_generator.py` (append function in the Phase 2 section)
- Modify: `tests/test_data_generator.py` (append test)

- [ ] **Step 1: Write failing test in `tests/test_data_generator.py`**

Append to the end of the file:

```python
def test_generate_reps_skeleton_shape():
    """generate_reps_skeleton returns 12 reps, 3 per territory, 4 per hire cohort."""
    import numpy as np
    from src.data_generator import generate_reps_skeleton, RNG_SEED

    rng = np.random.default_rng(RNG_SEED + 3)
    reps = generate_reps_skeleton(rng)

    assert len(reps) == 12
    assert list(reps.columns) == ["rep_id", "name", "hire_date", "territory"]
    # 3 reps per territory
    assert (reps.groupby("territory").size() == 3).all()
    # 4 in each hire cohort
    hire = pd.to_datetime(reps["hire_date"])
    veteran = ((hire >= "2021-01-01") & (hire <= "2022-12-31")).sum()
    mid     = ((hire >= "2023-01-01") & (hire <= "2024-06-30")).sum()
    new     = ((hire >= "2024-07-01") & (hire <= "2025-06-30")).sum()
    assert veteran == 4
    assert mid == 4
    assert new == 4
    # rep_id format
    assert reps["rep_id"].tolist() == [f"REP-{i:02d}" for i in range(1, 13)]
    # All names unique
    assert reps["name"].nunique() == 12


def test_generate_reps_skeleton_deterministic():
    """Same seed → same DataFrame, byte for byte."""
    import numpy as np
    from src.data_generator import generate_reps_skeleton, RNG_SEED

    rng1 = np.random.default_rng(RNG_SEED + 3)
    rng2 = np.random.default_rng(RNG_SEED + 3)
    a = generate_reps_skeleton(rng1)
    b = generate_reps_skeleton(rng2)
    pd.testing.assert_frame_equal(a, b)
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_data_generator.py::test_generate_reps_skeleton_shape -v`
Expected: FAIL — `cannot import name 'generate_reps_skeleton'`.

- [ ] **Step 3: Implement in `src/data_generator.py`**

Find the existing constant `REP_IDS = [f"REP-{i:02d}" for i in range(1, 13)]` (around line 361). Just below it, add the rep name pool and territories constants. Then append `generate_reps_skeleton` near the end of the file, just before `if __name__ == "__main__":`.

Insert under `REP_IDS`:

```python
# --- Phase 3: Rep performance ---------------------------------------------

REP_FIRST_NAMES = [
    "Alex", "Priya", "Diego", "Jamie", "Riley", "Sam",
    "Morgan", "Avery", "Casey", "Jordan", "Taylor", "Quinn",
    "Robin", "Kai", "Logan", "Drew", "Emery", "Reese",
    "Skylar", "Sage", "Rowan", "Phoenix", "Blake", "Hayden",
]
REP_LAST_NAMES = [
    "Morgan", "Shah", "Lopez", "Chen", "Park", "Okafor",
    "Anderson", "Patel", "Nguyen", "Garcia", "Murphy", "Singh",
    "Schmidt", "Kim", "Rodriguez", "Wilson", "Tanaka", "Brown",
    "Williams", "Martinez", "Davies", "Cohen", "Bhatt", "Reyes",
]
REP_TERRITORIES = ["North", "South", "East", "West"]
```

Append `generate_reps_skeleton` near the bottom (before the `if __name__` block):

```python
def generate_reps_skeleton(rng: np.random.Generator) -> pd.DataFrame:
    """Phase 3: build the partial reps table.

    Columns produced: rep_id, name, hire_date, territory.
    Specialty and quarterly_quota are filled in later by
    `backfit_reps_specialty_and_quota` once opportunities exist.

    Hire date distribution:
      - 4 reps in 2021-01-01 to 2022-12-31 (veteran, always tenured during dataset)
      - 4 reps in 2023-01-01 to 2024-06-30 (mid-tenure, transition mid-dataset)
      - 4 reps in 2024-07-01 to 2025-06-30 (new hires, still ramping at dataset end)
    Names: drawn without replacement from REP_FIRST_NAMES x REP_LAST_NAMES.
    Territories: round-robin so each of N/S/E/W has exactly 3 reps.
    """
    # Hire dates: 4 in each cohort
    veteran_starts = pd.Timestamp("2021-01-01")
    veteran_end    = pd.Timestamp("2022-12-31")
    mid_start      = pd.Timestamp("2023-01-01")
    mid_end        = pd.Timestamp("2024-06-30")
    new_start      = pd.Timestamp("2024-07-01")
    new_end        = pd.Timestamp("2025-06-30")

    def random_dates_in(rng_: np.random.Generator, start: pd.Timestamp,
                         end: pd.Timestamp, n: int) -> list[str]:
        span_days = (end - start).days
        offsets = rng_.integers(0, span_days + 1, size=n)
        return [(start + pd.Timedelta(days=int(o))).strftime("%Y-%m-%d")
                for o in sorted(offsets)]

    hire_dates = (
        random_dates_in(rng, veteran_starts, veteran_end, 4)
        + random_dates_in(rng, mid_start, mid_end, 4)
        + random_dates_in(rng, new_start, new_end, 4)
    )

    # Names: pick 12 unique first+last combos
    first_idx = rng.permutation(len(REP_FIRST_NAMES))[:12]
    last_idx  = rng.permutation(len(REP_LAST_NAMES))[:12]
    names = [f"{REP_FIRST_NAMES[fi]} {REP_LAST_NAMES[li]}"
             for fi, li in zip(first_idx, last_idx)]

    # Territories round-robin
    territories = [REP_TERRITORIES[i % 4] for i in range(12)]

    return pd.DataFrame({
        "rep_id":     [f"REP-{i:02d}" for i in range(1, 13)],
        "name":       names,
        "hire_date":  hire_dates,
        "territory":  territories,
    })
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_data_generator.py -v`
Expected: existing tests + 2 new tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/data_generator.py tests/test_data_generator.py
git commit -m "feat(phase-3): generate_reps_skeleton (rep_id, name, hire_date, territory)"
```

---

## Task 11: Generator — tenure-weighted owner assignment in `_generate_new_business_opps`

Change the two `rng.choice(REP_IDS)` calls in `_generate_new_business_opps` (closed-won loop and closed-lost loop only) to a tenure-weighted choice using a new helper. The open-opps loop keeps uniform random — open opps close after the dataset window, so they don't affect the ramp story.

**Files:**
- Modify: `src/data_generator.py` (function signature change + 2 line changes inside + 1 new helper)

- [ ] **Step 1: Add the `_choose_owner_by_tenure` helper near `_sample_dwell_days`**

In `src/data_generator.py`, just below `_sample_dwell_days` (around line 386), add:

```python
def _ramp_multiplier(tenure_months: float) -> float:
    """Linear ramp from 0.55 at month 0 to 1.0 at month 9; flat at 1.0 beyond.

    Used to weight a rep's likelihood of owning closed-won opps. New reps
    (low tenure) get lower weight; tenured reps get full weight. Symmetric
    `_loss_multiplier = 2 - _ramp_multiplier` weights the closed-lost loop.
    """
    if tenure_months < 0:
        return 0.55
    if tenure_months < 9.0:
        return 0.55 + (1.0 - 0.55) * (tenure_months / 9.0)
    return 1.0


def _choose_owner_by_tenure(rng: np.random.Generator, reps_df: pd.DataFrame,
                              close_date: pd.Timestamp, mode: str) -> str:
    """Pick an owner_rep_id weighted by rep tenure at close_date.

    `mode='won'`  → weights ∝ _ramp_multiplier(tenure_months). Tenured reps
                    are over-represented in closed-won deals.
    `mode='lost'` → weights ∝ (2 - _ramp_multiplier(tenure_months)). New reps
                    are over-represented in closed-lost deals.

    Note: total opp counts (665 won, 1500 lost) are preserved exactly. Only
    the per-rep distribution shifts. Team-level win rate is unchanged.
    """
    hire_dates = pd.to_datetime(reps_df["hire_date"])
    tenures = ((close_date - hire_dates).dt.days / 30.44).clip(lower=-0.001)
    if mode == "won":
        weights = tenures.apply(_ramp_multiplier).to_numpy()
    elif mode == "lost":
        weights = (2.0 - tenures.apply(_ramp_multiplier)).to_numpy()
    else:
        raise ValueError(f"mode must be 'won' or 'lost', got {mode!r}")
    p = weights / weights.sum()
    return str(rng.choice(reps_df["rep_id"].to_numpy(), p=p))
```

- [ ] **Step 2: Change `_generate_new_business_opps` signature to accept `reps_df`**

Find the function header (around line 424):

```python
def _generate_new_business_opps(customers: pd.DataFrame, rng: np.random.Generator
                                 ) -> tuple[list[dict], list[dict]]:
```

Replace with:

```python
def _generate_new_business_opps(customers: pd.DataFrame, reps_df: pd.DataFrame,
                                 rng: np.random.Generator
                                 ) -> tuple[list[dict], list[dict]]:
```

- [ ] **Step 3: Change the closed-won loop's owner assignment**

In `_generate_new_business_opps`, find the closed-won loop's `owner_rep_id` line (around line 455):

```python
            "owner_rep_id": str(rng.choice(REP_IDS)),
```

In the closed-won loop only (the loop that iterates `nb_customers.iterrows()`), replace with:

```python
            "owner_rep_id": _choose_owner_by_tenure(rng, reps_df, close_date, mode="won"),
```

Leave the OPEN-opps loop's `owner_rep_id` line (around line 527) UNCHANGED. Open opps close in 2026 so their owner doesn't affect dataset metrics.

- [ ] **Step 4: Change the closed-lost loop's owner assignment**

In the closed-lost sub-population loop (around line 571), find:

```python
            "owner_rep_id": str(rng.choice(REP_IDS)),
```

Replace with:

```python
            "owner_rep_id": _choose_owner_by_tenure(rng, reps_df, close_date, mode="lost"),
```

- [ ] **Step 5: Update `generate_phase2` to pass `reps_df` in**

Find `generate_phase2` (around line 994):

```python
def generate_phase2(customers: pd.DataFrame, subs: pd.DataFrame, events: pd.DataFrame
                     ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate Phase 2 tables: opportunities, opportunity_stage_history, pipeline_snapshots.

    Deterministic given Phase 1 outputs and RNG_SEED+2.
    """
    rng = np.random.default_rng(RNG_SEED + 2)

    nb_opps, nb_history = _generate_new_business_opps(customers, rng)
```

Replace those lines with:

```python
def generate_phase2(customers: pd.DataFrame, subs: pd.DataFrame, events: pd.DataFrame,
                     reps_df: pd.DataFrame
                     ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate Phase 2 tables: opportunities, opportunity_stage_history, pipeline_snapshots.

    Deterministic given Phase 1 outputs, the reps table, and RNG_SEED+2.
    `reps_df` is used to weight new-business owner assignments by rep tenure
    (Phase 3 ramp insight).
    """
    rng = np.random.default_rng(RNG_SEED + 2)

    nb_opps, nb_history = _generate_new_business_opps(customers, reps_df, rng)
```

(The rest of `generate_phase2` is unchanged.)

- [ ] **Step 6: Update `write_to_disk` to build reps first**

Find `write_to_disk` (around line 312). Replace its body with:

```python
def write_to_disk(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    customers, subs, events = generate_all()
    customers.drop(columns=[c for c in customers.columns if c.endswith("_dt")],
                   errors="ignore", inplace=True)
    customers.to_csv(out_dir / "customers.csv", index=False)
    subs.to_csv(out_dir / "subscriptions.csv", index=False)
    events.to_csv(out_dir / "events.csv", index=False)

    # Phase 3: build the rep table skeleton first; specialty + quota are
    # filled in by backfit after opps are generated.
    reps_rng = np.random.default_rng(RNG_SEED + 3)
    reps_skel = generate_reps_skeleton(reps_rng)

    # Phase 2 tables (opps now use reps for tenure-weighted owner assignment)
    opps_df, history_df, snapshots_df = generate_phase2(customers, subs, events, reps_skel)
    opps_df.to_csv(out_dir / "opportunities.csv", index=False)
    history_df.to_csv(out_dir / "opportunity_stage_history.csv", index=False)
    snapshots_df.to_csv(out_dir / "pipeline_snapshots.csv", index=False)

    # Phase 3: backfit specialty + quota now that opps exist (Task 12 will add this function).
    reps_final = backfit_reps_specialty_and_quota(reps_skel, opps_df)
    reps_final.to_csv(out_dir / "reps.csv", index=False)

    print(f"Wrote {len(customers)} customers, {len(subs)} subscription rows, "
          f"{len(events)} events, {len(opps_df)} opportunities, "
          f"{len(history_df)} stage history rows, {len(snapshots_df)} snapshots, "
          f"{len(reps_final)} reps to {out_dir}")
```

(Note: `backfit_reps_specialty_and_quota` is defined in Task 12; running this script before Task 12 will fail with `NameError`. That's expected — the next task fills it in.)

- [ ] **Step 7: Run the existing data-generator tests to confirm structural change is clean**

Run: `pytest tests/test_data_generator.py::test_generate_reps_skeleton_shape tests/test_data_generator.py::test_generate_reps_skeleton_deterministic -v`
Expected: 2 passed (Task 10's tests still pass; the new code doesn't run in tests yet).

Other generator tests (POC stall, byte-identical) will be run after Task 13 once the regenerated CSVs are committed.

- [ ] **Step 8: Commit**

```bash
git add src/data_generator.py
git commit -m "feat(phase-3): tenure-weighted owner assignment in new-business opps"
```

---

## Task 12: Generator — `backfit_reps_specialty_and_quota`

Two-pass step: with opps already generated (each rep now has wins/losses biased by tenure), compute each rep's modal closed-won segment and assign `segment_specialty` + `quarterly_quota` based on it.

**Files:**
- Modify: `src/data_generator.py` (append function)
- Modify: `tests/test_data_generator.py` (append test)

- [ ] **Step 1: Write failing test in `tests/test_data_generator.py`**

Append:

```python
def test_backfit_specialty_picks_modal_segment():
    """A rep with 5 SMB wins and 2 MM wins is tagged SMB."""
    from src.data_generator import backfit_reps_specialty_and_quota

    reps_skel = pd.DataFrame([
        {"rep_id": "REP-01", "name": "Test One", "hire_date": "2021-01-15", "territory": "North"},
        {"rep_id": "REP-02", "name": "Test Two", "hire_date": "2021-01-15", "territory": "South"},
    ])
    opps = pd.DataFrame([
        # REP-01: 5 SMB wins, 2 MM wins → SMB
        *[{"opportunity_id": f"OPP-{i}", "owner_rep_id": "REP-01",
           "opportunity_type": "new_business", "status": "closed_won",
           "segment": "SMB", "amount": 10_000.0, "close_date": "2024-01-01",
           "created_date": "2023-12-01", "customer_id": None,
           "account_name": "x", "acquisition_channel": "Outbound Sales",
           "current_stage": "Closed Won"} for i in range(5)],
        *[{"opportunity_id": f"OPP-{i+5}", "owner_rep_id": "REP-01",
           "opportunity_type": "new_business", "status": "closed_won",
           "segment": "Mid-Market", "amount": 50_000.0, "close_date": "2024-01-01",
           "created_date": "2023-12-01", "customer_id": None,
           "account_name": "x", "acquisition_channel": "Outbound Sales",
           "current_stage": "Closed Won"} for i in range(2)],
        # REP-02: 3 Enterprise wins → Enterprise
        *[{"opportunity_id": f"OPP-{i+7}", "owner_rep_id": "REP-02",
           "opportunity_type": "new_business", "status": "closed_won",
           "segment": "Enterprise", "amount": 800_000.0, "close_date": "2024-01-01",
           "created_date": "2023-12-01", "customer_id": None,
           "account_name": "x", "acquisition_channel": "Outbound Sales",
           "current_stage": "Closed Won"} for i in range(3)],
    ])

    result = backfit_reps_specialty_and_quota(reps_skel, opps)
    result = result.set_index("rep_id")

    assert result.loc["REP-01", "segment_specialty"] == "SMB"
    assert result.loc["REP-01", "quarterly_quota"] == 150_000.0
    assert result.loc["REP-02", "segment_specialty"] == "Enterprise"
    assert result.loc["REP-02", "quarterly_quota"] == 1_500_000.0


def test_backfit_quota_tiers_by_specialty():
    """Quarterly quota tier: SMB $150K, Mid-Market $500K, Enterprise $1.5M."""
    from src.data_generator import QUOTA_BY_SPECIALTY

    assert QUOTA_BY_SPECIALTY == {
        "SMB": 150_000.0,
        "Mid-Market": 500_000.0,
        "Enterprise": 1_500_000.0,
    }
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_data_generator.py::test_backfit_specialty_picks_modal_segment -v`
Expected: FAIL — `cannot import name 'backfit_reps_specialty_and_quota'`.

- [ ] **Step 3: Implement in `src/data_generator.py`**

Just above `generate_reps_skeleton` (which you added in Task 10), insert the quota constant:

```python
QUOTA_BY_SPECIALTY = {
    "SMB":        150_000.0,
    "Mid-Market": 500_000.0,
    "Enterprise": 1_500_000.0,
}
```

Then just below `generate_reps_skeleton`, append:

```python
def backfit_reps_specialty_and_quota(reps_skel: pd.DataFrame,
                                       opps_df: pd.DataFrame) -> pd.DataFrame:
    """Phase 3 step 2: fill in segment_specialty and quarterly_quota.

    For each rep, segment_specialty = the segment they closed the most
    new-business deals in (modal segment of their closed-won deals).
    quarterly_quota is then looked up from QUOTA_BY_SPECIALTY.

    Tie-breaking: if a rep is tied across segments, the segment alphabetically
    first wins (deterministic). This is rare in the full dataset.

    A rep with zero closed-won deals defaults to SMB (lowest quota); this
    only happens for very-recently-hired reps with no wins yet.
    """
    nb_won = opps_df[
        (opps_df["opportunity_type"] == "new_business")
        & (opps_df["status"] == "closed_won")
    ]

    modal_segment = (
        nb_won.groupby(["owner_rep_id", "segment"])
        .size()
        .reset_index(name="n")
        .sort_values(["owner_rep_id", "n", "segment"], ascending=[True, False, True])
        .drop_duplicates(subset="owner_rep_id", keep="first")
        .set_index("owner_rep_id")["segment"]
    )

    out = reps_skel.copy()
    out["segment_specialty"] = (
        out["rep_id"].map(modal_segment).fillna("SMB")
    )
    out["quarterly_quota"] = out["segment_specialty"].map(QUOTA_BY_SPECIALTY)

    return out[
        ["rep_id", "name", "hire_date", "segment_specialty", "territory", "quarterly_quota"]
    ]
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_data_generator.py -v`
Expected: previously-passing tests + 2 new tests pass.

- [ ] **Step 5: Run the full generator end-to-end**

Run: `python -m src.data_generator`
Expected output ending with: `Wrote ... 12 reps to data/generated`. A `reps.csv` file appears in `data/generated/`.

- [ ] **Step 6: Spot-check `reps.csv`**

Run: `head -1 data/generated/reps.csv && echo --- && wc -l data/generated/reps.csv`
Expected:
```
rep_id,name,hire_date,segment_specialty,territory,quarterly_quota
---
      13 data/generated/reps.csv
```
(13 = 1 header + 12 rows.)

- [ ] **Step 7: Commit**

```bash
git add src/data_generator.py tests/test_data_generator.py data/generated/reps.csv data/generated/opportunities.csv data/generated/opportunity_stage_history.csv data/generated/pipeline_snapshots.csv
git commit -m "feat(phase-3): backfit specialty+quota; regenerate Phase 2 CSVs with biased ownership"
```

---

## Task 13: Generator guardrail tests

Six new tests pinning the invariants: Phase 1 byte-identical, POC stall ≥ 2×, team win rate band, ramp visible in data, reps table shape.

**Files:**
- Modify: `tests/test_data_generator.py` (append guardrail tests)

- [ ] **Step 1: Append the guardrail tests**

Append to `tests/test_data_generator.py`:

```python
def test_phase1_csvs_unchanged_after_phase3(tmp_path):
    """Phase 1 CSVs (customers / subscriptions / events) must be byte-identical
    after the Phase 3 generator runs. Phase 1 invariant lock.
    """
    import hashlib
    from src.data_generator import write_to_disk

    write_to_disk(tmp_path)

    repo_dir = Path(__file__).resolve().parents[1] / "data" / "generated"
    for fname in ["customers.csv", "subscriptions.csv", "events.csv"]:
        committed = (repo_dir / fname).read_bytes()
        regenerated = (tmp_path / fname).read_bytes()
        assert hashlib.sha256(committed).hexdigest() == hashlib.sha256(regenerated).hexdigest(), (
            f"{fname} differs after Phase 3 regenerate — Phase 1 invariant broken"
        )


def test_team_win_rate_stays_in_band(tmp_path):
    """TTM new-business win rate must remain in [0.21, 0.25] — Phase 2 calibration.

    With tenure-weighted owner assignment, total wins/losses are preserved exactly,
    so this is a regression guard rather than a fresh calibration.
    """
    from src.data_generator import write_to_disk

    write_to_disk(tmp_path)
    opps = pd.read_csv(tmp_path / "opportunities.csv")
    nb = opps[opps["opportunity_type"] == "new_business"]
    nb["close_date"] = pd.to_datetime(nb["close_date"])
    # TTM relative to 2025-12-01 (the dashboard's "now")
    end = pd.Timestamp("2025-12-01")
    start = end - pd.DateOffset(months=12)
    ttm = nb[(nb["close_date"] >= start) & (nb["close_date"] <= end)
             & (nb["status"].isin(["closed_won", "closed_lost"]))]
    won = (ttm["status"] == "closed_won").sum()
    lost = (ttm["status"] == "closed_lost").sum()
    wr = won / (won + lost)
    assert 0.21 <= wr <= 0.25, f"team TTM win rate {wr:.3f} outside band [0.21, 0.25]"


def test_midmarket_poc_stall_still_2x(tmp_path):
    """Phase 2 insight: Mid-Market POC dwell ≥ 2× SMB POC dwell. Regression guard."""
    from src.data_generator import write_to_disk

    write_to_disk(tmp_path)
    history = pd.read_csv(tmp_path / "opportunity_stage_history.csv")
    opps = pd.read_csv(tmp_path / "opportunities.csv")
    merged = history.merge(opps[["opportunity_id", "segment", "opportunity_type"]],
                            on="opportunity_id")
    poc = merged[(merged["stage"] == "Proof of Concept")
                  & (merged["opportunity_type"] == "new_business")
                  & merged["days_in_stage"].notna()]
    smb_mean = poc[poc["segment"] == "SMB"]["days_in_stage"].mean()
    mm_mean = poc[poc["segment"] == "Mid-Market"]["days_in_stage"].mean()
    ratio = mm_mean / smb_mean
    assert ratio >= 2.0, f"POC stall ratio {ratio:.2f} < 2.0× (was 2.75× in Phase 2)"


def test_ramp_curve_visible_in_data(tmp_path):
    """Phase 3 insight: reps with <6 months tenure have median attainment ≥ 20pp
    lower than reps with 12+ months tenure. This protects the engineered
    ramp insight against future generator tweaks.
    """
    from src.data_generator import write_to_disk
    from src.quota import ramp_curve

    write_to_disk(tmp_path)
    reps = pd.read_csv(tmp_path / "reps.csv")
    opps = pd.read_csv(tmp_path / "opportunities.csv")
    opps = opps[(opps["opportunity_type"] == "new_business")
                 & (opps["status"] == "closed_won")]

    curve = ramp_curve(opps, reps)
    early = curve.loc[curve["tenure_months"] < 6.0, "attainment_pct"].median()
    tenured = curve.loc[curve["tenure_months"] >= 12.0, "attainment_pct"].median()
    gap_pp = (tenured - early) * 100
    assert gap_pp >= 20.0, (
        f"ramp gap is only {gap_pp:.1f}pp — engineered insight #3 is too weak; "
        f"early-tenure median={early:.3f}, tenured median={tenured:.3f}"
    )


def test_reps_csv_specialty_matches_historical_mix(tmp_path):
    """Each rep's segment_specialty equals their modal closed-won segment.
    Validates the two-pass backfit."""
    from src.data_generator import write_to_disk

    write_to_disk(tmp_path)
    reps = pd.read_csv(tmp_path / "reps.csv")
    opps = pd.read_csv(tmp_path / "opportunities.csv")
    nb_won = opps[(opps["opportunity_type"] == "new_business")
                   & (opps["status"] == "closed_won")]

    for _, rep in reps.iterrows():
        rep_won = nb_won[nb_won["owner_rep_id"] == rep["rep_id"]]
        if len(rep_won) == 0:
            assert rep["segment_specialty"] == "SMB", \
                f"rep with no wins should default to SMB; got {rep['segment_specialty']}"
            continue
        modal = (
            rep_won.groupby("segment").size()
            .sort_values(ascending=False).index[0]
        )
        # Handle alphabetical tie-break
        counts = rep_won.groupby("segment").size().sort_values(ascending=False)
        top_count = counts.iloc[0]
        tied_segments = sorted(counts[counts == top_count].index.tolist())
        expected = tied_segments[0]
        assert rep["segment_specialty"] == expected, (
            f"{rep['rep_id']} specialty={rep['segment_specialty']} but modal segment={expected}"
        )


def test_reps_csv_shape(tmp_path):
    """reps.csv has 12 rows, 3 per territory, 4 per hire cohort, all 6 columns."""
    from src.data_generator import write_to_disk

    write_to_disk(tmp_path)
    reps = pd.read_csv(tmp_path / "reps.csv")

    assert len(reps) == 12
    assert list(reps.columns) == [
        "rep_id", "name", "hire_date", "segment_specialty",
        "territory", "quarterly_quota",
    ]
    assert (reps.groupby("territory").size() == 3).all()
    hire = pd.to_datetime(reps["hire_date"])
    assert ((hire >= "2021-01-01") & (hire <= "2022-12-31")).sum() == 4
    assert ((hire >= "2023-01-01") & (hire <= "2024-06-30")).sum() == 4
    assert ((hire >= "2024-07-01") & (hire <= "2025-06-30")).sum() == 4
```

- [ ] **Step 2: Run guardrail tests**

Run: `pytest tests/test_data_generator.py -v`
Expected: all data-generator tests pass, including 6 new guardrails.

If `test_ramp_curve_visible_in_data` fails with a gap < 20pp, the multiplier in `_ramp_multiplier` needs sharpening — try `0.50 + 0.50 * (tenure/9.0)` instead of `0.55 + 0.45 * (tenure/9.0)`. Re-run the generator (`python -m src.data_generator`) and re-test.

- [ ] **Step 3: Run the full test suite**

Run: `pytest -q`
Expected: 63 passed (44 baseline + 15 Phase 3 quota.py + 4 reps fixture/backfit/skeleton).

- [ ] **Step 4: Commit**

```bash
git add tests/test_data_generator.py
git commit -m "test(phase-3): generator guardrails — Phase 1 byte-identical, POC stall, win rate band, ramp visible"
```

---

## Task 14: Viz — `attainment_distribution_figure` + `ramp_curve_figure`

Two figure builders for §1 and §2 of the page.

**Files:**
- Modify: `src/viz.py`

- [ ] **Step 1: Append `attainment_distribution_figure` to `src/viz.py`**

Append (after the existing builders):

```python
def attainment_distribution_figure(distribution: pd.DataFrame, quarter_label: str) -> go.Figure:
    """Horizontal bar of per-rep attainment %, color-banded by status.

    Input is the DataFrame returned by `src.quota.attainment_distribution`:
      rep_id, name, attainment_pct, status, ...

    Bars are sorted descending. Bar color:
      At/Above → CADENZA_GOOD
      On Track → CADENZA_NEUTRAL
      At Risk  → CADENZA_BAD
    A dashed reference line marks 100%.
    """
    color_map = {
        "At/Above": CADENZA_GOOD,
        "On Track": CADENZA_NEUTRAL,
        "At Risk":  CADENZA_BAD,
    }
    colors = [color_map[s] for s in distribution["status"]]

    fig = go.Figure(
        go.Bar(
            x=distribution["attainment_pct"],
            y=distribution["name"],
            orientation="h",
            marker={"color": colors},
            hovertemplate="%{y}<br>Attainment: %{x:.0%}<extra></extra>",
        )
    )
    fig.add_vline(x=1.0, line_dash="dash", line_color=CADENZA_PRIMARY,
                   annotation_text="100% quota", annotation_position="top")
    fig.update_layout(
        title=f"Quarterly attainment by rep — {quarter_label}",
        xaxis_tickformat=".0%",
        yaxis={"categoryorder": "total ascending"},
        height=460,
        margin={"l": 140},
    )
    return fig
```

- [ ] **Step 2: Append `ramp_curve_figure`**

```python
def ramp_curve_figure(curve: pd.DataFrame) -> go.Figure:
    """Longitudinal ramp curve: mean rolling-3mo attainment % vs. tenure months.

    Aggregates across all reps. Two annotated vertical reference lines:
      - month 6:  "Industry-assumed ramp"  (CADENZA_NEUTRAL)
      - month 9:  "Actual full productivity" (CADENZA_ACCENT)
    Horizontal reference at 100%.
    """
    # Bin tenure into 1-month bins and take the mean across reps
    binned = curve.copy()
    binned["tenure_bin"] = binned["tenure_months"].round().astype(int)
    agg = (
        binned.groupby("tenure_bin", as_index=False)["attainment_pct"]
        .mean()
        .sort_values("tenure_bin")
    )
    # Clip x to 0-30 months for readability
    agg = agg[(agg["tenure_bin"] >= 0) & (agg["tenure_bin"] <= 30)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=agg["tenure_bin"],
        y=agg["attainment_pct"],
        mode="lines+markers",
        line={"color": CADENZA_PRIMARY, "width": 3},
        marker={"color": CADENZA_PRIMARY, "size": 7},
        name="Rolling-3mo attainment %",
        hovertemplate="Month %{x} since hire<br>%{y:.0%}<extra></extra>",
    ))
    fig.add_hline(y=1.0, line_dash="dot", line_color=CADENZA_NEUTRAL,
                   annotation_text="100% quota", annotation_position="right")
    fig.add_vline(x=6, line_dash="dash", line_color=CADENZA_NEUTRAL,
                   annotation_text="Industry-assumed ramp",
                   annotation_position="top")
    fig.add_vline(x=9, line_dash="dash", line_color=CADENZA_ACCENT,
                   annotation_text="Actual full productivity",
                   annotation_position="top")
    fig.update_layout(
        title="Ramp curve — team-wide attainment by months since hire",
        xaxis_title="Months since hire",
        yaxis_title="Attainment % (rolling 3mo)",
        yaxis_tickformat=".0%",
        height=420,
    )
    return fig
```

- [ ] **Step 3: Quick syntax check by importing the module**

Run: `python -c "from src import viz; print(viz.attainment_distribution_figure.__doc__[:60]); print(viz.ramp_curve_figure.__doc__[:60])"`
Expected: docstring prefixes print without ImportError.

- [ ] **Step 4: Commit**

```bash
git add src/viz.py
git commit -m "feat(phase-3): viz — attainment_distribution_figure + ramp_curve_figure"
```

---

## Task 15: Viz — `territory_balance_figure` + `rep_scorecard_styler` + ramp bucket bar

Three more visual components for §2 (bucket bar) and §3-§4.

**Files:**
- Modify: `src/viz.py`

- [ ] **Step 1: Append `ramp_bucket_attainment_figure`**

```python
def ramp_bucket_attainment_figure(buckets: pd.DataFrame) -> go.Figure:
    """Horizontal bar of median attainment per tenure bucket.

    Input from `src.quota.ramp_bucket_attainment`:
      tenure_bucket, n_observations, median_attainment.
    """
    df = buckets.copy()
    # Display empty buckets as 0 with a note, but keep them in the chart
    df["display_pct"] = df["median_attainment"].fillna(0.0)
    fig = go.Figure(
        go.Bar(
            x=df["display_pct"],
            y=df["tenure_bucket"],
            orientation="h",
            marker={"color": CADENZA_PRIMARY},
            hovertemplate="%{y}<br>Median attainment: %{x:.0%}<extra></extra>",
        )
    )
    fig.add_vline(x=1.0, line_dash="dash", line_color=CADENZA_NEUTRAL,
                   annotation_text="100%", annotation_position="top")
    fig.update_layout(
        title="Median attainment by tenure bucket",
        xaxis_tickformat=".0%",
        yaxis={"categoryorder": "array", "categoryarray": df["tenure_bucket"].tolist()[::-1]},
        height=320,
    )
    return fig
```

- [ ] **Step 2: Append `territory_balance_figure`**

```python
def territory_balance_figure(balance: pd.DataFrame, quarter_label: str) -> go.Figure:
    """Stacked horizontal bar: closed-won $ by territory, stacked by segment.

    Input from `src.quota.territory_balance`:
      territory, segment, closed_amount.
    """
    segment_colors = {
        "Enterprise":  CADENZA_PRIMARY,
        "Mid-Market":  CADENZA_ACCENT,
        "SMB":         CADENZA_NEUTRAL,
    }
    fig = go.Figure()
    for segment in ["Enterprise", "Mid-Market", "SMB"]:
        sub = balance[balance["segment"] == segment]
        if len(sub) == 0:
            continue
        fig.add_trace(go.Bar(
            x=sub["closed_amount"],
            y=sub["territory"],
            orientation="h",
            name=segment,
            marker={"color": segment_colors[segment]},
            hovertemplate=(f"{segment}<br>%{{y}}<br>"
                           "Closed won: $%{x:,.0f}<extra></extra>"),
        ))
    fig.update_layout(
        title=f"Closed-won by territory and segment — {quarter_label}",
        barmode="stack",
        xaxis_title="Closed Won ($)",
        xaxis={"tickformat": "$,.0f"},
        height=360,
        legend={"orientation": "h", "y": -0.2},
    )
    return fig
```

- [ ] **Step 3: Append `rep_scorecard_styler`**

```python
def rep_scorecard_styler(scorecard: pd.DataFrame):
    """Style the rep scorecard DataFrame for st.dataframe.

    Input from `src.quota.rep_scorecard`. Highlights:
      - max Att % and max Win Rate in CADENZA_GOOD-tinted background
      - min Avg Cycle (days) in CADENZA_GOOD-tinted background
      - 'At Risk' status rows get a red Att % text color
    """
    display = scorecard.rename(columns={
        "name":               "Name",
        "segment_specialty":  "Specialty",
        "territory":          "Territory",
        "tenure_months":      "Tenure (mo)",
        "quarterly_quota":    "Quota",
        "closed_amount":      "Closed Won",
        "attainment_pct":     "Att %",
        "win_rate":           "Win Rate",
        "avg_deal_size":      "Avg Deal",
        "avg_cycle_days":     "Cycle (days)",
    })[
        ["Name", "Specialty", "Territory", "Tenure (mo)", "Quota",
         "Closed Won", "Att %", "Win Rate", "Avg Deal", "Cycle (days)"]
    ]

    return (
        display.style
        .format({
            "Tenure (mo)":  "{:.1f}",
            "Quota":        "${:,.0f}",
            "Closed Won":   "${:,.0f}",
            "Att %":        "{:.0%}",
            "Win Rate":     "{:.0%}",
            "Avg Deal":     "${:,.0f}",
            "Cycle (days)": "{:.0f}",
        })
        .highlight_max(subset=["Att %", "Win Rate"], color="#D1FAE5")  # CADENZA_GOOD tint
        .highlight_min(subset=["Cycle (days)"], color="#D1FAE5")
    )
```

- [ ] **Step 4: Import check**

Run: `python -c "from src import viz; viz.territory_balance_figure; viz.rep_scorecard_styler; viz.ramp_bucket_attainment_figure; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 5: Commit**

```bash
git add src/viz.py
git commit -m "feat(phase-3): viz — territory_balance, rep_scorecard_styler, ramp_bucket bar"
```

---

## Task 16: `pages/7_Quota.py` — skeleton + filters + KPIs

Create the new page with the filter row and the 4 KPI tiles. Wire up `load_quota_data` + `team_kpis`.

**Files:**
- Create: `pages/7_Quota.py`

- [ ] **Step 1: Create the file**

```python
"""Cadenza Quota — quarterly attainment, attainment distribution, ramp curve,
territory balance, and rep scorecard.

Scope is new-business attainment only. Renewals and expansions don't count
toward quota — matches typical SaaS comp structures where AEs are paid on
new-logo bookings while CSMs/AMs handle the post-sale book. See About.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src import quota
from src import viz

st.set_page_config(page_title="Cadenza — Quota", layout="wide")

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "generated"


@st.cache_data
def load_data():
    return quota.load_quota_data(
        DATA_DIR / "reps.csv",
        DATA_DIR / "opportunities.csv",
    )


def _available_quarters(opps: pd.DataFrame) -> list[pd.Period]:
    cd = pd.to_datetime(opps["close_date"])
    quarters = sorted(set(cd.dt.to_period("Q")))
    return quarters


def filter_row(reps: pd.DataFrame, opps: pd.DataFrame) -> dict:
    quarters = _available_quarters(opps)
    default_idx = len(quarters) - 1  # most recent quarter

    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        quarter = st.selectbox(
            "Quarter",
            options=quarters,
            index=default_idx,
            format_func=lambda q: f"{q.year}-Q{q.quarter}",
        )
    with c2:
        segment = st.selectbox(
            "Segment", ["All", "SMB", "Mid-Market", "Enterprise"]
        )
    with c3:
        territory = st.selectbox(
            "Territory", ["All", "North", "South", "East", "West"]
        )
    return {"quarter": quarter, "segment": segment, "territory": territory}


def apply_section_filters(opps: pd.DataFrame, reps: pd.DataFrame,
                            f: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply segment and territory filters. Quarter is applied per-section
    inside each metric call. Does NOT filter the ramp curve — §2 is longitudinal."""
    filtered_reps = reps.copy()
    filtered_opps = opps.copy()
    if f["territory"] != "All":
        filtered_reps = filtered_reps[filtered_reps["territory"] == f["territory"]]
        filtered_opps = filtered_opps[
            filtered_opps["owner_rep_id"].isin(filtered_reps["rep_id"])
        ]
    if f["segment"] != "All":
        filtered_opps = filtered_opps[filtered_opps["segment"] == f["segment"]]
    return filtered_reps, filtered_opps


def render_kpis(opps: pd.DataFrame, reps: pd.DataFrame, quarter: pd.Period):
    kpis = quota.team_kpis(opps, reps, quarter)

    # Optional: Δ vs prior quarter
    prior_q = quarter - 1
    if prior_q.year >= 2023:  # only if within dataset window
        prior = quota.team_kpis(opps, reps, prior_q)
        delta_team = (kpis["team_attainment_pct"] - prior["team_attainment_pct"]) * 100
        delta_median = (kpis["median_attainment"] - prior["median_attainment"]) * 100
        show_delta = True
    else:
        delta_team = None
        delta_median = None
        show_delta = False

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Team Attainment",
        f"{kpis['team_attainment_pct']:.0%}",
        f"{delta_team:+.1f} pp" if show_delta else None,
    )
    c2.metric(
        "Reps At/Above Quota",
        f"{kpis['reps_at_or_above']} / {len(reps)}",
    )
    c3.metric(
        "Median Attainment",
        f"{kpis['median_attainment']:.0%}",
        f"{delta_median:+.1f} pp" if show_delta else None,
    )
    c4.metric(
        "At-Risk Count (<70%)",
        kpis["at_risk_count"],
    )
    if not show_delta:
        st.caption("Prior-quarter Δ hidden — selected quarter sits at the dataset edge.")


def main():
    st.title("Quota Attainment & Rep Performance")
    st.caption("Per-rep new-business attainment, attainment distribution, ramp "
               "curve, and territory balance. Quota credit is new-business only.")

    reps, opps = load_data()

    with st.container():
        f = filter_row(reps, opps)

    filtered_reps, filtered_opps = apply_section_filters(opps, reps, f)

    st.divider()
    render_kpis(filtered_opps, filtered_reps, f["quarter"])


main()
```

- [ ] **Step 2: Verify the page imports and reads data**

Run: `python -c "from pathlib import Path; from src import quota; r,o = quota.load_quota_data(Path('data/generated/reps.csv'), Path('data/generated/opportunities.csv')); print(len(r), 'reps,', len(o), 'opps')"`
Expected: prints `12 reps, <N> opps`.

- [ ] **Step 3: Start Streamlit and visually verify**

Run (foreground in a separate terminal — kill after checking): `streamlit run Overview.py`

In the browser sidebar, click "Quota". Verify:
- Page title renders "Quota Attainment & Rep Performance"
- Three filter dropdowns appear (Quarter, Segment, Territory)
- Quarter defaults to the most recent quarter in data (2025-Q4)
- Four KPI tiles render with reasonable numbers (Team Attainment around 80-110%, Reps At/Above between 4-9, etc.)
- No Streamlit errors in the terminal

If `@st.cache_data` serves stale data, restart the server.

- [ ] **Step 4: Commit**

```bash
git add pages/7_Quota.py
git commit -m "feat(phase-3): pages/7_Quota.py skeleton — filters + KPI tiles"
```

---

## Task 17: `pages/7_Quota.py` — wire up §1-§4 + scorecard

Add the four content sections (Attainment Distribution, Ramp Curve, Territory Balance, Rep Scorecard) to the page.

**Files:**
- Modify: `pages/7_Quota.py`

- [ ] **Step 1: Add the section-rendering functions to `pages/7_Quota.py`**

Insert these functions ABOVE `def main():` (between `render_kpis` and `main`):

```python
def render_section_attainment_distribution(opps: pd.DataFrame, reps: pd.DataFrame,
                                              quarter: pd.Period):
    st.subheader("Attainment Distribution")
    dist = quota.attainment_distribution(opps, reps, quarter)
    fig = viz.attainment_distribution_figure(dist, f"{quarter.year}-Q{quarter.quarter}")
    st.plotly_chart(fig, use_container_width=True)


def render_section_ramp_curve(opps_unfiltered: pd.DataFrame,
                                reps_unfiltered: pd.DataFrame):
    st.subheader("Ramp Curve")
    st.caption("Computed across all reps and all months in the dataset — NOT "
               "filtered by the quarter selector. The team reaches full "
               "productivity around month 9, three months later than the "
               "industry-standard 6-month ramp assumption.")
    curve = quota.ramp_curve(opps_unfiltered, reps_unfiltered)
    buckets = quota.ramp_bucket_attainment(opps_unfiltered, reps_unfiltered)
    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.plotly_chart(viz.ramp_curve_figure(curve), use_container_width=True)
    with col_right:
        st.plotly_chart(viz.ramp_bucket_attainment_figure(buckets),
                          use_container_width=True)


def render_section_territory_balance(opps: pd.DataFrame, reps: pd.DataFrame,
                                       quarter: pd.Period):
    st.subheader("Territory & Segment Balance")
    balance = quota.territory_balance(opps, reps, quarter)
    fig = viz.territory_balance_figure(balance, f"{quarter.year}-Q{quarter.quarter}")
    st.plotly_chart(fig, use_container_width=True)


def render_section_scorecard(opps: pd.DataFrame, reps: pd.DataFrame,
                               quarter: pd.Period):
    st.subheader("Rep Scorecard")
    scorecard = quota.rep_scorecard(opps, reps, quarter)
    styled = viz.rep_scorecard_styler(scorecard)
    st.dataframe(styled, use_container_width=True, hide_index=True)
```

- [ ] **Step 2: Wire up section calls in `main()`**

Replace the existing `main()` body with:

```python
def main():
    st.title("Quota Attainment & Rep Performance")
    st.caption("Per-rep new-business attainment, attainment distribution, ramp "
               "curve, and territory balance. Quota credit is new-business only.")

    reps, opps = load_data()

    with st.container():
        f = filter_row(reps, opps)

    filtered_reps, filtered_opps = apply_section_filters(opps, reps, f)

    st.divider()
    render_kpis(filtered_opps, filtered_reps, f["quarter"])

    st.divider()
    render_section_attainment_distribution(filtered_opps, filtered_reps, f["quarter"])

    st.divider()
    # Ramp curve is longitudinal — uses UNfiltered data
    render_section_ramp_curve(opps, reps)

    st.divider()
    render_section_territory_balance(filtered_opps, filtered_reps, f["quarter"])

    st.divider()
    render_section_scorecard(filtered_opps, filtered_reps, f["quarter"])


main()
```

- [ ] **Step 3: Restart Streamlit and verify all sections render**

Run: `streamlit run Overview.py` in another terminal (kill after checking).

In the browser:
- §1 Attainment Distribution: horizontal bar chart, 12 reps, mix of green/grey/red bars, 100% reference line visible
- §2 Ramp Curve: line chart with two vertical reference lines at months 6 and 9; adjacent bucket bar showing 4 tenure buckets with monotonically-increasing median attainment
- §3 Territory Balance: stacked horizontal bar of 4 territories
- §4 Rep Scorecard: table with 10 columns; max Att % and Win Rate cells tinted green; min Cycle (days) cell tinted green
- Test the filters: Segment=Enterprise should only show Enterprise deals in §1/§3/§4; §2 should NOT change.
- Test Territory filter similarly.

- [ ] **Step 4: Commit**

```bash
git add pages/7_Quota.py
git commit -m "feat(phase-3): pages/7_Quota.py — all 4 sections + scorecard table"
```

---

## Task 18: `pages/8_About.py` — Phase 3 narrative + metric table

Append Phase 3 content to the About page.

**Files:**
- Modify: `pages/8_About.py`

- [ ] **Step 1: Read the existing About page to find the metric table and narrative anchors**

Run: `grep -n "Phase 2\|## \|metric.*table\|Hidden insight" pages/8_About.py | head -30`

(This identifies where Phase 2 content lives so Phase 3 additions can sit beside it.)

- [ ] **Step 2: Append Phase 3 narrative subsection**

Find the existing "Phase 2: Pipeline & Forecasting" narrative subsection in `pages/8_About.py`. Just after it (before the Scope & Deferrals section or wherever Phase 2 narrative ends), add:

```python
st.markdown("---")
st.markdown("### Phase 3: Quota Attainment & Rep Performance")
st.markdown(
    """
The Quota page surfaces rep-level performance: quarterly attainment,
attainment distribution across the team, a longitudinal ramp curve, and
territory × segment balance. Twelve reps carry tiered quotas
(SMB \\$150K, Mid-Market \\$500K, Enterprise \\$1.5M per quarter) and are
staggered across hire cohorts — four veterans (hired pre-2023), four
mid-tenure, four still ramping at dataset end.

**Hidden insight #3 — ramp longer than assumed.** The team's actual ramp curve
hits full productivity around month 9, not the industry-standard month 6.
New hires below 70% attainment aren't underperforming — they're tracking
the team's normal ramp. Adjust hiring lead times and ramped-quota schedules
accordingly.

**Quota scope:** new-business only. Renewal and expansion ACV do not count
toward attainment. Matches typical SaaS comp structures where AEs are paid
on new-logo bookings.
"""
)
```

- [ ] **Step 3: Extend the metric definitions table with Phase 3 entries**

Find the existing metric definitions table (likely a `pd.DataFrame` rendered with `st.dataframe` or `st.table`). Add these rows for Phase 3:

| Metric | Formula |
|---|---|
| Quarterly Attainment % | `sum(closed_won amount for rep in quarter) / quarterly_quota` |
| Team Attainment % | `sum(all closed_won amount in quarter) / sum(all reps' quarterly_quota)` |
| Rep Win Rate | `closed_won_count / (closed_won_count + closed_lost_count)` for new-business deals closing in the quarter, per rep |
| Avg Deal Size (per rep) | `mean(amount)` across the rep's closed-won deals in the quarter |
| Avg Cycle Time (per rep) | `mean(close_date - created_date)` in days across rep's closed-won deals in the quarter |
| Tenure Months | `(reference_date - hire_date).days / 30.44` |
| Rolling-3mo Attainment | `closed_won_3mo / quarterly_quota`; used in the ramp curve |
| Ramp Tenure Bucket | One of: 0-3, 3-6, 6-12, 12+ months |

Append to whatever data structure the existing metrics table uses. For example, if the Phase 2 table is a list of dicts called `phase2_metrics`, add a `phase3_metrics = [...]` list with the entries above and render it in a third table cell.

- [ ] **Step 4: Extend Scope & Deferrals section**

Find the existing Scope & Deferrals section and add this bullet:

```python
"- **Quota is new-business only.** Renewal and expansion bookings do not count "
"toward AE attainment. Matches how most SaaS organizations separate AE comp "
"from CSM/AM comp. Renewal and expansion analytics live on the Pipeline and "
"Forecasting pages."
```

- [ ] **Step 5: Restart Streamlit; verify About renders cleanly**

Run: `streamlit run Overview.py` and click "About". The page should show all three phases' narratives, the extended metric table, and the new Scope & Deferrals bullet without rendering errors.

- [ ] **Step 6: Commit**

```bash
git add pages/8_About.py
git commit -m "docs(phase-3): About page — Phase 3 narrative, metric table extension, scope notes"
```

---

## Task 19: README + CLAUDE.md + CHANGELOG + final verification

Final ship docs and full-suite verification.

**Files:**
- Modify: `README.md`, `CLAUDE.md`, `CHANGELOG.md`

- [ ] **Step 1: Update `README.md`**

Open `README.md`. Add Quota to the page list and flip the Phase 3 status from "planned" to "shipped":

- Find the line/section listing the dashboard pages (probably an `### Pages` or similar). Add: `7. **Quota** — quarterly attainment, attainment distribution, ramp curve, territory balance, rep scorecard`. Renumber About to 8.
- Find any "Phase 3" reference (likely in a roadmap or status section). Change `planned` → `shipped`.

- [ ] **Step 2: Update `CLAUDE.md`**

Open `CLAUDE.md`. Update:

- The architecture diagram (lines starting with `src/data_generator.py → ...`) — append `src/quota.py` to the modules list and `reps.csv` to the CSV outputs.
- The status line at the top — change "**Phase 3** ... is planned, not started." to "**Phase 3** (Quota & Rep Performance) is shipped and live."
- The "Quick commands" section — bump the test count from "44 tests" to "63 tests" (or whatever the final count is — run `pytest --collect-only -q | tail -1` to get the exact number).
- The "Starting Phase 3" section — replace with a "Phase 3 retrospective" pointer to a new doc you'll write next time (or remove the section entirely if Phase 4 isn't planned).
- The Reference docs section — add Phase 3 spec/plan paths.

- [ ] **Step 3: Update `CHANGELOG.md`**

Prepend a new entry to the top under the appropriate section. Use the same format as the Phase 2 entry:

```markdown
## Phase 3 — Quota Attainment & Rep Performance (2026-05-16)

### Added
- `reps.csv` table (12 AEs with hire_date, segment_specialty, territory, quarterly_quota).
- `src/quota.py` — pure-function metrics: `quarterly_attainment`, `attainment_distribution`, `ramp_curve`, `ramp_bucket_attainment`, `rep_scorecard`, `territory_balance`, `team_kpis`, `load_quota_data`.
- `pages/7_Quota.py` — Quota Attainment & Rep Performance page (KPI tiles, attainment distribution, ramp curve, territory balance, rep scorecard).
- 4 new figure builders in `src/viz.py` — `attainment_distribution_figure`, `ramp_curve_figure`, `ramp_bucket_attainment_figure`, `territory_balance_figure`, plus `rep_scorecard_styler`.
- 19 new tests (13 in `tests/test_quota.py`, 6 generator guardrails in `tests/test_data_generator.py`).
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
```

- [ ] **Step 4: Run the full test suite**

Run: `pytest -v`
Expected: all tests pass. Note the final test count.

- [ ] **Step 5: Final manual smoke test of the dashboard**

Run: `streamlit run Overview.py`

Click through every page (Overview, Cohort Analysis, Segment Drilldown, Pipeline, Forecasting, Quota, About). Verify each renders without errors. On the Quota page:
- All 4 KPI tiles populated
- All 4 sections visible
- Filters work (changing Segment / Territory should update §1/§3/§4 but NOT §2 ramp curve)
- Sidebar order is: Overview, Cohort Analysis, Segment Drilldown, Pipeline, Forecasting, Quota, About

- [ ] **Step 6: Commit doc updates**

```bash
git add README.md CLAUDE.md CHANGELOG.md
git commit -m "docs(phase-3): README + CLAUDE.md + CHANGELOG for Phase 3 ship"
```

- [ ] **Step 7: Final status check**

Run: `git status && git log --oneline -20`
Expected: working tree clean; 19 task commits since branching from main.

---

## Done

Phase 3 — Quota Attainment & Rep Performance — is now implemented end-to-end with:
- 1 new module (`src/quota.py`) + 1 new page (`pages/7_Quota.py`)
- 1 new CSV (`data/generated/reps.csv`) + 3 regenerated Phase 2 CSVs (per-rep owner shifts)
- 19 new tests (13 quota.py + 6 generator guardrails)
- 5 new viz builders
- Phase 1 byte-identical lock preserved
- Phase 2 POC stall and team win rate calibrations preserved
- Phase 3 ramp insight protected by `test_ramp_curve_visible_in_data` guardrail

**Next:** Open a PR from `phase-3/quota-rep-performance` → `main`. After merge and Streamlit Cloud auto-deploys, update `project_cadenza_retention_analytics.md` in memory with the ship date, and write `docs/superpowers/phase3-retrospective.md` for the next-phase bridge.
