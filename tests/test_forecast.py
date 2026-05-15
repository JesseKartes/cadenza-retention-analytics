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
