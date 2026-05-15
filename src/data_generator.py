"""Synthetic data generator for Cadenza, a fictional B2B sales engagement SaaS.

Produces three CSVs covering 36 months: customers.csv, subscriptions.csv, events.csv.

The generator deliberately encodes a hidden insight: customers acquired through
the 'Self-Serve Promo' channel during Q3 2024 churn at ~2x the rate of other
channels. Headline NRR/GRR still appear healthy; the cohort heatmap and channel
breakdown in the dashboard expose the pattern.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# --- Configuration ---------------------------------------------------------

START_MONTH = pd.Timestamp("2023-01-01")
END_MONTH = pd.Timestamp("2025-12-01")
RNG_SEED = 42

SEGMENTS = ["SMB", "Mid-Market", "Enterprise"]
SEGMENT_WEIGHTS = [0.70, 0.25, 0.05]

CHANNELS = [
    "Outbound Sales",
    "Inbound Marketing",
    "Partner Referral",
    "Self-Serve Promo",
    "Event/Conference",
]
CHANNEL_WEIGHTS_BASELINE = [0.30, 0.30, 0.10, 0.10, 0.20]

PLAN_TIERS = {"Starter": 50.0, "Growth": 120.0, "Scale": 250.0}
PLAN_WEIGHTS_BY_SEGMENT = {
    "SMB": {"Starter": 0.70, "Growth": 0.28, "Scale": 0.02},
    "Mid-Market": {"Starter": 0.20, "Growth": 0.65, "Scale": 0.15},
    "Enterprise": {"Starter": 0.05, "Growth": 0.35, "Scale": 0.60},
}

SEAT_RANGE_BY_SEGMENT = {
    "SMB": (3, 15),
    "Mid-Market": (15, 75),
    "Enterprise": (75, 400),
}

INDUSTRIES = [
    "Technology", "Financial Services", "Healthcare", "Manufacturing",
    "Retail", "Media", "Education", "Professional Services",
]

# Baseline new-customer acquisitions per month, plus seasonality
BASELINE_NEW_PER_MONTH = 20

# Engineered insight: Q3 2024 self-serve-promo bump
PROMO_MONTHS = [pd.Timestamp("2024-07-01"), pd.Timestamp("2024-08-01"), pd.Timestamp("2024-09-01")]
PROMO_EXTRA_PER_MONTH = 20  # ~60 extra customers, all tagged Self-Serve Promo

# Lifecycle probability params (monthly)
BASE_CHURN_PROB_BY_CHANNEL = {
    "Outbound Sales": 0.010,
    "Inbound Marketing": 0.012,
    "Partner Referral": 0.008,
    "Self-Serve Promo": 0.030,   # the engineered bad cohort
    "Event/Conference": 0.015,
}
SEGMENT_CHURN_MULT = {"SMB": 1.3, "Mid-Market": 1.0, "Enterprise": 0.4}

EXPANSION_PROB_BY_SEGMENT = {"SMB": 0.030, "Mid-Market": 0.050, "Enterprise": 0.080}
CONTRACTION_PROB_BY_SEGMENT = {"SMB": 0.010, "Mid-Market": 0.008, "Enterprise": 0.005}

EXPANSION_SEAT_GROWTH_RANGE = (0.05, 0.25)
CONTRACTION_SEAT_LOSS_RANGE = (0.05, 0.20)


@dataclass
class GeneratorConfig:
    start: pd.Timestamp = START_MONTH
    end: pd.Timestamp = END_MONTH
    baseline_new_per_month: int = BASELINE_NEW_PER_MONTH
    rng_seed: int = RNG_SEED


# --- Customer-table generation --------------------------------------------

def _months_between(start: pd.Timestamp, end: pd.Timestamp) -> list[pd.Timestamp]:
    return list(pd.date_range(start=start, end=end, freq="MS"))


def _seasonality_multiplier(month: pd.Timestamp) -> float:
    """Slight Q4 bump, Q1 dip in new acquisitions."""
    m = month.month
    if m in (10, 11):
        return 1.15
    if m in (1, 2):
        return 0.90
    return 1.0


def generate_customers(cfg: GeneratorConfig) -> pd.DataFrame:
    """Generate the customers table.

    Returns a DataFrame with columns:
        customer_id, company_name, segment, industry, signup_date, signup_cohort,
        acquisition_channel, plan_tier_initial, initial_seats, initial_mrr
    """
    rng = np.random.default_rng(cfg.rng_seed)
    months = _months_between(cfg.start, cfg.end)
    rows = []
    next_id = 1001

    for month in months:
        # Baseline acquisitions
        n = int(round(cfg.baseline_new_per_month * _seasonality_multiplier(month)))
        for _ in range(n):
            row = _make_customer_row(rng, next_id, month, promo=False)
            rows.append(row)
            next_id += 1

        # Promo cohort: extra Self-Serve Promo signups in Q3 2024
        if month in PROMO_MONTHS:
            for _ in range(PROMO_EXTRA_PER_MONTH):
                row = _make_customer_row(rng, next_id, month, promo=True)
                rows.append(row)
                next_id += 1

    return pd.DataFrame(rows)


def _make_customer_row(rng: np.random.Generator, cust_id: int,
                       signup_month: pd.Timestamp, promo: bool) -> dict:
    segment = rng.choice(SEGMENTS, p=SEGMENT_WEIGHTS)
    if promo:
        channel = "Self-Serve Promo"
        # Promo cohort skews SMB
        segment = rng.choice(SEGMENTS, p=[0.85, 0.13, 0.02])
    else:
        channel = rng.choice(CHANNELS, p=CHANNEL_WEIGHTS_BASELINE)

    plan_weights = PLAN_WEIGHTS_BY_SEGMENT[segment]
    plan = rng.choice(list(plan_weights.keys()), p=list(plan_weights.values()))
    seat_lo, seat_hi = SEAT_RANGE_BY_SEGMENT[segment]
    seats = int(rng.integers(seat_lo, seat_hi + 1))

    # Signup day within the month
    day = int(rng.integers(1, 28))
    signup_date = signup_month + pd.Timedelta(days=day - 1)

    mrr = seats * PLAN_TIERS[plan]

    return {
        "customer_id": f"CUST-{cust_id}",
        "company_name": _fake_company_name(rng),
        "segment": segment,
        "industry": rng.choice(INDUSTRIES),
        "signup_date": signup_date.strftime("%Y-%m-%d"),
        "signup_cohort": signup_month.strftime("%Y-%m"),
        "acquisition_channel": channel,
        "plan_tier_initial": plan,
        "initial_seats": seats,
        "initial_mrr": mrr,
    }


_NAME_PREFIXES = ["North", "Apex", "Quantum", "Helix", "Vector", "Lattice",
                  "Beacon", "Stratus", "Cobalt", "Citron", "Plinth", "Marlin",
                  "Tessera", "Halcyon", "Mosaic", "Glide", "Anvil", "Reverb"]
_NAME_SUFFIXES = ["Labs", "Works", "Systems", "Logic", "Group", "Dynamics",
                  "Holdings", "Partners", "Co", "Industries", "Solutions",
                  "Network", "Cloud", "Digital"]


def _fake_company_name(rng: np.random.Generator) -> str:
    return f"{rng.choice(_NAME_PREFIXES)} {rng.choice(_NAME_SUFFIXES)}"


# --- Subscription & event simulation ---------------------------------------

def generate_subscriptions_and_events(
    customers: pd.DataFrame, cfg: GeneratorConfig
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Simulate month-by-month subscription state and lifecycle events.

    Returns (subscriptions_df, events_df).
    """
    rng = np.random.default_rng(cfg.rng_seed + 1)
    months = _months_between(cfg.start, cfg.end)

    customers = customers.copy()
    customers["signup_date_dt"] = pd.to_datetime(customers["signup_date"])

    # Active state per customer: dict[customer_id] -> {seats, plan_tier, mrr, churned}
    state: dict[str, dict] = {}

    sub_rows = []
    event_rows = []

    for month in months:
        # Activate customers whose signup_date is in this month
        new_this_month = customers[
            (customers["signup_date_dt"] >= month)
            & (customers["signup_date_dt"] < month + pd.offsets.MonthBegin(1))
        ]
        activated_this_month: set[str] = set()
        for _, c in new_this_month.iterrows():
            state[c["customer_id"]] = {
                "seats": int(c["initial_seats"]),
                "plan_tier": c["plan_tier_initial"],
                "mrr": float(c["initial_mrr"]),
                "churned": False,
                "segment": c["segment"],
                "channel": c["acquisition_channel"],
            }
            activated_this_month.add(c["customer_id"])
            event_rows.append({
                "customer_id": c["customer_id"],
                "event_date": c["signup_date"],
                "event_type": "signup",
                "mrr_delta": float(c["initial_mrr"]),
                "reason": f"New {c['segment']} customer via {c['acquisition_channel']}",
            })

        # Walk active customers (excluding those that just signed up this month)
        # and decide their fate this month
        for cust_id, s in list(state.items()):
            if s["churned"] or cust_id in activated_this_month:
                continue

            # Churn check
            churn_p = (
                BASE_CHURN_PROB_BY_CHANNEL[s["channel"]]
                * SEGMENT_CHURN_MULT[s["segment"]]
                * _q1_churn_amplifier(month)
            )
            if rng.random() < churn_p:
                event_rows.append({
                    "customer_id": cust_id,
                    "event_date": _mid_month(month).strftime("%Y-%m-%d"),
                    "event_type": "churn",
                    "mrr_delta": -s["mrr"],
                    "reason": "Cancellation",
                })
                s["churned"] = True
                continue

            # Expansion check
            if rng.random() < EXPANSION_PROB_BY_SEGMENT[s["segment"]]:
                growth = rng.uniform(*EXPANSION_SEAT_GROWTH_RANGE)
                new_seats = max(s["seats"] + 1, int(round(s["seats"] * (1 + growth))))
                delta_mrr = (new_seats - s["seats"]) * PLAN_TIERS[s["plan_tier"]]
                event_rows.append({
                    "customer_id": cust_id,
                    "event_date": _mid_month(month).strftime("%Y-%m-%d"),
                    "event_type": "upgrade",
                    "mrr_delta": delta_mrr,
                    "reason": f"Seat expansion to {new_seats}",
                })
                s["seats"] = new_seats
                s["mrr"] = new_seats * PLAN_TIERS[s["plan_tier"]]

            # Contraction check (separate roll)
            elif rng.random() < CONTRACTION_PROB_BY_SEGMENT[s["segment"]]:
                loss = rng.uniform(*CONTRACTION_SEAT_LOSS_RANGE)
                new_seats = max(1, int(round(s["seats"] * (1 - loss))))
                delta_mrr = (new_seats - s["seats"]) * PLAN_TIERS[s["plan_tier"]]
                event_rows.append({
                    "customer_id": cust_id,
                    "event_date": _mid_month(month).strftime("%Y-%m-%d"),
                    "event_type": "downgrade",
                    "mrr_delta": delta_mrr,
                    "reason": f"Seat contraction to {new_seats}",
                })
                s["seats"] = new_seats
                s["mrr"] = new_seats * PLAN_TIERS[s["plan_tier"]]

        # Snapshot subscriptions for this month (active only)
        for cust_id, s in state.items():
            if s["churned"]:
                continue
            sub_rows.append({
                "customer_id": cust_id,
                "month": month.strftime("%Y-%m-%d"),
                "mrr": s["mrr"],
                "seats": s["seats"],
                "plan_tier": s["plan_tier"],
                "status": "active",
            })

    return pd.DataFrame(sub_rows), pd.DataFrame(event_rows)


def _q1_churn_amplifier(month: pd.Timestamp) -> float:
    """Slight Q1 churn elevation (budget cuts, renewals not renewed)."""
    return 1.20 if month.month in (1, 2) else 1.0


def _mid_month(month: pd.Timestamp) -> pd.Timestamp:
    return month + pd.Timedelta(days=14)


# --- CLI entry point -------------------------------------------------------

def generate_all(cfg: GeneratorConfig | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cfg = cfg or GeneratorConfig()
    customers = generate_customers(cfg)
    subs, events = generate_subscriptions_and_events(customers, cfg)
    return customers, subs, events


def write_to_disk(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    customers, subs, events = generate_all()
    customers.drop(columns=[c for c in customers.columns if c.endswith("_dt")], errors="ignore", inplace=True)
    customers.to_csv(out_dir / "customers.csv", index=False)
    subs.to_csv(out_dir / "subscriptions.csv", index=False)
    events.to_csv(out_dir / "events.csv", index=False)
    print(f"Wrote {len(customers)} customers, {len(subs)} subscription rows, {len(events)} events to {out_dir}")


if __name__ == "__main__":
    write_to_disk(Path(__file__).resolve().parents[1] / "data" / "generated")


# --- Phase 2: Pipeline & Forecasting --------------------------------------

# Stage taxonomy by opportunity type
NB_STAGES = ["Discovery", "Qualification", "Proof of Concept", "Negotiation"]
RENEWAL_STAGES = ["Renewal Discussion", "Negotiation"]
EXPANSION_STAGES = ["Expansion Discussion"]

# Mean dwell days per stage per segment (gamma-distributed in practice)
# Engineered insight: Mid-Market POC stall (~3x SMB dwell).
NB_STAGE_DWELL_DAYS = {
    "Discovery":         {"SMB": 7,  "Mid-Market": 10, "Enterprise": 14},
    "Qualification":     {"SMB": 10, "Mid-Market": 14, "Enterprise": 20},
    "Proof of Concept":  {"SMB": 15, "Mid-Market": 45, "Enterprise": 25},  # the gap
    "Negotiation":       {"SMB": 10, "Mid-Market": 18, "Enterprise": 25},
}

# Stage advance probability (rest = closed-lost in that stage)
# Engineered insight: Mid-Market POC -> Negotiation only ~40%.
NB_STAGE_ADVANCE_PROB = {
    "Discovery":        {"SMB": 0.85, "Mid-Market": 0.80, "Enterprise": 0.90},
    "Qualification":    {"SMB": 0.75, "Mid-Market": 0.70, "Enterprise": 0.85},
    "Proof of Concept": {"SMB": 0.70, "Mid-Market": 0.40, "Enterprise": 0.75},  # the gap
    "Negotiation":      {"SMB": 0.80, "Mid-Market": 0.75, "Enterprise": 0.85},
}

# Renewal / expansion are shorter cycles
RENEWAL_STAGE_DWELL_DAYS = {"Renewal Discussion": 30, "Negotiation": 15}
EXPANSION_STAGE_DWELL_DAYS = {"Expansion Discussion": 30}

# Rep pool (captured on opps; not surfaced in Phase 2)
REP_IDS = [f"REP-{i:02d}" for i in range(1, 13)]

# Pipeline snapshot dates (first of each quarter, Q1 2024 - Q4 2025)
SNAPSHOT_DATES = [pd.Timestamp(f"{y}-{m:02d}-01") for y in (2024, 2025) for m in (1, 4, 7, 10)]

# Forecast category by stage
FORECAST_CATEGORY_BY_STAGE = {
    "Discovery": "Pipeline",
    "Qualification": "Pipeline",
    "Proof of Concept": "Best Case",
    "Renewal Discussion": "Best Case",
    "Expansion Discussion": "Best Case",
    "Negotiation": "Commit",
}


def _sample_dwell_days(rng: np.random.Generator, mean_days: float) -> int:
    """Sample a positive-skew dwell time using a gamma with shape=2.

    Real-world dwell times have a long right tail (some deals drag); gamma(2)
    captures that without going negative. `mean = shape * scale` so scale = mean/2.
    """
    shape = 2.0
    scale = mean_days / shape
    return max(1, int(round(rng.gamma(shape, scale))))


def _walk_new_business_stages_backward(rng: np.random.Generator, close_date: pd.Timestamp,
                                        segment: str, end_stage: str | None,
                                        won: bool) -> list[dict]:
    """Build stage_history rows by walking backward from close_date.

    `end_stage` is the stage in which the deal closed (None means walked through
    all NB_STAGES and won). `won=True` means deal reached Negotiation and converted.

    Returns a list of dicts with: stage, entered_date, exited_date, days_in_stage.
    Dates are pd.Timestamp; serialization to ISO date happens at write time.
    """
    if end_stage is None:
        stages = NB_STAGES  # walked through all 4
    else:
        idx = NB_STAGES.index(end_stage)
        stages = NB_STAGES[:idx + 1]

    # Sample dwell times per stage
    dwells = [_sample_dwell_days(rng, NB_STAGE_DWELL_DAYS[s][segment]) for s in stages]

    # Build the history forward in time. Total = close_date - sum(dwells_before_close_stage)
    # For a won deal closing in Negotiation: deal exited Negotiation on close_date.
    # For a lost deal closing in stage X: deal exited X on close_date.
    history = []
    # Last stage exit = close_date
    end = close_date
    for stage_name, dwell in reversed(list(zip(stages, dwells))):
        start = end - pd.Timedelta(days=dwell)
        history.append({"stage": stage_name, "entered_date": start,
                        "exited_date": end, "days_in_stage": dwell})
        end = start

    history.reverse()  # chronological
    return history


def _generate_new_business_opps(customers: pd.DataFrame, rng: np.random.Generator
                                 ) -> tuple[list[dict], list[dict]]:
    """Generate new_business opportunities. Returns (opp_rows, stage_history_rows).

    Three sub-populations:
      1. Closed-won opps for every non-Self-Serve Phase 1 customer, closing on
         that customer's signup_date.
      2. Currently-open opps (~150), created in 2024-2025, in various stages,
         expected to close Q1-Q2 2026.
      3. Closed-lost opps (~80), walked through stages and dropped out somewhere.
    """
    opp_rows = []
    stage_history_rows = []
    next_id = 1

    # Sub-population 1: closed-won, one per non-Self-Serve Phase 1 customer
    nb_customers = customers[customers["acquisition_channel"] != "Self-Serve Promo"]
    for _, c in nb_customers.iterrows():
        close_date = pd.Timestamp(c["signup_date"])
        history = _walk_new_business_stages_backward(
            rng, close_date, c["segment"], end_stage=None, won=True
        )
        created_date = history[0]["entered_date"]
        opp_id = f"OPP-{next_id:05d}"
        next_id += 1
        opp_rows.append({
            "opportunity_id": opp_id,
            "customer_id": c["customer_id"],
            "account_name": c["company_name"],
            "segment": c["segment"],
            "acquisition_channel": c["acquisition_channel"],
            "owner_rep_id": str(rng.choice(REP_IDS)),
            "opportunity_type": "new_business",
            "created_date": created_date.strftime("%Y-%m-%d"),
            "close_date": close_date.strftime("%Y-%m-%d"),
            "amount": float(c["initial_mrr"]) * 12.0,
            "current_stage": "Closed Won",
            "status": "closed_won",
        })
        for h in history:
            stage_history_rows.append({
                "opportunity_id": opp_id,
                "stage": h["stage"],
                "entered_date": h["entered_date"].strftime("%Y-%m-%d"),
                "exited_date": h["exited_date"].strftime("%Y-%m-%d"),
                "days_in_stage": h["days_in_stage"],
            })

    # Sub-population 2: currently-open opps (~150)
    # Spread created_date across 2024-09 to 2025-12; sample a current stage based
    # on stage-advance probabilities; expected close_date = today + remaining stages' dwell.
    today = pd.Timestamp("2025-12-01")  # "Now" for the dashboard
    n_open = 150
    for _ in range(n_open):
        segment = str(rng.choice(SEGMENTS, p=SEGMENT_WEIGHTS))
        channel = str(rng.choice([c for c in CHANNELS if c != "Self-Serve Promo"]))
        created_offset_days = int(rng.integers(0, 365))  # up to a year before "today"
        created_date = today - pd.Timedelta(days=created_offset_days)

        # Walk stages forward from created_date until either a non-advance roll
        # (deal would have been lost — restart) or we reach a stage but "now"
        # has arrived. Tracks current stage at "today".
        cur = pd.Timestamp(created_date)
        history = []
        current_stage = None
        for stage in NB_STAGES:
            dwell = _sample_dwell_days(rng, NB_STAGE_DWELL_DAYS[stage][segment])
            entered = cur
            exit_date = cur + pd.Timedelta(days=dwell)
            if exit_date >= today:
                # Deal is still in this stage as of today
                current_stage = stage
                history.append({"stage": stage, "entered_date": entered,
                                "exited_date": None, "days_in_stage": None})
                break
            # Did the deal advance? If yes, continue. If no, this would have
            # been a lost deal — but we want open deals here, so restart the loop
            # by treating this deal as having advanced.
            history.append({"stage": stage, "entered_date": entered,
                            "exited_date": exit_date, "days_in_stage": dwell})
            cur = exit_date
        else:
            # Deal walked through all 4 stages but didn't close yet — extend
            # by setting current_stage = Negotiation with no exit
            current_stage = "Negotiation"
            # Replace the last history entry to be in-progress
            history[-1]["exited_date"] = None
            history[-1]["days_in_stage"] = None

        # Estimate expected close: today + average remaining-dwell across uncompleted stages
        remaining = NB_STAGES[NB_STAGES.index(current_stage):]
        expected_close_offset = sum(NB_STAGE_DWELL_DAYS[s][segment] for s in remaining)
        expected_close = today + pd.Timedelta(days=expected_close_offset)
        amount = float(rng.integers(5_000, 250_000))

        opp_id = f"OPP-{next_id:05d}"
        next_id += 1
        opp_rows.append({
            "opportunity_id": opp_id,
            "customer_id": None,
            "account_name": _fake_company_name(rng),
            "segment": segment,
            "acquisition_channel": channel,
            "owner_rep_id": str(rng.choice(REP_IDS)),
            "opportunity_type": "new_business",
            "created_date": created_date.strftime("%Y-%m-%d"),
            "close_date": expected_close.strftime("%Y-%m-%d"),
            "amount": amount,
            "current_stage": current_stage,
            "status": "open",
        })
        for h in history:
            stage_history_rows.append({
                "opportunity_id": opp_id,
                "stage": h["stage"],
                "entered_date": h["entered_date"].strftime("%Y-%m-%d"),
                "exited_date": h["exited_date"].strftime("%Y-%m-%d") if h["exited_date"] else None,
                "days_in_stage": h["days_in_stage"],
            })

    # Sub-population 3: closed-lost (~80)
    n_lost = 80
    for _ in range(n_lost):
        segment = str(rng.choice(SEGMENTS, p=SEGMENT_WEIGHTS))
        channel = str(rng.choice([c for c in CHANNELS if c != "Self-Serve Promo"]))
        # Pick stage where deal died — weighted by advance failures
        # Higher chance of dying in POC, especially for Mid-Market
        death_stage = str(rng.choice(NB_STAGES, p=[0.25, 0.25, 0.40, 0.10]))
        # Pick a close_date in 2024-2025
        close_date = pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(rng.integers(0, 730)))
        history = _walk_new_business_stages_backward(
            rng, close_date, segment, end_stage=death_stage, won=False
        )
        created_date = history[0]["entered_date"]
        amount = float(rng.integers(5_000, 250_000))

        opp_id = f"OPP-{next_id:05d}"
        next_id += 1
        opp_rows.append({
            "opportunity_id": opp_id,
            "customer_id": None,
            "account_name": _fake_company_name(rng),
            "segment": segment,
            "acquisition_channel": channel,
            "owner_rep_id": str(rng.choice(REP_IDS)),
            "opportunity_type": "new_business",
            "created_date": created_date.strftime("%Y-%m-%d"),
            "close_date": close_date.strftime("%Y-%m-%d"),
            "amount": amount,
            "current_stage": "Closed Lost",
            "status": "closed_lost",
        })
        for h in history:
            stage_history_rows.append({
                "opportunity_id": opp_id,
                "stage": h["stage"],
                "entered_date": h["entered_date"].strftime("%Y-%m-%d"),
                "exited_date": h["exited_date"].strftime("%Y-%m-%d"),
                "days_in_stage": h["days_in_stage"],
            })

    return opp_rows, stage_history_rows
