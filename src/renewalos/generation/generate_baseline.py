"""Generate clean baseline synthetic B2B source-domain rows."""

from __future__ import annotations

import random
from collections.abc import Sequence
from datetime import date, timedelta

from renewalos.generation.config import (
    DEFAULT_GENERATION_CONFIG,
    SYNTHETIC_DATA_LABEL,
    CsvRow,
    SyntheticDataConfig,
    TableMap,
    add_months,
    month_end,
)

SEGMENTS: tuple[str, ...] = ("SMB", "Mid-Market", "Enterprise")
REGIONS: tuple[str, ...] = ("North America", "EMEA", "APAC", "LATAM")
INDUSTRIES: tuple[str, ...] = (
    "Business Services",
    "Healthcare Operations",
    "Industrial Services",
    "Logistics",
    "Software",
    "Financial Operations",
)
PRODUCT_TIERS: tuple[str, ...] = ("Core", "Growth", "Scale")
TICKET_CATEGORIES: tuple[str, ...] = ("access", "billing", "workflow", "data_quality", "training")
INTERACTION_TYPES: tuple[str, ...] = (
    "business_review",
    "renewal_check_in",
    "training",
    "risk_review",
)
SENTIMENTS: tuple[str, ...] = ("positive", "neutral", "concerned")


def generate_baseline(
    config: SyntheticDataConfig = DEFAULT_GENERATION_CONFIG,
) -> TableMap:
    """Create clean baseline rows before incident injection."""

    rng = random.Random(config.random_seed)
    months = config.month_starts()

    accounts: list[CsvRow] = []
    contracts: list[CsvRow] = []
    billing_events: list[CsvRow] = []
    usage_events: list[CsvRow] = []
    support_tickets: list[CsvRow] = []
    cs_interactions: list[CsvRow] = []

    contract_counter = 1
    billing_counter = 1
    usage_counter = 1
    ticket_counter = 1
    interaction_counter = 1

    for account_number in range(1, config.portfolio_size + 1):
        account_id = f"ACC-{account_number:04d}"
        segment = _choose(rng, SEGMENTS, weights=(0.50, 0.35, 0.15))
        region = _choose(rng, REGIONS)
        industry = _choose(rng, INDUSTRIES)
        product_tier = _choose(rng, PRODUCT_TIERS)
        created_date = config.simulation_start - timedelta(days=rng.randint(45, 720))
        is_churned = rng.random() < 0.12
        churn_month_index = rng.randint(14, 22) if is_churned else None
        churn_date = month_end(months[churn_month_index]) if churn_month_index is not None else None
        lifecycle_status = "churned" if churn_date is not None else "active"
        crm_status = "churned" if churn_date is not None else _choose(rng, ("open", "renewed"))
        owner_id = f"CSM-{rng.randint(1, 24):03d}"
        base_arr = _base_arr_for_segment(rng, segment)

        accounts.append(
            _base_row(
                {
                    "account_id": account_id,
                    "account_name": f"Synthetic Account {account_number:04d} LLC",
                    "segment": segment,
                    "region": region,
                    "industry": industry,
                    "created_date": created_date.isoformat(),
                    "lifecycle_status": lifecycle_status,
                    "crm_renewal_status": crm_status,
                    "owner_id": owner_id,
                    "churn_date": churn_date.isoformat() if churn_date is not None else "",
                },
                config,
            )
        )

        account_contracts: list[CsvRow] = []
        contract_start = add_months(config.simulation_start, -rng.randint(0, 8))
        contract_arr = base_arr
        period_number = 1

        while contract_start <= config.simulation_end:
            natural_end = add_months(contract_start, 12) - timedelta(days=1)
            contract_end = natural_end
            status = "active" if natural_end >= config.simulation_end else "expired"

            if churn_date is not None and natural_end >= churn_date:
                contract_end = churn_date
                status = "cancelled"

            contract_id = f"CON-{contract_counter:05d}"
            contract_counter += 1
            contract = _base_row(
                {
                    "contract_id": contract_id,
                    "account_id": account_id,
                    "contract_start_date": contract_start.isoformat(),
                    "contract_end_date": contract_end.isoformat(),
                    "renewal_date": contract_end.isoformat(),
                    "status": status,
                    "arr_amount": str(contract_arr),
                    "product_tier": product_tier,
                    "period_number": str(period_number),
                },
                config,
            )
            contracts.append(contract)
            account_contracts.append(contract)

            billing_counter = _append_contract_billing_events(
                billing_events=billing_events,
                billing_counter=billing_counter,
                contract=contract,
                period_number=period_number,
                rng=rng,
                config=config,
            )

            if status == "cancelled" or contract_end >= config.simulation_end:
                break

            contract_start = contract_end + timedelta(days=1)
            period_number += 1
            contract_arr = _renewal_arr(rng, contract_arr)

        usage_counter = _append_usage_events(
            usage_events=usage_events,
            usage_counter=usage_counter,
            account_id=account_id,
            segment=segment,
            churn_date=churn_date,
            rng=rng,
            config=config,
        )
        ticket_counter = _append_support_tickets(
            support_tickets=support_tickets,
            ticket_counter=ticket_counter,
            account_id=account_id,
            churn_date=churn_date,
            rng=rng,
            config=config,
        )
        interaction_counter = _append_cs_interactions(
            cs_interactions=cs_interactions,
            interaction_counter=interaction_counter,
            account_id=account_id,
            contracts=account_contracts,
            rng=rng,
            config=config,
        )

    return {
        "accounts": accounts,
        "contracts": contracts,
        "billing_events": billing_events,
        "usage_events": usage_events,
        "support_tickets": support_tickets,
        "cs_interactions": cs_interactions,
        "incident_registry": [],
    }


def _append_contract_billing_events(
    billing_events: list[CsvRow],
    billing_counter: int,
    contract: CsvRow,
    period_number: int,
    rng: random.Random,
    config: SyntheticDataConfig,
) -> int:
    effective_date = max(_parse_date(contract["contract_start_date"]), config.simulation_start)
    if effective_date <= config.simulation_end:
        event_type = (
            "opening_arr"
            if period_number == 1 and effective_date == config.simulation_start
            else "renewal"
        )
        if period_number == 1 and effective_date > config.simulation_start:
            event_type = "new_arr"
        billing_counter = _append_billing_event(
            billing_events,
            billing_counter,
            contract,
            event_type,
            int(contract["arr_amount"]) if event_type != "renewal" else 0,
            effective_date,
            "posted",
            rng,
            config,
        )

    start_date = _parse_date(contract["contract_start_date"])
    end_date = _parse_date(contract["contract_end_date"])
    if contract["status"] != "cancelled":
        movement_date = add_months(start_date, rng.randint(3, 9))
        if config.simulation_start <= movement_date <= min(end_date, config.simulation_end):
            movement_type = _choose(rng, ("expansion_arr", "contraction_arr"), weights=(0.65, 0.35))
            amount = rng.choice((1200, 2400, 3600, 6000))
            if movement_type == "contraction_arr":
                amount *= -1
            billing_counter = _append_billing_event(
                billing_events,
                billing_counter,
                contract,
                movement_type,
                amount,
                movement_date,
                "posted",
                rng,
                config,
            )

    if (
        contract["status"] == "cancelled"
        and config.simulation_start <= end_date <= config.simulation_end
    ):
        billing_counter = _append_billing_event(
            billing_events,
            billing_counter,
            contract,
            "churned_arr",
            -int(contract["arr_amount"]),
            end_date,
            "cancelled",
            rng,
            config,
        )

    return billing_counter


def _append_billing_event(
    billing_events: list[CsvRow],
    billing_counter: int,
    contract: CsvRow,
    event_type: str,
    arr_delta: int,
    effective_date: date,
    billing_status: str,
    rng: random.Random,
    config: SyntheticDataConfig,
) -> int:
    received_at = effective_date + timedelta(days=rng.randint(1, 7))
    billing_events.append(
        _base_row(
            {
                "billing_event_id": f"BILL-{billing_counter:06d}",
                "account_id": contract["account_id"],
                "contract_id": contract["contract_id"],
                "event_date": effective_date.isoformat(),
                "effective_date": effective_date.isoformat(),
                "received_at": received_at.isoformat(),
                "event_type": event_type,
                "arr_delta": str(arr_delta),
                "amount": str(abs(arr_delta)),
                "billing_status": billing_status,
            },
            config,
        )
    )
    return billing_counter + 1


def _append_usage_events(
    usage_events: list[CsvRow],
    usage_counter: int,
    account_id: str,
    segment: str,
    churn_date: date | None,
    rng: random.Random,
    config: SyntheticDataConfig,
) -> int:
    segment_floor = {"SMB": 4, "Mid-Market": 15, "Enterprise": 40}[segment]
    segment_ceiling = {"SMB": 45, "Mid-Market": 140, "Enterprise": 420}[segment]

    for activity_month in config.month_starts():
        is_after_churn = churn_date is not None and activity_month > churn_date
        if is_after_churn:
            active_users = 0
            events_count = 0
            usage_status = "inactive"
        else:
            active_users = rng.randint(segment_floor, segment_ceiling)
            events_count = active_users * rng.randint(8, 35)
            usage_status = "active" if active_users > 0 else "inactive"

        usage_events.append(
            _base_row(
                {
                    "usage_event_id": f"USE-{usage_counter:07d}",
                    "account_id": account_id,
                    "activity_month": activity_month.isoformat(),
                    "active_users": str(active_users),
                    "events_count": str(events_count),
                    "usage_status": usage_status,
                    "extract_date": (month_end(activity_month) + timedelta(days=3)).isoformat(),
                },
                config,
            )
        )
        usage_counter += 1
    return usage_counter


def _append_support_tickets(
    support_tickets: list[CsvRow],
    ticket_counter: int,
    account_id: str,
    churn_date: date | None,
    rng: random.Random,
    config: SyntheticDataConfig,
) -> int:
    ticket_count = rng.randint(0, 5)
    event_end = min(churn_date or config.simulation_end, config.simulation_end)
    if event_end < config.simulation_start:
        return ticket_counter

    for _ in range(ticket_count):
        created_at = _random_date(rng, config.simulation_start, event_end)
        support_tickets.append(
            _base_row(
                {
                    "ticket_id": f"TICK-{ticket_counter:06d}",
                    "account_id": account_id,
                    "created_at": created_at.isoformat(),
                    "status": _choose(
                        rng,
                        ("open", "pending", "resolved"),
                        weights=(0.15, 0.20, 0.65),
                    ),
                    "severity": _choose(rng, ("low", "medium", "high"), weights=(0.55, 0.35, 0.10)),
                    "category": _choose(rng, TICKET_CATEGORIES),
                },
                config,
            )
        )
        ticket_counter += 1
    return ticket_counter


def _append_cs_interactions(
    cs_interactions: list[CsvRow],
    interaction_counter: int,
    account_id: str,
    contracts: Sequence[CsvRow],
    rng: random.Random,
    config: SyntheticDataConfig,
) -> int:
    for contract in contracts:
        renewal_date = _parse_date(contract["renewal_date"])
        if not config.simulation_start <= renewal_date <= config.simulation_end:
            continue

        for _ in range(rng.randint(1, 3)):
            earliest = max(config.simulation_start, renewal_date - timedelta(days=90))
            interaction_date = _random_date(rng, earliest, renewal_date)
            cs_interactions.append(
                _base_row(
                    {
                        "interaction_id": f"CSI-{interaction_counter:06d}",
                        "account_id": account_id,
                        "interaction_date": interaction_date.isoformat(),
                        "interaction_type": _choose(rng, INTERACTION_TYPES),
                        "sentiment": _choose(rng, SENTIMENTS, weights=(0.35, 0.45, 0.20)),
                        "csm_owner_id": f"CSM-{rng.randint(1, 24):03d}",
                        "notes_category": _choose(
                            rng,
                            ("renewal", "adoption", "support", "training"),
                        ),
                    },
                    config,
                )
            )
            interaction_counter += 1
    return interaction_counter


def _base_row(values: dict[str, str], config: SyntheticDataConfig) -> CsvRow:
    row = dict(values)
    row["synthetic_data_label"] = SYNTHETIC_DATA_LABEL
    row["scenario_version"] = config.scenario_version
    row["generation_layer"] = "baseline"
    row["quality_issue_type"] = ""
    return row


def _base_arr_for_segment(rng: random.Random, segment: str) -> int:
    if segment == "Enterprise":
        return rng.randrange(120_000, 360_001, 6_000)
    if segment == "Mid-Market":
        return rng.randrange(36_000, 144_001, 3_000)
    return rng.randrange(6_000, 48_001, 1_200)


def _renewal_arr(rng: random.Random, current_arr: int) -> int:
    multiplier = _choose(rng, ("0.90", "1.00", "1.10", "1.20"), weights=(0.12, 0.48, 0.30, 0.10))
    return int(round(current_arr * float(multiplier) / 100.0) * 100)


def _choose(
    rng: random.Random,
    values: Sequence[str],
    weights: Sequence[float] | None = None,
) -> str:
    return rng.choices(list(values), weights=weights, k=1)[0]


def _random_date(rng: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)
