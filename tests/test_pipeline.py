"""Tests for src/pipeline.py — validated against tiny_opportunities and
tiny_stage_history fixtures in conftest.py.
"""
from __future__ import annotations

import pytest

from src.pipeline import (
    total_pipeline,
    weighted_pipeline,
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
