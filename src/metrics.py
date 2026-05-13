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


def nrr(subs: pd.DataFrame, start_month: str, end_month: str) -> float:
    """Net Revenue Retention from start_month to end_month.

    Cohort = customers active at start_month.
    NRR = (cohort's MRR at end_month) / (cohort's MRR at start_month)

    Customers who churned between start and end are absent from end_month
    in the subscriptions table, so they contribute 0 to the numerator.
    NRR can exceed 100% because expansion is included.
    """
    start_df = _active(subs, start_month).set_index("customer_id")["mrr"]
    if start_df.sum() == 0:
        return 1.0
    end_df = _active(subs, end_month).set_index("customer_id")["mrr"]
    end_aligned = end_df.reindex(start_df.index, fill_value=0.0)
    return float(end_aligned.sum() / start_df.sum())


def grr(subs: pd.DataFrame, start_month: str, end_month: str) -> float:
    """Gross Revenue Retention from start_month to end_month.

    Same cohort as NRR, but each customer's end-period MRR is capped at
    their start-period MRR (expansion stripped). Cannot exceed 100%.
    """
    start_df = _active(subs, start_month).set_index("customer_id")["mrr"]
    if start_df.sum() == 0:
        return 1.0
    end_df = _active(subs, end_month).set_index("customer_id")["mrr"]
    end_aligned = end_df.reindex(start_df.index, fill_value=0.0)
    capped = pd.concat([end_aligned, start_df], axis=1).min(axis=1)
    return float(capped.sum() / start_df.sum())


def gross_revenue_churn(subs: pd.DataFrame, start_month: str, end_month: str) -> float:
    """Gross Revenue Churn = 1 - GRR."""
    return 1.0 - grr(subs, start_month, end_month)
