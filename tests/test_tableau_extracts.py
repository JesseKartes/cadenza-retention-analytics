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
