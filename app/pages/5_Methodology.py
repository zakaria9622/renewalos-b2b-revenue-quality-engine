from __future__ import annotations

import streamlit as st

from renewalos.app.formatting import SYNTHETIC_DISCLAIMER

st.set_page_config(page_title="RenewalOS Methodology", page_icon="RO", layout="wide")


def _refresh_control() -> None:
    if st.sidebar.button("Refresh data cache"):
        st.cache_data.clear()
        st.rerun()


_refresh_control()
st.title("Methodology")
st.info(SYNTHETIC_DISCLAIMER)

st.header("Documentation Map")
docs = [
    (
        "Project charter",
        "docs/project_charter.md",
        "Business problem, target users, decision workflow, and project guardrails.",
    ),
    (
        "Synthetic data methodology",
        "docs/synthetic_data_methodology.md",
        "Simulation scope, source grains, incident injection, and raw-data limits.",
    ),
    (
        "Quality-control framework",
        "docs/quality_control_framework.md",
        "Quality rules, incident detection coverage, and account-month quality gates.",
    ),
    (
        "Reconciliation methodology",
        "docs/reconciliation_methodology.md",
        "Diagnostic reconciliation statuses and why gaps are preserved.",
    ),
    (
        "Account-health methodology",
        "docs/account_health_methodology.md",
        "Rule-based health scoring, coverage gates, explanations, and limits.",
    ),
    (
        "CSM prioritization methodology",
        "docs/csm_prioritization_methodology.md",
        "Candidate eligibility, scenario inputs, optimization objective, and guardrails.",
    ),
    (
        "Scenario assumptions",
        "docs/scenario_assumptions.md",
        "Capacity, effort, effectiveness, and sensitivity assumptions.",
    ),
]
st.dataframe(
    [
        {
            "document": title,
            "path": path,
            "purpose": purpose,
        }
        for title, path, purpose in docs
    ],
    use_container_width=True,
    hide_index=True,
)

st.header("Project Limitations")
st.markdown(
    """
- All source records and outputs are synthetic.
- The app rebuilds deterministic synthetic demo artifacts when required.
- Management KPI reporting remains restricted by the trust-status model.
- Health scoring is rule-based and diagnostic, not predictive.
- Prioritization outputs are simulated recommendations under documented assumptions.
- Expected protected value is not observed retained revenue.
- No ML model, causal estimate, operational automation, deployment, or business-impact result
  is implemented.
"""
)
