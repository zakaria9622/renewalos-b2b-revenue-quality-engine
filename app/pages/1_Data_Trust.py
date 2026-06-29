from __future__ import annotations

import streamlit as st
from app.bootstrap_ui import ensure_demo_data_ready_for_streamlit

from renewalos.app import data_access
from renewalos.app.formatting import DATA_READINESS_WARNING, SYNTHETIC_DISCLAIMER
from renewalos.app.validation import AppDataError

st.set_page_config(page_title="RenewalOS Data Trust", page_icon="RO", layout="wide")


def _refresh_control() -> None:
    if st.sidebar.button("Refresh data cache"):
        st.cache_data.clear()
        st.rerun()


@st.cache_data(show_spinner=False)
def _load_data() -> dict[str, object]:
    return {
        "trust_counts": data_access.load_kpi_trust_status_counts(),
        "quality_counts": data_access.load_account_month_quality_counts(),
        "rule_summary": data_access.load_quality_rule_summary(),
        "coverage": data_access.load_incident_detection_coverage(),
    }


_refresh_control()
st.title("Data Trust")
st.info(SYNTHETIC_DISCLAIMER)
st.warning(DATA_READINESS_WARNING)
ensure_demo_data_ready_for_streamlit()

try:
    frames = _load_data()
except AppDataError as error:
    st.error(str(error))
    st.stop()

trust_counts = frames["trust_counts"]
quality_counts = frames["quality_counts"]
rule_summary = frames["rule_summary"]
coverage = frames["coverage"]

st.header("KPI Trust-Status Summary")
st.write(
    "`mart_kpi_trust_status` shows the current gate for future revenue metrics. "
    "The app does not relabel any row as trusted outside that model."
)
st.dataframe(trust_counts, use_container_width=True, hide_index=True)

if hasattr(trust_counts, "empty") and not trust_counts.empty:
    approved_rows = trust_counts[trust_counts["is_management_kpi_reporting_approved"]]
    if approved_rows.empty:
        st.warning(
            "No current account-month rows are approved for management KPI reporting by "
            "`mart_kpi_trust_status`."
        )

st.header("Account-Month Quality Status")
st.write(
    "Quality statuses preserve blocked, warning, eligible-with-caveat, and "
    "not-assessable-style gates where those values are present in current outputs."
)
st.dataframe(quality_counts, use_container_width=True, hide_index=True)
if hasattr(quality_counts, "empty") and not quality_counts.empty:
    st.bar_chart(quality_counts, x="quality_status", y="account_month_count")

st.header("Critical Quality-Rule Categories")
st.write(
    "Exception rows are grouped from existing quality-control tables. These are diagnostic "
    "review queues, not repaired source records."
)
st.dataframe(rule_summary, use_container_width=True, hide_index=True)

st.header("Incident Detection Coverage")
st.write(
    "`dq_incident_detection_coverage` compares registered synthetic incidents with detected "
    "quality exceptions."
)
st.dataframe(coverage, use_container_width=True, hide_index=True)
