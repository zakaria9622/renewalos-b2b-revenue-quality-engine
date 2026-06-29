from __future__ import annotations

import streamlit as st

from renewalos.app.bootstrap import (
    DeploymentBootstrapError,
    check_bootstrap_artifacts,
    ensure_demo_data_ready,
)


def ensure_demo_data_ready_for_streamlit() -> None:
    check = check_bootstrap_artifacts()
    if check.is_ready:
        return

    with st.status("Preparing synthetic demo data", expanded=True) as status:
        st.write(
            "Generated demo artifacts are missing or invalid. RenewalOS is rebuilding the "
            "deterministic synthetic pipeline before showing app outputs."
        )
        st.write("Missing or invalid artifact check:")
        for item in check.missing_items:
            st.write(f"- {item}")

        try:
            result = ensure_demo_data_ready()
        except DeploymentBootstrapError as error:
            status.update(
                label="Synthetic demo data initialization failed.",
                state="error",
                expanded=True,
            )
            st.error(str(error))
            st.stop()

        if result.initialized:
            st.write(
                "Rebuilt synthetic raw CSVs, the DuckDB/dbt warehouse outputs, and the "
                "simulated prioritization export."
            )
        else:
            st.write(
                "Required generated artifacts became available before this session rebuilt them."
            )
        status.update(label="Synthetic demo data ready.", state="complete", expanded=False)
        st.cache_data.clear()
