"""Page 5: Conformance Checking.

Presents token-based replay fitness, model precision, clinical sequence deviations,
cross-flow compliance comparisons, and process variant conformance matrix.
"""

import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from .data_loader import (
    load_conformance_summary,
    load_deviation_analysis,
    load_clinical_flows,
    resolve_data_path,
)


def render():
    """Render Conformance Checking Page."""
    st.markdown("## ⚖️ Clinical Pathway Conformance Checking")
    st.markdown(
        "Evaluates alignment between recorded hospital event sequences, the discovered Inductive Miner "
        "Petri net model, and normative clinical guidelines."
    )

    # -----------------------------------------------------------------------
    # CRITICAL CLINICAL INTERPRETATION NOTICE
    # -----------------------------------------------------------------------
    st.error(
        "🚨 **IMPORTANT CLINICAL INTERPRETATION NOTICE**:\n\n"
        "The reference Petri net (`outputs/careflow_petri_net.pnml`) is a **data-derived reference model** "
        "discovered directly from historical OPD records using PM4Py Inductive Miner. "
        "**Do NOT present 100% token replay fitness as 100% medical guideline compliance.**\n\n"
        "- **Model Fitness (100.0%)**: Confirms the discovered Petri net mathematically replays all observed sequences in the log.\n"
        "- **Clinical Guideline Compliance**: Evaluates whether pathways adhere to medical precedence (e.g. physician consultation before diagnostic testing, administrative registration before clinical evaluation)."
    )

    # -----------------------------------------------------------------------
    # Top Conformance KPIs
    # -----------------------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            label="TBR Log Fitness",
            value="100.0%",
            help="PM4Py token-based replay fitness against the Inductive Miner Petri net.",
        )
    with c2:
        st.metric(
            label="Model Precision",
            value="79.14%",
            help="Token replay precision score (avoidance of excessive generalisation).",
        )
    with c3:
        st.metric(
            label="Harmonic F-Measure",
            value="88.36%",
            help="Balanced harmonic mean of replay fitness and precision.",
        )
    with c4:
        st.metric(
            label="Pre-Consult Diagnostics",
            value="4.66%",
            delta="2,324 Cases",
            delta_color="inverse",
            help="Encounters where Imaging or Laboratory testing preceded Doctor Consultation.",
        )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Conformance & Sequence Metrics across Clinical Flows
    # -----------------------------------------------------------------------
    st.markdown("### 📊 Conformance Profile Across Clinical Flows (Flows 1–7)")
    flow_df = load_clinical_flows()

    if not flow_df.empty:
        fig_flow = go.Figure()
        fig_flow.add_trace(go.Bar(
            x=[f"Flow {r['Flow_Code']}" for _, r in flow_df.iterrows()],
            y=flow_df["Start_Conforming_Pct"],
            name="Start Registration (%)",
            marker_color="#17b978",
        ))
        fig_flow.add_trace(go.Bar(
            x=[f"Flow {r['Flow_Code']}" for _, r in flow_df.iterrows()],
            y=flow_df["Pre_Consult_Diag_Pct"],
            name="Pre-Consult Diagnostics (%)",
            marker_color="#d95f02",
        ))
        fig_flow.add_trace(go.Bar(
            x=[f"Flow {r['Flow_Code']}" for _, r in flow_df.iterrows()],
            y=flow_df["Loop_Repetition_Pct"],
            name="Activity Loops / Repetition (%)",
            marker_color="#7570b3",
        ))
        fig_flow.update_layout(
            title="Compliance & Deviation Distribution by Clinical Flow Category",
            barmode="group",
            yaxis=dict(title="Proportion of Flow Cases (%)", range=[0, 105]),
            legend=dict(x=0.6, y=1.1, orientation="h"),
            margin=dict(l=20, r=20, t=50, b=20),
            height=380,
        )
        st.plotly_chart(fig_flow, use_container_width=True)

        st.dataframe(
            flow_df,
            column_config={
                "Flow_Code": "Flow",
                "Flow_Name": "Clinical Pathway Definition",
                "Total_Cases": st.column_config.NumberColumn("Cases", format="%d"),
                "Case_Percentage": st.column_config.NumberColumn("Log Share (%)", format="%.2f%%"),
                "Start_Conforming_Pct": st.column_config.NumberColumn("Start Reg (%)", format="%.2f%%"),
                "Pre_Consult_Diag_Pct": st.column_config.NumberColumn("Pre-Consult Diag (%)", format="%.2f%%"),
                "Loop_Repetition_Pct": st.column_config.NumberColumn("Loops (%)", format="%.2f%%"),
                "Avg_Trace_Length": st.column_config.NumberColumn("Mean Length", format="%.2f"),
            },
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Empirical Clinical Sequence Deviations Explorer
    # -----------------------------------------------------------------------
    st.markdown("### ⚠️ Empirical Clinical Sequence Deviations")
    dev_df = load_deviation_analysis()

    if not dev_df.empty:
        col_dev_chart, col_dev_table = st.columns([5, 5])

        with col_dev_chart:
            # Filter top specific deviations
            chart_devs = dev_df[
                ~dev_df["deviation_pattern"].isin([
                    "Registration Not First Activity",
                    "Any Activity Repetition (Loop Execution)",
                    "Diagnostic Precedence Deviation: Any Diagnostic Before Consultation",
                ])
            ].head(8)

            fig_dev = px.bar(
                chart_devs,
                x="affected_cases",
                y="deviation_pattern",
                orientation="h",
                title="Top Observed Sequence Deviations",
                labels={"affected_cases": "Affected Cases", "deviation_pattern": "Deviation Pattern"},
                color="affected_cases",
                color_continuous_scale="Oranges",
                text="affected_cases",
            )
            fig_dev.update_traces(texttemplate="%{text:,}", textposition="outside")
            fig_dev.update_layout(coloraxis_showscale=False, yaxis={"autorange": "reversed"}, margin=dict(l=20, r=20, t=40, b=20), height=380)
            st.plotly_chart(fig_dev, use_container_width=True)

        with col_dev_table:
            cat_filter = st.selectbox(
                "Filter by Deviation Category:",
                ["All Categories"] + sorted(dev_df["deviation_category"].unique().tolist())
            )
            display_dev = dev_df.copy()
            if cat_filter != "All Categories":
                display_dev = display_dev[display_dev["deviation_category"] == cat_filter]

            st.dataframe(
                display_dev[["deviation_pattern", "affected_cases", "case_percentage", "clinical_interpretation"]],
                column_config={
                    "deviation_pattern": "Pattern",
                    "affected_cases": st.column_config.NumberColumn("Cases", format="%d"),
                    "case_percentage": st.column_config.NumberColumn("Share (%)", format="%.2f%%"),
                    "clinical_interpretation": "Clinical Interpretation",
                },
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Multi-Panel Conformance Visualization Image
    # -----------------------------------------------------------------------
    st.markdown("### 🖼️ Publication-Quality Conformance Visual Dashboard")
    conf_img = resolve_data_path("outputs/conformance_visualization.png")
    if os.path.exists(conf_img):
        st.image(conf_img, use_container_width=True, caption="CareFlow 4-Panel Conformance Checking and Deviation Overview")
    else:
        st.warning("Conformance visualization image not found at outputs/conformance_visualization.png")

