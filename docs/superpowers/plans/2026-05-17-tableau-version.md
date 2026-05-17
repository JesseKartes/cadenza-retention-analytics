# Cadenza Tableau Version Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a three-dashboard Tableau Public companion to the Cadenza Streamlit app (Retention / Sales Performance / Pipeline), using a Python pre-aggregation step to keep metric definitions identical across both products.

**Architecture:** Hybrid data prep. A new `scripts/build_tableau_extracts.py` calls existing pure functions in `src/metrics.py`, `src/cohorts.py`, `src/forecast.py`, `src/quota.py` to produce five pre-aggregated CSVs (long-format, Tableau-ready) plus three raw CSVs copied through. A Tableau workbook (`tableau/cadenza.twb`) connects to that single folder. Workbook publishes to Tableau Public; URL gets added to the Streamlit About page and the project README.

**Tech Stack:** Python 3.12, pandas (existing). Tableau Public (free). No new Python dependencies.

**Spec reference:** `docs/superpowers/specs/2026-05-17-tableau-version-design.md`

---

## File Structure

**New files:**
```
scripts/build_tableau_extracts.py           # Pre-aggregation script
tests/test_tableau_extracts.py              # Smoke tests for the 5 pre-agg outputs
data/tableau/tableau_monthly_metrics.csv    # Generated
data/tableau/tableau_cohort_retention.csv   # Generated
data/tableau/tableau_rep_attainment.csv     # Generated
data/tableau/tableau_ramp_curve.csv         # Generated
data/tableau/tableau_forecast_accuracy.csv  # Generated
data/tableau/opportunities.csv              # Copied from data/generated/
data/tableau/opportunity_stage_history.csv  # Copied
data/tableau/reps.csv                       # Copied
tableau/cadenza.twb                         # Tableau workbook (XML)
```

**Modified files:**
```
pages/8_About.py                            # Add "Tableau companion" link
README.md                                   # Add Tableau Public URL
.gitignore                                  # (maybe) ignore *.twbx if generated locally
```

**Untouched:**
- `data/generated/*.csv` (Phase 1 byte-identical lock holds)
- All `src/*.py` modules — pre-aggregation script *consumes* them, doesn't modify them
- All other Streamlit pages

---

## Conventions used throughout this plan

- **Tableau field naming:** Tableau auto-capitalizes CSV column names. `total_mrr` becomes `Total Mrr` in the field list. Calc field code below uses the Tableau-rendered names.
- **Calc field "copy-paste":** Every calculated field block below can be pasted verbatim into Tableau's calculation editor. Tableau's expression language is whitespace-tolerant; line breaks inside an expression are fine.
- **Worksheet → Dashboard:** Each chart is built as a worksheet first, then placed on its dashboard. The plan builds all worksheets for a dashboard, then assembles the dashboard.
- **Saves:** Save the workbook (`Cmd+S`) after each step that changes state. The plan calls out commits explicitly; saves are implicit between steps.

---

## Task 1: Set up data/tableau directory and pre-agg script skeleton

**Files:**
- Create: `scripts/build_tableau_extracts.py`
- Create: `data/tableau/` (directory)

- [ ] **Step 1: Create the data/tableau directory**

```bash
mkdir -p data/tableau
```

- [ ] **Step 2: Create the script skeleton**

Create `scripts/build_tableau_extracts.py`:

```python
"""Build flat, Tableau-friendly CSV extracts from data/generated/.

Outputs five pre-aggregated long-format CSVs plus three raw passthroughs into
data/tableau/. The pre-aggregated metrics are computed using the existing pure
functions in src/*.py so the Tableau workbook tells the same numerical story
as the Streamlit dashboard.

Run from repo root:
    python -m scripts.build_tableau_extracts
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from src import cohorts, forecast, metrics, quota

GENERATED = Path("data/generated")
TABLEAU = Path("data/tableau")


def load_inputs() -> dict[str, pd.DataFrame]:
    """Load every CSV the pre-aggregation needs."""
    return {
        "customers": pd.read_csv(GENERATED / "customers.csv"),
        "subscriptions": pd.read_csv(GENERATED / "subscriptions.csv"),
        "events": pd.read_csv(GENERATED / "events.csv"),
        "opportunities": pd.read_csv(GENERATED / "opportunities.csv"),
        "snapshots": pd.read_csv(GENERATED / "pipeline_snapshots.csv"),
        "reps": pd.read_csv(GENERATED / "reps.csv"),
    }


def copy_raw_files() -> None:
    """Copy raw CSVs that Tableau reads directly (opportunities, stage history, reps)."""
    for name in ["opportunities.csv", "opportunity_stage_history.csv", "reps.csv"]:
        shutil.copy(GENERATED / name, TABLEAU / name)


def main() -> None:
    TABLEAU.mkdir(parents=True, exist_ok=True)
    data = load_inputs()

    # Task 2-6 will add build_* function calls here.
    copy_raw_files()
    print(f"Wrote outputs to {TABLEAU.resolve()}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verify the skeleton runs**

Run: `python -m scripts.build_tableau_extracts`
Expected: `Wrote outputs to /Users/jesse/.../data/tableau`. The directory now contains the three raw passthrough files.

- [ ] **Step 4: Commit**

```bash
git add scripts/build_tableau_extracts.py data/tableau/opportunities.csv data/tableau/opportunity_stage_history.csv data/tableau/reps.csv
git commit -m "feat(tableau): pre-aggregation script skeleton + raw passthroughs"
```

---

## Task 2: Build `tableau_monthly_metrics.csv`

**Files:**
- Modify: `scripts/build_tableau_extracts.py`
- Create: `tests/test_tableau_extracts.py`

This file has one row per month with current-month MRR + waterfall components + trailing-12-month NRR/GRR/Logo Retention. Dashboard 1 uses it for all four KPI tiles and the NRR trend line.

- [ ] **Step 1: Write the failing test**

Create `tests/test_tableau_extracts.py`:

```python
"""Smoke tests for data/tableau/* extracts.

Each output gets three assertions: row count in band, no NaN in key columns,
and a known metric value matches the Streamlit pipeline.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

TABLEAU = Path("data/tableau")


@pytest.fixture(scope="module")
def monthly() -> pd.DataFrame:
    return pd.read_csv(TABLEAU / "tableau_monthly_metrics.csv")


def test_monthly_metrics_row_count(monthly: pd.DataFrame) -> None:
    # Jan 2023 -> Dec 2025 = 36 months
    assert len(monthly) == 36


def test_monthly_metrics_no_nan_in_mrr(monthly: pd.DataFrame) -> None:
    assert monthly["total_mrr"].notna().all()
    assert monthly["month"].notna().all()


def test_monthly_metrics_dec_2025_total_mrr_positive(monthly: pd.DataFrame) -> None:
    dec_2025 = monthly[monthly["month"] == "2025-12-01"]
    assert len(dec_2025) == 1
    assert dec_2025.iloc[0]["total_mrr"] > 0
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_tableau_extracts.py -v`
Expected: FAIL — `FileNotFoundError: data/tableau/tableau_monthly_metrics.csv`.

- [ ] **Step 3: Add `build_monthly_metrics` to the script**

Add this function to `scripts/build_tableau_extracts.py` above `main()`:

```python
def build_monthly_metrics(
    subs: pd.DataFrame, events: pd.DataFrame
) -> pd.DataFrame:
    """One row per month: MRR + waterfall components + TTM NRR/GRR/Logo Retention.

    TTM columns (nrr, grr, logo_retention) are NaN for the first 12 months
    because there's not yet a 12-month-prior cohort to compare against.
    """
    months = sorted(subs["month"].unique())
    rows = []
    for i, m in enumerate(months):
        prev = months[i - 1] if i > 0 else None
        m12_prior = months[i - 12] if i >= 12 else None

        total_mrr = float(
            subs[(subs["month"] == m) & (subs["status"] == "active")]["mrr"].sum()
        )

        if prev is not None:
            walk = metrics.mrr_waterfall(subs, events, prev, m)
            new_mrr, exp_mrr, con_mrr, chu_mrr = (
                walk["new"], walk["expansion"], walk["contraction"], walk["churn"],
            )
        else:
            new_mrr = exp_mrr = con_mrr = chu_mrr = 0.0

        if m12_prior is not None:
            nrr_v = metrics.nrr(subs, m12_prior, m)
            grr_v = metrics.grr(subs, m12_prior, m)
            logo_v = 1.0 - metrics.logo_churn(subs, m12_prior, m)
        else:
            nrr_v = grr_v = logo_v = float("nan")

        rows.append({
            "month": m,
            "total_mrr": total_mrr,
            "new_mrr": new_mrr,
            "expansion_mrr": exp_mrr,
            "contraction_mrr": con_mrr,
            "churn_mrr": chu_mrr,
            "nrr": nrr_v,
            "grr": grr_v,
            "logo_retention": logo_v,
        })
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Wire it into `main()`**

In `scripts/build_tableau_extracts.py`, update `main()`:

```python
def main() -> None:
    TABLEAU.mkdir(parents=True, exist_ok=True)
    data = load_inputs()

    monthly = build_monthly_metrics(data["subscriptions"], data["events"])
    monthly.to_csv(TABLEAU / "tableau_monthly_metrics.csv", index=False)

    copy_raw_files()
    print(f"Wrote outputs to {TABLEAU.resolve()}")
```

- [ ] **Step 5: Run the script**

Run: `python -m scripts.build_tableau_extracts`
Expected: completes without error. New file at `data/tableau/tableau_monthly_metrics.csv`.

- [ ] **Step 6: Run the tests, verify they pass**

Run: `pytest tests/test_tableau_extracts.py -v`
Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add scripts/build_tableau_extracts.py tests/test_tableau_extracts.py data/tableau/tableau_monthly_metrics.csv
git commit -m "feat(tableau): build monthly metrics extract"
```

---

## Task 3: Build `tableau_cohort_retention.csv`

**Files:**
- Modify: `scripts/build_tableau_extracts.py`
- Modify: `tests/test_tableau_extracts.py`

Long-format cohort retention with a channel dimension. Each row is one (signup_cohort × acquisition_channel × months_since_signup) point. Channel `"All"` is precomputed so the Tableau filter can show a weighted overall view without LOD calcs.

- [ ] **Step 1: Add failing tests**

Append to `tests/test_tableau_extracts.py`:

```python
@pytest.fixture(scope="module")
def cohort() -> pd.DataFrame:
    return pd.read_csv(TABLEAU / "tableau_cohort_retention.csv")


def test_cohort_retention_has_all_channel(cohort: pd.DataFrame) -> None:
    assert "All" in cohort["acquisition_channel"].unique()


def test_cohort_retention_no_nan_in_retention_pct(cohort: pd.DataFrame) -> None:
    assert cohort["retention_pct"].notna().all()


def test_cohort_retention_q3_2024_self_serve_visible(cohort: pd.DataFrame) -> None:
    """The engineered insight: Q3 2024 Self-Serve Promo churns harder than other channels."""
    q3_promo = cohort[
        (cohort["signup_cohort"].isin(["2024-07", "2024-08", "2024-09"]))
        & (cohort["acquisition_channel"] == "Self-Serve Promo")
        & (cohort["months_since_signup"] == 6)
    ]
    other_q3 = cohort[
        (cohort["signup_cohort"].isin(["2024-07", "2024-08", "2024-09"]))
        & (cohort["acquisition_channel"] != "Self-Serve Promo")
        & (cohort["acquisition_channel"] != "All")
        & (cohort["months_since_signup"] == 6)
    ]
    # Promo cohort retention at M6 should be meaningfully lower than other channels
    assert q3_promo["retention_pct"].mean() < other_q3["retention_pct"].mean() - 0.10
```

- [ ] **Step 2: Run the test, verify it fails**

Run: `pytest tests/test_tableau_extracts.py -v -k cohort`
Expected: FAIL — file not found.

- [ ] **Step 3: Add `build_cohort_retention` to the script**

```python
def build_cohort_retention(
    subs: pd.DataFrame, customers: pd.DataFrame
) -> pd.DataFrame:
    """Long-format cohort retention with channel dimension.

    Rows: (signup_cohort, acquisition_channel, months_since_signup, retention_pct, n_customers).
    Includes channel='All' as the weighted-overall view.
    """
    channels = list(customers["acquisition_channel"].unique()) + ["All"]
    out = []
    for ch in channels:
        if ch == "All":
            ch_customers = customers
        else:
            ch_customers = customers[customers["acquisition_channel"] == ch]
        if ch_customers.empty:
            continue
        matrix = cohorts.logo_retention_matrix(subs, ch_customers, max_months_since_signup=24)
        cohort_sizes = ch_customers.groupby("signup_cohort").size()
        # Melt the wide matrix to long format
        long = matrix.reset_index().melt(
            id_vars="signup_cohort",
            var_name="months_since_signup",
            value_name="retention_pct",
        )
        long = long.dropna(subset=["retention_pct"])
        long["acquisition_channel"] = ch
        long["n_customers"] = long["signup_cohort"].map(cohort_sizes).astype(int)
        out.append(long)
    return pd.concat(out, ignore_index=True)[
        ["signup_cohort", "acquisition_channel", "months_since_signup",
         "retention_pct", "n_customers"]
    ]
```

- [ ] **Step 4: Wire into `main()`**

```python
    cohort = build_cohort_retention(data["subscriptions"], data["customers"])
    cohort.to_csv(TABLEAU / "tableau_cohort_retention.csv", index=False)
```

- [ ] **Step 5: Run script + tests**

```bash
python -m scripts.build_tableau_extracts
pytest tests/test_tableau_extracts.py -v
```

Expected: 6 passed total.

- [ ] **Step 6: Commit**

```bash
git add scripts/build_tableau_extracts.py tests/test_tableau_extracts.py data/tableau/tableau_cohort_retention.csv
git commit -m "feat(tableau): build cohort retention extract with channel dimension"
```

---

## Task 4: Build `tableau_rep_attainment.csv`

**Files:**
- Modify: `scripts/build_tableau_extracts.py`
- Modify: `tests/test_tableau_extracts.py`

One row per (rep × quarter) — 12 reps × 12 quarters = up to 144 rows. Includes rep name + specialty pre-joined so Tableau doesn't need a data-source join.

- [ ] **Step 1: Add failing tests**

```python
@pytest.fixture(scope="module")
def rep_attainment() -> pd.DataFrame:
    return pd.read_csv(TABLEAU / "tableau_rep_attainment.csv")


def test_rep_attainment_row_count(rep_attainment: pd.DataFrame) -> None:
    # 12 reps × 12 quarters max; some reps not yet hired in early quarters
    assert 100 <= len(rep_attainment) <= 144


def test_rep_attainment_q4_2025_team_total_positive(rep_attainment: pd.DataFrame) -> None:
    q4 = rep_attainment[rep_attainment["quarter"] == "2025Q4"]
    assert q4["closed_amount"].sum() > 0
    assert "specialty" in rep_attainment.columns
```

- [ ] **Step 2: Run, verify failure**

Run: `pytest tests/test_tableau_extracts.py -v -k rep_attainment`
Expected: FAIL — file not found.

- [ ] **Step 3: Add `build_rep_attainment` to the script**

```python
def build_rep_attainment(
    opps: pd.DataFrame, reps: pd.DataFrame
) -> pd.DataFrame:
    """One row per (rep × quarter). Includes pre-hire filtering — reps don't get rows
    for quarters before their hire date.
    """
    opps = opps.copy()
    opps["close_date"] = pd.to_datetime(opps["close_date"])
    reps = reps.copy()
    reps["hire_date"] = pd.to_datetime(reps["hire_date"])

    quarters = pd.period_range(start="2023Q1", end="2025Q4", freq="Q")
    rows = []
    for q in quarters:
        attainment = quota.quarterly_attainment(opps, reps, q)
        for _, r in attainment.iterrows():
            rep_row = reps[reps["rep_id"] == r["rep_id"]].iloc[0]
            quarter_end = q.end_time
            if rep_row["hire_date"] > quarter_end:
                continue  # rep not yet hired
            tenure_months = (quarter_end - rep_row["hire_date"]).days / 30.44
            rows.append({
                "rep_id": r["rep_id"],
                "name": r["name"],
                "specialty": rep_row["segment_specialty"],
                "quarter": str(q),
                "closed_amount": float(r["closed_amount"]),
                "quarterly_quota": float(r["quarterly_quota"]),
                "attainment_pct": float(r["attainment_pct"]),
                "tenure_months_at_quarter_end": float(tenure_months),
            })
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Wire into main + run + test**

In `main()`, add:

```python
    rep_attainment = build_rep_attainment(data["opportunities"], data["reps"])
    rep_attainment.to_csv(TABLEAU / "tableau_rep_attainment.csv", index=False)
```

Then:

```bash
python -m scripts.build_tableau_extracts
pytest tests/test_tableau_extracts.py -v
```

Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/build_tableau_extracts.py tests/test_tableau_extracts.py data/tableau/tableau_rep_attainment.csv
git commit -m "feat(tableau): build rep attainment extract"
```

---

## Task 5: Build `tableau_ramp_curve.csv`

**Files:**
- Modify: `scripts/build_tableau_extracts.py`
- Modify: `tests/test_tableau_extracts.py`

SMB-cohort-only median attainment by integer tenure month (0-18). One line on the chart.

- [ ] **Step 1: Add failing tests**

```python
@pytest.fixture(scope="module")
def ramp() -> pd.DataFrame:
    return pd.read_csv(TABLEAU / "tableau_ramp_curve.csv")


def test_ramp_curve_covers_0_to_18(ramp: pd.DataFrame) -> None:
    assert ramp["tenure_month_bucket"].min() == 0
    assert ramp["tenure_month_bucket"].max() >= 12


def test_ramp_curve_shows_gradient(ramp: pd.DataFrame) -> None:
    """Insight: M0 attainment is meaningfully lower than M9+."""
    early = ramp[ramp["tenure_month_bucket"] <= 2]["median_attainment_pct"].mean()
    late = ramp[ramp["tenure_month_bucket"] >= 9]["median_attainment_pct"].mean()
    assert late - early >= 0.15
```

- [ ] **Step 2: Run, verify failure**

Run: `pytest tests/test_tableau_extracts.py -v -k ramp`
Expected: FAIL — file not found.

- [ ] **Step 3: Add `build_ramp_curve` to the script**

```python
def build_ramp_curve(
    opps: pd.DataFrame, reps: pd.DataFrame
) -> pd.DataFrame:
    """SMB-cohort median attainment by integer tenure month, 0 through 18.

    Uses src.quota.ramp_curve() to get the raw per-rep monthly series, then
    filters to SMB specialists and bins by integer tenure month.
    """
    smb_reps = reps[reps["segment_specialty"] == "SMB"]
    curve = quota.ramp_curve(opps, smb_reps)
    if curve.empty:
        return pd.DataFrame(columns=[
            "tenure_month_bucket", "median_attainment_pct", "n_data_points"
        ])
    curve["bucket"] = curve["tenure_months"].astype(int)
    out = (
        curve.groupby("bucket")
        .agg(
            median_attainment_pct=("attainment_pct", "median"),
            n_data_points=("attainment_pct", "size"),
        )
        .reset_index()
        .rename(columns={"bucket": "tenure_month_bucket"})
    )
    return out[out["tenure_month_bucket"] <= 18]
```

- [ ] **Step 4: Wire into main + run + test**

In `main()`:

```python
    ramp = build_ramp_curve(data["opportunities"], data["reps"])
    ramp.to_csv(TABLEAU / "tableau_ramp_curve.csv", index=False)
```

```bash
python -m scripts.build_tableau_extracts
pytest tests/test_tableau_extracts.py -v
```

Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/build_tableau_extracts.py tests/test_tableau_extracts.py data/tableau/tableau_ramp_curve.csv
git commit -m "feat(tableau): build SMB ramp curve extract"
```

---

## Task 6: Build `tableau_forecast_accuracy.csv`

**Files:**
- Modify: `scripts/build_tableau_extracts.py`
- Modify: `tests/test_tableau_extracts.py`

One row per (quarter × forecast_category). For each historical quarter, sum each forecast bucket as of quarter-start vs. actual closed-won in that quarter.

- [ ] **Step 1: Add failing tests**

```python
@pytest.fixture(scope="module")
def fc() -> pd.DataFrame:
    return pd.read_csv(TABLEAU / "tableau_forecast_accuracy.csv")


def test_forecast_accuracy_has_three_categories(fc: pd.DataFrame) -> None:
    assert set(fc["forecast_category"]) == {"Commit", "Best Case", "Pipeline"}


def test_forecast_accuracy_commit_tightest(fc: pd.DataFrame) -> None:
    """Commit should hit closer to actual than Pipeline category does (engineered)."""
    # accuracy_pct = forecasted / actual; closer to 1.0 = tighter
    commit_dev = (fc[fc["forecast_category"] == "Commit"]["accuracy_pct"] - 1.0).abs().mean()
    pipe_dev = (fc[fc["forecast_category"] == "Pipeline"]["accuracy_pct"] - 1.0).abs().mean()
    assert commit_dev < pipe_dev
```

- [ ] **Step 2: Run, verify failure**

Run: `pytest tests/test_tableau_extracts.py -v -k forecast`
Expected: FAIL — file not found.

- [ ] **Step 3: Add `build_forecast_accuracy` to the script**

```python
def build_forecast_accuracy(
    snapshots: pd.DataFrame, opps: pd.DataFrame
) -> pd.DataFrame:
    """One row per (quarter × forecast_category). For each quarter, takes the
    earliest snapshot in that quarter and sums each category, then compares
    against actual closed-won amount in the same quarter.
    """
    snapshots = snapshots.copy()
    snapshots["snapshot_date"] = pd.to_datetime(snapshots["snapshot_date"])
    opps = opps.copy()
    opps["close_date"] = pd.to_datetime(opps["close_date"])

    rows = []
    quarters = pd.period_range(start="2024Q1", end="2025Q4", freq="Q")
    for q in quarters:
        q_start = q.start_time
        q_end = q.end_time
        in_q_snaps = snapshots[
            (snapshots["snapshot_date"] >= q_start)
            & (snapshots["snapshot_date"] <= q_end)
        ]
        if in_q_snaps.empty:
            continue
        earliest = in_q_snaps["snapshot_date"].min()
        snap = snapshots[snapshots["snapshot_date"] == earliest]

        actual_total = float(opps[
            (opps["status"] == "closed_won")
            & (opps["close_date"] >= q_start)
            & (opps["close_date"] <= q_end)
        ]["amount"].sum())

        for cat in ["Commit", "Best Case", "Pipeline"]:
            fc_amt = float(snap[snap["forecast_category"] == cat]["amount"].sum())
            rows.append({
                "quarter": str(q),
                "forecast_category": cat,
                "forecasted_amount": fc_amt,
                "actual_amount": actual_total,
                "accuracy_pct": (fc_amt / actual_total) if actual_total > 0 else None,
            })
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Wire into main + run + test**

In `main()`:

```python
    fc = build_forecast_accuracy(data["snapshots"], data["opportunities"])
    fc.to_csv(TABLEAU / "tableau_forecast_accuracy.csv", index=False)
```

```bash
python -m scripts.build_tableau_extracts
pytest tests/test_tableau_extracts.py -v
```

Expected: 12 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/build_tableau_extracts.py tests/test_tableau_extracts.py data/tableau/tableau_forecast_accuracy.csv
git commit -m "feat(tableau): build forecast accuracy extract"
```

---

## Task 7: Final pre-agg sanity check

**Files:** (no new files)

- [ ] **Step 1: Run the full test suite, including existing Phase 1-3 tests**

Run: `pytest -v`
Expected: 69 existing tests + 12 new = 81 passed (or current existing count + 12).

- [ ] **Step 2: Eyeball the outputs**

```bash
ls -la data/tableau/
wc -l data/tableau/*.csv
```

Expected: 8 files total. Approximate row counts:
- `tableau_monthly_metrics.csv` ≈ 37 (36 data + header)
- `tableau_cohort_retention.csv` ≈ 3,500
- `tableau_rep_attainment.csv` ≈ 130
- `tableau_ramp_curve.csv` ≈ 19
- `tableau_forecast_accuracy.csv` ≈ 24
- The three raw passthroughs match `data/generated/` exactly.

- [ ] **Step 3: No commit needed** (no file changes — this is a verification gate)

---

## Task 8: Install Cadenza palette in Tableau

**Files:**
- Modify: `~/Documents/My Tableau Repository/Preferences.tps`

This is a one-time machine setup that makes the Cadenza colors available in every workbook on this machine.

- [ ] **Step 1: Open Preferences.tps in a text editor**

```bash
open "$HOME/Documents/My Tableau Repository/Preferences.tps"
```

If the file doesn't exist yet (fresh Tableau Public install), create it with this content:

```xml
<?xml version='1.0'?>
<workbook>
  <preferences>
  </preferences>
</workbook>
```

- [ ] **Step 2: Add the Cadenza palettes inside `<preferences>`**

Replace the empty `<preferences>` block with:

```xml
  <preferences>
    <color-palette name="Cadenza Categorical" type="regular">
      <color>#1F3A8A</color>
      <color>#06B6D4</color>
      <color>#10B981</color>
      <color>#EF4444</color>
      <color>#94A3B8</color>
    </color-palette>
    <color-palette name="Cadenza Diverging" type="ordered-diverging">
      <color>#EF4444</color>
      <color>#94A3B8</color>
      <color>#10B981</color>
    </color-palette>
    <color-palette name="Cadenza Sequential" type="ordered-sequential">
      <color>#E0E7FF</color>
      <color>#1F3A8A</color>
    </color-palette>
  </preferences>
```

- [ ] **Step 3: Restart Tableau Public if it's already open**

Quit Tableau Public entirely (`Cmd+Q`) and re-launch. Preferences only loads at startup.

- [ ] **Step 4: Verify the palette is available**

In Tableau Public: open a blank workbook → drag any dimension to Color on Marks → open the color editor → Palette dropdown. Expected: "Cadenza Categorical", "Cadenza Diverging", and "Cadenza Sequential" appear in the list.

- [ ] **Step 5: No commit** (Preferences.tps is outside the repo)

---

## Task 9: Create workbook, connect data sources

**Files:**
- Create: `tableau/cadenza.twb`

- [ ] **Step 1: Create the `tableau/` directory in the repo**

```bash
mkdir -p tableau
```

- [ ] **Step 2: Launch Tableau Public, save the workbook to `tableau/cadenza.twb`**

Open Tableau Public → New Workbook. Immediately File → Save As → navigate to `<repo>/tableau/` → save as `cadenza.twb` (XML format, NOT `.twbx` packaged).

Why .twb: the workbook is small XML; the data is in `data/tableau/`. Git diffs cleanly. We package as `.twbx` only at publish time.

- [ ] **Step 3: Add data source — Monthly Metrics**

Data → New Data Source → Text File → navigate to `<repo>/data/tableau/tableau_monthly_metrics.csv`.

Rename connection: right-click the data source name at the top of the Data pane → Rename → type "Monthly Metrics".

Verify field types:
- `Month` → change to Date if it imports as String (right-click → Change Data Type → Date).
- `Total Mrr`, `New Mrr`, `Expansion Mrr`, `Contraction Mrr`, `Churn Mrr` → Number (decimal). Should auto-detect.
- `Nrr`, `Grr`, `Logo Retention` → Number (decimal).

- [ ] **Step 4: Add data source — Cohort Retention**

Data → New Data Source → Text File → `tableau_cohort_retention.csv`. Rename to "Cohort Retention".

Field types:
- `Signup Cohort` → String (leave; it's "YYYY-MM" format and we'll treat it as ordinal).
- `Acquisition Channel` → String.
- `Months Since Signup` → Number (whole).
- `Retention Pct` → Number (decimal).
- `N Customers` → Number (whole).

- [ ] **Step 5: Add the remaining data sources**

For each, repeat: Data → New Data Source → Text File → select the CSV → rename connection.

| File | Connection name |
|---|---|
| `tableau_rep_attainment.csv` | Rep Attainment |
| `tableau_ramp_curve.csv` | Ramp Curve |
| `tableau_forecast_accuracy.csv` | Forecast Accuracy |
| `opportunities.csv` | Opportunities |
| `opportunity_stage_history.csv` | Stage History |
| `reps.csv` | Reps |

For `Opportunities`: change `Created Date` and `Close Date` to Date type.
For `Stage History`: change `Entered Date` and `Exited Date` to Date type.

- [ ] **Step 6: Save the workbook**

`Cmd+S`. The workbook now has 8 data sources connected.

- [ ] **Step 7: Commit**

```bash
git add tableau/cadenza.twb
git commit -m "feat(tableau): create workbook + connect all 8 data sources"
```

---

## Task 10: Dashboard 1 — Worksheet "Cohort Heatmap"

**Files:** `tableau/cadenza.twb` (modify)

The centerpiece chart for Dashboard 1. Rows = signup cohort, columns = months since signup, color = retention %.

- [ ] **Step 1: Create the worksheet**

Click the "+ New Worksheet" tab at the bottom. Rename it: right-click the tab → Rename → "Cohort Heatmap".

- [ ] **Step 2: Set the active data source to "Cohort Retention"**

In the Data pane (top left), click "Cohort Retention" so its fields appear.

- [ ] **Step 3: Build the matrix**

- Drag `Months Since Signup` → Columns shelf. Right-click the pill → set to **Dimension** (it imports as Measure; we want discrete column headers). Pill turns blue.
- Drag `Signup Cohort` → Rows shelf. Already discrete.
- Drag `Retention Pct` → Color (on the Marks card). Tableau aggregates as SUM by default — right-click the pill → Measure → Average.
- Change Marks type dropdown to **Square**.

- [ ] **Step 4: Add the channel filter**

- Drag `Acquisition Channel` → Filters shelf. In the dialog: check "All" → OK. Right-click the filter pill → Show Filter. The filter card appears on the right.
- Right-click the filter card title → Single Value (dropdown). Default value = "All".

- [ ] **Step 5: Configure the color encoding**

- Click the Color box on the Marks card → Edit Colors.
- Palette: **Cadenza Diverging** (Red → Slate → Green).
- Reversed: leave unchecked (low retention = red, high = green).
- Stepped Color: 5 steps.
- Advanced: Start = 0, End = 1. (Retention is 0–1 in this dataset; setting an explicit range keeps colors comparable across filter changes.)
- Click OK.

- [ ] **Step 6: Add a calculated field for the percentage label**

Analysis menu → Create Calculated Field. Name: `Retention Pct Label`. Formula:

```
IIF(AVG([Retention Pct]) IS NULL, "", STR(ROUND(AVG([Retention Pct]) * 100, 0)) + "%")
```

Click OK.

Drag `Retention Pct Label` → Label (on the Marks card).

- [ ] **Step 7: Format the axes**

- Right-click the `Months Since Signup` column header → Format → Header → font size 10.
- Right-click the worksheet area → Format → Lines → Grid Lines = None (cleaner look).

- [ ] **Step 8: Set the worksheet title**

Double-click the worksheet title at the top of the canvas → type `Cohort Retention by Channel`.

- [ ] **Step 9: Verify**

When `Acquisition Channel = Self-Serve Promo`, the 2024-07, 2024-08, 2024-09 rows should drop to red around `Months Since Signup = 6+`. Toggle through other channels to confirm those rows stay green-ish.

- [ ] **Step 10: Save + commit**

```bash
git add tableau/cadenza.twb
git commit -m "feat(tableau): cohort heatmap worksheet"
```

---

## Task 11: Dashboard 1 — Worksheet "M12 by Channel"

**Files:** `tableau/cadenza.twb`

Bar chart of 12-month retention, one bar per channel, sorted descending.

- [ ] **Step 1: Create + name the worksheet**

`+ New Worksheet` → rename to "M12 by Channel".

- [ ] **Step 2: Set data source to "Cohort Retention"**

- [ ] **Step 3: Filter to months_since_signup = 12 and exclude "All" channel**

- Drag `Months Since Signup` → Filters → choose At least 12 / at most 12 (or check the value 12 only) → OK.
- Drag `Acquisition Channel` → Filters → Exclude "All" (check all channels EXCEPT "All").

- [ ] **Step 4: Build the bar chart**

- Drag `Retention Pct` → Columns. Right-click → Measure → Average.
- Drag `Acquisition Channel` → Rows.
- Marks type: Bar (default).
- Right-click `Acquisition Channel` on Rows → Sort → Sort by: Field, Order: Descending, Field: Retention Pct, Aggregation: Average.

- [ ] **Step 5: Color by channel**

Drag `Acquisition Channel` → Color (Marks card). Click Color → Edit Colors → Palette: **Cadenza Categorical** → Assign Palette. Don't manually flag Self-Serve Promo red — the sort order already places it at the bottom, which is the visual story. Hand-coloring it red would read as biasing the viz.

- [ ] **Step 6: Add a 100% reference axis**

Drag `Retention Pct` → Label (Marks). Click Label → format as Percentage, 0 decimal places.

- [ ] **Step 7: Format the axis**

Right-click the `Retention Pct` axis → Edit Axis → Range: Fixed 0 to 1. → Tick marks: Major every 0.2.

Right-click the axis again → Format → Numbers → Percentage, 0 decimal places.

- [ ] **Step 8: Title + tooltip**

- Title: "M12 Retention by Channel".
- Click Tooltip (Marks card) → replace the default with:
  ```
  <Acquisition Channel>
  M12 Retention: <AVG(Retention Pct)>
  Cohort size: <SUM(N Customers)>
  ```

- [ ] **Step 9: Save + commit**

```bash
git commit -am "feat(tableau): M12 retention by channel bar"
```

---

## Task 12: Dashboard 1 — Worksheet "NRR Trend"

**Files:** `tableau/cadenza.twb`

Monthly NRR line over time with a 100% reference.

- [ ] **Step 1: Create worksheet "NRR Trend"**

- [ ] **Step 2: Data source = "Monthly Metrics"**

- [ ] **Step 3: Build the line**

- Drag `Month` → Columns. Right-click pill → Continuous Month (the green Month option, not the discrete blue one).
- Drag `Nrr` → Rows. Already a measure (sum by default — since each month has one row, sum and avg are equivalent here, but right-click → Measure → Average is more semantically correct).
- Marks type: Line.
- Filter: drag `Nrr` → Filters → exclude Null values (Special → Exclude Null Values), so the first 12 months (no TTM) don't show as zero.

- [ ] **Step 4: Add 100% reference line**

Click the Analytics pane (next to Data, top-left) → drag "Reference Line" → drop on the chart → choose "Entire Table" → Value = Constant 1.0 → Label = Custom: "100%" → Line: dashed, color `#94A3B8` (Cadenza Neutral).

- [ ] **Step 5: Format y-axis as percentage**

Right-click the `Nrr` axis → Format → Numbers → Percentage, 1 decimal place.

- [ ] **Step 6: Line color**

Click Color (Marks card) → set to `#1F3A8A` (Cadenza Primary).

- [ ] **Step 7: Title**

Worksheet title: "NRR (TTM) Trend".

- [ ] **Step 8: Save + commit**

```bash
git commit -am "feat(tableau): NRR trend worksheet"
```

---

## Task 13: Dashboard 1 — KPI tile worksheets (×4)

**Files:** `tableau/cadenza.twb`

Tableau "KPI tiles" are just single-number worksheets. Build all four in a row.

- [ ] **Step 1: Create worksheet "KPI - Current MRR"**

Data source: Monthly Metrics.

- Create calculated field. Analysis → Create Calculated Field. Name: `Current MRR`.
  ```
  IF [Month] = { MAX([Month]) } THEN [Total Mrr] END
  ```
  OK.
- Drag `Current MRR` → Text on Marks card. The pill becomes `SUM(Current MRR)` — leave as sum (only one non-null row).
- Marks type: Text (default).
- Click Text on Marks card → format the placeholder: font size 32, bold, color `#1F3A8A`. Add a second line below in the same Text editor: "Current MRR" (font size 12, regular, color `#94A3B8`).
- Format the value: right-click the `SUM(Current MRR)` pill → Format → Numbers → Currency (Custom), 0 decimal places, units = Thousands (K). Result reads e.g. "$540K".

- [ ] **Step 2: Create worksheet "KPI - NRR TTM"**

Same approach. Calc field name: `Latest NRR`. Formula:

```
IF [Month] = { MAX([Month]) } THEN [Nrr] END
```

Drag → Text. Format as Percentage, 1 decimal. Add label "Net Revenue Retention (TTM)".

- [ ] **Step 3: Create worksheet "KPI - GRR TTM"**

Calc field: `Latest GRR`. Formula:

```
IF [Month] = { MAX([Month]) } THEN [Grr] END
```

Format as percentage, 1 decimal. Label "Gross Revenue Retention (TTM)".

- [ ] **Step 4: Create worksheet "KPI - Logo Retention"**

Calc field: `Latest Logo Retention`. Formula:

```
IF [Month] = { MAX([Month]) } THEN [Logo Retention] END
```

Format as percentage, 1 decimal. Label "Logo Retention (TTM)".

- [ ] **Step 5: Save + commit**

```bash
git commit -am "feat(tableau): Dashboard 1 KPI tile worksheets"
```

---

## Task 14: Dashboard 1 — Assemble layout

**Files:** `tableau/cadenza.twb`

- [ ] **Step 1: Create the dashboard**

Click the "+ New Dashboard" icon at the bottom (next to worksheet tabs). Rename: right-click tab → "Cadenza Retention".

- [ ] **Step 2: Set dashboard size**

In the left panel under "Size", choose: Fixed size = "Generic Desktop" (1366 × 768) — Tableau Public default. Show grid lines for layout.

- [ ] **Step 3: Add the title**

Drag a Text object (from Objects panel on the left) to the top → type "Cadenza Retention" → font size 20, bold, color `#1F3A8A`. Set height = 50px.

- [ ] **Step 4: Add the KPI strip**

Below the title, drag a Horizontal container. Inside it, drag each of the four KPI worksheets (Current MRR, NRR TTM, GRR TTM, Logo Retention) left to right. For each KPI worksheet on the dashboard: click the worksheet → in the More Options (▾) → uncheck Title, uncheck Show Card, set "Fit" to Entire View. Set container height = 110px.

- [ ] **Step 5: Add the cohort heatmap**

Below the KPI strip, drag the "Cohort Heatmap" worksheet to the dashboard. It should take roughly the middle 50% of vertical space. Make sure the Acquisition Channel filter card is visible on the right side (it carried over from the worksheet). Move it to a docked position on the right.

- [ ] **Step 6: Add bottom row**

At the bottom, drag a Horizontal container. Drop the "M12 by Channel" worksheet into the left half and the "NRR Trend" worksheet into the right half.

- [ ] **Step 7: Add navigation button to Sales dashboard**

Drag a Navigation object (Objects panel) to the top-right corner of the dashboard. Configure: Navigate to = (will set after Dashboard 2 exists; for now leave empty). Button title: "→ Sales Performance". Background: `#1F3A8A`, text white.

- [ ] **Step 8: Apply the channel filter to all worksheets on this dashboard**

Right-click the Acquisition Channel filter card → Apply to Worksheets → Selected Worksheets → check "Cohort Heatmap" and "M12 by Channel" (NRR Trend doesn't use channel). The KPI tiles are channel-agnostic — they show overall, not channel-specific.

- [ ] **Step 9: Save + commit**

```bash
git commit -am "feat(tableau): assemble Dashboard 1 - Retention"
```

---

## Task 15: Dashboard 2 — Worksheet "Rep Attainment"

**Files:** `tableau/cadenza.twb`

Bar chart of attainment per rep for a selected quarter, sorted, colored by specialty.

- [ ] **Step 1: Create worksheet "Rep Attainment"**

Data source: Rep Attainment.

- [ ] **Step 2: Build the bars**

- Drag `Attainment Pct` → Columns. Right-click → Measure → Average (one row per rep × quarter; average and sum match after the quarter filter).
- Drag `Name` → Rows.
- Marks type: Bar.

- [ ] **Step 3: Add quarter filter**

- Drag `Quarter` → Filters → check 2025Q4 (default) → OK. Right-click filter pill → Show Filter. Right-click filter card → Single Value (list).

- [ ] **Step 4: Sort by attainment**

Right-click `Name` on Rows → Sort → Sort By: Field, Order: Descending, Field: Attainment Pct, Aggregation: Average.

- [ ] **Step 5: Color by specialty**

Drag `Specialty` → Color (Marks). Click Color → Edit Colors → assign:
- Enterprise → `#1F3A8A` (Cadenza Primary)
- Mid-Market → `#06B6D4` (Cadenza Accent)
- SMB → `#10B981` (Cadenza Good)

- [ ] **Step 6: Add 100% reference line**

Analytics pane → Reference Line → drag onto the Attainment Pct axis → Constant 1.0 → Label "Quota" → dashed, neutral color.

- [ ] **Step 7: Text labels on every bar (so 0% reps stay visible)**

- Drag `Attainment Pct` → Label (Marks).
- Click Label → Allow Labels to Overlap Other Marks (check). Alignment: end of bar.
- Right-click the labeled pill → Format → Numbers → Percentage, 0 decimal places.

- [ ] **Step 8: Format axis**

Right-click `Attainment Pct` axis → Edit Axis → Fixed: 0 to 2.0 (so outliers above 100% fit). Format → Percentage, 0 decimals.

- [ ] **Step 9: Title + tooltip**

Title: "Rep Attainment by Quarter".

Tooltip (Marks card):
```
<Name> — <Specialty>
Closed: <SUM(Closed Amount)>
Quota: <SUM(Quarterly Quota)>
Attainment: <AVG(Attainment Pct)>
Tenure: <AVG(Tenure Months At Quarter End)> months
```

- [ ] **Step 10: Save + commit**

```bash
git commit -am "feat(tableau): rep attainment bar worksheet"
```

---

## Task 16: Dashboard 2 — Worksheet "Forecast Accuracy"

**Files:** `tableau/cadenza.twb`

Grouped bar: Forecasted vs Actual for each forecast category, averaged across quarters.

- [ ] **Step 1: Create worksheet "Forecast Accuracy"**

Data source: Forecast Accuracy.

- [ ] **Step 2: Build a grouped bar via Measure Names**

- Drag `Forecast Category` → Columns.
- Drag `Measure Names` → Columns (after Forecast Category — second pill).
- Drag `Measure Values` → Rows.
- In the Measure Values shelf (right side of the canvas), keep only `Forecasted Amount` and `Actual Amount` — drag everything else out.
- Marks type: Bar.

- [ ] **Step 3: Color by forecast type**

Drag `Measure Names` → Color (Marks). Edit Colors:
- Forecasted Amount → `#06B6D4` (Cadenza Accent)
- Actual Amount → `#1F3A8A` (Cadenza Primary)

- [ ] **Step 4: Sort forecast categories**

Right-click `Forecast Category` on Columns → Sort → Manual → order: Commit, Best Case, Pipeline.

- [ ] **Step 5: Add data labels**

Drag `Measure Values` → Label. Format as Currency, 0 decimals, units = Thousands (K).

- [ ] **Step 6: Format y-axis**

Right-click axis → Format → Numbers → Currency, 0 decimals, Thousands.

- [ ] **Step 7: Title + tooltip**

Title: "Forecast vs Actual by Category".

Tooltip:
```
<Forecast Category> — <Measure Names>
<Quarter>: <SUM(Measure Values)>
```

- [ ] **Step 8: Save + commit**

```bash
git commit -am "feat(tableau): forecast accuracy grouped bar"
```

---

## Task 17: Dashboard 2 — Worksheet "Ramp Curve"

**Files:** `tableau/cadenza.twb`

Line chart of median attainment % by integer tenure month, with two reference lines.

- [ ] **Step 1: Create worksheet "Ramp Curve"**

Data source: Ramp Curve.

- [ ] **Step 2: Build the line**

- Drag `Tenure Month Bucket` → Columns. Continuous (green pill — leave as is).
- Drag `Median Attainment Pct` → Rows. Right-click → Measure → Average (each tenure bucket already has one value; this is just for the aggregation pill).
- Marks type: Line.

- [ ] **Step 3: Color the line**

Click Color (Marks) → `#1F3A8A` (Cadenza Primary). Increase line size by 2 notches.

- [ ] **Step 4: Add the two reference lines**

Analytics pane → drag Reference Line onto the `Tenure Month Bucket` axis.

**First reference line (Assumed ramp):**
- Scope: Entire Table
- Value: Constant 6
- Label: Custom — type: `Assumed ramp (6mo)`
- Line: dashed, color `#94A3B8` (Neutral)
- Fill above/below: None
- Label position: **Above** (top-left side of the line)

**Second reference line (Actual ramp):**
- Drag another Reference Line onto the same axis.
- Scope: Entire Table
- Value: Constant 9
- Label: Custom — type: `Actual ramp (~9mo)`
- Line: dashed, color `#94A3B8`
- Label position: **Above, aligned right** (so the two labels don't overlap)

- [ ] **Step 5: Format y-axis as percentage**

Right-click `Median Attainment Pct` axis → Format → Percentage, 0 decimals. Edit Axis → Range: 0 to 1.5.

- [ ] **Step 6: Title**

"SMB Ramp Curve (Median Attainment by Tenure)".

- [ ] **Step 7: Tooltip**

```
Tenure: <Tenure Month Bucket> months
Median Attainment: <AVG(Median Attainment Pct)>
Data points: <SUM(N Data Points)>
```

- [ ] **Step 8: Save + commit**

```bash
git commit -am "feat(tableau): SMB ramp curve worksheet"
```

---

## Task 18: Dashboard 2 — KPI tile worksheets (×4)

**Files:** `tableau/cadenza.twb`

- [ ] **Step 1: Create worksheet "KPI - Team Attainment"**

Data source: Rep Attainment.

- Calc field: `Team Attainment Q4 2025`. Formula:
  ```
  SUM(IF [Quarter] = "2025Q4" THEN [Closed Amount] END)
  /
  SUM(IF [Quarter] = "2025Q4" THEN [Quarterly Quota] END)
  ```
- Drag onto Text. Format as percentage, 0 decimals. Label: "Team Attainment — Q4 2025".

- [ ] **Step 2: Create worksheet "KPI - Pipeline Coverage"**

Data source: Opportunities.

- Calc field: `Open Pipeline Q1 2026`. Formula:
  ```
  SUM(IF [Status] = "open" THEN [Amount] END)
  ```
  (Open opps are forward-looking; we're measuring coverage for the next selling cycle.)

- Calc field: `Q1 2026 Quota Estimate`. Formula:
  ```
  // Sum of quarterly_quota across all 12 reps.
  // Derived from reps.csv: 4 SMB × $80K + 4 MM × $150K + 4 Enterprise × $500K = $2,920K.
  // Verify with: python -c "import pandas as pd; print(pd.read_csv('data/tableau/reps.csv')['quarterly_quota'].sum())"
  2920000
  ```

  (Tableau can't easily aggregate across data sources in a single-row KPI without data blending, which adds complexity disproportionate to the value. Hardcoding the team quota total is the pragmatic choice. Update this constant if quotas ever change in `reps.csv`.)

- Calc field: `Pipeline Coverage`. Formula:
  ```
  [Open Pipeline Q1 2026] / [Q1 2026 Quota Estimate]
  ```

- Drag `Pipeline Coverage` onto Text. Format as Number with one decimal + "x" suffix (e.g., "2.3x"): edit format → Custom: `0.0"x"`. Label: "Pipeline Coverage".

- [ ] **Step 3: Create worksheet "KPI - Forecast Accuracy"**

Data source: Forecast Accuracy.

- Calc field: `Commit Accuracy Avg`. Formula:
  ```
  AVG(IF [Forecast Category] = "Commit" THEN [Accuracy Pct] END)
  ```

- Drag onto Text. Format as percentage, 0 decimals. Label: "Commit Forecast Accuracy".

- [ ] **Step 4: Create worksheet "KPI - Win Rate"**

Data source: Opportunities.

- Calc field: `Win Rate`. Formula:
  ```
  SUM(IF [Status] = "closed_won" THEN 1 ELSE 0 END)
  /
  SUM(IF [Status] IN ("closed_won", "closed_lost") THEN 1 ELSE 0 END)
  ```

- Drag onto Text. Format as percentage, 0 decimals. Label: "Win Rate (All Time)".

- [ ] **Step 5: Save + commit**

```bash
git commit -am "feat(tableau): Dashboard 2 KPI tile worksheets"
```

---

## Task 19: Dashboard 2 — Assemble layout

**Files:** `tableau/cadenza.twb`

- [ ] **Step 1: New dashboard "Cadenza Sales Performance"**

Same size as Dashboard 1.

- [ ] **Step 2: Title bar**

Text object at top: "Cadenza Sales Performance", same styling as Dashboard 1.

- [ ] **Step 3: KPI strip**

Horizontal container under title with all four Dashboard 2 KPI worksheets: Team Attainment, Pipeline Coverage, Forecast Accuracy, Win Rate.

- [ ] **Step 4: Top row of charts**

Below the KPI strip, drag a Horizontal container. Left half: "Rep Attainment". Right half: "Forecast Accuracy".

- [ ] **Step 5: Bottom row**

Below the top row, drop the "Ramp Curve" worksheet — full width.

- [ ] **Step 6: Add filters**

Show the Quarter filter (carried over from Rep Attainment worksheet). Add Specialty filter:
- Drag `Specialty` (from Rep Attainment source) → Filters on the Rep Attainment worksheet first → Show Filter.
- It will appear on the dashboard. Set to Multi-Value (dropdown).

Apply Quarter filter to: Rep Attainment, Team Attainment KPI.
Apply Specialty filter to: Rep Attainment only.

- [ ] **Step 7: Navigation buttons**

Top-right corner: navigation button "← Retention" (target: Cadenza Retention dashboard).

Also: go back to the Dashboard 1 navigation button (Task 14 Step 7) and set its target to "Cadenza Sales Performance".

- [ ] **Step 8: Save + commit**

```bash
git commit -am "feat(tableau): assemble Dashboard 2 - Sales Performance"
```

---

## Task 20: Dashboard 3 — Worksheet "Pipeline by Stage"

**Files:** `tableau/cadenza.twb`

Horizontal stacked bar — stage on rows, $ on columns, stacked by segment.

- [ ] **Step 1: Create worksheet "Pipeline by Stage"**

Data source: Opportunities.

- [ ] **Step 2: Filter to open opps**

Drag `Status` → Filters → check "open" only.

- [ ] **Step 3: Build the stacked bar**

- Drag `Current Stage` → Rows.
- Drag `Amount` → Columns. Default SUM.
- Drag `Segment` → Color (Marks).
- Marks type: Bar.

- [ ] **Step 4: Sort stages in funnel order**

Right-click `Current Stage` on Rows → Sort → Manual → order: Discovery, Qualification, Proof of Concept, Negotiation.

- [ ] **Step 5: Color**

Edit Colors for Segment:
- Enterprise → `#1F3A8A`
- Mid-Market → `#06B6D4`
- SMB → `#10B981`

- [ ] **Step 6: Format axis**

X-axis → Format → Currency, 0 decimals, Thousands (K).

- [ ] **Step 7: Add segment filter (show on dashboard later)**

Drag `Segment` → Filters → All → Show Filter.

- [ ] **Step 8: Title + tooltip**

Title: "Open Pipeline by Stage".

Tooltip:
```
<Current Stage> — <Segment>
Pipeline: <SUM(Amount)>
# Deals: <COUNT(Opportunity Id)>
```

- [ ] **Step 9: Save + commit**

```bash
git commit -am "feat(tableau): pipeline by stage worksheet"
```

---

## Task 21: Dashboard 3 — Worksheet "Win Rate by Segment"

**Files:** `tableau/cadenza.twb`

- [ ] **Step 1: Create worksheet "Win Rate by Segment"**

Data source: Opportunities.

- [ ] **Step 2: Filter to closed deals**

Drag `Status` → Filters → check "closed_won" and "closed_lost".

- [ ] **Step 3: Create calc field "Win Rate by Segment"**

```
SUM(IF [Status] = "closed_won" THEN 1 ELSE 0 END)
/
COUNT([Opportunity Id])
```

- [ ] **Step 4: Build the chart**

- Drag `Segment` → Columns.
- Drag `Win Rate by Segment` calc → Rows.
- Sort: Segment → Manual → SMB, Mid-Market, Enterprise.

- [ ] **Step 5: Color + format**

Color: same Cadenza Categorical mapping as Pipeline by Stage.

Format y-axis: Percentage, 0 decimals. Edit Axis: Fixed 0 to 0.5.

Add data label: drag `Win Rate by Segment` → Label. Percentage, 0 decimals.

- [ ] **Step 6: Title**

"Win Rate by Segment (Closed Deals)".

- [ ] **Step 7: Save + commit**

```bash
git commit -am "feat(tableau): win rate by segment worksheet"
```

---

## Task 22: Dashboard 3 — Worksheet "Stage Velocity"

**Files:** `tableau/cadenza.twb`

Average days in stage per stage.

- [ ] **Step 1: Create worksheet "Stage Velocity"**

Data source: Stage History.

- [ ] **Step 2: Build the bar**

- Drag `Days In Stage` → Columns. Default SUM — right-click → Measure → Average.
- Drag `Stage` → Rows.
- Marks: Bar.

- [ ] **Step 3: Sort manually**

Right-click `Stage` → Sort → Manual → Discovery, Qualification, Proof of Concept, Negotiation, Closed Won, Closed Lost.

(If `stage_history.csv` doesn't include the closed stages, only the open ones will appear — fine.)

- [ ] **Step 4: Color, format, label**

Color: solid `#1F3A8A`.

Format axis: 0 decimals, suffix "days" (Custom format: `0" days"`).

Add label: drag `Days In Stage` → Label. Average. Format: `0.0" days"`.

- [ ] **Step 5: Title**

"Average Days in Stage".

- [ ] **Step 6: Save + commit**

```bash
git commit -am "feat(tableau): stage velocity worksheet"
```

---

## Task 23: Dashboard 3 — KPI tile worksheets (×4)

**Files:** `tableau/cadenza.twb`

- [ ] **Step 1: Create worksheet "KPI - Total Pipeline"**

Data source: Opportunities.

Calc field: `Total Open Pipeline`. Formula:
```
SUM(IF [Status] = "open" THEN [Amount] END)
```

Drag → Text. Format: Currency, 0 decimals, Thousands (K). Label "Total Open Pipeline".

- [ ] **Step 2: Create worksheet "KPI - Pipeline Coverage"**

Reuse the "KPI - Pipeline Coverage" worksheet from Task 18 (Step 2) — drop the same worksheet onto Dashboard 3 later.

If you want a separate copy with different framing on Dashboard 3, duplicate it (right-click tab → Duplicate) and rename.

- [ ] **Step 3: Create worksheet "KPI - Avg Deal Size"**

Data source: Opportunities.

Calc field: `Won Avg Deal Size`. Formula:
```
AVG(IF [Status] = "closed_won" THEN [Amount] END)
```

Drag → Text. Format: Currency, 0 decimals, Thousands (K). Label "Avg Won Deal Size".

- [ ] **Step 4: Create worksheet "KPI - Open Deals"**

Data source: Opportunities.

Calc field: `Open Deal Count`. Formula:
```
COUNT(IF [Status] = "open" THEN [Opportunity Id] END)
```

Drag → Text. Format: Number, 0 decimals. Label "# Open Deals".

- [ ] **Step 5: Save + commit**

```bash
git commit -am "feat(tableau): Dashboard 3 KPI tile worksheets"
```

---

## Task 24: Dashboard 3 — Assemble layout

**Files:** `tableau/cadenza.twb`

- [ ] **Step 1: New dashboard "Cadenza Pipeline"**

- [ ] **Step 2: Title bar, KPI strip, charts**

- Title at top.
- KPI strip horizontal container: Total Pipeline, Pipeline Coverage, Avg Deal Size, # Open Deals.
- Middle row: Pipeline by Stage (left) + Win Rate by Segment (right).
- Bottom row: Stage Velocity (full width).

- [ ] **Step 3: Filters**

Show Segment filter (from Pipeline by Stage worksheet). Apply to: Pipeline by Stage, Win Rate by Segment, Total Pipeline KPI, Avg Deal Size KPI, # Open Deals KPI.

- [ ] **Step 4: Navigation buttons**

Top-right: "← Retention" and "← Sales Performance" buttons.

Go back to Dashboards 1 and 2 and add their "→ Pipeline" buttons now that this dashboard exists.

- [ ] **Step 5: Save + commit**

```bash
git commit -am "feat(tableau): assemble Dashboard 3 - Pipeline"
```

---

## Task 25: Final polish pass

**Files:** `tableau/cadenza.twb`

- [ ] **Step 1: Walk through all three dashboards in presentation mode**

Top-right of the Tableau toolbar → Presentation Mode (Cmd+Enter). Click each navigation button. Verify:
- All transitions work.
- All filters reset to defaults when navigating between dashboards.
- No text overflows containers.
- No "Error" placeholders on any chart.

- [ ] **Step 2: Standardize fonts**

For every worksheet title: font size 14, bold, color `#1F3A8A`.
For every axis label: font size 10, regular, color `#94A3B8`.

To set globally: Format menu → Workbook → set font defaults.

- [ ] **Step 3: Standardize tooltips**

Each chart's tooltip should include:
- The dimension being hovered (e.g., rep name, channel, stage).
- The headline metric formatted properly.
- Cohort / count / contextualizing info where relevant.

Audit each worksheet's Tooltip text. The tooltip from Tasks 10-22 specs are starting points; trim verbose lines.

- [ ] **Step 4: Verify all KPI tiles read correctly**

Each tile should show:
- A large number (font 32, bold, primary color).
- A small label below (font 12, neutral color).
- No "Null" or "Error" text.

- [ ] **Step 5: Save + commit**

```bash
git commit -am "polish(tableau): consistent fonts, tooltips, KPI styling across dashboards"
```

---

## Task 26: Publish to Tableau Public + link from Streamlit

**Files:**
- Modify: `pages/8_About.py`
- Modify: `README.md`

- [ ] **Step 1: Sign in to Tableau Public from the desktop app**

Server menu → Tableau Public → Sign In. If you don't have an account, create one at `public.tableau.com/app/discover` (free).

- [ ] **Step 2: Publish**

Server → Tableau Public → Save to Tableau Public As → name: "Cadenza Retention Analytics" → Save.

Tableau will upload + open the published workbook in your browser. Copy the URL — it'll look like `https://public.tableau.com/views/CadenzaRetentionAnalytics/CadenzaRetention`.

- [ ] **Step 3: Set the workbook description on Tableau Public**

In the browser, click Edit Details on the published workbook. Description:

```
Cadenza — synthetic SaaS retention & sales analytics, demonstrating RevOps
fluency across retention, pipeline, and quota motions.

Streamlit companion: https://cadenza-retention-analytics.streamlit.app
GitHub: https://github.com/JesseKartes/revops_portfolio_claude
```

- [ ] **Step 4: Add link to Streamlit About page**

Open `pages/8_About.py`. Find the section near the top with the live-dashboard link. Add a new bullet:

```python
st.markdown("""
**Tableau companion:** [public.tableau.com/views/CadenzaRetentionAnalytics](<paste-url-here>)
A simplified Tableau version of this same analysis — three dashboards
(Retention, Sales Performance, Pipeline) for hiring teams that use Tableau,
Looker, or Power BI rather than Streamlit.
""")
```

(Adjust the exact placement to match the existing About page's structure.)

- [ ] **Step 5: Add link to README**

In `README.md`, find the "Live dashboard" line near the top. Add a second line:

```markdown
**Live Streamlit dashboard:** https://cadenza-retention-analytics.streamlit.app
**Tableau Public companion:** <paste-tableau-url-here>
```

- [ ] **Step 6: Final commit**

```bash
git add pages/8_About.py README.md
git commit -m "docs: link Tableau Public workbook from About page + README"
git push origin main
```

(Streamlit Cloud will auto-redeploy on push.)

---

## Done

All three dashboards live on Tableau Public, linked from the Streamlit About page and the README. Optional next steps captured in spec §10 (Story object, parameter actions, iframe embed, Power BI version) are out of scope for this build.

Tableau Public URL: paste here after publishing.

Total time invested: ~6 hours per the spec estimate.
