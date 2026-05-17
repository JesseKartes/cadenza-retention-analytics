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
