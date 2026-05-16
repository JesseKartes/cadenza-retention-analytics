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
