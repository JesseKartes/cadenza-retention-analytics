"""Tests for src/pipeline.py — validated against tiny_opportunities and
tiny_stage_history fixtures in conftest.py.
"""
from __future__ import annotations

import pytest

from src.pipeline import (
    total_pipeline,
    weighted_pipeline,
    pipeline_coverage,
)


def test_total_pipeline_sums_open_deals_created_on_or_before_as_of(tiny_opportunities):
    # Open deals at 2024-04-01: OPP-2 (60k), OPP-3 (200k), OPP-8 (40k) = 300k
    # Closed deals (OPP-1, 4, 5, 6, 7) are excluded.
    assert total_pipeline(tiny_opportunities, "2024-04-01") == pytest.approx(300_000.0)


def test_total_pipeline_excludes_deals_created_after_as_of(tiny_opportunities):
    # As of 2024-02-01: OPP-8 (created 2024-02-15) is excluded
    # OPP-3 (created 2024-01-15) included, OPP-2 (created 2024-02-01) included.
    # Result: 60k + 200k = 260k
    assert total_pipeline(tiny_opportunities, "2024-02-01") == pytest.approx(260_000.0)


def test_weighted_pipeline_applies_stage_probability(tiny_opportunities):
    # Open deals at 2024-04-01:
    #   OPP-2 in POC: 0.40 * 60_000 = 24_000
    #   OPP-3 in Negotiation: 0.65 * 200_000 = 130_000
    #   OPP-8 in Discovery: 0.10 * 40_000 = 4_000
    # Sum = 158_000
    assert weighted_pipeline(tiny_opportunities, "2024-04-01") == pytest.approx(158_000.0)


def test_pipeline_coverage_is_pipeline_over_target(tiny_opportunities):
    # total_pipeline at 2024-04-01 = 300_000. Target 100_000. Coverage = 3.0
    assert pipeline_coverage(tiny_opportunities, 100_000.0, "2024-04-01") == pytest.approx(3.0)


def test_pipeline_coverage_returns_zero_when_target_is_zero(tiny_opportunities):
    # Guard divide-by-zero. Returning 0 is the conservative choice — there's
    # no meaningful coverage ratio against a $0 target.
    assert pipeline_coverage(tiny_opportunities, 0.0, "2024-04-01") == 0.0


from src.pipeline import win_rate


def test_win_rate_won_over_closed(tiny_opportunities):
    # Closed deals (close_date in [2024-01-01, 2024-04-01)):
    #   won:  OPP-1 (2024-03-31), OPP-5 (2024-03-01), OPP-7 (2024-03-15) = 3
    #   lost: OPP-4 (2024-02-15), OPP-6 (2024-02-20) = 2
    # Rate = 3/5 = 0.60
    assert win_rate(tiny_opportunities, "2024-01-01", "2024-04-01") == pytest.approx(0.60)


def test_win_rate_returns_zero_when_no_closed_deals(tiny_opportunities):
    # No deals close in [2025-01-01, 2025-02-01)
    assert win_rate(tiny_opportunities, "2025-01-01", "2025-02-01") == 0.0


from src.pipeline import avg_sales_cycle_days


def test_avg_sales_cycle_days_for_won_deals(tiny_opportunities):
    # Won deals in [2024-01-01, 2024-04-01):
    #   OPP-1: 2024-03-31 − 2024-01-01 = 90 days
    #   OPP-5: 2024-03-01 − 2024-01-01 = 60 days
    #   OPP-7: 2024-03-15 − 2024-01-15 = 60 days
    # Avg = (90 + 60 + 60) / 3 = 70.0
    assert avg_sales_cycle_days(tiny_opportunities, "2024-01-01", "2024-04-01") == pytest.approx(70.0)
