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
