# Cadenza Phase 2 — Pipeline & Forecasting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the shipped Cadenza Retention Analytics app with two new Streamlit pages (Pipeline, Forecasting) backed by pure-function pandas modules, driven by synthetic opportunity / stage-history / snapshot data that links to Phase 1 customers, encoding a hidden "Mid-Market POC stall" insight.

**Architecture:** Additive to Phase 1. Generator gets new functions appended (Phase 1 generation untouched, byte-identical). Two new metric modules (`src/pipeline.py`, `src/forecast.py`) as pure functions tested against hand-built fixtures, same pattern as Phase 1's `metrics.py`. Two new Streamlit pages (`pages/5_Pipeline.py`, `pages/6_Forecasting.py`) plus a single Phase 1 file rename (`4_About.py` → `7_About.py`) so the sidebar order stays clean. No new dependencies.

**Tech Stack:** Python 3.12, pandas, numpy, plotly, streamlit, pytest (all already in Phase 1).

**Spec reference:** `docs/superpowers/specs/2026-05-15-cadenza-phase2-pipeline-forecasting-design.md`

---

## File Structure

**New files:**
```
src/pipeline.py                     # Pure functions: pipeline metrics
src/forecast.py                     # Pure functions: forecast metrics
pages/5_Pipeline.py                 # Pipeline page (Streamlit)
pages/6_Forecasting.py              # Forecasting page (Streamlit)
tests/test_pipeline.py              # Tests for src/pipeline.py
tests/test_forecast.py              # Tests for src/forecast.py
data/generated/opportunities.csv             # Generated, committed
data/generated/opportunity_stage_history.csv # Generated, committed
data/generated/pipeline_snapshots.csv        # Generated, committed
```

**Modified files (append-only, Phase 1 contents preserved):**
```
src/data_generator.py               # New generator functions appended
src/viz.py                          # New figure builders appended
tests/conftest.py                   # New fixtures appended
tests/test_data_generator.py        # Two new tests appended
README.md                           # Phase 2 pages added to list
CLAUDE.md                           # Architecture diagram updated
CHANGELOG.md                        # Phase 2 entry on ship
```

**Renamed (1 file, cosmetic for sidebar ordering, content extended):**
```
pages/4_About.py → pages/7_About.py
```

**Untouched:**
```
Overview.py
pages/2_Cohort_Analysis.py
pages/3_Segment_Drilldown.py
src/metrics.py
src/cohorts.py
data/generated/customers.csv         # Byte-identical (enforced by test)
data/generated/subscriptions.csv     # Byte-identical
data/generated/events.csv            # Byte-identical
requirements.txt                     # No new dependencies
.streamlit/config.toml
```

---

## Task 1: Phase 1 file rename — `4_About.py` → `7_About.py`

Smallest atomic, lowest-risk Phase 1 touch. Done first so we don't forget. Streamlit derives the sidebar label from filename minus the `N_` prefix, so rename preserves URL slug (`/About`) and label.

**Files:**
- Rename: `pages/4_About.py` → `pages/7_About.py`

- [ ] **Step 1: Rename the file**

```bash
git mv pages/4_About.py pages/7_About.py
```

- [ ] **Step 2: Verify existing Phase 1 tests still pass**

```bash
source .venv/bin/activate
pytest -v
```
Expected: 20 tests pass.

- [ ] **Step 3: Commit**

```bash
git add pages/
git commit -m "chore: rename 4_About.py to 7_About.py to keep About last in sidebar after Phase 2 pages"
```

---

## Task 2: Hand-built fixtures — `tiny_opportunities` and `tiny_stage_history`

Adds two fixtures to `tests/conftest.py` (Phase 1 fixtures stay). These are the contract for every metric test in Tasks 4–11.

**Files:**
- Modify: `tests/conftest.py` (append)

- [ ] **Step 1: Append `tiny_opportunities` and `tiny_stage_history` fixtures**

Append to the end of `tests/conftest.py`:

```python
@pytest.fixture
def tiny_opportunities() -> pd.DataFrame:
    """8 hand-crafted opps spanning 3 opp_types, all segments, win/loss outcomes.

    Hand-calculated answers (verified in tests):
      total_pipeline(as_of='2024-04-01')  = 300_000  (OPP-2 + OPP-3 + OPP-8)
      weighted_pipeline(as_of='2024-04-01') = 158_000
        = 0.40*60_000 + 0.65*200_000 + 0.10*40_000
      pipeline_coverage(target=100_000, as_of='2024-04-01') = 3.0
      win_rate(start='2024-01-01', end='2024-04-01')        = 0.60  (3 won / 5 closed)
      avg_sales_cycle_days(start='2024-01-01', end='2024-04-01') = 70
        = mean(90, 60, 60) for OPP-1, OPP-5, OPP-7

    Stage probabilities used:
      Discovery 0.10, Qualification 0.20, POC 0.40, Negotiation 0.65
      Renewal Discussion 0.75, Renewal Negotiation 0.90
      Expansion Discussion 0.80
    """
    rows = [
        # new_business — won
        {"opportunity_id": "OPP-1", "customer_id": "CUST-1", "account_name": "Apex Labs",
         "segment": "SMB", "acquisition_channel": "Outbound Sales", "owner_rep_id": "REP-01",
         "opportunity_type": "new_business",
         "created_date": "2024-01-01", "close_date": "2024-03-31", "amount": 12_000.0,
         "current_stage": "Closed Won", "status": "closed_won"},
        # new_business — open in POC (Mid-Market — part of the engineered stall)
        {"opportunity_id": "OPP-2", "customer_id": None, "account_name": "Quantum Works",
         "segment": "Mid-Market", "acquisition_channel": "Inbound Marketing", "owner_rep_id": "REP-02",
         "opportunity_type": "new_business",
         "created_date": "2024-02-01", "close_date": "2024-06-01", "amount": 60_000.0,
         "current_stage": "Proof of Concept", "status": "open"},
        # new_business — open in Negotiation
        {"opportunity_id": "OPP-3", "customer_id": None, "account_name": "Helix Systems",
         "segment": "Enterprise", "acquisition_channel": "Partner Referral", "owner_rep_id": "REP-03",
         "opportunity_type": "new_business",
         "created_date": "2024-01-15", "close_date": "2024-05-15", "amount": 200_000.0,
         "current_stage": "Negotiation", "status": "open"},
        # new_business — lost (died in POC)
        {"opportunity_id": "OPP-4", "customer_id": None, "account_name": "Vector Logic",
         "segment": "SMB", "acquisition_channel": "Outbound Sales", "owner_rep_id": "REP-01",
         "opportunity_type": "new_business",
         "created_date": "2024-01-01", "close_date": "2024-02-15", "amount": 8_000.0,
         "current_stage": "Closed Lost", "status": "closed_lost"},
        # renewal — won
        {"opportunity_id": "OPP-5", "customer_id": "CUST-100", "account_name": "Lattice Group",
         "segment": "Mid-Market", "acquisition_channel": "Inbound Marketing", "owner_rep_id": "REP-04",
         "opportunity_type": "renewal",
         "created_date": "2024-01-01", "close_date": "2024-03-01", "amount": 30_000.0,
         "current_stage": "Closed Won", "status": "closed_won"},
        # renewal — lost
        {"opportunity_id": "OPP-6", "customer_id": "CUST-200", "account_name": "Beacon Dynamics",
         "segment": "SMB", "acquisition_channel": "Outbound Sales", "owner_rep_id": "REP-05",
         "opportunity_type": "renewal",
         "created_date": "2024-01-01", "close_date": "2024-02-20", "amount": 10_000.0,
         "current_stage": "Closed Lost", "status": "closed_lost"},
        # expansion — won
        {"opportunity_id": "OPP-7", "customer_id": "CUST-300", "account_name": "Stratus Cloud",
         "segment": "Enterprise", "acquisition_channel": "Partner Referral", "owner_rep_id": "REP-06",
         "opportunity_type": "expansion",
         "created_date": "2024-01-15", "close_date": "2024-03-15", "amount": 24_000.0,
         "current_stage": "Closed Won", "status": "closed_won"},
        # new_business — open in Discovery (Mid-Market)
        {"opportunity_id": "OPP-8", "customer_id": None, "account_name": "Cobalt Industries",
         "segment": "Mid-Market", "acquisition_channel": "Inbound Marketing", "owner_rep_id": "REP-02",
         "opportunity_type": "new_business",
         "created_date": "2024-02-15", "close_date": "2024-08-15", "amount": 40_000.0,
         "current_stage": "Discovery", "status": "open"},
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def tiny_stage_history() -> pd.DataFrame:
    """Stage transitions for the new_business deals in tiny_opportunities.

    Hand-calculated answers (verified in tests):
      avg_days_in_stage('Proof of Concept', '2024-01-01', '2024-04-01) = 20.0
        = mean(14, 25, 21) for OPP-1, OPP-3, OPP-4
      avg_days_in_stage('Negotiation', '2024-01-01', '2024-04-01)      = 59.0
        = OPP-1 only (entered+exited Negotiation in window)
      stage_conversion('Proof of Concept', 'Negotiation',
                       '2024-01-01', '2024-04-01)                       ≈ 0.667
        = of {OPP-1, OPP-3, OPP-4} that exited POC,
          {OPP-1, OPP-3} reached Negotiation -> 2/3
      aging_deals(as_of='2024-04-01', threshold=30) returns {OPP-2, OPP-8}
        OPP-2: 46 days in POC
        OPP-3: 17 days in Negotiation (not aging)
        OPP-8: 46 days in Discovery
    """
    rows = [
        # OPP-1 walked all 4 NB stages, won
        {"opportunity_id": "OPP-1", "stage": "Discovery",        "entered_date": "2024-01-01", "exited_date": "2024-01-08", "days_in_stage": 7},
        {"opportunity_id": "OPP-1", "stage": "Qualification",    "entered_date": "2024-01-08", "exited_date": "2024-01-18", "days_in_stage": 10},
        {"opportunity_id": "OPP-1", "stage": "Proof of Concept", "entered_date": "2024-01-18", "exited_date": "2024-02-01", "days_in_stage": 14},
        {"opportunity_id": "OPP-1", "stage": "Negotiation",      "entered_date": "2024-02-01", "exited_date": "2024-03-31", "days_in_stage": 59},
        # OPP-2 — open, currently in POC
        {"opportunity_id": "OPP-2", "stage": "Discovery",        "entered_date": "2024-02-01", "exited_date": "2024-02-08", "days_in_stage": 7},
        {"opportunity_id": "OPP-2", "stage": "Qualification",    "entered_date": "2024-02-08", "exited_date": "2024-02-15", "days_in_stage": 7},
        {"opportunity_id": "OPP-2", "stage": "Proof of Concept", "entered_date": "2024-02-15", "exited_date": None,         "days_in_stage": None},
        # OPP-3 — open, walked through POC, currently in Negotiation
        {"opportunity_id": "OPP-3", "stage": "Discovery",        "entered_date": "2024-01-15", "exited_date": "2024-01-29", "days_in_stage": 14},
        {"opportunity_id": "OPP-3", "stage": "Qualification",    "entered_date": "2024-01-29", "exited_date": "2024-02-18", "days_in_stage": 20},
        {"opportunity_id": "OPP-3", "stage": "Proof of Concept", "entered_date": "2024-02-18", "exited_date": "2024-03-15", "days_in_stage": 25},
        {"opportunity_id": "OPP-3", "stage": "Negotiation",      "entered_date": "2024-03-15", "exited_date": None,         "days_in_stage": None},
        # OPP-4 — lost in POC
        {"opportunity_id": "OPP-4", "stage": "Discovery",        "entered_date": "2024-01-01", "exited_date": "2024-01-15", "days_in_stage": 14},
        {"opportunity_id": "OPP-4", "stage": "Qualification",    "entered_date": "2024-01-15", "exited_date": "2024-01-25", "days_in_stage": 10},
        {"opportunity_id": "OPP-4", "stage": "Proof of Concept", "entered_date": "2024-01-25", "exited_date": "2024-02-15", "days_in_stage": 21},
        # OPP-8 — open, in Discovery
        {"opportunity_id": "OPP-8", "stage": "Discovery",        "entered_date": "2024-02-15", "exited_date": None,         "days_in_stage": None},
    ]
    return pd.DataFrame(rows)
```

- [ ] **Step 2: Run the existing test suite to confirm no breakage**

```bash
pytest -v
```
Expected: 20 tests still pass. New fixtures are not referenced yet so they have no effect.

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add tiny_opportunities and tiny_stage_history fixtures for Phase 2 metric tests"
```

---

## Task 3: Hand-built `tiny_snapshots` fixture + empty pipeline/forecast modules

**Files:**
- Modify: `tests/conftest.py` (append)
- Create: `src/pipeline.py` (empty skeleton)
- Create: `src/forecast.py` (empty skeleton)

- [ ] **Step 1: Append `tiny_snapshots` fixture**

Append to the end of `tests/conftest.py`:

```python
@pytest.fixture
def tiny_snapshots() -> pd.DataFrame:
    """Quarterly pipeline snapshots for forecast metric tests.

    Two snapshot dates, drawing from the same OPP-N deals defined in
    tiny_opportunities.

    Hand-calculated answers:
      forecast_buckets(snapshot_date='2024-03-01') =
          {'commit': 12_000, 'best_case': 260_000, 'pipeline': 40_000}
        Commit    = OPP-1 (Negotiation)         = 12_000
        Best Case = OPP-2 + OPP-3 (POC)         = 60_000 + 200_000
        Pipeline  = OPP-8 (Discovery)           = 40_000

      forecast_accuracy(snapshot_date='2024-03-01') ≈ 1.755
        weighted_at_snapshot = 0.65*12_000 + 0.40*60_000 + 0.40*200_000 + 0.10*40_000
                             = 7_800 + 24_000 + 80_000 + 4_000 = 115_800
        actual closed_won in [2024-03-01, 2024-06-01):
          OPP-1 (12_000) + OPP-5 (30_000) + OPP-7 (24_000) = 66_000
        accuracy = 115_800 / 66_000 ≈ 1.755
    """
    rows = [
        {"snapshot_date": "2024-03-01", "opportunity_id": "OPP-1",
         "stage_at_snapshot": "Negotiation",      "amount": 12_000.0,
         "forecast_category": "Commit",    "expected_close_date": "2024-03-31"},
        {"snapshot_date": "2024-03-01", "opportunity_id": "OPP-2",
         "stage_at_snapshot": "Proof of Concept", "amount": 60_000.0,
         "forecast_category": "Best Case", "expected_close_date": "2024-06-01"},
        {"snapshot_date": "2024-03-01", "opportunity_id": "OPP-3",
         "stage_at_snapshot": "Proof of Concept", "amount": 200_000.0,
         "forecast_category": "Best Case", "expected_close_date": "2024-05-15"},
        {"snapshot_date": "2024-03-01", "opportunity_id": "OPP-8",
         "stage_at_snapshot": "Discovery",        "amount": 40_000.0,
         "forecast_category": "Pipeline",  "expected_close_date": "2024-08-15"},

        # Second snapshot for trend-test coverage
        {"snapshot_date": "2024-06-01", "opportunity_id": "OPP-2",
         "stage_at_snapshot": "Negotiation",      "amount": 60_000.0,
         "forecast_category": "Commit",    "expected_close_date": "2024-06-01"},
        {"snapshot_date": "2024-06-01", "opportunity_id": "OPP-8",
         "stage_at_snapshot": "Qualification",    "amount": 40_000.0,
         "forecast_category": "Pipeline",  "expected_close_date": "2024-08-15"},
    ]
    return pd.DataFrame(rows)
```

- [ ] **Step 2: Create empty `src/pipeline.py` with module docstring and shared stage-probability constants**

```python
"""Pipeline metric calculations for opportunity-level analytics.

All functions are pure: they take pandas DataFrames matching the schema of
`data/generated/opportunities.csv` and `opportunity_stage_history.csv`, and
return scalars or aggregated DataFrames.

Schema reminder:
    opportunities: opportunity_id, customer_id, account_name, segment,
                   acquisition_channel, owner_rep_id, opportunity_type,
                   created_date, close_date, amount, current_stage, status
        - status in {open, closed_won, closed_lost}
        - opportunity_type in {new_business, renewal, expansion}

    opportunity_stage_history: opportunity_id, stage, entered_date,
                               exited_date (NULL if currently in stage),
                               days_in_stage

The caller pre-filters opps by opp_type / segment / channel before calling
these functions — the API is intentionally stateless and minimal.
"""
from __future__ import annotations

import pandas as pd

# Stage win probabilities used for weighted pipeline. Mirrors the
# definitions in the Phase 2 design spec §5.2.
STAGE_PROBABILITY: dict[str, float] = {
    # new_business stages
    "Discovery": 0.10,
    "Qualification": 0.20,
    "Proof of Concept": 0.40,
    "Negotiation": 0.65,
    # renewal stages
    "Renewal Discussion": 0.75,
    # NOTE: renewal "Negotiation" uses 0.90 — but we share the key
    # "Negotiation" with new_business (0.65). The renewal case is rare in
    # the generated dataset; the design accepts the simplification of using
    # 0.65 for all Negotiation-named stages. Weighted pipeline is computed
    # primarily on new_business deals in practice.
    "Expansion Discussion": 0.80,
    # closed stages contribute 0 to weighted pipeline
    "Closed Won": 0.0,
    "Closed Lost": 0.0,
}
```

- [ ] **Step 3: Create empty `src/forecast.py` with module docstring**

```python
"""Forecasting metric calculations for pipeline-snapshot analytics.

All functions are pure: they take pandas DataFrames matching the schema of
`data/generated/pipeline_snapshots.csv` and `opportunities.csv`, and return
scalars or aggregated DataFrames.

Schema reminder:
    pipeline_snapshots: snapshot_date, opportunity_id, stage_at_snapshot,
                        amount, forecast_category, expected_close_date
        - forecast_category in {Commit, Best Case, Pipeline}
"""
from __future__ import annotations

import pandas as pd

from src.pipeline import STAGE_PROBABILITY
```

- [ ] **Step 4: Run pytest to confirm nothing broke**

```bash
pytest -v
```
Expected: 20 existing tests still pass; new modules import cleanly.

- [ ] **Step 5: Commit**

```bash
git add tests/conftest.py src/pipeline.py src/forecast.py
git commit -m "test: add tiny_snapshots fixture; scaffold src/pipeline.py and src/forecast.py"
```

---

## Task 4: `total_pipeline` (TDD)

**Files:**
- Create: `tests/test_pipeline.py`
- Modify: `src/pipeline.py` (append)

- [ ] **Step 1: Write the failing test**

Create `tests/test_pipeline.py`:

```python
"""Tests for src/pipeline.py — validated against tiny_opportunities and
tiny_stage_history fixtures in conftest.py.
"""
from __future__ import annotations

import pytest

from src.pipeline import (
    total_pipeline,
)


def test_total_pipeline_sums_open_deals_created_on_or_before_as_of(tiny_opportunities):
    # Open deals at 2024-04-01: OPP-2 (60k), OPP-3 (200k), OPP-8 (40k) = 300k
    # Closed deals (OPP-1, 4, 5, 6, 7) are excluded.
    assert total_pipeline(tiny_opportunities, "2024-04-01") == pytest.approx(300_000.0)


def test_total_pipeline_excludes_deals_created_after_as_of(tiny_opportunities):
    # As of 2024-02-01: OPP-8 (created 2024-02-15) is excluded
    # OPP-3 (created 2024-01-15) included, OPP-2 (created 2024-02-01) included.
    # Result: 60k + 200k = 260k
    assert total_pipeline(tiny_opportunities, "2024-02-01") == pytest.approx(260_000.0)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_pipeline.py -v
```
Expected: ImportError or AttributeError — `total_pipeline` not defined.

- [ ] **Step 3: Implement `total_pipeline` in `src/pipeline.py`**

Append to `src/pipeline.py`:

```python
def total_pipeline(opps: pd.DataFrame, as_of_date: str) -> float:
    """Sum of `amount` for open opps created on or before `as_of_date`.

    Formula: sum(amount where status='open' and created_date <= as_of_date)
    """
    open_opps = opps[
        (opps["status"] == "open")
        & (opps["created_date"] <= as_of_date)
    ]
    return float(open_opps["amount"].sum())
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_pipeline.py -v
```
Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/pipeline.py tests/test_pipeline.py
git commit -m "feat(pipeline): total_pipeline metric with hand-fixture tests"
```

---

## Task 5: `weighted_pipeline` (TDD)

**Files:**
- Modify: `tests/test_pipeline.py` (append)
- Modify: `src/pipeline.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_pipeline.py`:

```python
from src.pipeline import weighted_pipeline


def test_weighted_pipeline_applies_stage_probability(tiny_opportunities):
    # Open deals at 2024-04-01:
    #   OPP-2 in POC: 0.40 * 60_000 = 24_000
    #   OPP-3 in Negotiation: 0.65 * 200_000 = 130_000
    #   OPP-8 in Discovery: 0.10 * 40_000 = 4_000
    # Sum = 158_000
    assert weighted_pipeline(tiny_opportunities, "2024-04-01") == pytest.approx(158_000.0)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_pipeline.py::test_weighted_pipeline_applies_stage_probability -v
```
Expected: ImportError on `weighted_pipeline`.

- [ ] **Step 3: Implement `weighted_pipeline` in `src/pipeline.py`**

Append to `src/pipeline.py`:

```python
def weighted_pipeline(opps: pd.DataFrame, as_of_date: str) -> float:
    """Weighted-pipeline sum: each open deal's amount × its stage probability.

    Formula: sum(amount × STAGE_PROBABILITY[current_stage]
                 where status='open' and created_date <= as_of_date)
    """
    open_opps = opps[
        (opps["status"] == "open")
        & (opps["created_date"] <= as_of_date)
    ].copy()
    open_opps["weight"] = open_opps["current_stage"].map(STAGE_PROBABILITY).fillna(0.0)
    return float((open_opps["amount"] * open_opps["weight"]).sum())
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_pipeline.py -v
```
Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/pipeline.py tests/test_pipeline.py
git commit -m "feat(pipeline): weighted_pipeline metric with stage probability weighting"
```

---

## Task 6: `pipeline_coverage` (TDD)

**Files:**
- Modify: `tests/test_pipeline.py` (append)
- Modify: `src/pipeline.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_pipeline.py`:

```python
from src.pipeline import pipeline_coverage


def test_pipeline_coverage_is_pipeline_over_target(tiny_opportunities):
    # total_pipeline at 2024-04-01 = 300_000. Target 100_000. Coverage = 3.0
    assert pipeline_coverage(tiny_opportunities, 100_000.0, "2024-04-01") == pytest.approx(3.0)


def test_pipeline_coverage_returns_zero_when_target_is_zero(tiny_opportunities):
    # Guard divide-by-zero. Returning 0 is the conservative choice — there's
    # no meaningful coverage ratio against a $0 target.
    assert pipeline_coverage(tiny_opportunities, 0.0, "2024-04-01") == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_pipeline.py -v
```
Expected: ImportError on `pipeline_coverage`.

- [ ] **Step 3: Implement `pipeline_coverage`**

Append to `src/pipeline.py`:

```python
def pipeline_coverage(opps: pd.DataFrame, target: float, as_of_date: str) -> float:
    """Pipeline coverage = total_pipeline / target.

    Returns 0.0 if target == 0 (no meaningful ratio against a zero target).
    Conventionally reported as a multiple (e.g., 3.0× is healthy).
    """
    if target == 0:
        return 0.0
    return total_pipeline(opps, as_of_date) / target
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_pipeline.py -v
```
Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/pipeline.py tests/test_pipeline.py
git commit -m "feat(pipeline): pipeline_coverage = pipeline / target with target=0 guard"
```

---

## Task 7: `win_rate` (TDD)

**Files:**
- Modify: `tests/test_pipeline.py` (append)
- Modify: `src/pipeline.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_pipeline.py`:

```python
from src.pipeline import win_rate


def test_win_rate_won_over_closed(tiny_opportunities):
    # Closed deals (close_date in [2024-01-01, 2024-04-01)):
    #   won:  OPP-1 (2024-03-31), OPP-5 (2024-03-01), OPP-7 (2024-03-15) = 3
    #   lost: OPP-4 (2024-02-15), OPP-6 (2024-02-20) = 2
    # Rate = 3/5 = 0.60
    assert win_rate(tiny_opportunities, "2024-01-01", "2024-04-01") == pytest.approx(0.60)


def test_win_rate_returns_zero_when_no_closed_deals(tiny_opportunities):
    # No deals close in [2025-01-01, 2025-02-01)
    assert win_rate(tiny_opportunities, "2025-01-01", "2025-02-01") == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_pipeline.py -v
```
Expected: ImportError on `win_rate`.

- [ ] **Step 3: Implement `win_rate`**

Append to `src/pipeline.py`:

```python
def win_rate(opps: pd.DataFrame, start_date: str, end_date: str) -> float:
    """Win rate = closed_won / (closed_won + closed_lost) for deals closing in window.

    Window is [start_date, end_date) — inclusive of start, exclusive of end.
    Caller pre-filters by opp_type / segment / channel as needed.
    """
    closed = opps[
        (opps["status"].isin(["closed_won", "closed_lost"]))
        & (opps["close_date"] >= start_date)
        & (opps["close_date"] < end_date)
    ]
    if len(closed) == 0:
        return 0.0
    won = (closed["status"] == "closed_won").sum()
    return float(won) / len(closed)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_pipeline.py -v
```
Expected: 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/pipeline.py tests/test_pipeline.py
git commit -m "feat(pipeline): win_rate for closed deals in a window"
```

---

## Task 8: `avg_sales_cycle_days` (TDD)

**Files:**
- Modify: `tests/test_pipeline.py` (append)
- Modify: `src/pipeline.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_pipeline.py`:

```python
from src.pipeline import avg_sales_cycle_days


def test_avg_sales_cycle_days_for_won_deals(tiny_opportunities):
    # Won deals in [2024-01-01, 2024-04-01):
    #   OPP-1: 2024-03-31 − 2024-01-01 = 90 days
    #   OPP-5: 2024-03-01 − 2024-01-01 = 60 days
    #   OPP-7: 2024-03-15 − 2024-01-15 = 60 days
    # Avg = (90 + 60 + 60) / 3 = 70.0
    assert avg_sales_cycle_days(tiny_opportunities, "2024-01-01", "2024-04-01") == pytest.approx(70.0)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_pipeline.py::test_avg_sales_cycle_days_for_won_deals -v
```
Expected: ImportError.

- [ ] **Step 3: Implement `avg_sales_cycle_days`**

Append to `src/pipeline.py`:

```python
def avg_sales_cycle_days(opps: pd.DataFrame, start_date: str, end_date: str) -> float:
    """Average (close_date − created_date) in days for closed-won deals in window."""
    won = opps[
        (opps["status"] == "closed_won")
        & (opps["close_date"] >= start_date)
        & (opps["close_date"] < end_date)
    ].copy()
    if len(won) == 0:
        return 0.0
    cycle_days = (pd.to_datetime(won["close_date"]) - pd.to_datetime(won["created_date"])).dt.days
    return float(cycle_days.mean())
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_pipeline.py -v
```
Expected: 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/pipeline.py tests/test_pipeline.py
git commit -m "feat(pipeline): avg_sales_cycle_days for closed-won deals"
```

---

## Task 9: `avg_days_in_stage` (TDD)

**Files:**
- Modify: `tests/test_pipeline.py` (append)
- Modify: `src/pipeline.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_pipeline.py`:

```python
from src.pipeline import avg_days_in_stage


def test_avg_days_in_stage_only_counts_completed_occupancies(tiny_stage_history):
    # POC entries with entered_date in [2024-01-01, 2024-04-01) AND exited_date not null:
    #   OPP-1: 14, OPP-3: 25, OPP-4: 21 -> avg = 60/3 = 20.0
    # OPP-2's POC entry (entered 2024-02-15, still in stage) is excluded.
    assert avg_days_in_stage(tiny_stage_history, "Proof of Concept",
                              "2024-01-01", "2024-04-01") == pytest.approx(20.0)


def test_avg_days_in_stage_negotiation_single_completed(tiny_stage_history):
    # Negotiation: only OPP-1 (entered 2024-02-01, exited 2024-03-31, 59 days).
    # OPP-3 in Negotiation is in-progress (exited_date null) — excluded.
    assert avg_days_in_stage(tiny_stage_history, "Negotiation",
                              "2024-01-01", "2024-04-01") == pytest.approx(59.0)


def test_avg_days_in_stage_returns_zero_when_no_completed(tiny_stage_history):
    # No POC entries in [2025-01-01, 2025-02-01)
    assert avg_days_in_stage(tiny_stage_history, "Proof of Concept",
                              "2025-01-01", "2025-02-01") == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_pipeline.py -v
```
Expected: ImportError on `avg_days_in_stage`.

- [ ] **Step 3: Implement `avg_days_in_stage`**

Append to `src/pipeline.py`:

```python
def avg_days_in_stage(history: pd.DataFrame, stage: str,
                      start_date: str, end_date: str) -> float:
    """Average days_in_stage for completed (exited_date not null) stage
    occupancies where entered_date falls in [start_date, end_date).

    In-progress occupancies are excluded — their final dwell time is
    unknown. For aging analysis, use `aging_deals` instead.
    """
    rows = history[
        (history["stage"] == stage)
        & (history["entered_date"] >= start_date)
        & (history["entered_date"] < end_date)
        & history["exited_date"].notna()
    ]
    if len(rows) == 0:
        return 0.0
    return float(rows["days_in_stage"].mean())
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_pipeline.py -v
```
Expected: 11 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/pipeline.py tests/test_pipeline.py
git commit -m "feat(pipeline): avg_days_in_stage over completed stage occupancies"
```

---

## Task 10: `stage_conversion` (TDD)

**Files:**
- Modify: `tests/test_pipeline.py` (append)
- Modify: `src/pipeline.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_pipeline.py`:

```python
from src.pipeline import stage_conversion


def test_stage_conversion_poc_to_negotiation(tiny_stage_history):
    # Deals that entered POC in [2024-01-01, 2024-04-01) AND have exited POC:
    #   OPP-1 (exited 2024-02-01 → advanced)
    #   OPP-3 (exited 2024-03-15 → advanced)
    #   OPP-4 (exited 2024-02-15 → lost in POC)
    # OPP-2 also entered POC in window but hasn't exited — excluded.
    # Reached Negotiation: OPP-1, OPP-3 = 2 of 3 -> 0.667
    assert stage_conversion(tiny_stage_history, "Proof of Concept", "Negotiation",
                             "2024-01-01", "2024-04-01") == pytest.approx(2 / 3, abs=0.001)


def test_stage_conversion_returns_zero_when_no_entries(tiny_stage_history):
    # No POC entries in [2025-01-01, 2025-02-01)
    assert stage_conversion(tiny_stage_history, "Proof of Concept", "Negotiation",
                             "2025-01-01", "2025-02-01") == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_pipeline.py -v
```
Expected: ImportError on `stage_conversion`.

- [ ] **Step 3: Implement `stage_conversion`**

Append to `src/pipeline.py`:

```python
def stage_conversion(history: pd.DataFrame, from_stage: str, to_stage: str,
                     start_date: str, end_date: str) -> float:
    """Of opps that entered `from_stage` in [start, end) AND have since exited
    `from_stage` (one way or another), what fraction ever reached `to_stage`?

    Deals still sitting in `from_stage` (exited_date is null) are excluded
    because they haven't had time to advance or lose. Without this filter,
    fresh deals would artificially depress conversion.
    """
    entered = history[
        (history["stage"] == from_stage)
        & (history["entered_date"] >= start_date)
        & (history["entered_date"] < end_date)
        & history["exited_date"].notna()
    ]
    if len(entered) == 0:
        return 0.0
    opp_ids_that_exited_from_stage = set(entered["opportunity_id"])
    reached_to_stage = set(
        history[
            (history["stage"] == to_stage)
            & history["opportunity_id"].isin(opp_ids_that_exited_from_stage)
        ]["opportunity_id"]
    )
    return len(reached_to_stage) / len(opp_ids_that_exited_from_stage)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_pipeline.py -v
```
Expected: 13 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/pipeline.py tests/test_pipeline.py
git commit -m "feat(pipeline): stage_conversion rate for deals that exited from_stage in window"
```

---

## Task 11: `aging_deals` (TDD)

**Files:**
- Modify: `tests/test_pipeline.py` (append)
- Modify: `src/pipeline.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_pipeline.py`:

```python
from src.pipeline import aging_deals


def test_aging_deals_filters_by_current_stage_age(tiny_opportunities, tiny_stage_history):
    # As of 2024-04-01, threshold = 30:
    #   OPP-2 in POC since 2024-02-15 -> 46 days -> AGING
    #   OPP-3 in Negotiation since 2024-03-15 -> 17 days -> not aging
    #   OPP-8 in Discovery since 2024-02-15 -> 46 days -> AGING
    result = aging_deals(tiny_opportunities, tiny_stage_history, "2024-04-01", 30)
    assert set(result["opportunity_id"]) == {"OPP-2", "OPP-8"}


def test_aging_deals_empty_when_threshold_too_high(tiny_opportunities, tiny_stage_history):
    # No deal has been in current stage for >365 days at 2024-04-01
    result = aging_deals(tiny_opportunities, tiny_stage_history, "2024-04-01", 365)
    assert len(result) == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_pipeline.py -v
```
Expected: ImportError on `aging_deals`.

- [ ] **Step 3: Implement `aging_deals`**

Append to `src/pipeline.py`:

```python
def aging_deals(opps: pd.DataFrame, history: pd.DataFrame,
                as_of_date: str, threshold_days: int = 60) -> pd.DataFrame:
    """Return open opps whose days-in-current-stage exceeds `threshold_days`.

    Days-in-current-stage = as_of_date − entered_date of the row in `history`
    where opportunity_id matches and exited_date is null.

    Returns a DataFrame with the opp's row plus a `days_in_current_stage` column,
    sorted descending by that column. Empty DataFrame if no aging deals.
    """
    current_stage_entries = history[history["exited_date"].isna()].copy()
    current_stage_entries["days_in_current_stage"] = (
        pd.to_datetime(as_of_date) - pd.to_datetime(current_stage_entries["entered_date"])
    ).dt.days

    aging = current_stage_entries[current_stage_entries["days_in_current_stage"] > threshold_days]

    open_opps = opps[opps["status"] == "open"]
    joined = open_opps.merge(
        aging[["opportunity_id", "days_in_current_stage"]],
        on="opportunity_id",
        how="inner",
    )
    return joined.sort_values("days_in_current_stage", ascending=False)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_pipeline.py -v
```
Expected: 15 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/pipeline.py tests/test_pipeline.py
git commit -m "feat(pipeline): aging_deals returns open opps stuck past a threshold"
```

---

## Task 12: `forecast_buckets` (TDD)

**Files:**
- Create: `tests/test_forecast.py`
- Modify: `src/forecast.py` (append)

- [ ] **Step 1: Write the failing test**

Create `tests/test_forecast.py`:

```python
"""Tests for src/forecast.py — validated against tiny_snapshots and
tiny_opportunities fixtures in conftest.py.
"""
from __future__ import annotations

import pytest

from src.forecast import forecast_buckets


def test_forecast_buckets_sums_by_category(tiny_snapshots):
    # At snapshot 2024-03-01:
    #   Commit    = OPP-1 (Negotiation)         = 12_000
    #   Best Case = OPP-2 + OPP-3 (POC)         = 60_000 + 200_000 = 260_000
    #   Pipeline  = OPP-8 (Discovery)           = 40_000
    result = forecast_buckets(tiny_snapshots, "2024-03-01")
    assert result == {
        "commit": pytest.approx(12_000.0),
        "best_case": pytest.approx(260_000.0),
        "pipeline": pytest.approx(40_000.0),
    }


def test_forecast_buckets_empty_when_no_snapshot_for_date(tiny_snapshots):
    result = forecast_buckets(tiny_snapshots, "2099-01-01")
    assert result == {"commit": 0.0, "best_case": 0.0, "pipeline": 0.0}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_forecast.py -v
```
Expected: ImportError on `forecast_buckets`.

- [ ] **Step 3: Implement `forecast_buckets`**

Append to `src/forecast.py`:

```python
def forecast_buckets(snapshots: pd.DataFrame, snapshot_date: str) -> dict[str, float]:
    """Sum amounts by forecast_category for the given snapshot_date.

    Returns dict with keys 'commit', 'best_case', 'pipeline' (lowercase,
    snake_case). Zero-defaults if a category has no rows for the date.
    """
    rows = snapshots[snapshots["snapshot_date"] == snapshot_date]
    result = {"commit": 0.0, "best_case": 0.0, "pipeline": 0.0}
    if len(rows) == 0:
        return result
    by_cat = rows.groupby("forecast_category")["amount"].sum().to_dict()
    result["commit"] = float(by_cat.get("Commit", 0.0))
    result["best_case"] = float(by_cat.get("Best Case", 0.0))
    result["pipeline"] = float(by_cat.get("Pipeline", 0.0))
    return result
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_forecast.py -v
```
Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/forecast.py tests/test_forecast.py
git commit -m "feat(forecast): forecast_buckets sums snapshot amount by category"
```

---

## Task 13: `forecast_accuracy` (TDD)

**Files:**
- Modify: `tests/test_forecast.py` (append)
- Modify: `src/forecast.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_forecast.py`:

```python
from src.forecast import forecast_accuracy


def test_forecast_accuracy_weighted_over_actual(tiny_snapshots, tiny_opportunities):
    # Snapshot 2024-03-01:
    #   weighted_at_snapshot
    #     = 0.65*12_000 + 0.40*60_000 + 0.40*200_000 + 0.10*40_000
    #     = 7_800 + 24_000 + 80_000 + 4_000 = 115_800
    #   actual closed_won in [2024-03-01, 2024-06-01):
    #     OPP-1 (12_000) + OPP-5 (30_000) + OPP-7 (24_000) = 66_000
    #   accuracy = 115_800 / 66_000 ≈ 1.7545
    assert forecast_accuracy(tiny_snapshots, tiny_opportunities, "2024-03-01") == pytest.approx(115_800.0 / 66_000.0, abs=0.001)


def test_forecast_accuracy_returns_none_when_no_actuals(tiny_snapshots, tiny_opportunities):
    # No closed_won deals in [2099-01-01, 2099-04-01) — return None to signal
    # "can't compute" rather than dividing by zero.
    result = forecast_accuracy(tiny_snapshots, tiny_opportunities, "2099-01-01")
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_forecast.py -v
```
Expected: ImportError.

- [ ] **Step 3: Implement `forecast_accuracy`**

Append to `src/forecast.py`:

```python
def forecast_accuracy(snapshots: pd.DataFrame, opps: pd.DataFrame,
                      snapshot_date: str) -> float | None:
    """Forecast accuracy = weighted pipeline at snapshot ÷ actual closed-won
    in the 3 months starting at snapshot_date.

    Returns None if no closed-won deals exist in the window (can't compute
    a ratio against zero).

    Interpretation: 1.0 = perfect, >1.0 = over-forecasted, <1.0 = under-forecasted.
    """
    snap = snapshots[snapshots["snapshot_date"] == snapshot_date].copy()
    if len(snap) == 0:
        return None
    snap["weight"] = snap["stage_at_snapshot"].map(STAGE_PROBABILITY).fillna(0.0)
    weighted = float((snap["amount"] * snap["weight"]).sum())

    window_end = (pd.Timestamp(snapshot_date) + pd.DateOffset(months=3)).strftime("%Y-%m-%d")
    actual = opps[
        (opps["status"] == "closed_won")
        & (opps["close_date"] >= snapshot_date)
        & (opps["close_date"] < window_end)
    ]
    actual_total = float(actual["amount"].sum())
    if actual_total == 0:
        return None
    return weighted / actual_total
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_forecast.py -v
```
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/forecast.py tests/test_forecast.py
git commit -m "feat(forecast): forecast_accuracy ratio of weighted snapshot to actual closed-won"
```

---

## Task 14: `forecast_accuracy_trend` (TDD)

**Files:**
- Modify: `tests/test_forecast.py` (append)
- Modify: `src/forecast.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_forecast.py`:

```python
from src.forecast import forecast_accuracy_trend


def test_forecast_accuracy_trend_returns_row_per_snapshot(tiny_snapshots, tiny_opportunities):
    df = forecast_accuracy_trend(tiny_snapshots, tiny_opportunities)
    # tiny_snapshots has 2 distinct snapshot_dates
    assert set(df["snapshot_date"]) == {"2024-03-01", "2024-06-01"}
    assert set(df.columns) >= {"snapshot_date", "weighted_forecast", "actual_closed_won", "accuracy"}


def test_forecast_accuracy_trend_2024_03_01_row(tiny_snapshots, tiny_opportunities):
    df = forecast_accuracy_trend(tiny_snapshots, tiny_opportunities)
    row = df[df["snapshot_date"] == "2024-03-01"].iloc[0]
    assert row["weighted_forecast"] == pytest.approx(115_800.0)
    assert row["actual_closed_won"] == pytest.approx(66_000.0)
    assert row["accuracy"] == pytest.approx(115_800.0 / 66_000.0, abs=0.001)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_forecast.py -v
```
Expected: ImportError.

- [ ] **Step 3: Implement `forecast_accuracy_trend`**

Append to `src/forecast.py`:

```python
def forecast_accuracy_trend(snapshots: pd.DataFrame, opps: pd.DataFrame) -> pd.DataFrame:
    """Build a row-per-snapshot DataFrame with forecast, actual, and accuracy.

    Columns: snapshot_date, weighted_forecast, actual_closed_won, accuracy
    `accuracy` is None for snapshots where no closed-won deals fall in the
    3-month window after the snapshot date.
    """
    rows = []
    for snap_date in sorted(snapshots["snapshot_date"].unique()):
        snap = snapshots[snapshots["snapshot_date"] == snap_date].copy()
        snap["weight"] = snap["stage_at_snapshot"].map(STAGE_PROBABILITY).fillna(0.0)
        weighted = float((snap["amount"] * snap["weight"]).sum())

        window_end = (pd.Timestamp(snap_date) + pd.DateOffset(months=3)).strftime("%Y-%m-%d")
        actual = opps[
            (opps["status"] == "closed_won")
            & (opps["close_date"] >= snap_date)
            & (opps["close_date"] < window_end)
        ]
        actual_total = float(actual["amount"].sum())
        accuracy = (weighted / actual_total) if actual_total > 0 else None

        rows.append({
            "snapshot_date": snap_date,
            "weighted_forecast": weighted,
            "actual_closed_won": actual_total,
            "accuracy": accuracy,
        })
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_forecast.py -v
```
Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/forecast.py tests/test_forecast.py
git commit -m "feat(forecast): forecast_accuracy_trend builds row-per-snapshot DataFrame"
```

---

## Task 15: `forecast_bias_by_segment` (TDD)

**Files:**
- Modify: `tests/test_forecast.py` (append)
- Modify: `src/forecast.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_forecast.py`:

```python
from src.forecast import forecast_bias_by_segment


def test_forecast_bias_by_segment_groups_correctly(tiny_snapshots, tiny_opportunities):
    # Snapshot 2024-03-01, segments derived by joining snapshot -> opps:
    #   SMB:        OPP-1 weighted = 0.65*12_000 = 7_800.  Actual won SMB = OPP-1 (12_000)
    #   Mid-Market: OPP-2 + OPP-8 weighted = 0.40*60_000 + 0.10*40_000 = 28_000.
    #               Actual won Mid-Market = OPP-5 (30_000)
    #   Enterprise: OPP-3 weighted = 0.40*200_000 = 80_000.
    #               Actual won Enterprise = OPP-7 (24_000)
    df = forecast_bias_by_segment(tiny_snapshots, tiny_opportunities, "2024-03-01")
    by_seg = df.set_index("segment")
    assert by_seg.loc["SMB", "weighted_forecast"] == pytest.approx(7_800.0)
    assert by_seg.loc["SMB", "actual_closed_won"] == pytest.approx(12_000.0)
    assert by_seg.loc["Mid-Market", "weighted_forecast"] == pytest.approx(28_000.0)
    assert by_seg.loc["Mid-Market", "actual_closed_won"] == pytest.approx(30_000.0)
    assert by_seg.loc["Enterprise", "weighted_forecast"] == pytest.approx(80_000.0)
    assert by_seg.loc["Enterprise", "actual_closed_won"] == pytest.approx(24_000.0)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_forecast.py -v
```
Expected: ImportError.

- [ ] **Step 3: Implement `forecast_bias_by_segment`**

Append to `src/forecast.py`:

```python
def forecast_bias_by_segment(snapshots: pd.DataFrame, opps: pd.DataFrame,
                              snapshot_date: str) -> pd.DataFrame:
    """Per-segment forecast vs. actual for a single snapshot's quarter.

    Returns columns: segment, weighted_forecast, actual_closed_won, accuracy.
    The segment comes from joining the snapshot's opportunity_ids back to
    the opps table.
    """
    snap = snapshots[snapshots["snapshot_date"] == snapshot_date].copy()
    snap = snap.merge(opps[["opportunity_id", "segment"]], on="opportunity_id", how="left")
    snap["weight"] = snap["stage_at_snapshot"].map(STAGE_PROBABILITY).fillna(0.0)
    snap["weighted_amount"] = snap["amount"] * snap["weight"]

    forecast_by_seg = snap.groupby("segment")["weighted_amount"].sum().rename("weighted_forecast")

    window_end = (pd.Timestamp(snapshot_date) + pd.DateOffset(months=3)).strftime("%Y-%m-%d")
    actuals = opps[
        (opps["status"] == "closed_won")
        & (opps["close_date"] >= snapshot_date)
        & (opps["close_date"] < window_end)
    ]
    actual_by_seg = actuals.groupby("segment")["amount"].sum().rename("actual_closed_won")

    df = pd.concat([forecast_by_seg, actual_by_seg], axis=1).fillna(0.0).reset_index()
    df["accuracy"] = df.apply(
        lambda r: (r["weighted_forecast"] / r["actual_closed_won"]) if r["actual_closed_won"] > 0 else None,
        axis=1,
    )
    return df
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_forecast.py -v
```
Expected: 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/forecast.py tests/test_forecast.py
git commit -m "feat(forecast): forecast_bias_by_segment cross-tab of weighted vs. actual"
```

---

## Task 16: Generator constants + stage history helper

This task adds the configuration constants (stage dwell times, advance probabilities) and a helper that walks a deal through stages backwards from its close_date. Used by Tasks 17–20.

**Files:**
- Modify: `src/data_generator.py` (append)

- [ ] **Step 1: Append Phase 2 constants and helpers**

Append to the end of `src/data_generator.py`, after the Phase 1 code:

```python
# --- Phase 2: Pipeline & Forecasting --------------------------------------

# Stage taxonomy by opportunity type
NB_STAGES = ["Discovery", "Qualification", "Proof of Concept", "Negotiation"]
RENEWAL_STAGES = ["Renewal Discussion", "Negotiation"]
EXPANSION_STAGES = ["Expansion Discussion"]

# Mean dwell days per stage per segment (gamma-distributed in practice)
# Engineered insight: Mid-Market POC stall (~3x SMB dwell).
NB_STAGE_DWELL_DAYS = {
    "Discovery":         {"SMB": 7,  "Mid-Market": 10, "Enterprise": 14},
    "Qualification":     {"SMB": 10, "Mid-Market": 14, "Enterprise": 20},
    "Proof of Concept":  {"SMB": 15, "Mid-Market": 45, "Enterprise": 25},  # the gap
    "Negotiation":       {"SMB": 10, "Mid-Market": 18, "Enterprise": 25},
}

# Stage advance probability (rest = closed-lost in that stage)
# Engineered insight: Mid-Market POC -> Negotiation only ~40%.
NB_STAGE_ADVANCE_PROB = {
    "Discovery":        {"SMB": 0.85, "Mid-Market": 0.80, "Enterprise": 0.90},
    "Qualification":    {"SMB": 0.75, "Mid-Market": 0.70, "Enterprise": 0.85},
    "Proof of Concept": {"SMB": 0.70, "Mid-Market": 0.40, "Enterprise": 0.75},  # the gap
    "Negotiation":      {"SMB": 0.80, "Mid-Market": 0.75, "Enterprise": 0.85},
}

# Renewal / expansion are shorter cycles
RENEWAL_STAGE_DWELL_DAYS = {"Renewal Discussion": 30, "Negotiation": 15}
EXPANSION_STAGE_DWELL_DAYS = {"Expansion Discussion": 30}

# Rep pool (captured on opps; not surfaced in Phase 2)
REP_IDS = [f"REP-{i:02d}" for i in range(1, 13)]

# Pipeline snapshot dates (first of each quarter, Q1 2024 - Q4 2025)
SNAPSHOT_DATES = [pd.Timestamp(f"{y}-{m:02d}-01") for y in (2024, 2025) for m in (1, 4, 7, 10)]

# Forecast category by stage
FORECAST_CATEGORY_BY_STAGE = {
    "Discovery": "Pipeline",
    "Qualification": "Pipeline",
    "Proof of Concept": "Best Case",
    "Renewal Discussion": "Best Case",
    "Expansion Discussion": "Best Case",
    "Negotiation": "Commit",
}


def _sample_dwell_days(rng: np.random.Generator, mean_days: float) -> int:
    """Sample a positive-skew dwell time using a gamma with shape=2.

    Real-world dwell times have a long right tail (some deals drag); gamma(2)
    captures that without going negative. `mean = shape * scale` so scale = mean/2.
    """
    shape = 2.0
    scale = mean_days / shape
    return max(1, int(round(rng.gamma(shape, scale))))


def _walk_new_business_stages_backward(rng: np.random.Generator, close_date: pd.Timestamp,
                                        segment: str, end_stage: str | None,
                                        won: bool) -> list[dict]:
    """Build stage_history rows by walking backward from close_date.

    `end_stage` is the stage in which the deal closed (None means walked through
    all NB_STAGES and won). `won=True` means deal reached Negotiation and converted.

    Returns a list of dicts with: stage, entered_date, exited_date, days_in_stage.
    Dates are pd.Timestamp; serialization to ISO date happens at write time.
    """
    if end_stage is None:
        stages = NB_STAGES  # walked through all 4
    else:
        idx = NB_STAGES.index(end_stage)
        stages = NB_STAGES[:idx + 1]

    # Sample dwell times per stage
    dwells = [_sample_dwell_days(rng, NB_STAGE_DWELL_DAYS[s][segment]) for s in stages]

    # Build the history forward in time. Total = close_date - sum(dwells_before_close_stage)
    # For a won deal closing in Negotiation: deal exited Negotiation on close_date.
    # For a lost deal closing in stage X: deal exited X on close_date.
    history = []
    # Last stage exit = close_date
    end = close_date
    for stage_name, dwell in reversed(list(zip(stages, dwells))):
        start = end - pd.Timedelta(days=dwell)
        history.append({"stage": stage_name, "entered_date": start,
                        "exited_date": end, "days_in_stage": dwell})
        end = start

    history.reverse()  # chronological
    return history
```

- [ ] **Step 2: Run pytest to confirm Phase 1 still green and no import errors**

```bash
pytest -v
```
Expected: ~42 tests pass (20 Phase 1 + ~22 Phase 2 metric tests from Tasks 4–15). The exact count depends on how many test cases each task added.

- [ ] **Step 3: Commit**

```bash
git add src/data_generator.py
git commit -m "feat(generator): Phase 2 stage constants and stage-history backward-walk helper"
```

---

## Task 17: Generator — new_business won/open/lost opportunities

**Files:**
- Modify: `src/data_generator.py` (append)

- [ ] **Step 1: Append `_generate_new_business_opps`**

Append to `src/data_generator.py`:

```python
def _generate_new_business_opps(customers: pd.DataFrame, rng: np.random.Generator
                                 ) -> tuple[list[dict], list[dict]]:
    """Generate new_business opportunities. Returns (opp_rows, stage_history_rows).

    Three sub-populations:
      1. Closed-won opps for every non-Self-Serve Phase 1 customer, closing on
         that customer's signup_date.
      2. Currently-open opps (~150), created in 2024-2025, in various stages,
         expected to close Q1-Q2 2026.
      3. Closed-lost opps (~80), walked through stages and dropped out somewhere.
    """
    opp_rows = []
    stage_history_rows = []
    next_id = 1

    # Sub-population 1: closed-won, one per non-Self-Serve Phase 1 customer
    nb_customers = customers[customers["acquisition_channel"] != "Self-Serve Promo"]
    for _, c in nb_customers.iterrows():
        close_date = pd.Timestamp(c["signup_date"])
        history = _walk_new_business_stages_backward(
            rng, close_date, c["segment"], end_stage=None, won=True
        )
        created_date = history[0]["entered_date"]
        opp_id = f"OPP-{next_id:05d}"
        next_id += 1
        opp_rows.append({
            "opportunity_id": opp_id,
            "customer_id": c["customer_id"],
            "account_name": c["company_name"],
            "segment": c["segment"],
            "acquisition_channel": c["acquisition_channel"],
            "owner_rep_id": str(rng.choice(REP_IDS)),
            "opportunity_type": "new_business",
            "created_date": created_date.strftime("%Y-%m-%d"),
            "close_date": close_date.strftime("%Y-%m-%d"),
            "amount": float(c["initial_mrr"]) * 12.0,
            "current_stage": "Closed Won",
            "status": "closed_won",
        })
        for h in history:
            stage_history_rows.append({
                "opportunity_id": opp_id,
                "stage": h["stage"],
                "entered_date": h["entered_date"].strftime("%Y-%m-%d"),
                "exited_date": h["exited_date"].strftime("%Y-%m-%d"),
                "days_in_stage": h["days_in_stage"],
            })

    # Sub-population 2: currently-open opps (~150)
    # Spread created_date across 2024-09 to 2025-12; sample a current stage based
    # on stage-advance probabilities; expected close_date = today + remaining stages' dwell.
    today = pd.Timestamp("2025-12-01")  # "Now" for the dashboard
    n_open = 150
    for _ in range(n_open):
        segment = str(rng.choice(SEGMENTS, p=SEGMENT_WEIGHTS))
        channel = str(rng.choice([c for c in CHANNELS if c != "Self-Serve Promo"]))
        created_offset_days = int(rng.integers(0, 365))  # up to a year before "today"
        created_date = today - pd.Timedelta(days=created_offset_days)

        # Walk stages forward from created_date until either a non-advance roll
        # (deal would have been lost — restart) or we reach a stage but "now"
        # has arrived. Tracks current stage at "today".
        cur = pd.Timestamp(created_date)
        history = []
        current_stage = None
        for stage in NB_STAGES:
            dwell = _sample_dwell_days(rng, NB_STAGE_DWELL_DAYS[stage][segment])
            entered = cur
            exit_date = cur + pd.Timedelta(days=dwell)
            if exit_date >= today:
                # Deal is still in this stage as of today
                current_stage = stage
                history.append({"stage": stage, "entered_date": entered,
                                "exited_date": None, "days_in_stage": None})
                break
            # Did the deal advance? If yes, continue. If no, this would have
            # been a lost deal — but we want open deals here, so restart the loop
            # by treating this deal as having advanced.
            history.append({"stage": stage, "entered_date": entered,
                            "exited_date": exit_date, "days_in_stage": dwell})
            cur = exit_date
        else:
            # Deal walked through all 4 stages but didn't close yet — extend
            # by setting current_stage = Negotiation with no exit
            current_stage = "Negotiation"
            # Replace the last history entry to be in-progress
            history[-1]["exited_date"] = None
            history[-1]["days_in_stage"] = None

        # Estimate expected close: today + average remaining-dwell across uncompleted stages
        remaining = NB_STAGES[NB_STAGES.index(current_stage):]
        expected_close_offset = sum(NB_STAGE_DWELL_DAYS[s][segment] for s in remaining)
        expected_close = today + pd.Timedelta(days=expected_close_offset)
        amount = float(rng.integers(5_000, 250_000))

        opp_id = f"OPP-{next_id:05d}"
        next_id += 1
        opp_rows.append({
            "opportunity_id": opp_id,
            "customer_id": None,
            "account_name": _fake_company_name(rng),
            "segment": segment,
            "acquisition_channel": channel,
            "owner_rep_id": str(rng.choice(REP_IDS)),
            "opportunity_type": "new_business",
            "created_date": created_date.strftime("%Y-%m-%d"),
            "close_date": expected_close.strftime("%Y-%m-%d"),
            "amount": amount,
            "current_stage": current_stage,
            "status": "open",
        })
        for h in history:
            stage_history_rows.append({
                "opportunity_id": opp_id,
                "stage": h["stage"],
                "entered_date": h["entered_date"].strftime("%Y-%m-%d"),
                "exited_date": h["exited_date"].strftime("%Y-%m-%d") if h["exited_date"] else None,
                "days_in_stage": h["days_in_stage"],
            })

    # Sub-population 3: closed-lost (~80)
    n_lost = 80
    for _ in range(n_lost):
        segment = str(rng.choice(SEGMENTS, p=SEGMENT_WEIGHTS))
        channel = str(rng.choice([c for c in CHANNELS if c != "Self-Serve Promo"]))
        # Pick stage where deal died — weighted by advance failures
        # Higher chance of dying in POC, especially for Mid-Market
        death_stage = str(rng.choice(NB_STAGES, p=[0.25, 0.25, 0.40, 0.10]))
        # Pick a close_date in 2024-2025
        close_date = pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(rng.integers(0, 730)))
        history = _walk_new_business_stages_backward(
            rng, close_date, segment, end_stage=death_stage, won=False
        )
        created_date = history[0]["entered_date"]
        amount = float(rng.integers(5_000, 250_000))

        opp_id = f"OPP-{next_id:05d}"
        next_id += 1
        opp_rows.append({
            "opportunity_id": opp_id,
            "customer_id": None,
            "account_name": _fake_company_name(rng),
            "segment": segment,
            "acquisition_channel": channel,
            "owner_rep_id": str(rng.choice(REP_IDS)),
            "opportunity_type": "new_business",
            "created_date": created_date.strftime("%Y-%m-%d"),
            "close_date": close_date.strftime("%Y-%m-%d"),
            "amount": amount,
            "current_stage": "Closed Lost",
            "status": "closed_lost",
        })
        for h in history:
            stage_history_rows.append({
                "opportunity_id": opp_id,
                "stage": h["stage"],
                "entered_date": h["entered_date"].strftime("%Y-%m-%d"),
                "exited_date": h["exited_date"].strftime("%Y-%m-%d"),
                "days_in_stage": h["days_in_stage"],
            })

    return opp_rows, stage_history_rows
```

- [ ] **Step 2: Smoke-test by calling the function in a python REPL**

```bash
python -c "
from src.data_generator import generate_customers, GeneratorConfig, _generate_new_business_opps
import numpy as np
cfg = GeneratorConfig()
customers = generate_customers(cfg)
rng = np.random.default_rng(cfg.rng_seed + 2)
opps, history = _generate_new_business_opps(customers, rng)
print(f'opps: {len(opps)}, history: {len(history)}')
print('first opp:', opps[0])
print('first history:', history[0])
"
```
Expected: a few hundred opps printed, no exceptions.

- [ ] **Step 3: Commit**

```bash
git add src/data_generator.py
git commit -m "feat(generator): new_business opportunities (won/open/lost) with stage histories"
```

---

## Task 18: Generator — renewal opportunities

**Files:**
- Modify: `src/data_generator.py` (append)

- [ ] **Step 1: Append `_generate_renewal_opps`**

Append to `src/data_generator.py`:

```python
def _generate_renewal_opps(customers: pd.DataFrame, subs: pd.DataFrame,
                            events: pd.DataFrame, rng: np.random.Generator,
                            next_id_start: int) -> tuple[list[dict], list[dict], int]:
    """Generate renewal opportunities. Returns (opp_rows, stage_history_rows, next_id).

    One renewal opp per (customer × annual signup anniversary) that falls within
    the data window. Win/loss determined by Phase 1 lifecycle:
      - Won if customer was active 30+ days after anniversary
      - Lost if customer churned within ±30 days of anniversary
    """
    opp_rows = []
    stage_history_rows = []
    next_id = next_id_start

    data_end = pd.Timestamp("2025-12-31")
    customer_churn_dates = (
        events[events["event_type"] == "churn"]
        .set_index("customer_id")["event_date"]
        .to_dict()
    )

    for _, c in customers.iterrows():
        signup = pd.Timestamp(c["signup_date"])
        # Check each annual anniversary that falls in the window
        anniv_year = 1
        while True:
            anniv = signup + pd.DateOffset(years=anniv_year)
            if anniv > data_end:
                break

            # Determine win/loss
            churn_date_str = customer_churn_dates.get(c["customer_id"])
            won = True
            close_date = anniv
            if churn_date_str is not None:
                churn_date = pd.Timestamp(churn_date_str)
                if abs((anniv - churn_date).days) <= 30:
                    won = False
                    close_date = churn_date
                elif churn_date < anniv:
                    # Customer churned before this anniversary — no renewal opp at all
                    anniv_year += 1
                    continue

            # Amount = customer's MRR at opp creation time × 12
            created_date = anniv - pd.Timedelta(days=60)
            # Look up MRR at created_date's month (use start-of-month month string)
            cust_subs = subs[(subs["customer_id"] == c["customer_id"])]
            month_key = created_date.strftime("%Y-%m-01")
            month_row = cust_subs[cust_subs["month"] == month_key]
            if len(month_row) == 0:
                # Customer wasn't active at created_date (e.g. churned before) — skip
                anniv_year += 1
                continue
            mrr_at_renewal = float(month_row.iloc[0]["mrr"])
            amount = mrr_at_renewal * 12.0

            # Stage history: Renewal Discussion -> Negotiation -> Won/Lost
            disc_dwell = _sample_dwell_days(rng, RENEWAL_STAGE_DWELL_DAYS["Renewal Discussion"])
            neg_dwell = _sample_dwell_days(rng, RENEWAL_STAGE_DWELL_DAYS["Negotiation"])

            opp_id = f"OPP-{next_id:05d}"
            next_id += 1

            if won:
                disc_entered = created_date
                disc_exited = disc_entered + pd.Timedelta(days=disc_dwell)
                neg_entered = disc_exited
                neg_exited = close_date
                stage_history_rows.append({
                    "opportunity_id": opp_id, "stage": "Renewal Discussion",
                    "entered_date": disc_entered.strftime("%Y-%m-%d"),
                    "exited_date": disc_exited.strftime("%Y-%m-%d"),
                    "days_in_stage": disc_dwell,
                })
                stage_history_rows.append({
                    "opportunity_id": opp_id, "stage": "Negotiation",
                    "entered_date": neg_entered.strftime("%Y-%m-%d"),
                    "exited_date": neg_exited.strftime("%Y-%m-%d"),
                    "days_in_stage": (neg_exited - neg_entered).days,
                })
                current_stage = "Closed Won"
                status = "closed_won"
            else:
                # Lost: died in Renewal Discussion (most common) or Negotiation
                if rng.random() < 0.7:
                    death_stage = "Renewal Discussion"
                else:
                    death_stage = "Negotiation"
                if death_stage == "Renewal Discussion":
                    disc_entered = close_date - pd.Timedelta(days=disc_dwell)
                    stage_history_rows.append({
                        "opportunity_id": opp_id, "stage": "Renewal Discussion",
                        "entered_date": disc_entered.strftime("%Y-%m-%d"),
                        "exited_date": close_date.strftime("%Y-%m-%d"),
                        "days_in_stage": (close_date - disc_entered).days,
                    })
                    created_date = disc_entered
                else:
                    disc_entered = close_date - pd.Timedelta(days=disc_dwell + neg_dwell)
                    disc_exited = disc_entered + pd.Timedelta(days=disc_dwell)
                    stage_history_rows.append({
                        "opportunity_id": opp_id, "stage": "Renewal Discussion",
                        "entered_date": disc_entered.strftime("%Y-%m-%d"),
                        "exited_date": disc_exited.strftime("%Y-%m-%d"),
                        "days_in_stage": disc_dwell,
                    })
                    stage_history_rows.append({
                        "opportunity_id": opp_id, "stage": "Negotiation",
                        "entered_date": disc_exited.strftime("%Y-%m-%d"),
                        "exited_date": close_date.strftime("%Y-%m-%d"),
                        "days_in_stage": (close_date - disc_exited).days,
                    })
                    created_date = disc_entered
                current_stage = "Closed Lost"
                status = "closed_lost"

            opp_rows.append({
                "opportunity_id": opp_id,
                "customer_id": c["customer_id"],
                "account_name": c["company_name"],
                "segment": c["segment"],
                "acquisition_channel": c["acquisition_channel"],
                "owner_rep_id": str(rng.choice(REP_IDS)),
                "opportunity_type": "renewal",
                "created_date": created_date.strftime("%Y-%m-%d"),
                "close_date": close_date.strftime("%Y-%m-%d"),
                "amount": amount,
                "current_stage": current_stage,
                "status": status,
            })
            anniv_year += 1

    return opp_rows, stage_history_rows, next_id
```

- [ ] **Step 2: Smoke-test**

```bash
python -c "
from src.data_generator import (generate_customers, generate_subscriptions_and_events,
                                 GeneratorConfig, _generate_renewal_opps)
import numpy as np
cfg = GeneratorConfig()
customers = generate_customers(cfg)
subs, events = generate_subscriptions_and_events(customers, cfg)
rng = np.random.default_rng(cfg.rng_seed + 2)
opps, history, next_id = _generate_renewal_opps(customers, subs, events, rng, 1)
print(f'renewal opps: {len(opps)}, history: {len(history)}, next_id={next_id}')
print('first renewal opp:', opps[0])
"
```
Expected: ~1,000-1,500 renewal opps printed.

- [ ] **Step 3: Commit**

```bash
git add src/data_generator.py
git commit -m "feat(generator): renewal opportunities linked to Phase 1 churn events"
```

---

## Task 19: Generator — expansion opportunities

**Files:**
- Modify: `src/data_generator.py` (append)

- [ ] **Step 1: Append `_generate_expansion_opps`**

Append to `src/data_generator.py`:

```python
def _generate_expansion_opps(customers: pd.DataFrame, events: pd.DataFrame,
                              rng: np.random.Generator, next_id_start: int
                              ) -> tuple[list[dict], list[dict], int]:
    """Generate expansion opportunities — one per Phase 1 upgrade event.

    Returns (opp_rows, stage_history_rows, next_id).
    """
    opp_rows = []
    stage_history_rows = []
    next_id = next_id_start

    upgrades = events[events["event_type"] == "upgrade"]
    cust_by_id = customers.set_index("customer_id")

    for _, ev in upgrades.iterrows():
        cust_id = ev["customer_id"]
        if cust_id not in cust_by_id.index:
            continue
        c = cust_by_id.loc[cust_id]

        close_date = pd.Timestamp(ev["event_date"])
        dwell = _sample_dwell_days(rng, EXPANSION_STAGE_DWELL_DAYS["Expansion Discussion"])
        lead_time = int(rng.integers(30, 61))
        created_date = close_date - pd.Timedelta(days=lead_time)
        stage_entered = created_date
        # Expansion Discussion is a single stage — entered at created_date, exited at close
        amount = float(ev["mrr_delta"]) * 12.0

        opp_id = f"OPP-{next_id:05d}"
        next_id += 1

        opp_rows.append({
            "opportunity_id": opp_id,
            "customer_id": cust_id,
            "account_name": c["company_name"],
            "segment": c["segment"],
            "acquisition_channel": c["acquisition_channel"],
            "owner_rep_id": str(rng.choice(REP_IDS)),
            "opportunity_type": "expansion",
            "created_date": created_date.strftime("%Y-%m-%d"),
            "close_date": close_date.strftime("%Y-%m-%d"),
            "amount": amount,
            "current_stage": "Closed Won",
            "status": "closed_won",
        })
        stage_history_rows.append({
            "opportunity_id": opp_id,
            "stage": "Expansion Discussion",
            "entered_date": stage_entered.strftime("%Y-%m-%d"),
            "exited_date": close_date.strftime("%Y-%m-%d"),
            "days_in_stage": (close_date - stage_entered).days,
        })

    return opp_rows, stage_history_rows, next_id
```

- [ ] **Step 2: Smoke-test**

```bash
python -c "
from src.data_generator import (generate_customers, generate_subscriptions_and_events,
                                 GeneratorConfig, _generate_expansion_opps)
import numpy as np
cfg = GeneratorConfig()
customers = generate_customers(cfg)
subs, events = generate_subscriptions_and_events(customers, cfg)
rng = np.random.default_rng(cfg.rng_seed + 2)
opps, history, next_id = _generate_expansion_opps(customers, events, rng, 1)
print(f'expansion opps: {len(opps)}, history: {len(history)}, next_id={next_id}')
"
```
Expected: ~500-1,000 expansion opps printed.

- [ ] **Step 3: Commit**

```bash
git add src/data_generator.py
git commit -m "feat(generator): expansion opportunities linked to Phase 1 upgrade events"
```

---

## Task 20: Generator — pipeline snapshots + `generate_all_phase2` wiring + CSV write

**Files:**
- Modify: `src/data_generator.py` (append + edit `generate_all` and `write_to_disk`)
- Modify: `data/generated/opportunities.csv` (new file, written by generator)
- Modify: `data/generated/opportunity_stage_history.csv`
- Modify: `data/generated/pipeline_snapshots.csv`

- [ ] **Step 1: Append `_generate_pipeline_snapshots`**

Append to `src/data_generator.py`:

```python
def _generate_pipeline_snapshots(opps_df: pd.DataFrame, history_df: pd.DataFrame) -> list[dict]:
    """Reconstruct opportunity state at each quarterly snapshot date.

    For each (snapshot_date × opportunity), if the deal existed and was open at
    that date, record the stage it was in at that moment.
    """
    snapshot_rows = []
    # Pre-index history by opp for fast lookup
    history_df = history_df.copy()
    history_df["entered_date_ts"] = pd.to_datetime(history_df["entered_date"])
    history_df["exited_date_ts"] = pd.to_datetime(history_df["exited_date"])

    opps_df = opps_df.copy()
    opps_df["created_date_ts"] = pd.to_datetime(opps_df["created_date"])
    opps_df["close_date_ts"] = pd.to_datetime(opps_df["close_date"])

    for snap_date in SNAPSHOT_DATES:
        # Deals open at snap_date: created on/before, AND
        #   - status='open', OR
        #   - status closed but close_date > snap_date
        open_at_snap = opps_df[
            (opps_df["created_date_ts"] <= snap_date)
            & (
                (opps_df["status"] == "open")
                | (opps_df["close_date_ts"] > snap_date)
            )
        ]
        for _, opp in open_at_snap.iterrows():
            opp_history = history_df[history_df["opportunity_id"] == opp["opportunity_id"]]
            # Find the stage the deal was in at snap_date
            in_stage = opp_history[
                (opp_history["entered_date_ts"] <= snap_date)
                & (
                    opp_history["exited_date_ts"].isna()
                    | (opp_history["exited_date_ts"] > snap_date)
                )
            ]
            if len(in_stage) == 0:
                continue
            stage = in_stage.iloc[0]["stage"]
            snapshot_rows.append({
                "snapshot_date": snap_date.strftime("%Y-%m-%d"),
                "opportunity_id": opp["opportunity_id"],
                "stage_at_snapshot": stage,
                "amount": opp["amount"],
                "forecast_category": FORECAST_CATEGORY_BY_STAGE.get(stage, "Pipeline"),
                "expected_close_date": opp["close_date"],
            })
    return snapshot_rows


def generate_phase2(customers: pd.DataFrame, subs: pd.DataFrame, events: pd.DataFrame
                     ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate Phase 2 tables: opportunities, opportunity_stage_history, pipeline_snapshots.

    Deterministic given Phase 1 outputs and RNG_SEED+2.
    """
    rng = np.random.default_rng(RNG_SEED + 2)

    nb_opps, nb_history = _generate_new_business_opps(customers, rng)
    next_id = len(nb_opps) + 1

    ren_opps, ren_history, next_id = _generate_renewal_opps(customers, subs, events, rng, next_id)
    exp_opps, exp_history, next_id = _generate_expansion_opps(customers, events, rng, next_id)

    opps_df = pd.DataFrame(nb_opps + ren_opps + exp_opps)
    history_df = pd.DataFrame(nb_history + ren_history + exp_history)

    snapshots = _generate_pipeline_snapshots(opps_df, history_df)
    snapshots_df = pd.DataFrame(snapshots)

    return opps_df, history_df, snapshots_df
```

- [ ] **Step 2: Modify `write_to_disk` to also write Phase 2 CSVs**

Find the existing `write_to_disk` function in `src/data_generator.py` and replace it with:

```python
def write_to_disk(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    customers, subs, events = generate_all()
    customers.drop(columns=[c for c in customers.columns if c.endswith("_dt")], errors="ignore", inplace=True)
    customers.to_csv(out_dir / "customers.csv", index=False)
    subs.to_csv(out_dir / "subscriptions.csv", index=False)
    events.to_csv(out_dir / "events.csv", index=False)

    # Phase 2 tables
    opps_df, history_df, snapshots_df = generate_phase2(customers, subs, events)
    opps_df.to_csv(out_dir / "opportunities.csv", index=False)
    history_df.to_csv(out_dir / "opportunity_stage_history.csv", index=False)
    snapshots_df.to_csv(out_dir / "pipeline_snapshots.csv", index=False)

    print(f"Wrote {len(customers)} customers, {len(subs)} subscription rows, "
          f"{len(events)} events, {len(opps_df)} opportunities, "
          f"{len(history_df)} stage history rows, {len(snapshots_df)} snapshots to {out_dir}")
```

- [ ] **Step 3: Run the generator end-to-end**

```bash
python -m src.data_generator
```
Expected output: a line like `Wrote 720 customers, ~9500 subscription rows, ~2500 events, ~3200 opportunities, ~8000 stage history rows, ~1200 snapshots to .../data/generated`.

- [ ] **Step 4: Quick sanity check on the generated data**

```bash
python -c "
import pandas as pd
opps = pd.read_csv('data/generated/opportunities.csv')
print('opp counts by type:'); print(opps['opportunity_type'].value_counts())
print('status counts:'); print(opps['status'].value_counts())
print('segment x status:'); print(opps.groupby(['segment','status']).size())
history = pd.read_csv('data/generated/opportunity_stage_history.csv')
print(f'history rows: {len(history)}')
snapshots = pd.read_csv('data/generated/pipeline_snapshots.csv')
print(f'snapshot rows: {len(snapshots)}; unique snapshot dates: {snapshots[\"snapshot_date\"].nunique()}')
"
```
Expected: opportunity_type roughly 60% renewal, 30% new_business, 10% expansion. status mostly closed_won.

- [ ] **Step 5: Run pytest to confirm Phase 1 metric tests still pass and no new failures**

```bash
pytest -v
```
Expected: all ~42 tests pass. Phase 1 byte-identical test is added in Task 21 — for now we just verify nothing broke.

- [ ] **Step 6: Commit (generator code + generated CSVs)**

```bash
git add src/data_generator.py data/generated/opportunities.csv data/generated/opportunity_stage_history.csv data/generated/pipeline_snapshots.csv
git commit -m "feat(generator): pipeline_snapshots + generate_phase2 wiring; commit generated CSVs"
```

---

## Task 21: Insight-protection + Phase 1 byte-identical tests

**Files:**
- Modify: `tests/test_data_generator.py` (append)

- [ ] **Step 1: Append the two new tests**

Append to `tests/test_data_generator.py`:

```python
import hashlib
from pathlib import Path

import pandas as pd
import pytest


DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "generated"


@pytest.fixture(scope="module")
def generated_phase2():
    """Load the committed Phase 2 CSVs."""
    opps = pd.read_csv(DATA_DIR / "opportunities.csv")
    history = pd.read_csv(DATA_DIR / "opportunity_stage_history.csv")
    return opps, history


def test_midmarket_poc_stall_is_at_least_2x_smb(generated_phase2):
    """Engineered insight protection: Mid-Market dwells in POC at least 2x as
    long as SMB does. If a future tweak weakens this, the test fails loudly.
    """
    opps, history = generated_phase2

    nb_opps = opps[opps["opportunity_type"] == "new_business"]
    poc = history[history["stage"] == "Proof of Concept"]
    poc_completed = poc[poc["exited_date"].notna()].copy()
    joined = poc_completed.merge(
        nb_opps[["opportunity_id", "segment"]], on="opportunity_id", how="inner"
    )

    by_seg = joined.groupby("segment")["days_in_stage"].mean()
    assert "Mid-Market" in by_seg.index and "SMB" in by_seg.index
    ratio = by_seg["Mid-Market"] / by_seg["SMB"]
    assert ratio >= 2.0, (
        f"Mid-Market POC stall insight has weakened: Mid-Market avg POC dwell = "
        f"{by_seg['Mid-Market']:.1f} days, SMB = {by_seg['SMB']:.1f} days, "
        f"ratio = {ratio:.2f} (must be ≥ 2.0). Re-tune NB_STAGE_DWELL_DAYS."
    )


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_phase1_csvs_unchanged_after_phase2_generator():
    """Running the full generator (including Phase 2) must produce the same
    customers.csv / subscriptions.csv / events.csv as Phase 1 committed.

    Compares hashes of currently-committed Phase 1 CSVs to freshly-regenerated
    output. If they differ, Phase 2 generator code has accidentally consumed
    Phase 1's RNG stream or otherwise perturbed determinism.
    """
    import tempfile
    from src.data_generator import write_to_disk

    expected = {
        "customers.csv": _file_hash(DATA_DIR / "customers.csv"),
        "subscriptions.csv": _file_hash(DATA_DIR / "subscriptions.csv"),
        "events.csv": _file_hash(DATA_DIR / "events.csv"),
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        write_to_disk(Path(tmpdir))
        for name, expected_hash in expected.items():
            actual_hash = _file_hash(Path(tmpdir) / name)
            assert actual_hash == expected_hash, (
                f"{name} differs after regeneration. Phase 2 generator is "
                f"perturbing Phase 1 RNG or outputs."
            )
```

- [ ] **Step 2: Run the tests**

```bash
pytest tests/test_data_generator.py -v
```
Expected: existing Phase 1 generator tests pass + 2 new tests pass.

If `test_midmarket_poc_stall_is_at_least_2x_smb` fails: increase `NB_STAGE_DWELL_DAYS["Proof of Concept"]["Mid-Market"]` (e.g., 45 → 55) and decrease the SMB value (15 → 12), regenerate (`python -m src.data_generator`), and re-run.

- [ ] **Step 3: Commit**

```bash
git add tests/test_data_generator.py
git commit -m "test: insight-protection (Mid-Market POC ≥ 2x SMB) and Phase 1 byte-identical invariant"
```

---

## Task 22: Viz builders — stage funnel, velocity heatmap, forecast trends, segment bars

**Files:**
- Modify: `src/viz.py` (append)

- [ ] **Step 1: Append new figure builders**

Append to `src/viz.py`:

```python
def stage_funnel_figure(opps: pd.DataFrame, as_of_date: str) -> go.Figure:
    """Funnel of total pipeline $ by stage, new_business deals only.

    Stages in NB order; bars colored from cyan (early) to indigo (late).
    """
    nb_open = opps[
        (opps["opportunity_type"] == "new_business")
        & (opps["status"] == "open")
        & (opps["created_date"] <= as_of_date)
    ]
    stages = ["Discovery", "Qualification", "Proof of Concept", "Negotiation"]
    by_stage = nb_open.groupby("current_stage")["amount"].sum().reindex(stages, fill_value=0)

    fig = go.Figure(go.Funnel(
        y=stages,
        x=by_stage.values,
        textinfo="value+percent initial",
        marker={"color": [CADENZA_ACCENT, "#0EA5E9", CADENZA_PRIMARY, "#0F172A"]},
    ))
    fig.update_layout(
        title="Pipeline by Stage (New Business)",
        height=420,
        xaxis_title="Pipeline ($)",
    )
    return fig


def stage_velocity_heatmap(history: pd.DataFrame, opps: pd.DataFrame,
                            start_date: str, end_date: str) -> go.Figure:
    """Heatmap of average days-in-stage, rows=segment, cols=new_business stage.

    Cell color: green (fast) to red (slow) via the Cadenza palette. This is
    where the Mid-Market POC stall pops visually.
    """
    nb_opps = opps[opps["opportunity_type"] == "new_business"]
    poc = history[history["exited_date"].notna()].copy()
    poc["entered_date"] = pd.to_datetime(poc["entered_date"])
    poc = poc[
        (poc["entered_date"] >= pd.Timestamp(start_date))
        & (poc["entered_date"] < pd.Timestamp(end_date))
    ]
    joined = poc.merge(nb_opps[["opportunity_id", "segment"]], on="opportunity_id", how="inner")

    stages = ["Discovery", "Qualification", "Proof of Concept", "Negotiation"]
    segments = ["SMB", "Mid-Market", "Enterprise"]
    matrix = (
        joined.groupby(["segment", "stage"])["days_in_stage"].mean()
        .unstack(level="stage")
        .reindex(index=segments, columns=stages)
    )

    fig = go.Figure(go.Heatmap(
        z=matrix.values,
        x=stages,
        y=segments,
        colorscale=[[0.0, CADENZA_GOOD], [0.5, "#FCD34D"], [1.0, CADENZA_BAD]],
        text=matrix.round(1).values,
        texttemplate="%{text} days",
        colorbar={"title": "Avg days"},
        hovertemplate="%{y} · %{x}<br>Avg %{z:.1f} days<extra></extra>",
    ))
    fig.update_layout(
        title="Stage Velocity — Average Days in Stage, by Segment",
        height=360,
        xaxis_title="Stage",
        yaxis_title="Segment",
    )
    return fig


def forecast_buckets_figure(buckets: dict[str, float], target: float | None = None) -> go.Figure:
    """Horizontal stacked bar: Commit / Best Case / Pipeline for a single snapshot."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=["Forecast"], x=[buckets["commit"]], name="Commit",
        orientation="h", marker_color=CADENZA_PRIMARY,
        text=f"${buckets['commit']:,.0f}", textposition="inside",
    ))
    fig.add_trace(go.Bar(
        y=["Forecast"], x=[buckets["best_case"]], name="Best Case",
        orientation="h", marker_color=CADENZA_ACCENT,
        text=f"${buckets['best_case']:,.0f}", textposition="inside",
    ))
    fig.add_trace(go.Bar(
        y=["Forecast"], x=[buckets["pipeline"]], name="Pipeline",
        orientation="h", marker_color=CADENZA_NEUTRAL,
        text=f"${buckets['pipeline']:,.0f}", textposition="inside",
    ))
    if target is not None:
        fig.add_vline(x=target, line_dash="dash", line_color=CADENZA_BAD,
                      annotation_text=f"Target: ${target:,.0f}", annotation_position="top")
    fig.update_layout(
        barmode="stack",
        title="Forecast Buckets",
        height=200,
        xaxis_title="$",
        showlegend=True,
    )
    return fig


def forecast_bias_bar(bias: pd.DataFrame) -> go.Figure:
    """Grouped bar: per-segment weighted_forecast vs. actual_closed_won."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=bias["segment"], y=bias["weighted_forecast"], name="Weighted Forecast",
        marker_color=CADENZA_PRIMARY,
    ))
    fig.add_trace(go.Bar(
        x=bias["segment"], y=bias["actual_closed_won"], name="Actual Closed-Won",
        marker_color=CADENZA_ACCENT,
    ))
    fig.update_layout(
        barmode="group",
        title="Forecast vs. Actual — by Segment",
        height=380,
        yaxis_title="$",
    )
    return fig
```

- [ ] **Step 2: Quick visual smoke-test in a Python REPL**

```bash
python -c "
import pandas as pd
from src import viz
opps = pd.read_csv('data/generated/opportunities.csv')
history = pd.read_csv('data/generated/opportunity_stage_history.csv')
fig1 = viz.stage_funnel_figure(opps, '2025-12-01')
fig2 = viz.stage_velocity_heatmap(history, opps, '2024-01-01', '2025-12-31')
fig3 = viz.forecast_buckets_figure({'commit': 50000, 'best_case': 120000, 'pipeline': 30000}, target=200000)
print('all three figures built successfully:', type(fig1).__name__, type(fig2).__name__, type(fig3).__name__)
"
```
Expected: all 3 figure objects build without exceptions.

- [ ] **Step 3: Commit**

```bash
git add src/viz.py
git commit -m "feat(viz): stage funnel, velocity heatmap, forecast buckets bar, segment bias bar"
```

---

## Task 23: `pages/5_Pipeline.py`

**Files:**
- Create: `pages/5_Pipeline.py`

- [ ] **Step 1: Create the page**

```python
"""Cadenza Pipeline — pipeline coverage, stage velocity, conversion, aging.

The hero viz is the Stage Velocity Heatmap, which surfaces the engineered
'Mid-Market POC stall' insight without further drilling.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src import pipeline as pl
from src import viz

st.set_page_config(page_title="Cadenza — Pipeline", layout="wide")

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "generated"


@st.cache_data
def load_data():
    opps = pd.read_csv(DATA_DIR / "opportunities.csv")
    history = pd.read_csv(DATA_DIR / "opportunity_stage_history.csv")
    return opps, history


def sidebar_filters(opps: pd.DataFrame) -> dict:
    st.sidebar.markdown("## Cadenza")
    st.sidebar.caption("Sales engagement platform · fictional · portfolio project")
    st.sidebar.divider()
    st.sidebar.markdown("### Filters")

    as_of = st.sidebar.date_input("As-of date", value=pd.Timestamp("2025-12-01"))
    segments = ["All"] + sorted(opps["segment"].unique().tolist())
    segment = st.sidebar.selectbox("Segment", segments)
    channels = ["All"] + sorted(opps["acquisition_channel"].unique().tolist())
    channel = st.sidebar.selectbox("Acquisition channel", channels)
    types = ["All"] + sorted(opps["opportunity_type"].unique().tolist())
    opp_type = st.sidebar.selectbox("Opportunity type", types)
    return {"as_of": as_of.strftime("%Y-%m-%d"), "segment": segment,
            "channel": channel, "opp_type": opp_type}


def apply_filters(opps: pd.DataFrame, f: dict) -> pd.DataFrame:
    v = opps
    if f["segment"] != "All":
        v = v[v["segment"] == f["segment"]]
    if f["channel"] != "All":
        v = v[v["acquisition_channel"] == f["channel"]]
    if f["opp_type"] != "All":
        v = v[v["opportunity_type"] == f["opp_type"]]
    return v


def main():
    st.title("Pipeline")
    st.caption("Open deals, stage velocity, conversion, and aging. The Stage "
               "Velocity Heatmap surfaces a Mid-Market POC stall.")

    opps_all, history_all = load_data()
    f = sidebar_filters(opps_all)
    opps = apply_filters(opps_all, f)

    # Editable target
    target = st.sidebar.number_input("Quarterly pipeline target ($)",
                                      min_value=0, value=5_000_000, step=100_000)

    # KPIs
    cur_total = pl.total_pipeline(opps, f["as_of"])
    cur_weighted = pl.weighted_pipeline(opps, f["as_of"])
    cur_coverage = pl.pipeline_coverage(opps, target, f["as_of"])
    ttm_start = (pd.Timestamp(f["as_of"]) - pd.DateOffset(months=12)).strftime("%Y-%m-01")
    cur_win = pl.win_rate(opps, ttm_start, f["as_of"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Pipeline", f"${cur_total:,.0f}")
    c2.metric("Weighted Pipeline", f"${cur_weighted:,.0f}")
    c3.metric("Coverage Ratio", f"{cur_coverage:.2f}×",
              delta="healthy" if cur_coverage >= 3.0 else "below 3×",
              delta_color="normal" if cur_coverage >= 3.0 else "inverse")
    c4.metric("Win Rate (TTM)", f"{cur_win:.1%}")

    st.divider()

    # Pipeline mix companion stat
    open_mix = opps[(opps["status"] == "open") & (opps["created_date"] <= f["as_of"])]
    mix = open_mix.groupby("opportunity_type")["amount"].sum().to_dict()
    st.caption(
        f"Pipeline mix: ${mix.get('new_business', 0):,.0f} new · "
        f"${mix.get('renewal', 0):,.0f} renewal · "
        f"${mix.get('expansion', 0):,.0f} expansion"
    )

    # Stage Funnel
    st.plotly_chart(viz.stage_funnel_figure(opps, f["as_of"]), use_container_width=True)

    # Stage Velocity Heatmap — hero viz
    st.subheader("Stage Velocity by Segment")
    st.caption("Average days each segment spends in each new-business stage. "
               "Watch the Proof of Concept column.")
    history = history_all[history_all["opportunity_id"].isin(opps["opportunity_id"])]
    st.plotly_chart(
        viz.stage_velocity_heatmap(history, opps, ttm_start, f["as_of"]),
        use_container_width=True,
    )

    # Stage Conversion Table
    st.subheader("Stage-to-Stage Conversion")
    transitions = [
        ("Discovery", "Qualification"),
        ("Qualification", "Proof of Concept"),
        ("Proof of Concept", "Negotiation"),
        ("Negotiation", "Closed Won"),
    ]
    seg_rows = []
    for seg in ["SMB", "Mid-Market", "Enterprise"]:
        seg_opp_ids = opps[opps["segment"] == seg]["opportunity_id"]
        seg_hist = history_all[history_all["opportunity_id"].isin(seg_opp_ids)]
        row = {"segment": seg}
        for fr, to in transitions:
            if to == "Closed Won":
                # Use the deals where final stage was Negotiation AND status=won
                won_ids = set(opps[
                    (opps["segment"] == seg)
                    & (opps["status"] == "closed_won")
                    & (opps["opportunity_type"] == "new_business")
                ]["opportunity_id"])
                neg_entered_ids = set(seg_hist[seg_hist["stage"] == "Negotiation"]["opportunity_id"])
                rate = len(won_ids & neg_entered_ids) / len(neg_entered_ids) if neg_entered_ids else 0.0
            else:
                rate = pl.stage_conversion(seg_hist, fr, to, ttm_start, f["as_of"])
            row[f"{fr[:4]}→{to[:4]}"] = rate
        seg_rows.append(row)
    conv_df = pd.DataFrame(seg_rows).set_index("segment")
    st.dataframe(
        conv_df.style.format("{:.0%}").highlight_min(axis=0, color="#FECACA"),
        use_container_width=True,
    )

    # Aging Deals
    st.subheader("Aging Deals — open > 60 days in current stage")
    aging = pl.aging_deals(opps, history_all, f["as_of"], threshold_days=60)
    if len(aging) == 0:
        st.info("No aging deals. (Threshold = 60 days in current stage.)")
    else:
        display_cols = ["opportunity_id", "account_name", "segment", "current_stage",
                        "days_in_current_stage", "amount", "owner_rep_id"]
        st.dataframe(
            aging[display_cols].head(50),
            use_container_width=True,
            hide_index=True,
            column_config={"amount": st.column_config.NumberColumn(format="$%.0f")},
        )


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the dashboard locally and visit the Pipeline page**

```bash
streamlit run Overview.py
```
Open http://localhost:8501, click "Pipeline" in the sidebar. Verify:
- All 4 KPI tiles render with reasonable values.
- Stage Funnel shows 4 stages.
- Stage Velocity Heatmap shows Mid-Market with a markedly slower POC stage than SMB / Enterprise.
- Stage Conversion table shows percentages with Mid-Market POC→Negotiation highlighted as the lowest.
- Aging Deals table renders.

Stop the server with Ctrl+C.

- [ ] **Step 3: Commit**

```bash
git add pages/5_Pipeline.py
git commit -m "feat(app): pipeline page with KPIs, funnel, velocity heatmap, conversion, aging"
```

---

## Task 24: `pages/6_Forecasting.py`

**Files:**
- Create: `pages/6_Forecasting.py`

- [ ] **Step 1: Create the page**

```python
"""Cadenza Forecasting — commit/best-case/pipeline buckets, accuracy trend,
segment-level bias.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src import forecast as fc
from src import viz

st.set_page_config(page_title="Cadenza — Forecasting", layout="wide")

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "generated"


@st.cache_data
def load_data():
    opps = pd.read_csv(DATA_DIR / "opportunities.csv")
    snapshots = pd.read_csv(DATA_DIR / "pipeline_snapshots.csv")
    return opps, snapshots


def main():
    st.title("Forecasting")
    st.caption("Quarterly forecast buckets, accuracy trend, and segment-level bias.")

    opps, snapshots = load_data()

    snap_dates = sorted(snapshots["snapshot_date"].unique())
    snap_date = st.sidebar.selectbox("Snapshot quarter", snap_dates, index=len(snap_dates) - 1)

    target = st.sidebar.number_input("Quarter target ($)",
                                      min_value=0, value=2_000_000, step=100_000)

    buckets = fc.forecast_buckets(snapshots, snap_date)
    last_completed = snap_dates[snap_dates.index(snap_date) - 1] if snap_dates.index(snap_date) > 0 else None
    last_acc = fc.forecast_accuracy(snapshots, opps, last_completed) if last_completed else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Commit", f"${buckets['commit']:,.0f}")
    c2.metric("Best Case", f"${buckets['best_case']:,.0f}")
    c3.metric("Pipeline", f"${buckets['pipeline']:,.0f}")
    c4.metric("Last-Quarter Accuracy",
              f"{last_acc:.1%}" if last_acc is not None else "n/a",
              help="Weighted forecast at last snapshot ÷ actual closed-won that quarter.")

    st.divider()

    st.subheader(f"Forecast Buckets — {snap_date}")
    st.plotly_chart(viz.forecast_buckets_figure(buckets, target=target), use_container_width=True)

    st.subheader("Forecast Accuracy Trend")
    st.caption("Per quarterly snapshot: weighted forecast vs. actual closed-won. "
               "100% = perfect; >100% = over-forecast.")
    trend = fc.forecast_accuracy_trend(snapshots, opps).dropna(subset=["accuracy"])
    if len(trend) > 0:
        st.plotly_chart(
            viz.trend_figure(trend, "snapshot_date", ["accuracy"],
                              "Forecast Accuracy Over Time", reference=1.0),
            use_container_width=True,
        )
    else:
        st.info("No snapshots with completed quarters yet.")

    st.subheader(f"Forecast Bias by Segment — {snap_date}")
    bias = fc.forecast_bias_by_segment(snapshots, opps, snap_date)
    st.plotly_chart(viz.forecast_bias_bar(bias), use_container_width=True)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the dashboard and visit the Forecasting page**

```bash
streamlit run Overview.py
```
Open http://localhost:8501, click "Forecasting" in the sidebar. Verify:
- 4 KPI tiles render.
- Forecast Buckets stacked bar renders with the target line.
- Forecast Accuracy Trend line shows 8 data points (one per snapshot).
- Forecast Bias by Segment grouped bar renders.

Stop with Ctrl+C.

- [ ] **Step 3: Commit**

```bash
git add pages/6_Forecasting.py
git commit -m "feat(app): forecasting page with buckets, accuracy trend, segment bias"
```

---

## Task 25: Update `pages/7_About.py` — extend metric definitions, add Phase 2 narrative

The current About page is a simple markdown-only page (no DataFrame). Metric definitions are a markdown table inside an `st.markdown` block.

**Files:**
- Modify: `pages/7_About.py`

- [ ] **Step 1: Extend the existing metric definitions markdown table**

The Phase 1 metric table is in an `st.markdown` block under the "Metric definitions" `st.subheader`. Append Phase 2 rows so the table becomes a single combined table. Replace this block:

```python
    st.subheader("Metric definitions")
    st.markdown(
        """
        | Metric | Formula | Notes |
        | --- | --- | --- |
        | **ARR** | MRR × 12 | Point-in-time run rate. |
        | **Logo Churn** | customers_churned_in_period ÷ customers_active_at_start | Counts customers. |
        | **Gross Revenue Churn** | (churn_MRR + contraction_MRR) ÷ MRR_at_start | Excludes expansion. |
        | **GRR** | 1 − Gross Revenue Churn, capped at 100% | Floor retention. |
        | **NRR** | (start_MRR − churn − contraction + expansion) ÷ start_MRR | Includes expansion; can exceed 100%. |

        TTM = trailing 12 months. All numerators and denominators use a cohort
        defined as "customers active at the start of the period."
        """
    )
```

with the extended version:

```python
    st.subheader("Metric definitions")
    st.markdown(
        """
        **Phase 1 — Retention**

        | Metric | Formula | Notes |
        | --- | --- | --- |
        | **ARR** | MRR × 12 | Point-in-time run rate. |
        | **Logo Churn** | customers_churned_in_period ÷ customers_active_at_start | Counts customers. |
        | **Gross Revenue Churn** | (churn_MRR + contraction_MRR) ÷ MRR_at_start | Excludes expansion. |
        | **GRR** | 1 − Gross Revenue Churn, capped at 100% | Floor retention. |
        | **NRR** | (start_MRR − churn − contraction + expansion) ÷ start_MRR | Includes expansion; can exceed 100%. |

        **Phase 2 — Pipeline & Forecasting**

        | Metric | Formula | Notes |
        | --- | --- | --- |
        | **Total Pipeline** | sum(amount) for open opps with created_date ≤ as_of | Includes all opp types unless filtered. |
        | **Weighted Pipeline** | sum(amount × stage_probability) for open opps | Discovery 10%, Qualification 20%, POC 40%, Negotiation 65%. |
        | **Pipeline Coverage** | total_pipeline ÷ quarter_target | Reported as a multiple; 3.0× is the conventional healthy threshold. |
        | **Win Rate (TTM)** | closed_won ÷ (closed_won + closed_lost) over close_date window | Pre-filter by opp_type — renewals win ~90%, new business ~25%. |
        | **Avg Sales Cycle (days)** | mean(close_date − created_date) for closed-won in window | Closed-won only; loss cycles distort. |
        | **Avg Days in Stage** | mean(days_in_stage) over completed (exited) stage occupancies in window | Excludes in-progress stages. |
        | **Stage Conversion** | of deals that exited from_stage, fraction that ever reached to_stage | Excludes deals still in from_stage. |
        | **Forecast Buckets** | sum by category: Negotiation = Commit, POC/Renewal/Expansion Disc = Best Case, Discovery/Qual = Pipeline | Standard RevOps categorization. |
        | **Forecast Accuracy** | weighted_pipeline at snapshot ÷ actual closed-won in [snapshot, snapshot + 3mo) | 1.0 = perfect; >1.0 = over-forecast; <1.0 = under-forecast. |

        TTM = trailing 12 months. All numerators and denominators use a cohort
        defined as "customers active at the start of the period."
        """
    )
```

- [ ] **Step 2: Add a Phase 2 narrative section**

Find the "## The story" section in the first `st.markdown` block (under the page title), and after the existing "## What I'd do next at a real company" section, append a new Phase 2 narrative. Specifically, edit the existing big `st.markdown` block to add this new content just before the closing `"""`:

```markdown

        ## Phase 2 — Pipeline & Forecasting

        Phase 2 adds opportunity-level data on top of the Phase 1 subscription model.
        Each non-Self-Serve Phase 1 customer was won as a new-business opportunity
        that closed on their signup date; each annual renewal and each Phase 1
        upgrade event spawns its own opportunity record. Self-Serve Promo customers
        have no opportunity (self-serve is no-touch).

        Three motions are modeled distinctly:

        - **New Business** — five-stage cycle (Discovery → Qualification → POC → Negotiation → Closed)
        - **Renewal** — short two-stage cycle on each annual anniversary; lost renewals align
          to Phase 1 churn events within ±30 days
        - **Expansion** — one-stage cycle, closes on the date of the Phase 1 upgrade event

        The engineered Phase 2 insight: **Mid-Market deals stall in Proof of Concept ~2×
        longer than SMB or Enterprise**, with markedly worse POC → Negotiation conversion.
        Surfaces in the Stage Velocity Heatmap on the Pipeline page. The recommendation:
        the POC motion is built for SMB (fast, self-guided) and Enterprise (custom,
        white-glove); Mid-Market falls in the gap and needs its own playbook.
```

- [ ] **Step 3: Update the tech-stack section to mention Phase 2 modules**

Find this block:

```python
    st.subheader("Tech stack")
    st.markdown(
        """
        - Python 3.11, pandas, numpy
        - Streamlit (app) + Plotly (charts)
        - pytest (test suite proving metric formulas against hand-built fixtures)
        - GitHub + Streamlit Community Cloud (deployment)
        """
    )
```

Replace with:

```python
    st.subheader("Tech stack")
    st.markdown(
        """
        - Python 3.12, pandas, numpy
        - Streamlit (app) + Plotly (charts)
        - pytest (~44 tests across two phases, hand-built fixtures)
        - GitHub + Streamlit Community Cloud (deployment)

        **Architecture:** Pure-function data pipeline. `src/data_generator.py` produces
        deterministic CSVs (seed=42). `src/metrics.py` + `src/cohorts.py` compute
        retention; `src/pipeline.py` + `src/forecast.py` compute pipeline metrics.
        `src/viz.py` builds Plotly figures with no Streamlit imports. Pages in
        `Overview.py` and `pages/*.py` are presentation-only.
        """
    )
```

- [ ] **Step 4: Visually verify**

```bash
streamlit run Overview.py
```
Open http://localhost:8501, navigate to "About". Confirm:
- Phase 2 narrative renders below "What I'd do next"
- Metric table now has both Phase 1 and Phase 2 sub-tables
- Tech stack reflects Python 3.12 and the new modules

Stop with Ctrl+C.

- [ ] **Step 5: Commit**

```bash
git add pages/7_About.py
git commit -m "docs(app): extend About page with Phase 2 metric definitions and narrative"
```

---

## Task 26: Update README, CLAUDE.md, CHANGELOG; final test run and verification

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update `README.md`**

Find the section that lists the dashboard pages (likely a bullet list naming Overview / Cohort Analysis / Segment Drilldown / About) and add the two new Phase 2 pages. Add a brief Phase 2 paragraph if Phase 1 had a "Phase" structure.

Use the Edit tool. The exact lines depend on the current README, but the additions should include:
- "Pipeline — pipeline coverage, stage velocity (the Mid-Market POC stall), conversion, aging deals"
- "Forecasting — commit/best-case/pipeline buckets, forecast accuracy trend, segment bias"
- A short note that Phase 2 is shipped with the same conventions (TDD with hand-built fixtures, Cadenza brand palette).

- [ ] **Step 2: Update `CLAUDE.md`**

Update the architecture diagram in CLAUDE.md to reflect new modules:

```
src/data_generator.py → data/generated/*.csv → src/metrics.py + src/cohorts.py + src/pipeline.py + src/forecast.py → src/viz.py → Overview.py + pages/
```

Flip Phase 2's status from "planned, not started" to "shipped" in the project overview.

- [ ] **Step 3: Update `CHANGELOG.md`**

Add a new entry at the top:

```markdown
## Phase 2 — Pipeline & Forecasting

**Date:** 2026-05-15 (planning) / shipped on completion

- Generator extended with opportunities, opportunity_stage_history, pipeline_snapshots
- Three opportunity types: new_business, renewal, expansion — linked to Phase 1 customers
- Two new pages: Pipeline (stage funnel, velocity heatmap, conversion, aging) and Forecasting (buckets, accuracy trend, segment bias)
- Engineered insight: Mid-Market POC stall (~2× SMB dwell, ~half the POC→Negotiation conversion)
- Phase 1 data, modules, pages, tests untouched (byte-identical CSVs enforced by test)
- `pages/4_About.py` renamed to `pages/7_About.py` for sidebar ordering
- ~24 new pytest tests (metric tests + insight protection + Phase 1 invariant); total suite ~44 tests, all green
```

- [ ] **Step 4: Run the full test suite**

```bash
pytest -v
```
Expected: ~44 tests total (20 Phase 1 + ~22 Phase 2 metric + 2 new generator tests), all pass.

- [ ] **Step 5: Manually verify the live app**

```bash
streamlit run Overview.py
```
Walk through every page in order:
1. **Overview** — same as Phase 1, unchanged.
2. **Cohort Analysis** — same as Phase 1, unchanged.
3. **Segment Drilldown** — same as Phase 1, unchanged.
4. **Pipeline (NEW)** — verify KPIs, funnel, heatmap, conversion, aging table.
5. **Forecasting (NEW)** — verify buckets, accuracy trend, segment bias.
6. **About** — now appears last in sidebar; verify Phase 2 metric defs and narrative render.

Stop with Ctrl+C.

- [ ] **Step 6: Commit**

```bash
git add README.md CLAUDE.md CHANGELOG.md
git commit -m "docs: README + CLAUDE + CHANGELOG updates for Phase 2 shipping"
```

- [ ] **Step 7: Verify clean state**

```bash
git status
git log --oneline -30
```
Expected: clean working tree; ~26 new commits since the start of Phase 2; one logical commit per task.

---

## Done

At this point Phase 2 is complete. The two new pages are live locally; pushing to `main` triggers a Streamlit Cloud auto-redeploy and the same URL (`https://cadenza-retention-analytics.streamlit.app`) will surface both new pages.

The dashboard now demonstrates both halves of SaaS RevOps fluency: retention (Phase 1) and pipeline/forecasting (Phase 2). The two engineered insights — Self-Serve Promo churn and Mid-Market POC stall — give the case study two distinct "moments" worth a 30-second talking point each in an interview.
