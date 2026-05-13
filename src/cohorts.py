"""Cohort retention matrix construction.

Given the customers + subscriptions tables, build a matrix indexed by
signup cohort (YYYY-MM) with columns = months-since-signup and values =
the share of the cohort that's still active that many months later.
"""
from __future__ import annotations

import pandas as pd


def logo_retention_matrix(
    subs: pd.DataFrame,
    customers: pd.DataFrame,
    max_months_since_signup: int = 24,
) -> pd.DataFrame:
    """Build a logo (customer-count) retention cohort matrix.

    Rows: signup_cohort (YYYY-MM string).
    Cols: months since signup (int 0..max_months_since_signup).
    Cells: share of cohort still active at that month-of-life.
    """
    cohort_sizes = customers.groupby("signup_cohort").size()

    active = subs[subs["status"] == "active"].merge(
        customers[["customer_id", "signup_cohort"]],
        on="customer_id",
    )
    active["signup_period"] = pd.PeriodIndex(active["signup_cohort"], freq="M")
    active["active_period"] = pd.to_datetime(active["month"]).dt.to_period("M")
    active["months_since_signup"] = (
        active["active_period"].astype(int) - active["signup_period"].astype(int)
    )
    active = active[active["months_since_signup"].between(0, max_months_since_signup)]

    counts = (
        active.groupby(["signup_cohort", "months_since_signup"])["customer_id"]
        .nunique()
        .unstack(fill_value=0)
    )
    retention = counts.div(cohort_sizes, axis=0).dropna(how="all")
    return retention
