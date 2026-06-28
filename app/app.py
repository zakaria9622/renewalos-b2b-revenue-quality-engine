import streamlit as st

FOUNDATION_MESSAGE = "RenewalOS foundation created — no data pipeline, KPI calculations, or decision outputs are implemented yet."  # noqa: E501

st.set_page_config(page_title="RenewalOS", page_icon="RO")
st.title("RenewalOS")
st.write(FOUNDATION_MESSAGE)
