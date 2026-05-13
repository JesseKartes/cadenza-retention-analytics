"""Metric correctness tests, computed against hand-built fixtures with
known answers (see conftest.py).
"""
from __future__ import annotations

import pytest

from src.metrics import arr, logo_churn, gross_revenue_churn, grr, nrr, mrr_waterfall


def test_arr_is_mrr_times_twelve(tiny_subs):
    # Jan 2024 active MRR = 100 + 200 + 300 + 400 = 1000
    assert arr(tiny_subs, "2024-01-01") == 12_000.0


def test_arr_excludes_churned_customers(tiny_subs):
    # March: CUST-3 has churned, so absent. MRR = 100 + 250 + 350 + 500 = 1200
    assert arr(tiny_subs, "2024-03-01") == 14_400.0


def test_logo_churn_jan_to_mar(tiny_subs):
    # Active in Jan: {CUST-1, CUST-2, CUST-3, CUST-4} = 4 customers
    # Active in Mar (from that cohort): {CUST-1, CUST-2, CUST-4} = 3
    # Churned = 1 -> 1/4 = 0.25
    assert logo_churn(tiny_subs, "2024-01-01", "2024-03-01") == pytest.approx(0.25)


def test_logo_churn_feb_to_mar(tiny_subs):
    # Feb -> Mar: cohort = active in Feb = {1,2,3,4,5}. Active in Mar = {1,2,4,5}. Churned = 1 (CUST-3) -> 1/5 = 0.20
    assert logo_churn(tiny_subs, "2024-02-01", "2024-03-01") == pytest.approx(0.20)


def test_nrr_jan_to_mar(tiny_subs):
    # Cohort = active in Jan: {1,2,3,4}, starting MRR = 1000
    # Their Mar MRR: CUST-1=100, CUST-2=250, CUST-3=0 (churned), CUST-4=350 -> 700
    # NRR = 700 / 1000 = 0.70
    assert nrr(tiny_subs, "2024-01-01", "2024-03-01") == pytest.approx(0.70)


def test_nrr_feb_to_mar_with_expansion_and_churn(tiny_subs):
    # Feb -> Mar: cohort = {1,2,3,4,5}, starting MRR = 100+250+300+350+500 = 1500
    # Their Mar MRR: 100+250+0+350+500 = 1200 -> NRR = 1200/1500 = 0.80
    assert nrr(tiny_subs, "2024-02-01", "2024-03-01") == pytest.approx(0.80)


def test_grr_caps_expansion_at_start_mrr(tiny_subs):
    # Jan -> Mar: cohort = {1,2,3,4}, starting MRR = 1000
    # GRR caps each customer's end MRR at their start MRR:
    #   CUST-1: min(100, 100) = 100
    #   CUST-2: min(250, 200) = 200  (expansion stripped)
    #   CUST-3: min(0, 300) = 0      (churned)
    #   CUST-4: min(350, 400) = 350  (contracted)
    # Sum = 650 -> GRR = 650/1000 = 0.65
    assert grr(tiny_subs, "2024-01-01", "2024-03-01") == pytest.approx(0.65)


def test_gross_revenue_churn_is_one_minus_grr(tiny_subs):
    # = 1 - 0.65 = 0.35
    assert gross_revenue_churn(tiny_subs, "2024-01-01", "2024-03-01") == pytest.approx(0.35)


def test_grr_with_no_starting_customers_returns_one(tiny_subs):
    # Pick a month with no activity
    assert grr(tiny_subs, "2030-01-01", "2030-02-01") == 1.0


def test_mrr_waterfall_jan_to_mar(tiny_subs, tiny_events):
    # Starting MRR (Jan): 100+200+300+400 = 1000
    # Period = events after 2024-01-01 and up to 2024-03-31
    # New (signup, Feb): +500 (CUST-5)
    # Expansion (Feb): +50 (CUST-2)
    # Contraction (Feb): -50 (CUST-4)
    # Churn (Mar): -300 (CUST-3)
    # Ending MRR (Mar): 100+250+0+350+500 = 1200
    result = mrr_waterfall(tiny_subs, tiny_events, "2024-01-01", "2024-03-01")
    assert result["starting"] == pytest.approx(1000.0)
    assert result["new"] == pytest.approx(500.0)
    assert result["expansion"] == pytest.approx(50.0)
    assert result["contraction"] == pytest.approx(-50.0)
    assert result["churn"] == pytest.approx(-300.0)
    assert result["ending"] == pytest.approx(1200.0)
    # Waterfall identity must hold (within float precision)
    walk = result["starting"] + result["new"] + result["expansion"] + result["contraction"] + result["churn"]
    assert walk == pytest.approx(result["ending"])
