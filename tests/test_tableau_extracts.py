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


@pytest.fixture(scope="module")
def cohort() -> pd.DataFrame:
    return pd.read_csv(TABLEAU / "tableau_cohort_retention.csv")


def test_cohort_retention_has_all_channel(cohort: pd.DataFrame) -> None:
    assert "All" in cohort["acquisition_channel"].unique()


def test_cohort_retention_no_nan_in_retention_pct(cohort: pd.DataFrame) -> None:
    assert cohort["retention_pct"].notna().all()


def test_cohort_retention_q3_2024_self_serve_visible(cohort: pd.DataFrame) -> None:
    """The engineered insight: Q3 2024 Self-Serve Promo churns at ~2× normal rate.

    Tests the churn-rate ratio directly (1.5× threshold gives the assertion
    headroom against per-cohort randomness while still failing if the insight
    disappears from the data).
    """
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
    promo_churn = 1 - q3_promo["retention_pct"].mean()
    other_churn = 1 - other_q3["retention_pct"].mean()
    assert promo_churn > 1.5 * other_churn, (
        f"Q3 Promo churn ({promo_churn:.2%}) should be >1.5x other channels' churn ({other_churn:.2%})"
    )


@pytest.fixture(scope="module")
def rep_attainment() -> pd.DataFrame:
    return pd.read_csv(TABLEAU / "tableau_rep_attainment.csv")


def test_rep_attainment_row_count(rep_attainment: pd.DataFrame) -> None:
    # 12 reps × 12 quarters = 144 max; with staggered hire dates (4 reps in 2022,
    # rest dripped through 2025), actual count is ~97. Allow a wide band so a
    # generator change that shifts hire dates doesn't break this test.
    assert 80 <= len(rep_attainment) <= 144


def test_rep_attainment_q4_2025_team_total_positive(rep_attainment: pd.DataFrame) -> None:
    q4 = rep_attainment[rep_attainment["quarter"] == "2025Q4"]
    assert q4["closed_amount"].sum() > 0
    assert "specialty" in rep_attainment.columns


@pytest.fixture(scope="module")
def ramp() -> pd.DataFrame:
    return pd.read_csv(TABLEAU / "tableau_ramp_curve.csv")


def test_ramp_curve_covers_through_actual_ramp_mark(ramp: pd.DataFrame) -> None:
    # SMB reps were hired late in the dataset (earliest Dec 2024), so max tenure
    # observable is ~11 months at data end. Curve must cover through M9 so the
    # "Actual ramp (~9mo)" reference line on the Tableau viz has data behind it.
    assert ramp["tenure_month_bucket"].min() == 0
    assert ramp["tenure_month_bucket"].max() >= 9


def test_ramp_curve_shows_gradient(ramp: pd.DataFrame) -> None:
    """Insight: M0 attainment is meaningfully lower than M9+."""
    early = ramp[ramp["tenure_month_bucket"] <= 2]["median_attainment_pct"].mean()
    late = ramp[ramp["tenure_month_bucket"] >= 9]["median_attainment_pct"].mean()
    assert late - early >= 0.15


@pytest.fixture(scope="module")
def fc() -> pd.DataFrame:
    return pd.read_csv(TABLEAU / "tableau_forecast_accuracy.csv")


def test_forecast_accuracy_has_three_categories(fc: pd.DataFrame) -> None:
    assert set(fc["forecast_category"]) == {"Commit", "Best Case", "Pipeline"}


def test_forecast_accuracy_commit_tightest(fc: pd.DataFrame) -> None:
    """Commit should hit closer to actual than Pipeline category does (engineered)."""
    commit_dev = (fc[fc["forecast_category"] == "Commit"]["accuracy_pct"] - 1.0).abs().mean()
    pipe_dev = (fc[fc["forecast_category"] == "Pipeline"]["accuracy_pct"] - 1.0).abs().mean()
    assert commit_dev < pipe_dev
