from __future__ import annotations

import pandas as pd
import streamlit as st

from renewalos.app import data_access
from renewalos.app.formatting import SYNTHETIC_DISCLAIMER
from renewalos.app.validation import AppDataError

st.set_page_config(page_title="RenewalOS Reconciliation", page_icon="RO", layout="wide")


def _refresh_control() -> None:
    if st.sidebar.button("Refresh local data"):
        st.cache_data.clear()
        st.rerun()


@st.cache_data(show_spinner=False)
def _load_data() -> dict[str, pd.DataFrame]:
    return {
        "status_counts": data_access.load_reconciliation_status_counts(),
        "gap_summary": data_access.load_reconciliation_gap_summary(),
        "details": data_access.load_reconciliation_details(),
    }


_refresh_control()
st.title("Revenue Reconciliation")
st.info(SYNTHETIC_DISCLAIMER)
st.warning(
    "This is a diagnostic reconciliation view. It is not certified ARR, NRR, GRR, churn, "
    "or renewal reporting."
)

try:
    frames = _load_data()
except AppDataError as error:
    st.error(str(error))
    st.stop()

status_counts = frames["status_counts"]
gap_summary = frames["gap_summary"]
details = frames["details"].copy()

st.header("Observed Reconciliation Statuses")
st.dataframe(status_counts, use_container_width=True, hide_index=True)
if not status_counts.empty:
    st.bar_chart(status_counts, x="reconciliation_status", y="account_month_count")

st.header("Reconciliation Gap Summary")
st.write("Gaps are retained as diagnostics and are not forced to zero.")
st.dataframe(gap_summary, use_container_width=True, hide_index=True)

st.header("Account-Month Diagnostics")
details["account_month"] = details["account_month"].astype(str)

with st.container(border=True):
    st.subheader("Filters")
    account_options = ["All"] + sorted(details["account_id"].dropna().astype(str).unique().tolist())
    selected_account = st.selectbox("Account", account_options)
    month_options = ["All"] + sorted(
        details["account_month"].dropna().astype(str).unique().tolist(),
        reverse=True,
    )
    selected_month = st.selectbox("Period", month_options)
    status_options = sorted(
        details["reconciliation_status"].dropna().astype(str).unique().tolist()
    )
    selected_statuses = st.multiselect(
        "Reconciliation status",
        status_options,
        default=status_options,
    )

filtered = details
if selected_account != "All":
    filtered = filtered[filtered["account_id"] == selected_account]
if selected_month != "All":
    filtered = filtered[filtered["account_month"] == selected_month]
if selected_statuses:
    filtered = filtered[filtered["reconciliation_status"].isin(selected_statuses)]

st.dataframe(filtered.head(1000), use_container_width=True, hide_index=True)
st.caption("Showing up to 1,000 filtered diagnostic rows on screen.")
