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
    Cells: share of cohort still active at that month-of-life. NaN for cells
    that represent calendar months past the latest month in `subs` — the
    cohort literally hasn't reached that age yet.
    """
    max_period_ord = pd.to_datetime(subs["month"]).max().to_period("M").ordinal

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
    retention = counts.div(cohort_sizes, axis=0)
    retention = _mask_future_months(retention, max_period_ord)
    return retention.dropna(how="all")


def revenue_retention_matrix(
    subs: pd.DataFrame,
    customers: pd.DataFrame,
    max_months_since_signup: int = 24,
) -> pd.DataFrame:
    """Build a revenue (MRR-weighted) retention cohort matrix.

    Numerator: sum of cohort's MRR at month-of-life N.
    Denominator: sum of cohort's MRR at signup (M0).

    Can exceed 100% if expansion outpaces churn within the cohort.
    Cells representing calendar months past the latest month in `subs` are
    NaN — the cohort literally hasn't reached that age yet.
    """
    max_period_ord = pd.to_datetime(subs["month"]).max().to_period("M").ordinal

    subs = subs.copy()
    subs["active_period"] = pd.to_datetime(subs["month"]).dt.to_period("M")
    subs = subs[subs["status"] == "active"].merge(
        customers[["customer_id", "signup_cohort"]],
        on="customer_id",
    )
    subs["signup_period"] = pd.PeriodIndex(subs["signup_cohort"], freq="M")
    subs["months_since_signup"] = (
        subs["active_period"].astype(int) - subs["signup_period"].astype(int)
    )
    subs = subs[subs["months_since_signup"].between(0, max_months_since_signup)]

    mrr_by_cohort_age = (
        subs.groupby(["signup_cohort", "months_since_signup"])["mrr"].sum().unstack(fill_value=0.0)
    )
    starting_mrr = mrr_by_cohort_age[0].replace(0, pd.NA)
    retention = mrr_by_cohort_age.div(starting_mrr, axis=0)
    retention = _mask_future_months(retention, max_period_ord)
    return retention.dropna(how="all")


def _mask_future_months(retention: pd.DataFrame, max_period_ord: int) -> pd.DataFrame:
    """Set cells to NaN where cohort + months_since_signup > the dataset's latest month.

    Distinguishes 'cohort hasn't aged this far yet' (NaN, blank in heatmap) from
    'cohort reached this age but had 0% retention' (0.0, painted red).
    """
    cohort_ords = [pd.Period(c, freq="M").ordinal for c in retention.index]
    cohort_ords_arr = pd.Series(cohort_ords).to_numpy()
    months_arr = retention.columns.to_numpy()
    allowed = cohort_ords_arr[:, None] + months_arr[None, :] <= max_period_ord
    return retention.where(allowed)
