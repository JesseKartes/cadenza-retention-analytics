"""Core SaaS retention metric calculations.

All functions are pure: they take pandas DataFrames matching the schema
of the generated CSVs and return scalars or aggregated DataFrames.

Schema reminder:
    subscriptions: customer_id, month, mrr, seats, plan_tier, status
        - one row per customer per month they are active
        - churned customers are simply absent from later months
    events: customer_id, event_date, event_type, mrr_delta, reason
        - event_type in {signup, upgrade, downgrade, churn, renewal}
"""
from __future__ import annotations

import pandas as pd


def _active(subs: pd.DataFrame, month: str) -> pd.DataFrame:
    """Active subscriptions in a given month (status == 'active')."""
    return subs[(subs["month"] == month) & (subs["status"] == "active")]


def arr(subs: pd.DataFrame, month: str) -> float:
    """Annual Recurring Revenue at a point in time.

    ARR = sum(active customers' MRR) * 12
    """
    return float(_active(subs, month)["mrr"].sum()) * 12.0


def logo_churn(subs: pd.DataFrame, start_month: str, end_month: str) -> float:
    """Logo (customer-count) churn from start_month to end_month.

    = (customers active at start_month but NOT at end_month) / (customers active at start_month)
    """
    start_ids = set(_active(subs, start_month)["customer_id"])
    end_ids = set(_active(subs, end_month)["customer_id"])
    if not start_ids:
        return 0.0
    churned = start_ids - end_ids
    return len(churned) / len(start_ids)
