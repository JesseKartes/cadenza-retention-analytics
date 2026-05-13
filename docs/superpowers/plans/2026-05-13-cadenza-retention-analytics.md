# Cadenza Retention Analytics — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python/Streamlit portfolio application that calculates the canonical SaaS retention metrics (ARR, NRR, GRR, Logo Churn, Gross Revenue Churn, cohort retention) over a synthetic 36-month subscription dataset for fictional company "Cadenza," surfacing a deliberately-engineered hidden churn pattern in a specific acquisition-channel cohort.

**Architecture:** A four-stage pipeline. (1) `src/data_generator.py` produces three flat CSVs (`customers.csv`, `subscriptions.csv`, `events.csv`). (2) `src/metrics.py` and `src/cohorts.py` compute aggregates from those CSVs using pandas. (3) `src/viz.py` provides reusable Plotly chart builders. (4) `streamlit_app.py` plus three `pages/*.py` files render the multi-page Streamlit dashboard. Strict separation: data layer is CSV files, business logic is pure pandas functions, presentation is Streamlit + Plotly. Each layer is independently testable.

**Tech Stack:** Python 3.11+, pandas, numpy, plotly, streamlit, pytest.

**Spec reference:** `docs/superpowers/specs/2026-05-13-cadenza-retention-analytics-design.md`

---

## File Structure (locked from spec)

```
revops_portfolio_claude/
├── README.md                     # Case-study format (Task 17)
├── requirements.txt              # Task 1
├── streamlit_app.py              # Entry point + Overview page (Task 12)
├── pages/
│   ├── 2_Cohort_Analysis.py     # Task 13
│   ├── 3_Segment_Drilldown.py   # Task 14
│   └── 4_About.py                # Task 15
├── src/
│   ├── __init__.py               # Task 1
│   ├── data_generator.py         # Tasks 2-5
│   ├── metrics.py                # Tasks 6-8
│   ├── cohorts.py                # Tasks 9-10
│   └── viz.py                    # Task 11
├── data/
│   └── generated/                # Created by generator; .gitkeep in Task 1
│       ├── customers.csv
│       ├── subscriptions.csv
│       └── events.csv
├── tests/
│   ├── __init__.py               # Task 1
│   ├── conftest.py               # Shared fixtures (Task 6)
│   ├── test_metrics.py           # Tasks 6-8
│   ├── test_cohorts.py           # Tasks 9-10
│   └── test_data_generator.py    # Task 4
└── .streamlit/
    └── config.toml               # Cadenza theme (Task 16)
```

**Responsibilities:**
- `data_generator.py` — produces the three CSVs. Pure function from a config object to (customers_df, subscriptions_df, events_df). CLI wrapper writes them to disk.
- `metrics.py` — pure functions taking pandas DataFrames and returning scalar metric values or aggregated DataFrames. No IO, no Streamlit imports.
- `cohorts.py` — cohort matrix construction. Same purity constraint.
- `viz.py` — Plotly figure builders. Functions take DataFrames/values, return `plotly.graph_objects.Figure`. No Streamlit imports (testable + reusable).
- `streamlit_app.py` and `pages/*.py` — thin presentation layer. Read CSVs (cached via `@st.cache_data`), call metric/cohort/viz functions, render.

---

## Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`
- Create: `data/generated/.gitkeep`
- Modify: `.gitignore` (add `data/generated/*.csv` line — actually we WILL commit a snapshot for Streamlit Cloud deploy)

- [ ] **Step 1: Create `requirements.txt`**

```
streamlit==1.40.0
pandas==2.2.3
numpy==2.1.3
plotly==5.24.1
pytest==8.3.4
```

- [ ] **Step 2: Create `src/__init__.py`** (empty file)

- [ ] **Step 3: Create `tests/__init__.py`** (empty file)

- [ ] **Step 4: Create `data/generated/.gitkeep`** (empty file — preserves directory in git)

- [ ] **Step 5: Verify `.gitignore` allows committing generated CSVs**

Open `.gitignore`. The line `# data/generated/*.csv` should already be commented out. The generated CSVs WILL be committed because Streamlit Cloud needs them at deploy time and they're part of the portfolio artifact. Leave the line commented.

- [ ] **Step 6: Create Python virtual environment and install dependencies**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Add `.venv/` line to `.gitignore` if not already present (it is).

- [ ] **Step 7: Smoke-test the install**

```bash
python -c "import streamlit, pandas, numpy, plotly, pytest; print('OK')"
```
Expected output: `OK`

- [ ] **Step 8: Commit**

```bash
git add requirements.txt src/__init__.py tests/__init__.py data/generated/.gitkeep
git commit -m "chore: scaffold project structure and dependencies"
```

---

## Task 2: Data generator — config and customer table

**Files:**
- Create: `src/data_generator.py`

This task builds the generator's foundation: a typed config object, and the customer-table generator. Subscription/event simulation comes in Task 3.

- [ ] **Step 1: Create `src/data_generator.py` with config and constants**

```python
"""Synthetic data generator for Cadenza, a fictional B2B sales engagement SaaS.

Produces three CSVs covering 36 months: customers.csv, subscriptions.csv, events.csv.

The generator deliberately encodes a hidden insight: customers acquired through
the 'Self-Serve Promo' channel during Q3 2024 churn at ~2x the rate of other
channels. Headline NRR/GRR still appear healthy; the cohort heatmap and channel
breakdown in the dashboard expose the pattern.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

# --- Configuration ---------------------------------------------------------

START_MONTH = pd.Timestamp("2023-01-01")
END_MONTH = pd.Timestamp("2025-12-01")
RNG_SEED = 42

SEGMENTS = ["SMB", "Mid-Market", "Enterprise"]
SEGMENT_WEIGHTS = [0.70, 0.25, 0.05]

CHANNELS = [
    "Outbound Sales",
    "Inbound Marketing",
    "Partner Referral",
    "Self-Serve Promo",
    "Event/Conference",
]
CHANNEL_WEIGHTS_BASELINE = [0.30, 0.30, 0.10, 0.10, 0.20]

PLAN_TIERS = {"Starter": 50.0, "Growth": 120.0, "Scale": 250.0}
PLAN_WEIGHTS_BY_SEGMENT = {
    "SMB": {"Starter": 0.70, "Growth": 0.28, "Scale": 0.02},
    "Mid-Market": {"Starter": 0.20, "Growth": 0.65, "Scale": 0.15},
    "Enterprise": {"Starter": 0.05, "Growth": 0.35, "Scale": 0.60},
}

SEAT_RANGE_BY_SEGMENT = {
    "SMB": (3, 15),
    "Mid-Market": (15, 75),
    "Enterprise": (75, 400),
}

INDUSTRIES = [
    "Technology", "Financial Services", "Healthcare", "Manufacturing",
    "Retail", "Media", "Education", "Professional Services",
]

# Baseline new-customer acquisitions per month, plus seasonality
BASELINE_NEW_PER_MONTH = 20

# Engineered insight: Q3 2024 self-serve-promo bump
PROMO_MONTHS = [pd.Timestamp("2024-07-01"), pd.Timestamp("2024-08-01"), pd.Timestamp("2024-09-01")]
PROMO_EXTRA_PER_MONTH = 20  # ~60 extra customers, all tagged Self-Serve Promo

# Lifecycle probability params (monthly)
BASE_CHURN_PROB_BY_CHANNEL = {
    "Outbound Sales": 0.010,
    "Inbound Marketing": 0.012,
    "Partner Referral": 0.008,
    "Self-Serve Promo": 0.025,   # the engineered bad cohort
    "Event/Conference": 0.015,
}
SEGMENT_CHURN_MULT = {"SMB": 1.3, "Mid-Market": 1.0, "Enterprise": 0.4}

EXPANSION_PROB_BY_SEGMENT = {"SMB": 0.030, "Mid-Market": 0.050, "Enterprise": 0.080}
CONTRACTION_PROB_BY_SEGMENT = {"SMB": 0.010, "Mid-Market": 0.008, "Enterprise": 0.005}

EXPANSION_SEAT_GROWTH_RANGE = (0.05, 0.25)
CONTRACTION_SEAT_LOSS_RANGE = (0.05, 0.20)


@dataclass
class GeneratorConfig:
    start: pd.Timestamp = START_MONTH
    end: pd.Timestamp = END_MONTH
    baseline_new_per_month: int = BASELINE_NEW_PER_MONTH
    rng_seed: int = RNG_SEED


# --- Customer-table generation --------------------------------------------

def _months_between(start: pd.Timestamp, end: pd.Timestamp) -> list[pd.Timestamp]:
    return list(pd.date_range(start=start, end=end, freq="MS"))


def _seasonality_multiplier(month: pd.Timestamp) -> float:
    """Slight Q4 bump, Q1 dip in new acquisitions."""
    m = month.month
    if m in (10, 11):
        return 1.15
    if m in (1, 2):
        return 0.90
    return 1.0


def generate_customers(cfg: GeneratorConfig) -> pd.DataFrame:
    """Generate the customers table.

    Returns a DataFrame with columns:
        customer_id, company_name, segment, industry, signup_date, signup_cohort,
        acquisition_channel, plan_tier_initial, initial_seats, initial_mrr
    """
    rng = np.random.default_rng(cfg.rng_seed)
    months = _months_between(cfg.start, cfg.end)
    rows = []
    next_id = 1001

    for month in months:
        # Baseline acquisitions
        n = int(round(cfg.baseline_new_per_month * _seasonality_multiplier(month)))
        for _ in range(n):
            row = _make_customer_row(rng, next_id, month, promo=False)
            rows.append(row)
            next_id += 1

        # Promo cohort: extra Self-Serve Promo signups in Q3 2024
        if month in PROMO_MONTHS:
            for _ in range(PROMO_EXTRA_PER_MONTH):
                row = _make_customer_row(rng, next_id, month, promo=True)
                rows.append(row)
                next_id += 1

    return pd.DataFrame(rows)


def _make_customer_row(rng: np.random.Generator, cust_id: int,
                       signup_month: pd.Timestamp, promo: bool) -> dict:
    segment = rng.choice(SEGMENTS, p=SEGMENT_WEIGHTS)
    if promo:
        channel = "Self-Serve Promo"
        # Promo cohort skews SMB
        segment = rng.choice(SEGMENTS, p=[0.85, 0.13, 0.02])
    else:
        channel = rng.choice(CHANNELS, p=CHANNEL_WEIGHTS_BASELINE)

    plan_weights = PLAN_WEIGHTS_BY_SEGMENT[segment]
    plan = rng.choice(list(plan_weights.keys()), p=list(plan_weights.values()))
    seat_lo, seat_hi = SEAT_RANGE_BY_SEGMENT[segment]
    seats = int(rng.integers(seat_lo, seat_hi + 1))

    # Signup day within the month
    day = int(rng.integers(1, 28))
    signup_date = signup_month + pd.Timedelta(days=day - 1)

    mrr = seats * PLAN_TIERS[plan]

    return {
        "customer_id": f"CUST-{cust_id}",
        "company_name": _fake_company_name(rng),
        "segment": segment,
        "industry": rng.choice(INDUSTRIES),
        "signup_date": signup_date.strftime("%Y-%m-%d"),
        "signup_cohort": signup_month.strftime("%Y-%m"),
        "acquisition_channel": channel,
        "plan_tier_initial": plan,
        "initial_seats": seats,
        "initial_mrr": mrr,
    }


_NAME_PREFIXES = ["North", "Apex", "Quantum", "Helix", "Vector", "Lattice",
                  "Beacon", "Stratus", "Cobalt", "Citron", "Plinth", "Marlin",
                  "Tessera", "Halcyon", "Mosaic", "Glide", "Anvil", "Reverb"]
_NAME_SUFFIXES = ["Labs", "Works", "Systems", "Logic", "Group", "Dynamics",
                  "Holdings", "Partners", "Co", "Industries", "Solutions",
                  "Network", "Cloud", "Digital"]


def _fake_company_name(rng: np.random.Generator) -> str:
    return f"{rng.choice(_NAME_PREFIXES)} {rng.choice(_NAME_SUFFIXES)}"
```

- [ ] **Step 2: Smoke-test that the customer generator runs**

```bash
python -c "from src.data_generator import GeneratorConfig, generate_customers; df = generate_customers(GeneratorConfig()); print(df.shape); print(df.head()); print(df['acquisition_channel'].value_counts())"
```
Expected: shape with 600–800 rows, `Self-Serve Promo` count noticeably elevated because of the Q3 2024 bump.

- [ ] **Step 3: Commit**

```bash
git add src/data_generator.py
git commit -m "feat(data): add generator config and customer table generation"
```

---

## Task 3: Data generator — subscription lifecycle simulation

**Files:**
- Modify: `src/data_generator.py`

This task adds the month-by-month simulation that produces `subscriptions` (one row per customer per active month) and `events` (signup/upgrade/downgrade/churn rows).

- [ ] **Step 1: Append the subscription simulation to `src/data_generator.py`**

Append at the end of the file:

```python
# --- Subscription & event simulation ---------------------------------------

def generate_subscriptions_and_events(
    customers: pd.DataFrame, cfg: GeneratorConfig
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Simulate month-by-month subscription state and lifecycle events.

    Returns (subscriptions_df, events_df).
    """
    rng = np.random.default_rng(cfg.rng_seed + 1)
    months = _months_between(cfg.start, cfg.end)

    customers = customers.copy()
    customers["signup_date_dt"] = pd.to_datetime(customers["signup_date"])

    # Active state per customer: dict[customer_id] -> {seats, plan_tier, mrr, churned}
    state: dict[str, dict] = {}

    sub_rows = []
    event_rows = []

    for month in months:
        # Activate customers whose signup_date is in this month
        new_this_month = customers[
            (customers["signup_date_dt"] >= month)
            & (customers["signup_date_dt"] < month + pd.offsets.MonthBegin(1))
        ]
        for _, c in new_this_month.iterrows():
            state[c["customer_id"]] = {
                "seats": int(c["initial_seats"]),
                "plan_tier": c["plan_tier_initial"],
                "mrr": float(c["initial_mrr"]),
                "churned": False,
                "segment": c["segment"],
                "channel": c["acquisition_channel"],
            }
            event_rows.append({
                "customer_id": c["customer_id"],
                "event_date": c["signup_date"],
                "event_type": "signup",
                "mrr_delta": float(c["initial_mrr"]),
                "reason": f"New {c['segment']} customer via {c['acquisition_channel']}",
            })

        # Walk all active customers and decide their fate this month
        for cust_id, s in list(state.items()):
            if s["churned"]:
                continue

            # Churn check
            churn_p = (
                BASE_CHURN_PROB_BY_CHANNEL[s["channel"]]
                * SEGMENT_CHURN_MULT[s["segment"]]
                * _q1_churn_amplifier(month)
            )
            if rng.random() < churn_p:
                event_rows.append({
                    "customer_id": cust_id,
                    "event_date": _mid_month(month).strftime("%Y-%m-%d"),
                    "event_type": "churn",
                    "mrr_delta": -s["mrr"],
                    "reason": "Cancellation",
                })
                s["churned"] = True
                continue

            # Expansion check
            if rng.random() < EXPANSION_PROB_BY_SEGMENT[s["segment"]]:
                growth = rng.uniform(*EXPANSION_SEAT_GROWTH_RANGE)
                new_seats = max(s["seats"] + 1, int(round(s["seats"] * (1 + growth))))
                delta_mrr = (new_seats - s["seats"]) * PLAN_TIERS[s["plan_tier"]]
                event_rows.append({
                    "customer_id": cust_id,
                    "event_date": _mid_month(month).strftime("%Y-%m-%d"),
                    "event_type": "upgrade",
                    "mrr_delta": delta_mrr,
                    "reason": f"Seat expansion to {new_seats}",
                })
                s["seats"] = new_seats
                s["mrr"] = new_seats * PLAN_TIERS[s["plan_tier"]]

            # Contraction check (separate roll)
            elif rng.random() < CONTRACTION_PROB_BY_SEGMENT[s["segment"]]:
                loss = rng.uniform(*CONTRACTION_SEAT_LOSS_RANGE)
                new_seats = max(1, int(round(s["seats"] * (1 - loss))))
                delta_mrr = (new_seats - s["seats"]) * PLAN_TIERS[s["plan_tier"]]
                event_rows.append({
                    "customer_id": cust_id,
                    "event_date": _mid_month(month).strftime("%Y-%m-%d"),
                    "event_type": "downgrade",
                    "mrr_delta": delta_mrr,
                    "reason": f"Seat contraction to {new_seats}",
                })
                s["seats"] = new_seats
                s["mrr"] = new_seats * PLAN_TIERS[s["plan_tier"]]

        # Snapshot subscriptions for this month (active only)
        for cust_id, s in state.items():
            if s["churned"]:
                continue
            sub_rows.append({
                "customer_id": cust_id,
                "month": month.strftime("%Y-%m-%d"),
                "mrr": s["mrr"],
                "seats": s["seats"],
                "plan_tier": s["plan_tier"],
                "status": "active",
            })

    return pd.DataFrame(sub_rows), pd.DataFrame(event_rows)


def _q1_churn_amplifier(month: pd.Timestamp) -> float:
    """Slight Q1 churn elevation (budget cuts, renewals not renewed)."""
    return 1.20 if month.month in (1, 2) else 1.0


def _mid_month(month: pd.Timestamp) -> pd.Timestamp:
    return month + pd.Timedelta(days=14)
```

- [ ] **Step 2: Smoke-test the simulation**

```bash
python -c "
from src.data_generator import GeneratorConfig, generate_customers, generate_subscriptions_and_events
cfg = GeneratorConfig()
customers = generate_customers(cfg)
subs, events = generate_subscriptions_and_events(customers, cfg)
print('customers:', customers.shape)
print('subscriptions:', subs.shape)
print('events:', events.shape)
print('event types:', events['event_type'].value_counts().to_dict())
print('last month MRR sum:', subs[subs['month']=='2025-12-01']['mrr'].sum())
"
```

Expected:
- customers shape around (760, 10)
- subscriptions shape in low five figures
- events with all five event_types present
- last-month MRR sum in the high hundreds of thousands to low millions

- [ ] **Step 3: Commit**

```bash
git add src/data_generator.py
git commit -m "feat(data): simulate subscription lifecycle and events"
```

---

## Task 4: Data generator — verify engineered insight + sanity tests

**Files:**
- Create: `tests/test_data_generator.py`

This task locks in the **engineered insight** with explicit tests, so future changes can't accidentally erase it. The pattern: Self-Serve Promo Q3 2024 cohort churns ~2× the rest.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_data_generator.py`:

```python
"""Tests that the synthetic data generator produces the patterns the
dashboard is built to surface. These are sanity tests, not unit tests:
they verify the macro behavior of the simulation.
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.data_generator import (
    GeneratorConfig,
    generate_customers,
    generate_subscriptions_and_events,
)


@pytest.fixture(scope="module")
def generated():
    cfg = GeneratorConfig()
    customers = generate_customers(cfg)
    subs, events = generate_subscriptions_and_events(customers, cfg)
    return customers, subs, events


def test_customer_count_is_reasonable(generated):
    customers, _, _ = generated
    assert 600 <= len(customers) <= 900


def test_all_three_segments_present(generated):
    customers, _, _ = generated
    assert set(customers["segment"].unique()) == {"SMB", "Mid-Market", "Enterprise"}


def test_all_five_channels_present(generated):
    customers, _, _ = generated
    assert set(customers["acquisition_channel"].unique()) == {
        "Outbound Sales", "Inbound Marketing", "Partner Referral",
        "Self-Serve Promo", "Event/Conference",
    }


def test_q3_2024_promo_cohort_overrepresents_self_serve(generated):
    """The engineered bump should make Self-Serve Promo visibly dominate Q3 2024."""
    customers, _, _ = generated
    q3_2024 = customers[customers["signup_cohort"].isin(["2024-07", "2024-08", "2024-09"])]
    channel_mix = q3_2024["acquisition_channel"].value_counts(normalize=True)
    assert channel_mix.get("Self-Serve Promo", 0) > 0.40, (
        f"Self-Serve Promo should be >40% of Q3 2024 cohort, got {channel_mix.to_dict()}"
    )


def test_self_serve_promo_q3_cohort_churns_worse(generated):
    """The core engineered insight: Q3 2024 Self-Serve Promo cohort has
    materially worse 12-month retention than the rest of the book."""
    customers, subs, _ = generated

    target_cohorts = ["2024-07", "2024-08", "2024-09"]
    promo_q3 = customers[
        (customers["signup_cohort"].isin(target_cohorts))
        & (customers["acquisition_channel"] == "Self-Serve Promo")
    ]
    other_cohorts = customers[
        (customers["signup_cohort"].isin(target_cohorts))
        & (customers["acquisition_channel"] != "Self-Serve Promo")
    ]

    def retained_at_m12(cohort_customers: pd.DataFrame) -> float:
        if len(cohort_customers) == 0:
            return 1.0
        retained = 0
        for _, c in cohort_customers.iterrows():
            signup = pd.Timestamp(c["signup_date"]).to_period("M")
            target = (signup + 12).to_timestamp().strftime("%Y-%m-%d")
            still_active = (
                (subs["customer_id"] == c["customer_id"])
                & (subs["month"] == target)
            ).any()
            if still_active:
                retained += 1
        return retained / len(cohort_customers)

    promo_retention = retained_at_m12(promo_q3)
    other_retention = retained_at_m12(other_cohorts)

    assert other_retention - promo_retention > 0.15, (
        f"Promo cohort M12 retention ({promo_retention:.2%}) should be at "
        f"least 15 points worse than other Q3 2024 channels ({other_retention:.2%})."
    )


def test_total_mrr_grows_over_time(generated):
    _, subs, _ = generated
    first_month_mrr = subs[subs["month"] == "2023-01-01"]["mrr"].sum()
    last_month_mrr = subs[subs["month"] == "2025-12-01"]["mrr"].sum()
    assert last_month_mrr > first_month_mrr * 3, (
        f"Expected meaningful growth over 36 months; got {first_month_mrr:.0f} -> {last_month_mrr:.0f}"
    )


def test_event_types_cover_full_lifecycle(generated):
    _, _, events = generated
    types = set(events["event_type"].unique())
    assert {"signup", "churn"} <= types
    # upgrades/downgrades should exist but not strictly required every run
    assert "upgrade" in types
```

- [ ] **Step 2: Run tests to verify they pass (the generator should already satisfy them)**

```bash
pytest tests/test_data_generator.py -v
```

If any test fails:
- `test_q3_2024_promo_cohort_overrepresents_self_serve` failing → bump `PROMO_EXTRA_PER_MONTH` from 20 → 25 in `src/data_generator.py`.
- `test_self_serve_promo_q3_cohort_churns_worse` failing → bump `BASE_CHURN_PROB_BY_CHANNEL["Self-Serve Promo"]` from 0.025 → 0.030.

Iterate until all tests pass. Do **not** change the test thresholds — they encode the spec.

- [ ] **Step 3: Commit**

```bash
git add tests/test_data_generator.py src/data_generator.py
git commit -m "test(data): lock in the engineered insight with sanity tests"
```

---

## Task 5: Data generator — CLI runner and snapshot

**Files:**
- Modify: `src/data_generator.py` (add CLI block)
- Create: `data/generated/customers.csv`, `data/generated/subscriptions.csv`, `data/generated/events.csv`

- [ ] **Step 1: Add CLI block to `src/data_generator.py`**

Append at the bottom:

```python
# --- CLI entry point -------------------------------------------------------

def generate_all(cfg: GeneratorConfig | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cfg = cfg or GeneratorConfig()
    customers = generate_customers(cfg)
    subs, events = generate_subscriptions_and_events(customers, cfg)
    return customers, subs, events


def write_to_disk(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    customers, subs, events = generate_all()
    customers.drop(columns=[c for c in customers.columns if c.endswith("_dt")], errors="ignore", inplace=True)
    customers.to_csv(out_dir / "customers.csv", index=False)
    subs.to_csv(out_dir / "subscriptions.csv", index=False)
    events.to_csv(out_dir / "events.csv", index=False)
    print(f"Wrote {len(customers)} customers, {len(subs)} subscription rows, {len(events)} events to {out_dir}")


if __name__ == "__main__":
    write_to_disk(Path(__file__).resolve().parents[1] / "data" / "generated")
```

- [ ] **Step 2: Run the generator to produce the CSVs**

```bash
python -m src.data_generator
```

Expected output: `Wrote ~760 customers, ~15000-20000 subscription rows, ~3000-5000 events to .../data/generated`.

- [ ] **Step 3: Verify the CSVs exist and look right**

```bash
wc -l data/generated/*.csv
head -3 data/generated/customers.csv
head -3 data/generated/subscriptions.csv
head -3 data/generated/events.csv
```

- [ ] **Step 4: Commit (including the generated CSV snapshot — needed for Streamlit Cloud deploy)**

```bash
git add src/data_generator.py data/generated/customers.csv data/generated/subscriptions.csv data/generated/events.csv
git commit -m "feat(data): add CLI runner and commit generated dataset snapshot"
```

---

## Task 6: Metrics — fixtures, ARR, and Logo Churn

**Files:**
- Create: `tests/conftest.py`
- Create: `src/metrics.py`
- Create: `tests/test_metrics.py`

TDD discipline: tests first with hand-built fixtures that have known answers, then implementation. Hand-built fixtures are non-negotiable — they're how we prove the formula is right.

- [ ] **Step 1: Create `tests/conftest.py` with hand-built fixtures**

```python
"""Hand-built fixtures with known metric answers. These are the contract:
if the metric calculations stop matching these expected values, the math
is wrong, not the fixture.
"""
from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def tiny_subs() -> pd.DataFrame:
    """5 customers across 3 months (2024-01, 2024-02, 2024-03).

    Lifecycle:
      CUST-1: $100 -> $100 -> $100  (flat)
      CUST-2: $200 -> $250 -> $250  (expansion in Feb)
      CUST-3: $300 -> $300 -> churn (churn in Mar)
      CUST-4: $400 -> $350 -> $350  (contraction in Feb)
      CUST-5:  n/a -> $500 -> $500  (new in Feb)
    """
    rows = [
        {"customer_id": "CUST-1", "month": "2024-01-01", "mrr": 100.0, "seats": 1, "plan_tier": "Starter", "status": "active"},
        {"customer_id": "CUST-1", "month": "2024-02-01", "mrr": 100.0, "seats": 1, "plan_tier": "Starter", "status": "active"},
        {"customer_id": "CUST-1", "month": "2024-03-01", "mrr": 100.0, "seats": 1, "plan_tier": "Starter", "status": "active"},

        {"customer_id": "CUST-2", "month": "2024-01-01", "mrr": 200.0, "seats": 2, "plan_tier": "Growth", "status": "active"},
        {"customer_id": "CUST-2", "month": "2024-02-01", "mrr": 250.0, "seats": 2, "plan_tier": "Growth", "status": "active"},
        {"customer_id": "CUST-2", "month": "2024-03-01", "mrr": 250.0, "seats": 2, "plan_tier": "Growth", "status": "active"},

        {"customer_id": "CUST-3", "month": "2024-01-01", "mrr": 300.0, "seats": 3, "plan_tier": "Growth", "status": "active"},
        {"customer_id": "CUST-3", "month": "2024-02-01", "mrr": 300.0, "seats": 3, "plan_tier": "Growth", "status": "active"},
        # CUST-3 churns in March -> absent from 2024-03-01

        {"customer_id": "CUST-4", "month": "2024-01-01", "mrr": 400.0, "seats": 4, "plan_tier": "Growth", "status": "active"},
        {"customer_id": "CUST-4", "month": "2024-02-01", "mrr": 350.0, "seats": 4, "plan_tier": "Growth", "status": "active"},
        {"customer_id": "CUST-4", "month": "2024-03-01", "mrr": 350.0, "seats": 4, "plan_tier": "Growth", "status": "active"},

        {"customer_id": "CUST-5", "month": "2024-02-01", "mrr": 500.0, "seats": 5, "plan_tier": "Scale", "status": "active"},
        {"customer_id": "CUST-5", "month": "2024-03-01", "mrr": 500.0, "seats": 5, "plan_tier": "Scale", "status": "active"},
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def tiny_events() -> pd.DataFrame:
    rows = [
        {"customer_id": "CUST-1", "event_date": "2024-01-15", "event_type": "signup", "mrr_delta": 100.0, "reason": "new"},
        {"customer_id": "CUST-2", "event_date": "2024-01-15", "event_type": "signup", "mrr_delta": 200.0, "reason": "new"},
        {"customer_id": "CUST-2", "event_date": "2024-02-15", "event_type": "upgrade", "mrr_delta": 50.0, "reason": "expansion"},
        {"customer_id": "CUST-3", "event_date": "2024-01-15", "event_type": "signup", "mrr_delta": 300.0, "reason": "new"},
        {"customer_id": "CUST-3", "event_date": "2024-03-15", "event_type": "churn", "mrr_delta": -300.0, "reason": "cancel"},
        {"customer_id": "CUST-4", "event_date": "2024-01-15", "event_type": "signup", "mrr_delta": 400.0, "reason": "new"},
        {"customer_id": "CUST-4", "event_date": "2024-02-15", "event_type": "downgrade", "mrr_delta": -50.0, "reason": "contraction"},
        {"customer_id": "CUST-5", "event_date": "2024-02-15", "event_type": "signup", "mrr_delta": 500.0, "reason": "new"},
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def tiny_customers() -> pd.DataFrame:
    rows = [
        {"customer_id": "CUST-1", "segment": "SMB", "acquisition_channel": "Outbound Sales", "signup_cohort": "2024-01", "signup_date": "2024-01-15"},
        {"customer_id": "CUST-2", "segment": "Mid-Market", "acquisition_channel": "Inbound Marketing", "signup_cohort": "2024-01", "signup_date": "2024-01-15"},
        {"customer_id": "CUST-3", "segment": "Mid-Market", "acquisition_channel": "Outbound Sales", "signup_cohort": "2024-01", "signup_date": "2024-01-15"},
        {"customer_id": "CUST-4", "segment": "Enterprise", "acquisition_channel": "Partner Referral", "signup_cohort": "2024-01", "signup_date": "2024-01-15"},
        {"customer_id": "CUST-5", "segment": "Enterprise", "acquisition_channel": "Self-Serve Promo", "signup_cohort": "2024-02", "signup_date": "2024-02-15"},
    ]
    return pd.DataFrame(rows)
```

- [ ] **Step 2: Write the failing tests for ARR and Logo Churn**

Create `tests/test_metrics.py`:

```python
"""Metric correctness tests, computed against hand-built fixtures with
known answers (see conftest.py).
"""
from __future__ import annotations

import pytest

from src.metrics import arr, logo_churn


def test_arr_is_mrr_times_twelve(tiny_subs):
    # Jan 2024 active MRR = 100 + 200 + 300 + 400 = 1000
    assert arr(tiny_subs, "2024-01-01") == 12_000.0


def test_arr_excludes_churned_customers(tiny_subs):
    # March: CUST-3 has churned, so absent. MRR = 100 + 250 + 350 + 500 = 1200
    assert arr(tiny_subs, "2024-03-01") == 14_400.0


def test_logo_churn_jan_to_mar(tiny_subs):
    # Active in Jan: {CUST-1, CUST-2, CUST-3, CUST-4} = 4 customers
    # Active in Mar (from that cohort): {CUST-1, CUST-2, CUST-4} = 3
    # Churned = 1 -> 1/4 = 0.25
    assert logo_churn(tiny_subs, "2024-01-01", "2024-03-01") == pytest.approx(0.25)


def test_logo_churn_when_nobody_churns(tiny_subs):
    # Feb -> Mar: cohort = active in Feb = {1,2,3,4,5}. Active in Mar = {1,2,4,5}. Churned = 1 (CUST-3) -> 1/5 = 0.20
    assert logo_churn(tiny_subs, "2024-02-01", "2024-03-01") == pytest.approx(0.20)
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_metrics.py -v
```
Expected: `ImportError` — `src.metrics` does not exist yet.

- [ ] **Step 4: Implement `src/metrics.py` (ARR and Logo Churn)**

Create `src/metrics.py`:

```python
"""Core SaaS retention metric calculations.

All functions are pure: they take pandas DataFrames matching the schema
of the generated CSVs and return scalars or aggregated DataFrames.

Schema reminder:
    subscriptions: customer_id, month, mrr, seats, plan_tier, status
        - one row per customer per month they are active
        - churned customers are simply absent from later months
    events: customer_id, event_date, event_type, mrr_delta, reason
        - event_type in {signup, upgrade, downgrade, churn, renewal}
"""
from __future__ import annotations

import pandas as pd


def _active(subs: pd.DataFrame, month: str) -> pd.DataFrame:
    """Active subscriptions in a given month (status == 'active')."""
    return subs[(subs["month"] == month) & (subs["status"] == "active")]


def arr(subs: pd.DataFrame, month: str) -> float:
    """Annual Recurring Revenue at a point in time.

    ARR = sum(active customers' MRR) * 12
    """
    return float(_active(subs, month)["mrr"].sum()) * 12.0


def logo_churn(subs: pd.DataFrame, start_month: str, end_month: str) -> float:
    """Logo (customer-count) churn from start_month to end_month.

    = (customers active at start_month but NOT at end_month) / (customers active at start_month)
    """
    start_ids = set(_active(subs, start_month)["customer_id"])
    end_ids = set(_active(subs, end_month)["customer_id"])
    if not start_ids:
        return 0.0
    churned = start_ids - end_ids
    return len(churned) / len(start_ids)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_metrics.py -v
```
Expected: 4 passing.

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py tests/test_metrics.py src/metrics.py
git commit -m "feat(metrics): ARR and logo churn with hand-built fixtures"
```

---

## Task 7: Metrics — Gross Revenue Churn, GRR, NRR

**Files:**
- Modify: `src/metrics.py`
- Modify: `tests/test_metrics.py`

- [ ] **Step 1: Append failing tests to `tests/test_metrics.py`**

Add the import: `from src.metrics import gross_revenue_churn, grr, nrr` to the top of the file, then append:

```python
def test_nrr_jan_to_mar(tiny_subs):
    # Cohort = active in Jan: {1,2,3,4}, starting MRR = 1000
    # Their Mar MRR: CUST-1=100, CUST-2=250, CUST-3=0 (churned), CUST-4=350 -> 700
    # NRR = 700 / 1000 = 0.70
    assert nrr(tiny_subs, "2024-01-01", "2024-03-01") == pytest.approx(0.70)


def test_nrr_includes_expansion_above_100(tiny_subs):
    # Feb -> Mar: cohort = {1,2,3,4,5}, starting MRR = 100+250+300+350+500 = 1500
    # Their Mar MRR: 100+250+0+350+500 = 1200 -> NRR = 1200/1500 = 0.80
    assert nrr(tiny_subs, "2024-02-01", "2024-03-01") == pytest.approx(0.80)


def test_grr_caps_expansion_at_start_mrr(tiny_subs):
    # Jan -> Mar: cohort = {1,2,3,4}, starting MRR = 1000
    # GRR caps each customer's end MRR at their start MRR:
    #   CUST-1: min(100, 100) = 100
    #   CUST-2: min(250, 200) = 200  (expansion stripped)
    #   CUST-3: min(0, 300) = 0      (churned)
    #   CUST-4: min(350, 400) = 350  (contracted)
    # Sum = 650 -> GRR = 650/1000 = 0.65
    assert grr(tiny_subs, "2024-01-01", "2024-03-01") == pytest.approx(0.65)


def test_gross_revenue_churn_is_one_minus_grr(tiny_subs):
    # = 1 - 0.65 = 0.35
    assert gross_revenue_churn(tiny_subs, "2024-01-01", "2024-03-01") == pytest.approx(0.35)


def test_grr_with_no_starting_customers_returns_one(tiny_subs):
    # Pick a month with no activity
    assert grr(tiny_subs, "2030-01-01", "2030-02-01") == 1.0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_metrics.py -v
```
Expected: import errors for nrr, grr, gross_revenue_churn.

- [ ] **Step 3: Append implementations to `src/metrics.py`**

```python
def nrr(subs: pd.DataFrame, start_month: str, end_month: str) -> float:
    """Net Revenue Retention from start_month to end_month.

    Cohort = customers active at start_month.
    NRR = (cohort's MRR at end_month) / (cohort's MRR at start_month)

    Customers who churned between start and end are absent from end_month
    in the subscriptions table, so they contribute 0 to the numerator.
    NRR can exceed 100% because expansion is included.
    """
    start_df = _active(subs, start_month).set_index("customer_id")["mrr"]
    if start_df.sum() == 0:
        return 1.0
    end_df = _active(subs, end_month).set_index("customer_id")["mrr"]
    end_aligned = end_df.reindex(start_df.index, fill_value=0.0)
    return float(end_aligned.sum() / start_df.sum())


def grr(subs: pd.DataFrame, start_month: str, end_month: str) -> float:
    """Gross Revenue Retention from start_month to end_month.

    Same cohort as NRR, but each customer's end-period MRR is capped at
    their start-period MRR (expansion stripped). Cannot exceed 100%.
    """
    start_df = _active(subs, start_month).set_index("customer_id")["mrr"]
    if start_df.sum() == 0:
        return 1.0
    end_df = _active(subs, end_month).set_index("customer_id")["mrr"]
    end_aligned = end_df.reindex(start_df.index, fill_value=0.0)
    capped = pd.concat([end_aligned, start_df], axis=1).min(axis=1)
    return float(capped.sum() / start_df.sum())


def gross_revenue_churn(subs: pd.DataFrame, start_month: str, end_month: str) -> float:
    """Gross Revenue Churn = 1 - GRR."""
    return 1.0 - grr(subs, start_month, end_month)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_metrics.py -v
```
Expected: 9 passing.

- [ ] **Step 5: Commit**

```bash
git add tests/test_metrics.py src/metrics.py
git commit -m "feat(metrics): NRR, GRR, and gross revenue churn"
```

---

## Task 8: Metrics — MRR Waterfall components

**Files:**
- Modify: `src/metrics.py`
- Modify: `tests/test_metrics.py`

- [ ] **Step 1: Append failing test to `tests/test_metrics.py`**

```python
from src.metrics import mrr_waterfall


def test_mrr_waterfall_jan_to_mar(tiny_subs, tiny_events):
    # Starting MRR (Jan): 100+200+300+400 = 1000
    # Period = events after 2024-01-01 and up to 2024-03-31
    # New (signup, Feb): +500 (CUST-5)
    # Expansion (Feb): +50 (CUST-2)
    # Contraction (Feb): -50 (CUST-4)
    # Churn (Mar): -300 (CUST-3)
    # Ending MRR (Mar): 100+250+0+350+500 = 1200
    result = mrr_waterfall(tiny_subs, tiny_events, "2024-01-01", "2024-03-01")
    assert result["starting"] == pytest.approx(1000.0)
    assert result["new"] == pytest.approx(500.0)
    assert result["expansion"] == pytest.approx(50.0)
    assert result["contraction"] == pytest.approx(-50.0)
    assert result["churn"] == pytest.approx(-300.0)
    assert result["ending"] == pytest.approx(1200.0)
    # Waterfall identity must hold (within float precision)
    walk = result["starting"] + result["new"] + result["expansion"] + result["contraction"] + result["churn"]
    assert walk == pytest.approx(result["ending"])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_metrics.py::test_mrr_waterfall_jan_to_mar -v
```
Expected: ImportError on `mrr_waterfall`.

- [ ] **Step 3: Append implementation to `src/metrics.py`**

```python
def mrr_waterfall(
    subs: pd.DataFrame, events: pd.DataFrame, start_month: str, end_month: str
) -> dict[str, float]:
    """SaaS MRR waterfall for the period (start_month, end_month].

    Returns a dict with starting, new, expansion, contraction (negative),
    churn (negative), and ending. The identity
        starting + new + expansion + contraction + churn = ending
    must hold.

    The period is exclusive of start_month and inclusive of end_month, so
    that signups and changes occurring DURING the start month aren't double-counted
    against the starting balance.
    """
    starting = float(_active(subs, start_month)["mrr"].sum())
    ending = float(_active(subs, end_month)["mrr"].sum())

    period_events = events[(events["event_date"] > start_month) & (events["event_date"] <= _end_of_month(end_month))]

    def _sum(event_type: str) -> float:
        return float(period_events[period_events["event_type"] == event_type]["mrr_delta"].sum())

    return {
        "starting": starting,
        "new": _sum("signup"),
        "expansion": _sum("upgrade"),
        "contraction": _sum("downgrade"),
        "churn": _sum("churn"),
        "ending": ending,
    }


def _end_of_month(month: str) -> str:
    """Return YYYY-MM-DD of the last day of the month given a YYYY-MM-01 string."""
    ts = pd.Timestamp(month)
    return (ts + pd.offsets.MonthEnd(0)).strftime("%Y-%m-%d")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_metrics.py -v
```
Expected: 10 passing.

- [ ] **Step 5: Commit**

```bash
git add tests/test_metrics.py src/metrics.py
git commit -m "feat(metrics): MRR waterfall components with identity test"
```

---

## Task 9: Cohorts — logo retention matrix

**Files:**
- Create: `src/cohorts.py`
- Create: `tests/test_cohorts.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_cohorts.py`:

```python
from __future__ import annotations

import pandas as pd
import pytest

from src.cohorts import logo_retention_matrix


def test_logo_retention_basic(tiny_subs, tiny_customers):
    """The Jan 2024 cohort has 4 customers (1,2,3,4). At M0=Jan all 4 are active.
    At M1=Feb all 4 are still active. At M2=Mar CUST-3 has churned, so 3/4.
    The Feb 2024 cohort has 1 customer (CUST-5). At M0=Feb retained = 1.
    At M1=Mar still active = 1.
    """
    matrix = logo_retention_matrix(tiny_subs, tiny_customers)
    assert matrix.loc["2024-01", 0] == pytest.approx(1.0)
    assert matrix.loc["2024-01", 1] == pytest.approx(1.0)
    assert matrix.loc["2024-01", 2] == pytest.approx(0.75)
    assert matrix.loc["2024-02", 0] == pytest.approx(1.0)
    assert matrix.loc["2024-02", 1] == pytest.approx(1.0)


def test_logo_retention_handles_empty_cohort(tiny_subs, tiny_customers):
    """Cohorts with no customers should not appear in the result."""
    matrix = logo_retention_matrix(tiny_subs, tiny_customers)
    assert "2023-12" not in matrix.index
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_cohorts.py -v
```
Expected: ImportError.

- [ ] **Step 3: Create `src/cohorts.py`**

```python
"""Cohort retention matrix construction.

Given the customers + subscriptions tables, build a matrix indexed by
signup cohort (YYYY-MM) with columns = months-since-signup and values =
the share of the cohort that's still active that many months later.
"""
from __future__ import annotations

import pandas as pd


def logo_retention_matrix(
    subs: pd.DataFrame,
    customers: pd.DataFrame,
    max_months_since_signup: int = 24,
) -> pd.DataFrame:
    """Build a logo (customer-count) retention cohort matrix.

    Rows: signup_cohort (YYYY-MM string).
    Cols: months since signup (int 0..max_months_since_signup).
    Cells: share of cohort still active at that month-of-life.
    """
    cohort_sizes = customers.groupby("signup_cohort").size()

    active = subs[subs["status"] == "active"].merge(
        customers[["customer_id", "signup_cohort"]],
        on="customer_id",
    )
    active["signup_period"] = pd.PeriodIndex(active["signup_cohort"], freq="M")
    active["active_period"] = pd.to_datetime(active["month"]).dt.to_period("M")
    active["months_since_signup"] = (
        active["active_period"].astype(int) - active["signup_period"].astype(int)
    )
    active = active[active["months_since_signup"].between(0, max_months_since_signup)]

    counts = (
        active.groupby(["signup_cohort", "months_since_signup"])["customer_id"]
        .nunique()
        .unstack(fill_value=0)
    )
    retention = counts.div(cohort_sizes, axis=0).dropna(how="all")
    return retention
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_cohorts.py -v
```
Expected: 2 passing.

- [ ] **Step 5: Commit**

```bash
git add tests/test_cohorts.py src/cohorts.py
git commit -m "feat(cohorts): logo retention cohort matrix"
```

---

## Task 10: Cohorts — revenue retention matrix

**Files:**
- Modify: `src/cohorts.py`
- Modify: `tests/test_cohorts.py`

- [ ] **Step 1: Append failing test to `tests/test_cohorts.py`**

```python
from src.cohorts import revenue_retention_matrix


def test_revenue_retention_basic(tiny_subs, tiny_customers):
    """Jan 2024 cohort starting MRR = 100+200+300+400 = 1000.
    At M1 (Feb), same cohort MRR = 100+250+300+350 = 1000  -> 100%
    At M2 (Mar), same cohort MRR = 100+250+0+350 = 700  -> 70%
    """
    matrix = revenue_retention_matrix(tiny_subs, tiny_customers)
    assert matrix.loc["2024-01", 0] == pytest.approx(1.0)
    assert matrix.loc["2024-01", 1] == pytest.approx(1.0)
    assert matrix.loc["2024-01", 2] == pytest.approx(0.70)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_cohorts.py::test_revenue_retention_basic -v
```
Expected: ImportError.

- [ ] **Step 3: Append implementation to `src/cohorts.py`**

```python
def revenue_retention_matrix(
    subs: pd.DataFrame,
    customers: pd.DataFrame,
    max_months_since_signup: int = 24,
) -> pd.DataFrame:
    """Build a revenue (MRR-weighted) retention cohort matrix.

    Numerator: sum of cohort's MRR at month-of-life N.
    Denominator: sum of cohort's MRR at signup (M0).

    Can exceed 100% if expansion outpaces churn within the cohort.
    """
    subs = subs.copy()
    subs["active_period"] = pd.to_datetime(subs["month"]).dt.to_period("M")
    subs = subs[subs["status"] == "active"].merge(
        customers[["customer_id", "signup_cohort"]],
        on="customer_id",
    )
    subs["signup_period"] = pd.PeriodIndex(subs["signup_cohort"], freq="M")
    subs["months_since_signup"] = (
        subs["active_period"].astype(int) - subs["signup_period"].astype(int)
    )
    subs = subs[subs["months_since_signup"].between(0, max_months_since_signup)]

    mrr_by_cohort_age = (
        subs.groupby(["signup_cohort", "months_since_signup"])["mrr"].sum().unstack(fill_value=0.0)
    )
    starting_mrr = mrr_by_cohort_age[0].replace(0, pd.NA)
    retention = mrr_by_cohort_age.div(starting_mrr, axis=0).dropna(how="all")
    return retention
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_cohorts.py -v
```
Expected: 3 passing.

- [ ] **Step 5: Commit**

```bash
git add tests/test_cohorts.py src/cohorts.py
git commit -m "feat(cohorts): revenue retention cohort matrix"
```

---

## Task 11: Visualization helpers

**Files:**
- Create: `src/viz.py`

These are pure Plotly figure builders. No Streamlit imports — the Streamlit pages will import and `st.plotly_chart()` the returned figures.

- [ ] **Step 1: Create `src/viz.py`**

```python
"""Plotly figure builders for the Cadenza dashboard.

All functions take plain pandas DataFrames / Python scalars and return
plotly.graph_objects.Figure objects. They are independent of Streamlit
so they can be unit-tested or reused.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# Cadenza brand palette
CADENZA_PRIMARY = "#1F3A8A"      # deep indigo
CADENZA_ACCENT = "#06B6D4"        # cyan
CADENZA_GOOD = "#10B981"          # green
CADENZA_BAD = "#EF4444"           # red
CADENZA_NEUTRAL = "#94A3B8"       # slate


def waterfall_figure(walk: dict[str, float]) -> go.Figure:
    """SaaS MRR Waterfall: Starting -> New -> Expansion -> Contraction -> Churn -> Ending."""
    fig = go.Figure(
        go.Waterfall(
            measure=["absolute", "relative", "relative", "relative", "relative", "total"],
            x=["Starting MRR", "+ New", "+ Expansion", "- Contraction", "- Churn", "Ending MRR"],
            y=[walk["starting"], walk["new"], walk["expansion"], walk["contraction"], walk["churn"], walk["ending"]],
            connector={"line": {"color": CADENZA_NEUTRAL}},
            increasing={"marker": {"color": CADENZA_GOOD}},
            decreasing={"marker": {"color": CADENZA_BAD}},
            totals={"marker": {"color": CADENZA_PRIMARY}},
        )
    )
    fig.update_layout(
        title="MRR Waterfall",
        showlegend=False,
        yaxis_title="MRR ($)",
        height=420,
    )
    return fig


def trend_figure(df: pd.DataFrame, x_col: str, y_cols: list[str],
                 title: str, reference: float | None = None) -> go.Figure:
    """Line chart with optional horizontal reference (e.g., 100% for NRR/GRR)."""
    fig = go.Figure()
    palette = [CADENZA_PRIMARY, CADENZA_ACCENT, CADENZA_NEUTRAL]
    for i, col in enumerate(y_cols):
        fig.add_trace(go.Scatter(
            x=df[x_col], y=df[col], mode="lines+markers",
            name=col, line={"color": palette[i % len(palette)]}
        ))
    if reference is not None:
        fig.add_hline(y=reference, line_dash="dash", line_color=CADENZA_NEUTRAL,
                      annotation_text=f"{reference:.0%}", annotation_position="right")
    fig.update_layout(title=title, height=380, yaxis_tickformat=".0%")
    return fig


def cohort_heatmap(matrix: pd.DataFrame, title: str) -> go.Figure:
    """Cohort retention heatmap with diverging color scale around 100%."""
    z = matrix.values
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=[f"M{c}" for c in matrix.columns],
            y=matrix.index.astype(str),
            colorscale=[
                [0.0, CADENZA_BAD],
                [0.5, "#FCD34D"],
                [0.8, CADENZA_GOOD],
                [1.0, CADENZA_PRIMARY],
            ],
            zmin=0, zmax=1.2,
            colorbar={"title": "Retention", "tickformat": ".0%"},
            hovertemplate="Cohort %{y}<br>%{x}<br>Retention: %{z:.1%}<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        height=560,
        xaxis_title="Months since signup",
        yaxis_title="Signup cohort",
        yaxis_autorange="reversed",
    )
    return fig


def m12_retention_bar(matrix: pd.DataFrame, highlight_cohorts: list[str] | None = None) -> go.Figure:
    """Bar chart of each cohort's M12 retention, sorted ascending."""
    if 12 not in matrix.columns:
        return go.Figure().update_layout(title="M12 retention (not enough history)")
    s = matrix[12].dropna().sort_values()
    colors = [CADENZA_BAD if (highlight_cohorts and c in highlight_cohorts) else CADENZA_PRIMARY for c in s.index]
    fig = go.Figure(go.Bar(x=s.index.astype(str), y=s.values, marker_color=colors))
    fig.add_hline(y=s.mean(), line_dash="dash", line_color=CADENZA_NEUTRAL,
                  annotation_text=f"Avg {s.mean():.0%}", annotation_position="right")
    fig.update_layout(
        title="M12 Retention by Signup Cohort",
        yaxis_tickformat=".0%",
        height=400,
    )
    return fig


def grouped_metric_bar(df: pd.DataFrame, group_col: str, value_col: str, title: str,
                       is_percent: bool = True) -> go.Figure:
    """Bar chart of a metric grouped by segment/channel."""
    fig = px.bar(df, x=group_col, y=value_col, title=title,
                 color_discrete_sequence=[CADENZA_PRIMARY])
    if is_percent:
        fig.update_layout(yaxis_tickformat=".0%")
    fig.update_layout(height=380)
    return fig
```

- [ ] **Step 2: Smoke-test viz module loads and a function works on real data**

```bash
python -c "
import pandas as pd
from src.viz import waterfall_figure
fig = waterfall_figure({'starting': 100000, 'new': 20000, 'expansion': 5000, 'contraction': -3000, 'churn': -8000, 'ending': 114000})
print('OK, figure type:', type(fig).__name__)
"
```
Expected: `OK, figure type: Figure`

- [ ] **Step 3: Commit**

```bash
git add src/viz.py
git commit -m "feat(viz): Plotly figure builders for KPIs, waterfall, cohort, trends"
```

---

## Task 12: Streamlit — app entry, sidebar, Overview page

**Files:**
- Create: `streamlit_app.py`

- [ ] **Step 1: Create `streamlit_app.py`**

```python
"""Cadenza Retention Analytics — Streamlit entry point + Overview page.

Other pages live in pages/. Streamlit auto-discovers them and renders them
in the sidebar nav.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src import cohorts, metrics, viz

st.set_page_config(
    page_title="Cadenza Retention Analytics",
    page_icon=":bar_chart:",
    layout="wide",
)

DATA_DIR = Path(__file__).resolve().parent / "data" / "generated"


@st.cache_data
def load_data():
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    subs = pd.read_csv(DATA_DIR / "subscriptions.csv")
    events = pd.read_csv(DATA_DIR / "events.csv")
    return customers, subs, events


def sidebar_filters(customers: pd.DataFrame, subs: pd.DataFrame) -> dict:
    st.sidebar.markdown("## Cadenza")
    st.sidebar.caption("Sales engagement platform · fictional · portfolio project")
    st.sidebar.divider()
    st.sidebar.markdown("### Filters")

    months = sorted(subs["month"].unique())
    end_default = months[-1]
    end_month = st.sidebar.selectbox("Reporting month", months, index=len(months) - 1)

    segments = ["All"] + sorted(customers["segment"].unique().tolist())
    segment = st.sidebar.selectbox("Segment", segments)

    channels = ["All"] + sorted(customers["acquisition_channel"].unique().tolist())
    channel = st.sidebar.selectbox("Acquisition channel", channels)

    return {"end_month": end_month, "segment": segment, "channel": channel}


def apply_filters(customers: pd.DataFrame, subs: pd.DataFrame, f: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    cust = customers
    if f["segment"] != "All":
        cust = cust[cust["segment"] == f["segment"]]
    if f["channel"] != "All":
        cust = cust[cust["acquisition_channel"] == f["channel"]]
    subs_f = subs[subs["customer_id"].isin(cust["customer_id"])]
    return cust, subs_f


def render_overview(customers: pd.DataFrame, subs: pd.DataFrame, events: pd.DataFrame, f: dict):
    st.title("Overview")
    st.caption("Cadenza — the canonical SaaS retention dashboard. All data is synthetic.")

    end_month = f["end_month"]
    start_month_ttm = (pd.Timestamp(end_month) - pd.DateOffset(months=12)).strftime("%Y-%m-01")
    prev_month_ttm = (pd.Timestamp(start_month_ttm) - pd.DateOffset(months=12)).strftime("%Y-%m-01")

    cur_arr = metrics.arr(subs, end_month)
    cur_nrr = metrics.nrr(subs, start_month_ttm, end_month)
    cur_grr = metrics.grr(subs, start_month_ttm, end_month)
    cur_logo_churn = metrics.logo_churn(subs, start_month_ttm, end_month)
    cur_rev_churn = metrics.gross_revenue_churn(subs, start_month_ttm, end_month)

    prev_arr = metrics.arr(subs, start_month_ttm) if start_month_ttm in subs["month"].values else None
    prev_nrr = metrics.nrr(subs, prev_month_ttm, start_month_ttm) if prev_month_ttm in subs["month"].values else None

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("ARR", f"${cur_arr:,.0f}",
              delta=f"${cur_arr - prev_arr:,.0f}" if prev_arr else None)
    c2.metric("NRR (TTM)", f"{cur_nrr:.1%}",
              delta=f"{cur_nrr - prev_nrr:+.1%}" if prev_nrr else None)
    c3.metric("GRR (TTM)", f"{cur_grr:.1%}")
    c4.metric("Logo Churn (TTM)", f"{cur_logo_churn:.1%}")
    c5.metric("Gross Revenue Churn (TTM)", f"{cur_rev_churn:.1%}")

    st.divider()

    # MRR Waterfall — last 3 months
    waterfall_start = (pd.Timestamp(end_month) - pd.DateOffset(months=3)).strftime("%Y-%m-01")
    walk = metrics.mrr_waterfall(subs, events[events["customer_id"].isin(customers["customer_id"])],
                                  waterfall_start, end_month)
    st.subheader(f"MRR Waterfall — {waterfall_start} to {end_month}")
    st.plotly_chart(viz.waterfall_figure(walk), use_container_width=True)

    # NRR / GRR monthly trend (rolling 12-month)
    months = sorted(subs["month"].unique())
    trend_rows = []
    for m in months:
        start = (pd.Timestamp(m) - pd.DateOffset(months=12)).strftime("%Y-%m-01")
        if start not in months:
            continue
        trend_rows.append({
            "month": m,
            "NRR": metrics.nrr(subs, start, m),
            "GRR": metrics.grr(subs, start, m),
        })
    trend = pd.DataFrame(trend_rows)
    if not trend.empty:
        st.subheader("NRR and GRR — trailing 12-month, by reporting month")
        st.plotly_chart(viz.trend_figure(trend, "month", ["NRR", "GRR"],
                                          "Retention Trend", reference=1.0),
                        use_container_width=True)


def main():
    customers, subs, events = load_data()
    f = sidebar_filters(customers, subs)
    cust_f, subs_f = apply_filters(customers, subs, f)
    render_overview(cust_f, subs_f, events, f)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Launch Streamlit and verify the Overview page renders**

```bash
streamlit run streamlit_app.py
```

In the browser at `http://localhost:8501`:
- KPI tiles show realistic numbers (ARR in the millions, NRR ~105-115%, GRR ~85-95%)
- MRR Waterfall renders without error
- Trend chart renders with NRR and GRR lines
- Sidebar filters change the values when toggled
- Stop the server with Ctrl-C

- [ ] **Step 3: Commit**

```bash
git add streamlit_app.py
git commit -m "feat(app): Streamlit overview page with KPIs, waterfall, and trend"
```

---

## Task 13: Streamlit — Cohort Analysis page

**Files:**
- Create: `pages/2_Cohort_Analysis.py`

- [ ] **Step 1: Create `pages/2_Cohort_Analysis.py`**

```python
"""Cohort Analysis page — the hero visualization.

Flipping the acquisition-channel filter to 'Self-Serve Promo' should make
the Q3 2024 cohort visibly underperform — that's the engineered insight.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src import cohorts, viz

st.set_page_config(page_title="Cadenza — Cohort Analysis", layout="wide")

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "generated"


@st.cache_data
def load_data():
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    subs = pd.read_csv(DATA_DIR / "subscriptions.csv")
    return customers, subs


def main():
    st.title("Cohort Analysis")
    st.caption("Each row is a signup-month cohort. Columns are months since signup. "
               "Read across a row to see how that cohort retains over time.")

    customers, subs = load_data()

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        view = st.radio("View", ["Logo retention", "Revenue retention"], horizontal=True)
    with col2:
        channels = ["All"] + sorted(customers["acquisition_channel"].unique().tolist())
        channel = st.selectbox("Acquisition channel", channels)
    with col3:
        segments = ["All"] + sorted(customers["segment"].unique().tolist())
        segment = st.selectbox("Segment", segments)

    cust = customers
    if channel != "All":
        cust = cust[cust["acquisition_channel"] == channel]
    if segment != "All":
        cust = cust[cust["segment"] == segment]
    subs_f = subs[subs["customer_id"].isin(cust["customer_id"])]

    if view == "Logo retention":
        matrix = cohorts.logo_retention_matrix(subs_f, cust)
        title = "Logo Retention Cohort"
    else:
        matrix = cohorts.revenue_retention_matrix(subs_f, cust)
        title = "Revenue Retention Cohort"

    if matrix.empty:
        st.warning("No data for the selected filters.")
        return

    st.plotly_chart(viz.cohort_heatmap(matrix, title), use_container_width=True)

    # Highlight the engineered cohorts when looking at all channels or self-serve
    promo_cohorts = ["2024-07", "2024-08", "2024-09"] if channel in ("All", "Self-Serve Promo") else None
    st.plotly_chart(viz.m12_retention_bar(matrix, highlight_cohorts=promo_cohorts),
                    use_container_width=True)

    if channel == "Self-Serve Promo":
        st.info(
            "**Insight:** The Q3 2024 Self-Serve Promo cohort (Jul/Aug/Sep 2024) "
            "shows materially worse retention than other channels. This pattern "
            "is invisible in company-wide headlines but emerges here. See the "
            "**Segment & Channel Deep-Dive** page for the quantified gap."
        )


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Launch Streamlit and verify the Cohort Analysis page renders**

```bash
streamlit run streamlit_app.py
```

In the browser, click "2 Cohort Analysis" in the sidebar:
- Heatmap renders with green/yellow/red cells
- Toggle View → Revenue retention renders too
- Filter Acquisition channel → "Self-Serve Promo" — the Q3 2024 rows should be visibly redder than others, and an info callout appears.
- Stop the server.

- [ ] **Step 3: Commit**

```bash
git add pages/2_Cohort_Analysis.py
git commit -m "feat(app): cohort analysis page with logo/revenue heatmap toggle"
```

---

## Task 14: Streamlit — Segment & Channel Deep-Dive page

**Files:**
- Create: `pages/3_Segment_Drilldown.py`

- [ ] **Step 1: Create `pages/3_Segment_Drilldown.py`**

```python
"""Segment & Channel Deep-Dive — quantifies the cohort insight.

Shows NRR/GRR/Logo Churn split by segment and channel, plus an explorable
account table.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src import metrics

st.set_page_config(page_title="Cadenza — Segment & Channel", layout="wide")

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "generated"


@st.cache_data
def load_data():
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    subs = pd.read_csv(DATA_DIR / "subscriptions.csv")
    return customers, subs


def metrics_by_group(customers: pd.DataFrame, subs: pd.DataFrame,
                     group_col: str, start_month: str, end_month: str) -> pd.DataFrame:
    rows = []
    for value in sorted(customers[group_col].unique()):
        group_ids = customers[customers[group_col] == value]["customer_id"]
        group_subs = subs[subs["customer_id"].isin(group_ids)]
        rows.append({
            group_col: value,
            "NRR": metrics.nrr(group_subs, start_month, end_month),
            "GRR": metrics.grr(group_subs, start_month, end_month),
            "Logo Churn": metrics.logo_churn(group_subs, start_month, end_month),
        })
    return pd.DataFrame(rows)


def main():
    st.title("Segment & Channel Deep-Dive")
    st.caption("This is where the headline numbers get decomposed. The engineered insight: "
               "Self-Serve Promo has noticeably worse retention than other channels.")

    customers, subs = load_data()

    months = sorted(subs["month"].unique())
    end_month = st.selectbox("Reporting month", months, index=len(months) - 1)
    start_month = (pd.Timestamp(end_month) - pd.DateOffset(months=12)).strftime("%Y-%m-01")
    st.caption(f"Trailing 12 months: {start_month} → {end_month}")

    st.subheader("By Segment")
    seg_df = metrics_by_group(customers, subs, "segment", start_month, end_month)
    st.dataframe(
        seg_df.style.format({"NRR": "{:.1%}", "GRR": "{:.1%}", "Logo Churn": "{:.1%}"}),
        use_container_width=True,
    )

    st.subheader("By Acquisition Channel")
    chan_df = metrics_by_group(customers, subs, "acquisition_channel", start_month, end_month)
    chan_df = chan_df.sort_values("GRR")
    st.dataframe(
        chan_df.style.format({"NRR": "{:.1%}", "GRR": "{:.1%}", "Logo Churn": "{:.1%}"})
                     .highlight_min(subset=["GRR", "NRR"], color="#FECACA")
                     .highlight_max(subset=["Logo Churn"], color="#FECACA"),
        use_container_width=True,
    )

    st.divider()
    st.subheader("Account Explorer")
    st.caption("Filter to the channel/segment of interest and inspect individual customer trajectories.")

    col1, col2 = st.columns(2)
    seg_filter = col1.selectbox("Segment", ["All"] + sorted(customers["segment"].unique().tolist()))
    chan_filter = col2.selectbox("Channel", ["All"] + sorted(customers["acquisition_channel"].unique().tolist()))

    view = customers.copy()
    if seg_filter != "All":
        view = view[view["segment"] == seg_filter]
    if chan_filter != "All":
        view = view[view["acquisition_channel"] == chan_filter]

    # Add lifecycle status: active at end_month or churned
    active_end = set(subs[(subs["month"] == end_month) & (subs["status"] == "active")]["customer_id"])
    view = view.assign(status=view["customer_id"].apply(lambda x: "active" if x in active_end else "churned"))
    cur_mrr = subs[subs["month"] == end_month].set_index("customer_id")["mrr"]
    view = view.assign(current_mrr=view["customer_id"].map(cur_mrr).fillna(0).round(0))

    display_cols = ["customer_id", "company_name", "segment", "acquisition_channel",
                    "signup_cohort", "plan_tier_initial", "current_mrr", "status"]
    st.dataframe(view[display_cols], use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Launch Streamlit and verify the page renders**

```bash
streamlit run streamlit_app.py
```

Click "3 Segment Drilldown":
- Segment table shows three rows with NRR/GRR/Churn percentages
- Channel table shows five rows — Self-Serve Promo should be at the top (worst GRR), highlighted red
- Account Explorer table renders with all columns, filter dropdowns work
- Stop the server.

- [ ] **Step 3: Commit**

```bash
git add pages/3_Segment_Drilldown.py
git commit -m "feat(app): segment and channel drilldown with account explorer"
```

---

## Task 15: Streamlit — About / Methodology page

**Files:**
- Create: `pages/4_About.py`

- [ ] **Step 1: Create `pages/4_About.py`**

```python
"""About / Methodology — the portfolio narrative wrapper."""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Cadenza — About", layout="wide")


def main():
    st.title("About this project")

    st.markdown(
        """
        **Cadenza Retention Analytics** is a portfolio project demonstrating SaaS
        revenue operations fluency. The data is synthetic. The dashboard, the metric
        calculations, and the insight it surfaces are real.

        ## The story
        Cadenza is a (fictional) B2B sales engagement platform. On the surface,
        the company's retention metrics look healthy — NRR around 108%, GRR around 91%.
        But when you decompose by acquisition channel, a **Self-Serve Promo** cohort
        from Q3 2024 churns at roughly **2× the rate** of customers from other channels.
        The Cohort Analysis and Segment & Channel pages of this dashboard surface that
        pattern.

        ## What I'd do next at a real company
        - **CSM intervention playbook** for the Self-Serve Promo cohort: contract-end
          outreach 60 days early, value-realization check-ins, expansion offers.
        - **Channel-quality scoring** partnered with marketing: weight new-customer
          acquisitions by 12-month retention probability, not just first-month MRR.
        - **Tighter promo gating**: require a minimum 90-day product engagement
          threshold before discount eligibility on future promotional campaigns.
        """
    )

    st.divider()

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

    st.divider()

    st.subheader("Tech stack")
    st.markdown(
        """
        - Python 3.11, pandas, numpy
        - Streamlit (app) + Plotly (charts)
        - pytest (test suite proving metric formulas against hand-built fixtures)
        - GitHub + Streamlit Community Cloud (deployment)
        """
    )

    st.subheader("Links")
    st.markdown(
        """
        - **Source code:** https://github.com/_TODO_YOUR_USERNAME/cadenza-retention-analytics
        - **Author:** [Jesse Kartes](https://www.linkedin.com/in/_TODO_) — RevOps / Sales Operations
        """
    )


if __name__ == "__main__":
    main()
```

> **Note:** The two `_TODO_` placeholders in the Links section are intentional — they're filled in at deploy time once the GitHub repo URL and LinkedIn URL are known. Task 18's checklist includes filling these in.

- [ ] **Step 2: Verify the page renders**

```bash
streamlit run streamlit_app.py
```

Click "4 About". Confirm the narrative reads correctly and the metric table renders. Stop the server.

- [ ] **Step 3: Commit**

```bash
git add pages/4_About.py
git commit -m "feat(app): about page with narrative, metric defs, and links"
```

---

## Task 16: Cadenza theme

**Files:**
- Create: `.streamlit/config.toml`

- [ ] **Step 1: Create `.streamlit/config.toml`**

```toml
[theme]
base = "light"
primaryColor = "#1F3A8A"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F1F5F9"
textColor = "#0F172A"
font = "sans serif"
```

- [ ] **Step 2: Verify theme applies**

```bash
streamlit run streamlit_app.py
```

The sidebar and primary widgets should now use the deep indigo (#1F3A8A) as the accent color. Stop the server.

- [ ] **Step 3: Commit**

```bash
git add .streamlit/config.toml
git commit -m "style: apply Cadenza brand theme to Streamlit app"
```

---

## Task 17: Case-study README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md`** in case-study format

```markdown
# Cadenza Retention Analytics

A SaaS retention analytics application I built as a portfolio project while interviewing for Revenue Operations / Sales Operations roles in SaaS.

**Live dashboard:** _TODO link after Streamlit Cloud deploy_

**Author:** Jesse Kartes · [LinkedIn](https://www.linkedin.com/in/_TODO_)

---

## The story

Cadenza is a fictional B2B sales engagement platform. I generated 36 months of synthetic subscription data for 600+ customers across three segments, five acquisition channels, and three plan tiers. I then built a Streamlit application that surfaces the canonical SaaS retention metrics — ARR, NRR, GRR, Logo Churn, Gross Revenue Churn — plus a cohort retention heatmap.

The dataset deliberately encodes a pattern that real RevOps teams encounter: customers acquired through a Q3 2024 self-serve promotional channel churn at roughly **2× the rate** of customers from other channels. The dashboard's job is to surface that pattern.

## What the dashboard shows

- **Overview** — headline KPIs (ARR ~$X, NRR ~108%, GRR ~91%), MRR waterfall, and trailing-12-month retention trend. At first glance, the company looks healthy.
- **Cohort Analysis** — the heatmap. Filter to "Self-Serve Promo" and the Q3 2024 cohort lights up red.
- **Segment & Channel Deep-Dive** — quantifies the gap. Self-Serve Promo GRR comes in around 71% vs. ~93% for other channels.
- **About** — methodology, metric formulas, and what I'd recommend at a real company (CSM intervention plan, channel-quality scoring, tighter promo gating).

## How it's built

```
Python data generator  →  3 flat CSVs  →  pandas metric/cohort modules  →  Streamlit + Plotly dashboard
```

- `src/data_generator.py` — synthetic data simulator (lifecycle, expansion, contraction, churn, the encoded insight).
- `src/metrics.py` — ARR, Logo Churn, Gross Revenue Churn, GRR, NRR, MRR Waterfall. Pure pandas functions.
- `src/cohorts.py` — logo and revenue retention cohort matrices.
- `src/viz.py` — Plotly figure builders. Pure functions, no Streamlit imports.
- `streamlit_app.py` + `pages/*.py` — four-page dashboard.
- `tests/` — pytest suite. Hand-built fixtures with hand-calculated expected metric values prove the formulas are correct. The data generator has sanity tests that lock in the engineered pattern.

## Running it locally

```bash
git clone https://github.com/_TODO_/cadenza-retention-analytics.git
cd cadenza-retention-analytics
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.data_generator   # regenerates the CSVs (optional; a snapshot is committed)
streamlit run streamlit_app.py
```

## Running the tests

```bash
pytest -v
```

## Why I built this

I spent five years owning forecasting and renewal analytics for $250M of new sales and $5M MRR of recurring lease revenue at an industrial company. Translating that experience into SaaS-native language is the bridge this project builds. Every metric, formula, and visual choice in this dashboard is something a SaaS finance or RevOps team would recognize on day one.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: case-study README"
```

---

## Task 18: End-to-end verification and final polish

**Files:**
- Possibly: `pages/4_About.py`, `README.md` (placeholder fills if user has provided GitHub/LinkedIn URLs)

- [ ] **Step 1: Run the entire test suite**

```bash
pytest -v
```
Expected: all tests pass (10 metrics tests + 3 cohort tests + 7 data-generator tests = 20 passing).

- [ ] **Step 2: Run the app and click through every page**

```bash
streamlit run streamlit_app.py
```

Walk through each page:
- Overview — KPIs realistic (NRR 105-115%, GRR 85-95%), waterfall identity visually holds (start + bars = end), trend chart shows reasonable monthly variation.
- Cohort Analysis — heatmap renders, view toggle works, channel filter to "Self-Serve Promo" highlights Q3 2024 rows as red, insight callout appears.
- Segment Drilldown — segment table reads correctly (Enterprise has best retention, SMB worst), channel table places Self-Serve Promo at the bottom (worst GRR), Account Explorer filters work.
- About — narrative reads cleanly, metric table renders, links visible.

If anything looks wrong, fix and re-test before the final commit. Stop the server.

- [ ] **Step 3: Optionally fill in real URLs in `pages/4_About.py` and `README.md`**

If the user has provided GitHub repo URL and LinkedIn URL, replace the `_TODO_` placeholders. Otherwise leave for the deploy step.

- [ ] **Step 4: Tag the milestone**

```bash
git tag -a v0.1.0-phase1 -m "Phase 1: Retention analytics complete"
```

- [ ] **Step 5: Confirm final tree state**

```bash
git log --oneline
ls -la
pytest -v
```

All tests passing, ~18 commits in history, project ready for GitHub push and Streamlit Cloud deploy.

---

## Out-of-scope reminders (do NOT do in Phase 1)

- Pipeline analytics, forecast-vs-actual, weighted pipeline coverage → **Phase 2.**
- Quota attainment, rep scorecards, ramp analysis → **Phase 3.**
- ML-based at-risk scoring → explicitly deferred.
- Real Salesforce/HubSpot connectors → not a portfolio concern.
- Auth, multi-tenancy, role-based views → not a portfolio concern.
