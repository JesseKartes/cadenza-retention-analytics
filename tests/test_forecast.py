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
