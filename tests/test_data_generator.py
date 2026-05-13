"""Tests that the synthetic data generator produces the patterns the
dashboard is built to surface. These are sanity tests, not unit tests:
they verify the macro behavior of the simulation.
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.data_generator import (
    GeneratorConfig,
    generate_customers,
    generate_subscriptions_and_events,
)


@pytest.fixture(scope="module")
def generated():
    cfg = GeneratorConfig()
    customers = generate_customers(cfg)
    subs, events = generate_subscriptions_and_events(customers, cfg)
    return customers, subs, events


def test_customer_count_is_reasonable(generated):
    customers, _, _ = generated
    assert 600 <= len(customers) <= 900


def test_all_three_segments_present(generated):
    customers, _, _ = generated
    assert set(customers["segment"].unique()) == {"SMB", "Mid-Market", "Enterprise"}


def test_all_five_channels_present(generated):
    customers, _, _ = generated
    assert set(customers["acquisition_channel"].unique()) == {
        "Outbound Sales", "Inbound Marketing", "Partner Referral",
        "Self-Serve Promo", "Event/Conference",
    }


def test_q3_2024_promo_cohort_overrepresents_self_serve(generated):
    """The engineered bump should make Self-Serve Promo visibly dominate Q3 2024."""
    customers, _, _ = generated
    q3_2024 = customers[customers["signup_cohort"].isin(["2024-07", "2024-08", "2024-09"])]
    channel_mix = q3_2024["acquisition_channel"].value_counts(normalize=True)
    assert channel_mix.get("Self-Serve Promo", 0) > 0.40, (
        f"Self-Serve Promo should be >40% of Q3 2024 cohort, got {channel_mix.to_dict()}"
    )


def test_self_serve_promo_q3_cohort_churns_worse(generated):
    """The core engineered insight: Q3 2024 Self-Serve Promo cohort has
    materially worse 12-month retention than the rest of the book."""
    customers, subs, _ = generated

    target_cohorts = ["2024-07", "2024-08", "2024-09"]
    promo_q3 = customers[
        (customers["signup_cohort"].isin(target_cohorts))
        & (customers["acquisition_channel"] == "Self-Serve Promo")
    ]
    other_cohorts = customers[
        (customers["signup_cohort"].isin(target_cohorts))
        & (customers["acquisition_channel"] != "Self-Serve Promo")
    ]

    def retained_at_m12(cohort_customers: pd.DataFrame) -> float:
        if len(cohort_customers) == 0:
            return 1.0
        retained = 0
        for _, c in cohort_customers.iterrows():
            signup = pd.Timestamp(c["signup_date"]).to_period("M")
            target = (signup + 12).to_timestamp().strftime("%Y-%m-%d")
            still_active = (
                (subs["customer_id"] == c["customer_id"])
                & (subs["month"] == target)
            ).any()
            if still_active:
                retained += 1
        return retained / len(cohort_customers)

    promo_retention = retained_at_m12(promo_q3)
    other_retention = retained_at_m12(other_cohorts)

    assert other_retention - promo_retention > 0.15, (
        f"Promo cohort M12 retention ({promo_retention:.2%}) should be at "
        f"least 15 points worse than other Q3 2024 channels ({other_retention:.2%})."
    )


def test_total_mrr_grows_over_time(generated):
    _, subs, _ = generated
    first_month_mrr = subs[subs["month"] == "2023-01-01"]["mrr"].sum()
    last_month_mrr = subs[subs["month"] == "2025-12-01"]["mrr"].sum()
    assert last_month_mrr > first_month_mrr * 3, (
        f"Expected meaningful growth over 36 months; got {first_month_mrr:.0f} -> {last_month_mrr:.0f}"
    )


def test_event_types_cover_full_lifecycle(generated):
    _, _, events = generated
    types = set(events["event_type"].unique())
    assert {"signup", "churn"} <= types
    # upgrades/downgrades should exist but not strictly required every run
    assert "upgrade" in types
