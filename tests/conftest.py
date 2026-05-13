"""Hand-built fixtures with known metric answers. These are the contract:
if the metric calculations stop matching these expected values, the math
is wrong, not the fixture.
"""
from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def tiny_subs() -> pd.DataFrame:
    """5 customers across 3 months (2024-01, 2024-02, 2024-03).

    Lifecycle:
      CUST-1: $100 -> $100 -> $100  (flat)
      CUST-2: $200 -> $250 -> $250  (expansion in Feb)
      CUST-3: $300 -> $300 -> churn (churn in Mar)
      CUST-4: $400 -> $350 -> $350  (contraction in Feb)
      CUST-5:  n/a -> $500 -> $500  (new in Feb)
    """
    rows = [
        {"customer_id": "CUST-1", "month": "2024-01-01", "mrr": 100.0, "seats": 1, "plan_tier": "Starter", "status": "active"},
        {"customer_id": "CUST-1", "month": "2024-02-01", "mrr": 100.0, "seats": 1, "plan_tier": "Starter", "status": "active"},
        {"customer_id": "CUST-1", "month": "2024-03-01", "mrr": 100.0, "seats": 1, "plan_tier": "Starter", "status": "active"},

        {"customer_id": "CUST-2", "month": "2024-01-01", "mrr": 200.0, "seats": 2, "plan_tier": "Growth", "status": "active"},
        {"customer_id": "CUST-2", "month": "2024-02-01", "mrr": 250.0, "seats": 2, "plan_tier": "Growth", "status": "active"},
        {"customer_id": "CUST-2", "month": "2024-03-01", "mrr": 250.0, "seats": 2, "plan_tier": "Growth", "status": "active"},

        {"customer_id": "CUST-3", "month": "2024-01-01", "mrr": 300.0, "seats": 3, "plan_tier": "Growth", "status": "active"},
        {"customer_id": "CUST-3", "month": "2024-02-01", "mrr": 300.0, "seats": 3, "plan_tier": "Growth", "status": "active"},
        # CUST-3 churns in March -> absent from 2024-03-01

        {"customer_id": "CUST-4", "month": "2024-01-01", "mrr": 400.0, "seats": 4, "plan_tier": "Growth", "status": "active"},
        {"customer_id": "CUST-4", "month": "2024-02-01", "mrr": 350.0, "seats": 4, "plan_tier": "Growth", "status": "active"},
        {"customer_id": "CUST-4", "month": "2024-03-01", "mrr": 350.0, "seats": 4, "plan_tier": "Growth", "status": "active"},

        {"customer_id": "CUST-5", "month": "2024-02-01", "mrr": 500.0, "seats": 5, "plan_tier": "Scale", "status": "active"},
        {"customer_id": "CUST-5", "month": "2024-03-01", "mrr": 500.0, "seats": 5, "plan_tier": "Scale", "status": "active"},
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def tiny_events() -> pd.DataFrame:
    rows = [
        {"customer_id": "CUST-1", "event_date": "2024-01-15", "event_type": "signup", "mrr_delta": 100.0, "reason": "new"},
        {"customer_id": "CUST-2", "event_date": "2024-01-15", "event_type": "signup", "mrr_delta": 200.0, "reason": "new"},
        {"customer_id": "CUST-2", "event_date": "2024-02-15", "event_type": "upgrade", "mrr_delta": 50.0, "reason": "expansion"},
        {"customer_id": "CUST-3", "event_date": "2024-01-15", "event_type": "signup", "mrr_delta": 300.0, "reason": "new"},
        {"customer_id": "CUST-3", "event_date": "2024-03-15", "event_type": "churn", "mrr_delta": -300.0, "reason": "cancel"},
        {"customer_id": "CUST-4", "event_date": "2024-01-15", "event_type": "signup", "mrr_delta": 400.0, "reason": "new"},
        {"customer_id": "CUST-4", "event_date": "2024-02-15", "event_type": "downgrade", "mrr_delta": -50.0, "reason": "contraction"},
        {"customer_id": "CUST-5", "event_date": "2024-02-15", "event_type": "signup", "mrr_delta": 500.0, "reason": "new"},
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def tiny_customers() -> pd.DataFrame:
    rows = [
        {"customer_id": "CUST-1", "segment": "SMB", "acquisition_channel": "Outbound Sales", "signup_cohort": "2024-01", "signup_date": "2024-01-15"},
        {"customer_id": "CUST-2", "segment": "Mid-Market", "acquisition_channel": "Inbound Marketing", "signup_cohort": "2024-01", "signup_date": "2024-01-15"},
        {"customer_id": "CUST-3", "segment": "Mid-Market", "acquisition_channel": "Outbound Sales", "signup_cohort": "2024-01", "signup_date": "2024-01-15"},
        {"customer_id": "CUST-4", "segment": "Enterprise", "acquisition_channel": "Partner Referral", "signup_cohort": "2024-01", "signup_date": "2024-01-15"},
        {"customer_id": "CUST-5", "segment": "Enterprise", "acquisition_channel": "Self-Serve Promo", "signup_cohort": "2024-02", "signup_date": "2024-02-15"},
    ]
    return pd.DataFrame(rows)
