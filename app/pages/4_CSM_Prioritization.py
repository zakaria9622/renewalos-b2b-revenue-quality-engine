from __future__ import annotations

import pandas as pd
import streamlit as st

from renewalos.app import data_access
from renewalos.app.bootstrap_ui import ensure_demo_data_ready_for_streamlit
from renewalos.app.formatting import SYNTHETIC_DISCLAIMER
from renewalos.app.validation import AppDataError
from renewalos.prioritization.config import DEFAULT_PRIORITIZATION_SCENARIO

st.set_page_config(page_title="RenewalOS CSM Prioritization", page_icon="RO", layout="wide")


def _refresh_control() -> None:
    if st.sidebar.button("Refresh data cache"):
        st.cache_data.clear()
        st.rerun()


@st.cache_data(show_spinner=False)
def _load_data() -> dict[str, pd.DataFrame]:
    return {
        "assumptions": data_access.load_scenario_assumptions(),
        "candidate_summary": data_access.load_candidate_eligibility_summary(),
        "input_summary": data_access.load_prioritization_input_summary(),
        "export": data_access.load_prioritization_export(),
    }


_refresh_control()
st.title("CSM Prioritization")
st.info(SYNTHETIC_DISCLAIMER)
st.warning(
    "Recommendations are simulated scenario outputs. Expected protected value is a synthetic "
    "scenario estimate, not observed retained revenue or business impact."
)
ensure_demo_data_ready_for_streamlit()

try:
    frames = _load_data()
except AppDataError as error:
    st.error(str(error))
    st.stop()

assumptions = frames["assumptions"]
candidate_summary = frames["candidate_summary"]
input_summary = frames["input_summary"]
export = frames["export"].copy()

st.header("Current Simulated Scenario Assumptions")
st.dataframe(assumptions, use_container_width=True, hide_index=True)

st.header("Candidate Eligibility And Exclusions")
st.write(
    "`mart_csm_priority_candidates` keeps blocked and not-assessable rows visible with "
    "exclusion reasons."
)
st.dataframe(candidate_summary, use_container_width=True, hide_index=True)

st.header("Prioritization Input Summary")
st.write(
    "`mart_csm_prioritization_inputs` contains only eligible candidate rows and simulated "
    "scenario fields."
)
st.dataframe(input_summary, use_container_width=True, hide_index=True)

st.header("Capacity Used Versus Available")
selected = export[export["recommendation_status"] == "selected"].copy()
selected["estimated_effort_hours"] = pd.to_numeric(
    selected["estimated_effort_hours"],
    errors="coerce",
).fillna(0)
selected["expected_protected_value"] = pd.to_numeric(
    selected["expected_protected_value"],
    errors="coerce",
).fillna(0)
scenario = DEFAULT_PRIORITIZATION_SCENARIO
capacity = pd.DataFrame.from_records(
    [
        {
            "scenario_id": scenario.scenario_id,
            "objective": scenario.objective,
            "selected_account_months": len(selected),
            "account_capacity": scenario.total_account_capacity,
            "used_csm_hours": round(float(selected["estimated_effort_hours"].sum()), 2),
            "available_csm_hours": scenario.available_csm_hours_per_month,
            "synthetic_expected_protected_value": round(
                float(selected["expected_protected_value"].sum()),
                2,
            ),
        }
    ]
)
st.dataframe(capacity, use_container_width=True, hide_index=True)

invalid_selected = selected[
    selected["assessment_status"].isin(["blocked_due_to_data_quality", "not_assessable"])
    | (selected["quality_status"] == "blocked")
]
if invalid_selected.empty:
    st.success("Blocked, quality-blocked, and not-assessable rows are not selected.")
else:
    st.error("Selected rows include blocked or not-assessable account-months.")
    st.dataframe(invalid_selected, use_container_width=True, hide_index=True)

st.header("Selected And Non-Selected Recommendations")
export["account_month"] = export["account_month"].astype(str)
status_options = sorted(export["recommendation_status"].dropna().astype(str).unique().tolist())
selected_statuses = st.multiselect(
    "Recommendation status",
    status_options,
    default=["selected", "not_selected"],
)
filtered = export
if selected_statuses:
    filtered = filtered[filtered["recommendation_status"].isin(selected_statuses)]

display_columns = [
    "account_id",
    "account_month",
    "recommendation_status",
    "priority_tier",
    "expected_protected_value",
    "estimated_effort_hours",
    "selection_reason",
    "non_selection_reason",
    "scenario_id",
    "assumption_version",
    "quality_status",
    "assessment_status",
    "health_band",
    "renewal_urgency",
    "explanation_drivers",
]
st.dataframe(filtered[display_columns].head(1000), use_container_width=True, hide_index=True)
st.caption("Showing up to 1,000 filtered recommendation rows on screen.")

st.download_button(
    label="Download current prioritization export",
    data=export.to_csv(index=False).encode("utf-8"),
    file_name="renewalos_csm_prioritization_recommendations.csv",
    mime="text/csv",
)
