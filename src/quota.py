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


def attainment_distribution(opps: pd.DataFrame, reps: pd.DataFrame,
                              quarter: pd.Period) -> pd.DataFrame:
    """Per-rep attainment for the quarter, sorted descending. Powers §1 of the page.

    Returns the same columns as `quarterly_attainment`, sorted by attainment_pct desc.
    """
    return quarterly_attainment(opps, reps, quarter).sort_values(
        "attainment_pct", ascending=False
    ).reset_index(drop=True)


def ramp_curve(opps: pd.DataFrame, reps: pd.DataFrame) -> pd.DataFrame:
    """Per-rep rolling-3-month attainment indexed by tenure-months-since-hire.

    For each rep and each calendar month from their `hire_date` through the latest
    close_date in the data, computes:
      - `tenure_months` = (month - hire_date).days / 30.44
      - `closed_amount_3mo` = sum of closed-won new-business amounts for that rep
        in the trailing 3-month window ending in this month
      - `attainment_pct` = closed_amount_3mo / quarterly_quota

    Months before a rep's hire_date are not emitted. Months after hire with zero
    closes get attainment_pct = 0.0 (not NaN) so the longitudinal chart has no gaps.

    Returns long-form DataFrame: rep_id, month, tenure_months, attainment_pct.
    """
    closed_won = opps[
        (opps["status"] == "closed_won")
        & (opps["opportunity_type"] == "new_business")
    ].copy()
    closed_won["close_date"] = pd.to_datetime(closed_won["close_date"])
    closed_won["close_month"] = closed_won["close_date"].values.astype("datetime64[M]")

    reps = reps.copy()
    reps["hire_date"] = pd.to_datetime(reps["hire_date"])

    if len(closed_won) == 0:
        return pd.DataFrame(columns=["rep_id", "month", "tenure_months", "attainment_pct"])

    data_max_month = pd.Timestamp(closed_won["close_month"].max())

    rows = []
    for _, rep in reps.iterrows():
        start = pd.Timestamp(rep["hire_date"]).to_period("M").to_timestamp()
        # Walk one month at a time
        months = pd.date_range(start=start, end=data_max_month, freq="MS")
        rep_closes = closed_won[closed_won["owner_rep_id"] == rep["rep_id"]]
        # Monthly closed-won totals
        monthly = (
            rep_closes.groupby("close_month")["amount"]
            .sum()
            .reindex(months, fill_value=0.0)
        )
        rolling_3mo = monthly.rolling(window=3, min_periods=1).sum()
        for m, amt_3mo in rolling_3mo.items():
            tenure = (m - rep["hire_date"]).days / 30.44
            if tenure < 0:
                continue
            rows.append({
                "rep_id": rep["rep_id"],
                "month": m,
                "tenure_months": tenure,
                "attainment_pct": float(amt_3mo) / float(rep["quarterly_quota"]),
            })
    return pd.DataFrame(rows)


RAMP_BUCKETS = [
    ("0-3 mo",  0.0,  3.0),
    ("3-6 mo",  3.0,  6.0),
    ("6-12 mo", 6.0, 12.0),
    ("12+ mo", 12.0, float("inf")),
]


def ramp_bucket_attainment(opps: pd.DataFrame, reps: pd.DataFrame) -> pd.DataFrame:
    """Median attainment_pct across all (rep × month) observations, bucketed by tenure.

    Buckets: 0-3, 3-6, 6-12, 12+ months. Median is across all rep-months that fall
    into each bucket — so a rep contributes multiple data points as their tenure grows.

    Returns DataFrame with: tenure_bucket, n_observations, median_attainment.
    median_attainment is NaN if a bucket has no observations.
    """
    curve = ramp_curve(opps, reps)
    out = []
    for label, lo, hi in RAMP_BUCKETS:
        mask = (curve["tenure_months"] >= lo) & (curve["tenure_months"] < hi)
        in_bucket = curve.loc[mask, "attainment_pct"]
        out.append({
            "tenure_bucket": label,
            "n_observations": int(in_bucket.shape[0]),
            "median_attainment": float(in_bucket.median()) if len(in_bucket) else float("nan"),
        })
    return pd.DataFrame(out)


def rep_scorecard(opps: pd.DataFrame, reps: pd.DataFrame,
                    quarter: pd.Period) -> pd.DataFrame:
    """One row per rep with attainment, win rate, deal size, cycle time for the quarter.

    Reuses `quarterly_attainment` for closed_amount / attainment_pct / status.
    Additional columns:
      win_rate     = closed_won_count / (closed_won_count + closed_lost_count) for
                     new-business deals with close_date in quarter, per rep
      avg_deal_size = mean amount of rep's closed-won deals in quarter
      avg_cycle_days = mean (close_date - created_date).days across rep's
                       closed-won deals in quarter
      tenure_months = (quarter_end - hire_date).days / 30.44

    Returns DataFrame ordered by attainment_pct desc.
    """
    attainment = quarterly_attainment(opps, reps, quarter)

    quarter_end = pd.Period(quarter).to_timestamp(how="end").normalize()
    reps = reps.copy()
    reps["hire_date"] = pd.to_datetime(reps["hire_date"])
    reps["tenure_months"] = (quarter_end - reps["hire_date"]).dt.days / 30.44

    nb = opps[opps["opportunity_type"] == "new_business"].copy()
    nb["close_date"] = pd.to_datetime(nb["close_date"])
    nb["created_date"] = pd.to_datetime(nb["created_date"])
    in_q = nb[nb["close_date"].dt.to_period("Q") == quarter]

    closed_won_q = in_q[in_q["status"] == "closed_won"]
    closed_lost_q = in_q[in_q["status"] == "closed_lost"]

    won_per_rep = closed_won_q.groupby("owner_rep_id").size()
    lost_per_rep = closed_lost_q.groupby("owner_rep_id").size()
    avg_size_per_rep = closed_won_q.groupby("owner_rep_id")["amount"].mean()

    closed_won_q = closed_won_q.assign(
        cycle_days=(closed_won_q["close_date"] - closed_won_q["created_date"]).dt.days
    )
    avg_cycle_per_rep = closed_won_q.groupby("owner_rep_id")["cycle_days"].mean()

    extras = pd.DataFrame({
        "won_count": won_per_rep,
        "lost_count": lost_per_rep,
        "avg_deal_size": avg_size_per_rep,
        "avg_cycle_days": avg_cycle_per_rep,
    }).fillna(0.0)
    extras["win_rate"] = extras["won_count"] / (extras["won_count"] + extras["lost_count"])
    extras = extras.reset_index().rename(columns={"owner_rep_id": "rep_id"})

    out = (
        reps[["rep_id", "name", "segment_specialty", "territory", "tenure_months",
              "quarterly_quota"]]
        .merge(
            attainment[["rep_id", "closed_amount", "attainment_pct", "status"]],
            on="rep_id", how="left",
        )
        .merge(
            extras[["rep_id", "win_rate", "avg_deal_size", "avg_cycle_days"]],
            on="rep_id", how="left",
        )
    )
    out = out.fillna({"win_rate": 0.0, "avg_deal_size": 0.0, "avg_cycle_days": 0.0})
    return out.sort_values("attainment_pct", ascending=False).reset_index(drop=True)


def territory_balance(opps: pd.DataFrame, reps: pd.DataFrame,
                       quarter: pd.Period) -> pd.DataFrame:
    """Closed-won new-business $ by territory × segment for the quarter.

    Powers the stacked horizontal bar in §3 of the Quota page. Each row's
    territory comes from the rep table (joined on owner_rep_id); segment
    comes from the opp.

    Returns DataFrame with: territory, segment, closed_amount.
    """
    closed_won = opps[
        (opps["status"] == "closed_won")
        & (opps["opportunity_type"] == "new_business")
    ].copy()
    closed_won["close_date"] = pd.to_datetime(closed_won["close_date"])
    in_q = closed_won[closed_won["close_date"].dt.to_period("Q") == quarter]

    merged = in_q.merge(
        reps[["rep_id", "territory"]],
        left_on="owner_rep_id", right_on="rep_id", how="left",
    )
    grouped = (
        merged.groupby(["territory", "segment"], as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "closed_amount"})
    )
    return grouped


def team_kpis(opps: pd.DataFrame, reps: pd.DataFrame, quarter: pd.Period) -> dict:
    """Returns the 4 KPI tile values for the Quota page header.

    - team_attainment_pct = sum(closed_won $) / sum(quarterly_quota) across all reps
    - reps_at_or_above    = count of reps with attainment >= 1.0
    - median_attainment   = median attainment_pct across all reps
    - at_risk_count       = count of reps with attainment < 0.7
    """
    att = quarterly_attainment(opps, reps, quarter)
    return {
        "team_attainment_pct": float(att["closed_amount"].sum() / att["quarterly_quota"].sum()),
        "reps_at_or_above": int((att["attainment_pct"] >= 1.0).sum()),
        "median_attainment": float(att["attainment_pct"].median()),
        "at_risk_count": int((att["attainment_pct"] < 0.7).sum()),
    }


def load_quota_data(reps_path: Path, opps_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """IO boundary for the Streamlit page. The only impure function in this module.

    Returns:
      (reps_df, opps_df) where opps_df is pre-filtered to new-business
      closed-won and closed-lost only (open opps don't count toward attainment).
    """
    reps_df = pd.read_csv(reps_path)
    opps_df = pd.read_csv(opps_path)
    opps_df = opps_df[
        (opps_df["opportunity_type"] == "new_business")
        & (opps_df["status"].isin(["closed_won", "closed_lost"]))
    ].reset_index(drop=True)
    return reps_df, opps_df
