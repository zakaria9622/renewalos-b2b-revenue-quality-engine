from __future__ import annotations

import streamlit as st

from app.bootstrap_ui import ensure_demo_data_ready_for_streamlit
from renewalos.app import data_access
from renewalos.app.formatting import DATA_READINESS_WARNING, SYNTHETIC_DISCLAIMER
from renewalos.app.validation import AppDataError, validate_warehouse_ready

st.set_page_config(
    page_title="RenewalOS Control Tower",
    page_icon="RO",
    layout="wide",
)


def _refresh_control() -> None:
    if st.sidebar.button("Refresh data cache"):
        st.cache_data.clear()
        st.rerun()


@st.cache_data(show_spinner=False)
def _load_trust_counts() -> object:
    return data_access.load_kpi_trust_status_counts()


_refresh_control()

st.title("RenewalOS - B2B Revenue Reconciliation & Account-Health Decision System")
st.info(SYNTHETIC_DISCLAIMER)
st.warning(DATA_READINESS_WARNING)
ensure_demo_data_ready_for_streamlit()

st.header("Current Implementation Scope")
st.write(
    "This app reads the deterministic synthetic DuckDB warehouse, dbt diagnostic marts, and "
    "generated CSM prioritization export. When those generated demo artifacts are missing, it "
    "rebuilds the same synthetic pipeline before displaying outputs. It does not use real "
    "customer data, train models, or calculate trusted management KPIs."
)

try:
    validation = validate_warehouse_ready()
    trust_counts = _load_trust_counts()
except AppDataError as error:
    st.error(str(error))
    st.stop()

st.subheader("Synthetic Demo Data Readiness")
st.write(f"Warehouse: `{validation.database_path}`")
st.write(
    "The app can read the required dbt outputs. Review the Data Trust page before using any "
    "diagnostic table for interpretation."
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

st.caption("Streamlit interface for a fully synthetic scenario demo.")
