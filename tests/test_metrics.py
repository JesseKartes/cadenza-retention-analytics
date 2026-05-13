"""Metric correctness tests, computed against hand-built fixtures with
known answers (see conftest.py).
"""
from __future__ import annotations

import pytest

from src.metrics import arr, logo_churn


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


def test_logo_churn_when_nobody_churns(tiny_subs):
    # Feb -> Mar: cohort = active in Feb = {1,2,3,4,5}. Active in Mar = {1,2,4,5}. Churned = 1 (CUST-3) -> 1/5 = 0.20
    assert logo_churn(tiny_subs, "2024-02-01", "2024-03-01") == pytest.approx(0.20)
