from __future__ import annotations

import pandas as pd
import pytest

from src.cohorts import logo_retention_matrix, revenue_retention_matrix


def test_logo_retention_basic(tiny_subs, tiny_customers):
    """The Jan 2024 cohort has 4 customers (1,2,3,4). At M0=Jan all 4 are active.
    At M1=Feb all 4 are still active. At M2=Mar CUST-3 has churned, so 3/4.
    The Feb 2024 cohort has 1 customer (CUST-5). At M0=Feb retained = 1.
    At M1=Mar still active = 1.
    """
    matrix = logo_retention_matrix(tiny_subs, tiny_customers)
    assert matrix.loc["2024-01", 0] == pytest.approx(1.0)
    assert matrix.loc["2024-01", 1] == pytest.approx(1.0)
    assert matrix.loc["2024-01", 2] == pytest.approx(0.75)
    assert matrix.loc["2024-02", 0] == pytest.approx(1.0)
    assert matrix.loc["2024-02", 1] == pytest.approx(1.0)


def test_logo_retention_handles_empty_cohort(tiny_subs, tiny_customers):
    """Cohorts with no customers should not appear in the result."""
    matrix = logo_retention_matrix(tiny_subs, tiny_customers)
    assert "2023-12" not in matrix.index


def test_revenue_retention_basic(tiny_subs, tiny_customers):
    """Jan 2024 cohort starting MRR = 100+200+300+400 = 1000.
    At M1 (Feb), same cohort MRR = 100+250+300+350 = 1000  -> 100%
    At M2 (Mar), same cohort MRR = 100+250+0+350 = 700  -> 70%
    """
    matrix = revenue_retention_matrix(tiny_subs, tiny_customers)
    assert matrix.loc["2024-01", 0] == pytest.approx(1.0)
    assert matrix.loc["2024-01", 1] == pytest.approx(1.0)
    assert matrix.loc["2024-01", 2] == pytest.approx(0.70)
