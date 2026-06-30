from __future__ import annotations

import pandas as pd
import streamlit as st

from renewalos.app import data_access
from renewalos.app.bootstrap_ui import ensure_demo_data_ready_for_streamlit
from renewalos.app.formatting import SYNTHETIC_DISCLAIMER
from renewalos.app.validation import AppDataError

st.set_page_config(page_title="RenewalOS Account Health", page_icon="RO", layout="wide")


def _refresh_control() -> None:
    if st.sidebar.button("Refresh data cache"):
        st.cache_data.clear()
        st.rerun()


@st.cache_data(show_spinner=False)
def _load_data() -> dict[str, pd.DataFrame]:
    return {
        "coverage": data_access.load_health_coverage(),
        "bands": data_access.load_health_band_distribution(),
        "details": data_access.load_account_health_details(),
    }


@st.cache_data(show_spinner=False)
def _load_explanations(account_id: str, account_month: str) -> pd.DataFrame:
    return data_access.load_health_explanations(account_id=account_id, account_month=account_month)


_refresh_control()
st.title("Account Health")
st.info(SYNTHETIC_DISCLAIMER)
st.warning(
    "This is an explainable rule-based health framework. It is not a predictive churn model, "
    "renewal prediction, or automated outreach instruction."
)
ensure_demo_data_ready_for_streamlit()

try:
    frames = _load_data()
except AppDataError as error:
    st.error(str(error))
    st.stop()

coverage = frames["coverage"]
bands = frames["bands"]
details = frames["details"].copy()
details["account_month"] = details["account_month"].astype(str)

st.header("Health Assessment Coverage")
st.dataframe(coverage, use_container_width=True, hide_index=True)

st.header("Health-Band Distribution For Eligible Records")
st.write("Bands are shown only for rows that passed the account-health scoring gate.")
st.dataframe(bands, use_container_width=True, hide_index=True)
if not bands.empty:
    st.bar_chart(bands, x="health_band", y="account_month_count")

st.header("Account-Month Detail")
with st.container(border=True):
    st.subheader("Filters")
    status_options = sorted(details["assessment_status"].dropna().astype(str).unique().tolist())
    selected_statuses = st.multiselect(
        "Assessment status",
        status_options,
        default=status_options,
    )
    band_options = sorted(details["health_band"].dropna().astype(str).unique().tolist())
    selected_bands = st.multiselect("Health band", band_options, default=band_options)
    account_options = ["All"] + sorted(details["account_id"].dropna().astype(str).unique().tolist())
    selected_account = st.selectbox("Account", account_options)

filtered = details
if selected_statuses:
    filtered = filtered[filtered["assessment_status"].isin(selected_statuses)]
if selected_bands:
    band_filter = filtered["health_band"].isin(selected_bands) | filtered["health_band"].isna()
    filtered = filtered[band_filter]
if selected_account != "All":
    filtered = filtered[filtered["account_id"] == selected_account]

st.dataframe(filtered.head(1000), use_container_width=True, hide_index=True)
st.caption("Showing up to 1,000 filtered diagnostic rows on screen.")

st.header("Explanation Drivers")
if filtered.empty:
    st.write("No account-month rows match the current filters.")
else:
    option_frame = filtered[["account_id", "account_month", "assessment_status"]].head(500)
    options = [
        f"{row.account_id} | {row.account_month} | {row.assessment_status}"
        for row in option_frame.itertuples(index=False)
    ]
    selected = st.selectbox("Selected account-month", options)
    selected_account_id, selected_account_month, _status = [
        part.strip() for part in selected.split("|")
    ]
    explanations = _load_explanations(selected_account_id, selected_account_month)
    st.dataframe(explanations, use_container_width=True, hide_index=True)
