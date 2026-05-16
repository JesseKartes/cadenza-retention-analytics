"""Tests for src/quota.py — Cadenza Phase 3 quota / rep performance metrics."""
from __future__ import annotations

import pandas as pd
import pytest


def test_module_importable():
    """Smoke check: the empty module imports cleanly."""
    from src import quota  # noqa: F401


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
