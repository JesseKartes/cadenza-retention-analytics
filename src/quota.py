"""Cadenza Quota & Rep Performance — quarterly attainment, ramp, scorecard, territory.

Scope is new-business opportunities only. Renewal and expansion ACV does not
count toward attainment — matches how most SaaS orgs separate AE comp from
CSM/AM comp. See the About page's Scope & Deferrals section.

The third engineered insight surfaces here: the team's actual ramp curve hits
full productivity at ~9 months, not the industry-assumed 6.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def quarterly_attainment(opps: pd.DataFrame, reps: pd.DataFrame,
                          quarter: pd.Period) -> pd.DataFrame:
    """Per-rep closed-won total vs. quarterly quota for the given quarter.

    Numerator: sum of `amount` for closed-won new-business opps with
      `close_date` in `quarter`, grouped by `owner_rep_id`.
    Denominator: each rep's `quarterly_quota` from the reps table.
    Status:
      - 'At/Above' if attainment_pct >= 1.0
      - 'On Track' if 0.7 <= attainment_pct < 1.0
      - 'At Risk'  if attainment_pct < 0.7

    Returns DataFrame with columns:
      rep_id, name, quarterly_quota, closed_amount, attainment_pct, status.
    """
    closed_won = opps[
        (opps["status"] == "closed_won")
        & (opps["opportunity_type"] == "new_business")
    ].copy()
    closed_won["close_date"] = pd.to_datetime(closed_won["close_date"])
    in_quarter = closed_won[closed_won["close_date"].dt.to_period("Q") == quarter]

    per_rep = (
        in_quarter.groupby("owner_rep_id", as_index=False)["amount"]
        .sum()
        .rename(columns={"owner_rep_id": "rep_id", "amount": "closed_amount"})
    )

    merged = reps[["rep_id", "name", "quarterly_quota"]].merge(
        per_rep, on="rep_id", how="left"
    )
    merged["closed_amount"] = merged["closed_amount"].fillna(0.0)
    merged["attainment_pct"] = merged["closed_amount"] / merged["quarterly_quota"]
    merged["status"] = merged["attainment_pct"].apply(_attainment_status)
    return merged


def _attainment_status(pct: float) -> str:
    if pct >= 1.0:
        return "At/Above"
    if pct >= 0.7:
        return "On Track"
    return "At Risk"
