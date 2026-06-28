from __future__ import annotations

import streamlit as st

from renewalos.app import data_access
from renewalos.app.formatting import DATA_READINESS_WARNING, SYNTHETIC_DISCLAIMER
from renewalos.app.validation import AppDataError, validate_warehouse_ready

st.set_page_config(
    page_title="RenewalOS Control Tower",
    page_icon="RO",
    layout="wide",
)


def _refresh_control() -> None:
    if st.sidebar.button("Refresh local data"):
        st.cache_data.clear()
        st.rerun()


@st.cache_data(show_spinner=False)
def _load_trust_counts() -> object:
    return data_access.load_kpi_trust_status_counts()


_refresh_control()

st.title("RenewalOS — B2B Revenue Reconciliation & Account-Health Decision System")
st.info(SYNTHETIC_DISCLAIMER)
st.warning(DATA_READINESS_WARNING)

st.header("Current Implementation Scope")
st.write(
    "This local app reads the existing DuckDB warehouse, dbt diagnostic marts, and generated "
    "CSM prioritization export. It does not create data, transform business logic, train models, "
    "or calculate new management KPIs."
)

try:
    validation = validate_warehouse_ready()
    trust_counts = _load_trust_counts()
except AppDataError as error:
    st.error(str(error))
    st.stop()

st.subheader("Local Data Readiness")
st.write(f"Warehouse: `{validation.database_path}`")
st.write(
    "The app can read the required local dbt outputs. Review the Data Trust page before using "
    "any diagnostic table for interpretation."
)
st.dataframe(trust_counts, use_container_width=True, hide_index=True)

st.subheader("Navigation")
st.write(
    "Use the sidebar pages to inspect quality gates, reconciliation diagnostics, account-health "
    "coverage, simulated CSM prioritization, and methodology documentation."
)
st.markdown(
    """
- **Data Trust:** KPI gate status, quality blockers, and incident detection coverage.
- **Revenue Reconciliation:** Diagnostic reconciliation statuses and account-month gaps.
- **Account Health:** Rule-based health coverage, detail rows, and explanations.
- **CSM Prioritization:** Simulated capacity-constrained recommendations and exclusions.
- **Methodology:** Documentation map and project limitations.
"""
)

st.caption("Local-only Streamlit interface. No deployment is configured in this repository.")
