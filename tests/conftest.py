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


@pytest.fixture
def tiny_opportunities() -> pd.DataFrame:
    """8 hand-crafted opps spanning 3 opp_types, all segments, win/loss outcomes.

    Hand-calculated answers (verified in tests):
      total_pipeline(as_of='2024-04-01')  = 300_000  (OPP-2 + OPP-3 + OPP-8)
      weighted_pipeline(as_of='2024-04-01') = 158_000
        = 0.40*60_000 + 0.65*200_000 + 0.10*40_000
      pipeline_coverage(target=100_000, as_of='2024-04-01') = 3.0
      win_rate(start='2024-01-01', end='2024-04-01')        = 0.60  (3 won / 5 closed)
      avg_sales_cycle_days(start='2024-01-01', end='2024-04-01') = 70
        = mean(90, 60, 60) for OPP-1, OPP-5, OPP-7

    Stage probabilities used:
      Discovery 0.10, Qualification 0.20, POC 0.40, Negotiation 0.65
      Renewal Discussion 0.75, Renewal Negotiation 0.90
      Expansion Discussion 0.80
    """
    rows = [
        # new_business — won
        {"opportunity_id": "OPP-1", "customer_id": "CUST-1", "account_name": "Apex Labs",
         "segment": "SMB", "acquisition_channel": "Outbound Sales", "owner_rep_id": "REP-01",
         "opportunity_type": "new_business",
         "created_date": "2024-01-01", "close_date": "2024-03-31", "amount": 12_000.0,
         "current_stage": "Closed Won", "status": "closed_won"},
        # new_business — open in POC (Mid-Market — part of the engineered stall)
        {"opportunity_id": "OPP-2", "customer_id": None, "account_name": "Quantum Works",
         "segment": "Mid-Market", "acquisition_channel": "Inbound Marketing", "owner_rep_id": "REP-02",
         "opportunity_type": "new_business",
         "created_date": "2024-02-01", "close_date": "2024-06-01", "amount": 60_000.0,
         "current_stage": "Proof of Concept", "status": "open"},
        # new_business — open in Negotiation
        {"opportunity_id": "OPP-3", "customer_id": None, "account_name": "Helix Systems",
         "segment": "Enterprise", "acquisition_channel": "Partner Referral", "owner_rep_id": "REP-03",
         "opportunity_type": "new_business",
         "created_date": "2024-01-15", "close_date": "2024-05-15", "amount": 200_000.0,
         "current_stage": "Negotiation", "status": "open"},
        # new_business — lost (died in POC)
        {"opportunity_id": "OPP-4", "customer_id": None, "account_name": "Vector Logic",
         "segment": "SMB", "acquisition_channel": "Outbound Sales", "owner_rep_id": "REP-01",
         "opportunity_type": "new_business",
         "created_date": "2024-01-01", "close_date": "2024-02-15", "amount": 8_000.0,
         "current_stage": "Closed Lost", "status": "closed_lost"},
        # renewal — won
        {"opportunity_id": "OPP-5", "customer_id": "CUST-100", "account_name": "Lattice Group",
         "segment": "Mid-Market", "acquisition_channel": "Inbound Marketing", "owner_rep_id": "REP-04",
         "opportunity_type": "renewal",
         "created_date": "2024-01-01", "close_date": "2024-03-01", "amount": 30_000.0,
         "current_stage": "Closed Won", "status": "closed_won"},
        # renewal — lost
        {"opportunity_id": "OPP-6", "customer_id": "CUST-200", "account_name": "Beacon Dynamics",
         "segment": "SMB", "acquisition_channel": "Outbound Sales", "owner_rep_id": "REP-05",
         "opportunity_type": "renewal",
         "created_date": "2024-01-01", "close_date": "2024-02-20", "amount": 10_000.0,
         "current_stage": "Closed Lost", "status": "closed_lost"},
        # expansion — won
        {"opportunity_id": "OPP-7", "customer_id": "CUST-300", "account_name": "Stratus Cloud",
         "segment": "Enterprise", "acquisition_channel": "Partner Referral", "owner_rep_id": "REP-06",
         "opportunity_type": "expansion",
         "created_date": "2024-01-15", "close_date": "2024-03-15", "amount": 24_000.0,
         "current_stage": "Closed Won", "status": "closed_won"},
        # new_business — open in Discovery (Mid-Market)
        {"opportunity_id": "OPP-8", "customer_id": None, "account_name": "Cobalt Industries",
         "segment": "Mid-Market", "acquisition_channel": "Inbound Marketing", "owner_rep_id": "REP-02",
         "opportunity_type": "new_business",
         "created_date": "2024-02-15", "close_date": "2024-08-15", "amount": 40_000.0,
         "current_stage": "Discovery", "status": "open"},
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def tiny_stage_history() -> pd.DataFrame:
    """Stage transitions for the new_business deals in tiny_opportunities.

    Hand-calculated answers (verified in tests):
      avg_days_in_stage('Proof of Concept', '2024-01-01', '2024-04-01) = 20.0
        = mean(14, 25, 21) for OPP-1, OPP-3, OPP-4
      avg_days_in_stage('Negotiation', '2024-01-01', '2024-04-01)      = 59.0
        = OPP-1 only (entered+exited Negotiation in window)
      stage_conversion('Proof of Concept', 'Negotiation',
                       '2024-01-01', '2024-04-01)                       ≈ 0.667
        = of {OPP-1, OPP-3, OPP-4} that exited POC,
          {OPP-1, OPP-3} reached Negotiation -> 2/3
      aging_deals(as_of='2024-04-01', threshold=30) returns {OPP-2, OPP-8}
        OPP-2: 46 days in POC
        OPP-3: 17 days in Negotiation (not aging)
        OPP-8: 46 days in Discovery
    """
    rows = [
        # OPP-1 walked all 4 NB stages, won
        {"opportunity_id": "OPP-1", "stage": "Discovery",        "entered_date": "2024-01-01", "exited_date": "2024-01-08", "days_in_stage": 7},
        {"opportunity_id": "OPP-1", "stage": "Qualification",    "entered_date": "2024-01-08", "exited_date": "2024-01-18", "days_in_stage": 10},
        {"opportunity_id": "OPP-1", "stage": "Proof of Concept", "entered_date": "2024-01-18", "exited_date": "2024-02-01", "days_in_stage": 14},
        {"opportunity_id": "OPP-1", "stage": "Negotiation",      "entered_date": "2024-02-01", "exited_date": "2024-03-31", "days_in_stage": 59},
        # OPP-2 — open, currently in POC
        {"opportunity_id": "OPP-2", "stage": "Discovery",        "entered_date": "2024-02-01", "exited_date": "2024-02-08", "days_in_stage": 7},
        {"opportunity_id": "OPP-2", "stage": "Qualification",    "entered_date": "2024-02-08", "exited_date": "2024-02-15", "days_in_stage": 7},
        {"opportunity_id": "OPP-2", "stage": "Proof of Concept", "entered_date": "2024-02-15", "exited_date": None,         "days_in_stage": None},
        # OPP-3 — open, walked through POC, currently in Negotiation
        {"opportunity_id": "OPP-3", "stage": "Discovery",        "entered_date": "2024-01-15", "exited_date": "2024-01-29", "days_in_stage": 14},
        {"opportunity_id": "OPP-3", "stage": "Qualification",    "entered_date": "2024-01-29", "exited_date": "2024-02-18", "days_in_stage": 20},
        {"opportunity_id": "OPP-3", "stage": "Proof of Concept", "entered_date": "2024-02-18", "exited_date": "2024-03-15", "days_in_stage": 25},
        {"opportunity_id": "OPP-3", "stage": "Negotiation",      "entered_date": "2024-03-15", "exited_date": None,         "days_in_stage": None},
        # OPP-4 — lost in POC
        {"opportunity_id": "OPP-4", "stage": "Discovery",        "entered_date": "2024-01-01", "exited_date": "2024-01-15", "days_in_stage": 14},
        {"opportunity_id": "OPP-4", "stage": "Qualification",    "entered_date": "2024-01-15", "exited_date": "2024-01-25", "days_in_stage": 10},
        {"opportunity_id": "OPP-4", "stage": "Proof of Concept", "entered_date": "2024-01-25", "exited_date": "2024-02-15", "days_in_stage": 21},
        # OPP-8 — open, in Discovery
        {"opportunity_id": "OPP-8", "stage": "Discovery",        "entered_date": "2024-02-15", "exited_date": None,         "days_in_stage": None},
    ]
    return pd.DataFrame(rows)
