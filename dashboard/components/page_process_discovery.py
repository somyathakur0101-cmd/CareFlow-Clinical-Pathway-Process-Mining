"""Page 3: Process Discovery.

Presents Directly-Follows Graphs (DFG), Petri Net process model, activity frequencies,
start/end activity distributions, and interactive process variant exploration.
"""

import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from .data_loader import (
    load_activity_frequencies,
    load_start_end_activities,
    load_process_variants,
    load_transition_times,
    resolve_data_path,
)


def render():
    """Render Process Discovery Page."""
    st.markdown("## 🔍 Clinical Process Discovery")
    st.markdown(
        "Discovered directly from 123,969 recorded hospital events across 49,912 outpatient encounters "
        "using PM4Py Inductive Miner and Directly-Follows Graph (DFG) algorithms."
    )

    # -----------------------------------------------------------------------
    # Process Metrics Banner
    # -----------------------------------------------------------------------
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Events", "123,969")
    with c2:
        st.metric("Total Encounters", "49,912")
    with c3:
        st.metric("DFG Edges", "20 Distinct")
    with c4:
        st.metric("Petri Net Places", "17 Places")
    with c5:
        st.metric("Process Variants", "287 Distinct")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Interactive Tabs: Visual Maps vs Tables & Distributions
    # -----------------------------------------------------------------------
    tab1, tab2, tab3 = st.tabs(["🗺️ Process Maps & Models", "📊 Process Variants Explorer", "🎯 Activity & Endpoint Distributions"])

    with tab1:
        st.markdown("### Process Map Architectures")
        map_choice = st.radio(
            "Select Process Visualization:",
            ["Directly-Follows Graph (DFG)", "Inductive Miner Petri Net", "Top Variants Frequency"],
            horizontal=True,
        )

        if map_choice == "Directly-Follows Graph (DFG)":
            st.markdown("#### Directly-Follows Graph (20 Edges, 74,057 Transitions)")
            st.markdown(
                "Shows the sequential flow and frequency of transitions between consecutive clinical events. "
                "Edge thickness and labels denote observed case transition volume."
            )
            dfg_img = resolve_data_path("outputs/careflow_dfg.png")
            if os.path.exists(dfg_img):
                st.image(dfg_img, use_container_width=True, caption="Directly-Follows Graph of CareFlow OPD Pathway")
            else:
                st.warning("DFG image not found at outputs/careflow_dfg.png")

        elif map_choice == "Inductive Miner Petri Net":
            st.markdown("#### Inductive Miner Workflow Petri Net (Sound Workflow Net)")
            st.markdown(
                "Discovered Petri Net with **17 places**, **21 transitions** (5 visible activities, 16 silent $\\tau$ routing transitions), "
                "and **48 arcs**. Sound workflow structure guarantees proper start at `source:1` and termination at `sink:1`."
            )
            pn_img = resolve_data_path("outputs/careflow_petri_net.png")
            if os.path.exists(pn_img):
                st.image(pn_img, use_container_width=True, caption="Discovered Inductive Miner Petri Net Model")
            else:
                st.warning("Petri Net image not found at outputs/careflow_petri_net.png")

        else:
            st.markdown("#### Top Process Variants Volume & Cumulative Coverage")
            var_img = resolve_data_path("outputs/careflow_variants.png")
            if os.path.exists(var_img):
                st.image(var_img, use_container_width=True, caption="Process Variants Distribution Chart")
            else:
                st.warning("Variants image not found at outputs/careflow_variants.png")

        # Interactive DFG Transition Table
        st.markdown("---")
        st.markdown("#### 🔗 Interactive Transition Frequencies (DFG Edges)")
        trans_df = load_transition_times()
        if not trans_df.empty:
            cnt_col = "transition_count" if "transition_count" in trans_df.columns else "count"
            med_col = "median_duration_minutes" if "median_duration_minutes" in trans_df.columns else "median_minutes"
            p90_col = "p90_duration_minutes" if "p90_duration_minutes" in trans_df.columns else "p90_minutes"
            zero_col = "zero_duration_count" if "zero_duration_count" in trans_df.columns else "zero_duration_pct"

            min_count = st.slider("Filter by minimum transition count:", 1, 1000, 10)
            filtered_trans = trans_df[trans_df[cnt_col] >= min_count][
                ["source_activity", "target_activity", cnt_col, med_col, p90_col, zero_col]
            ].sort_values(cnt_col, ascending=False)
            st.dataframe(
                filtered_trans,
                column_config={
                    "source_activity": "Source Activity",
                    "target_activity": "Target Activity",
                    cnt_col: st.column_config.NumberColumn("Transition Count", format="%d"),
                    med_col: st.column_config.NumberColumn("Median Wait (min)", format="%.1f"),
                    p90_col: st.column_config.NumberColumn("P90 Wait (min)", format="%.1f"),
                    zero_col: st.column_config.NumberColumn("Simultaneous Events", format="%d"),
                },
                use_container_width=True,
                hide_index=True,
            )

    with tab2:
        st.markdown("### 🧬 Process Variants Distribution & Pareto Analysis")
        var_df = load_process_variants()
        if not var_df.empty:
            # Top 10 Pareto Chart
            top10 = var_df.head(10).copy()
            top10["cum_pct_float"] = top10["cumulative_percentage"].astype(str).str.replace("%", "").astype(float)
            top10["case_pct_float"] = top10["case_percentage"].astype(str).str.replace("%", "").astype(float)

            fig_p = go.Figure()
            fig_p.add_trace(go.Bar(
                x=top10["variant_id"],
                y=top10["case_count"],
                name="Case Count",
                marker_color="#1e3d59",
                text=top10["case_count"],
                textposition="outside",
            ))
            fig_p.add_trace(go.Scatter(
                x=top10["variant_id"],
                y=top10["cum_pct_float"],
                name="Cumulative %",
                yaxis="y2",
                mode="lines+markers",
                marker_color="#d95f02",
                line=dict(width=3),
            ))
            fig_p.update_layout(
                title="Top 10 Process Variants (Pareto Volume vs. Cumulative %)",
                yaxis=dict(title="Encounter Cases"),
                yaxis2=dict(title="Cumulative Coverage (%)", overlaying="y", side="right", range=[0, 105]),
                legend=dict(x=0.8, y=1.15, orientation="h"),
                margin=dict(l=20, r=20, t=50, b=20),
                height=380,
            )
            st.plotly_chart(fig_p, use_container_width=True)

            st.markdown("#### Searchable Process Variants Table")
            search_act = st.selectbox(
                "Filter variants containing activity:",
                ["All Activities", "Laboratory Examination", "Imaging Procedure", "Pharmacy Dispensing", "Doctor Consultation & Prescription"]
            )
            filtered_var = var_df.copy()
            if search_act != "All Activities":
                filtered_var = filtered_var[filtered_var["activity_sequence"].str.contains(search_act, na=False)]

            st.dataframe(
                filtered_var[["variant_id", "case_count", "case_percentage", "cumulative_percentage", "activities_length", "activity_sequence"]],
                column_config={
                    "variant_id": "Variant ID",
                    "case_count": st.column_config.NumberColumn("Cases", format="%d"),
                    "case_percentage": "Case %",
                    "cumulative_percentage": "Cumulative %",
                    "activities_length": "Length",
                    "activity_sequence": "Clinical Pathway Sequence",
                },
                use_container_width=True,
                hide_index=True,
            )

    with tab3:
        st.markdown("### 🎯 Activity Frequency & Boundary Entry/Exit Points")
        col_act, col_se = st.columns([5, 5])

        with col_act:
            act_df = load_activity_frequencies()
            count_col = "event_count" if "event_count" in act_df.columns else "absolute_frequency"
            fig_a = px.bar(
                act_df,
                x=count_col,
                y="activity",
                orientation="h",
                title="Activity Absolute Event Volume",
                labels={count_col: "Total Events Recorded", "activity": "Activity"},
                color=count_col,
                color_continuous_scale="Teal",
                text=count_col,
            )
            fig_a.update_traces(texttemplate="%{text:,}", textposition="inside")
            fig_a.update_layout(coloraxis_showscale=False, yaxis={"autorange": "reversed"}, margin=dict(l=20, r=20, t=40, b=20), height=350)
            st.plotly_chart(fig_a, use_container_width=True)

        with col_se:
            se_df = load_start_end_activities()
            if not se_df.empty:
                start_col = "start_count" if "start_count" in se_df.columns else "start_cases"
                end_col = "end_count" if "end_count" in se_df.columns else "end_cases"
                # Grouped start vs end
                fig_se = go.Figure()
                fig_se.add_trace(go.Bar(
                    y=se_df["activity"],
                    x=se_df[start_col],
                    name="Start Activity (Entry)",
                    orientation="h",
                    marker_color="#17b978",
                ))
                fig_se.add_trace(go.Bar(
                    y=se_df["activity"],
                    x=se_df[end_col],
                    name="End Activity (Exit)",
                    orientation="h",
                    marker_color="#e7298a",
                ))
                fig_se.update_layout(
                    title="Start vs. End Activity Distribution",
                    barmode="group",
                    yaxis={"autorange": "reversed"},
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=350,
                    legend=dict(x=0.6, y=1.1, orientation="h"),
                )
                st.plotly_chart(fig_se, use_container_width=True)

        st.info(
            "📌 **Boundary Routing Insights**: **99.16%** of encounters cleanly initiate at `Appointment Registration`. "
            "**83.37%** conclude at `Doctor Consultation & Prescription`, while **10.86%** exit directly after final "
            "`Laboratory Examination` results and **5.57%** exit after `Imaging Procedure`."
        )
