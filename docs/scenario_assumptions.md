# Scenario Assumptions

This file documents the simulated assumptions used by the RenewalOS CSM prioritization layer.
These values are not estimated from real company data and are not intervention-effectiveness
claims.

## Scenario Metadata

- Scenario ID: `synthetic_csm_capacity_v1`
- Assumption version: `simulated_prioritization_assumptions_v1`
- Solver seed: `20260228`
- Objective: maximize simulated expected protected value under capacity constraints.

## Capacity Assumptions

| Assumption | Value | Rationale | Sensitivity Risk |
| --- | ---: | --- | --- |
| Available CSM hours per month | 96 | Simulates limited monthly time for targeted outreach after meetings and admin work. | Higher hours select more accounts; lower hours make selection more concentrated. |
| CSM count | 4 | Represents a small team for a portfolio-scale scenario. | More CSMs increase account-contact capacity. |
| Max accounts per CSM | 12 | Keeps outreach volume bounded so recommendations do not imply unlimited follow-up capacity. | Raising this can overstate feasible coverage. |
| Max accounts to contact | 48 | Caps the scenario at the team-level account-contact limit. | A lower cap forces stricter tradeoffs even when hours remain. |
| Max solver candidate pool | 960 | Bounds the local OR-Tools solve to the top eligible account-months by scenario priority score. | A smaller pool can miss lower-ranked combinations; a larger pool can slow validation. |

## Tier Assumptions

| Priority Tier | Estimated Effort Hours | Assumed Effectiveness | Rationale |
| --- | ---: | ---: | --- |
| `tier_1` | 4.0 | 0.18 | Highest concern rows are assumed to require more effort and have the largest simulated response potential. |
| `tier_2` | 3.0 | 0.10 | Medium concern rows are assumed to need moderate follow-up with lower simulated response potential. |
| `tier_3` | 1.5 | 0.04 | Lower concern rows are assumed to need lighter touch and have the lowest simulated response potential. |

## Health And Renewal Factors

Health severity factors:

- `critical`: 1.00
- `at_risk`: 0.75
- `monitor`: 0.35
- `stable`: 0.10

Renewal urgency factors:

- `high`: 1.00
- `unknown_missing_renewal_date`: 1.00
- `medium`: 0.75
- `low`: 0.45
- all other values: 0.20

`estimated_account_value_at_risk` is calculated as revenue exposure multiplied by the health and
renewal factors. `expected_protected_value` then multiplies that scenario input by the assumed
intervention effectiveness.

## Validation Needed Before Real Use

A real company would need to replace these assumptions with evidence from governed historical data
or controlled experiments. At minimum, real use would require:

- validated source-system contracts, billing, usage, support, and Customer Success data;
- approved definitions for revenue exposure and renewal timing;
- measured intervention cost and capacity;
- observed intervention outcomes;
- fairness, governance, and escalation review;
- monitoring for drift and operational misuse.

Until those steps exist, this layer is synthetic scenario analysis only.
