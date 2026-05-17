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


def build_ramp_curve(
    opps: pd.DataFrame, reps: pd.DataFrame
) -> pd.DataFrame:
    """Team-wide ramp curve: median attainment by integer tenure month, smoothed.

    Mirrors the Streamlit ramp chart's methodology (src/viz.py:ramp_curve_figure):
    median across all reps within each integer-month bucket, then a 3-month
    centered rolling smooth on top to damp Enterprise lumpiness.

    The SMB-only insight test lives in src/quota.py; this chart is team-wide
    because that's where the "Assumed 6mo vs Actual ~9mo" story is told.
    """
    curve = quota.ramp_curve(opps, reps)
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
    out = out[out["tenure_month_bucket"] <= 18].sort_values("tenure_month_bucket")
    out["median_attainment_pct"] = (
        out["median_attainment_pct"].rolling(window=3, center=True, min_periods=1).mean()
    )
    return out.reset_index(drop=True)


def main() -> None:
    TABLEAU.mkdir(parents=True, exist_ok=True)
    data = load_inputs()

    monthly = build_monthly_metrics(data["subscriptions"], data["events"])
    monthly.to_csv(TABLEAU / "tableau_monthly_metrics.csv", index=False)

    cohort = build_cohort_retention(data["subscriptions"], data["customers"])
    cohort.to_csv(TABLEAU / "tableau_cohort_retention.csv", index=False)

    rep_attainment = build_rep_attainment(data["opportunities"], data["reps"])
    rep_attainment.to_csv(TABLEAU / "tableau_rep_attainment.csv", index=False)

    ramp = build_ramp_curve(data["opportunities"], data["reps"])
    ramp.to_csv(TABLEAU / "tableau_ramp_curve.csv", index=False)

    copy_raw_files()
    print(f"Wrote outputs to {TABLEAU.resolve()}")


if __name__ == "__main__":
    main()
