"""Pipeline metric calculations for opportunity-level analytics.

All functions are pure: they take pandas DataFrames matching the schema of
`data/generated/opportunities.csv` and `opportunity_stage_history.csv`, and
return scalars or aggregated DataFrames.

Schema reminder:
    opportunities: opportunity_id, customer_id, account_name, segment,
                   acquisition_channel, owner_rep_id, opportunity_type,
                   created_date, close_date, amount, current_stage, status
        - status in {open, closed_won, closed_lost}
        - opportunity_type in {new_business, renewal, expansion}

    opportunity_stage_history: opportunity_id, stage, entered_date,
                               exited_date (NULL if currently in stage),
                               days_in_stage

The caller pre-filters opps by opp_type / segment / channel before calling
these functions — the API is intentionally stateless and minimal.
"""
from __future__ import annotations

import pandas as pd

# Stage win probabilities used for weighted pipeline. Mirrors the
# definitions in the Phase 2 design spec §5.2.
STAGE_PROBABILITY: dict[str, float] = {
    # new_business stages
    "Discovery": 0.10,
    "Qualification": 0.20,
    "Proof of Concept": 0.40,
    "Negotiation": 0.65,
    # renewal stages
    "Renewal Discussion": 0.75,
    # NOTE: renewal "Negotiation" uses 0.90 — but we share the key
    # "Negotiation" with new_business (0.65). The renewal case is rare in
    # the generated dataset; the design accepts the simplification of using
    # 0.65 for all Negotiation-named stages. Weighted pipeline is computed
    # primarily on new_business deals in practice.
    "Expansion Discussion": 0.80,
    # closed stages contribute 0 to weighted pipeline
    "Closed Won": 0.0,
    "Closed Lost": 0.0,
}


def total_pipeline(opps: pd.DataFrame, as_of_date: str) -> float:
    """Sum of `amount` for open opps created on or before `as_of_date`.

    Formula: sum(amount where status='open' and created_date <= as_of_date)
    """
    open_opps = opps[
        (opps["status"] == "open")
        & (opps["created_date"] <= as_of_date)
    ]
    return float(open_opps["amount"].sum())


def weighted_pipeline(opps: pd.DataFrame, as_of_date: str) -> float:
    """Weighted-pipeline sum: each open deal's amount × its stage probability.

    Formula: sum(amount × STAGE_PROBABILITY[current_stage]
                 where status='open' and created_date <= as_of_date)
    """
    open_opps = opps[
        (opps["status"] == "open")
        & (opps["created_date"] <= as_of_date)
    ].copy()
    open_opps["weight"] = open_opps["current_stage"].map(STAGE_PROBABILITY).fillna(0.0)
    return float((open_opps["amount"] * open_opps["weight"]).sum())
