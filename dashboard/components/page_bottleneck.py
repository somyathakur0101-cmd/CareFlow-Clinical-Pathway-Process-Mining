"""Page 4: Bottleneck and Waiting-Time Analysis.

Presents inter-event transition times, activity turnaround times (TAT),
slowest clinical pathways, and data quality / timestamp integrity audits.
"""

import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from .data_loader import (
    load_transition_times,
    load_clinical_flows,
    resolve_data_path,
)


def render():
    """Render Bottleneck Analysis Page."""
    st.markdown("## ⏱️ Bottleneck & Waiting-Time Analysis")
    st.markdown(
        "Quantifies operational delays, departmental turnaround times, and inter-activity waiting periods "
        "calculated strictly from validated timestamps."
    )

    # -----------------------------------------------------------------------
    # Top KPI Metrics Cards
    # -----------------------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            label="Lab Median TAT",
            value="125.0 min",
            delta="P90: 470.0 min",
            delta_color="inverse",
            help="Laboratory Turnaround Time bounded across N=13,175 verified specimen orders.",
        )
    with c2:
        st.metric(
            label="Imaging Median TAT",
            value="3.0 min",
            delta="P90: 13.0 min",
            delta_color="normal",
            help="Imaging Turnaround Time bounded across N=5,412 procedures (radiology acquisition to completion).",
        )
    with c3:
        st.metric(
            label="Intake Wait (Reg → Consult)",
            value="48.0 min",
            delta="P90: 178.0 min",
            delta_color="inverse",
            help="Median observed waiting time from appointment registration to physician consultation.",
        )
    with c4:
        st.metric(
            label="Consult → Imaging Wait",
            value="42.0 min",
            delta="P90: 136.0 min",
            delta_color="inverse",
            help="Median observed interval between consultation order and imaging acquisition.",
        )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Methodological Principle Banner
    # -----------------------------------------------------------------------
    st.warning(
        "⚠️ **Clinical Distinction**: Observed waiting time represents elapsed EMR timestamp intervals. "
        "It must **not** be equated with active physician treatment delay or medical negligence. "
        "Simultaneous timestamps (0 min) represent batch electronic order entry, while long spans (> 24 hours) "
        "reflect multi-day cross-session visits or asynchronous laboratory batch processing."
    )

    # -----------------------------------------------------------------------
    # Departmental Turnaround Times (Lab vs Imaging)
    # -----------------------------------------------------------------------
    st.markdown("### 🔬 Departmental Turnaround Times (TAT)")
    col_lab, col_img = st.columns([5, 5])

    with col_lab:
        tat_lab_data = [
            {"Metric": "Minimum", "Minutes": 0.0},
            {"Metric": "25th Percentile (Q1)", "Minutes": 48.0},
            {"Metric": "Median (P50)", "Minutes": 125.0},
            {"Metric": "Mean", "Minutes": 302.3},
            {"Metric": "75th Percentile (Q3)", "Minutes": 242.0},
            {"Metric": "90th Percentile (P90)", "Minutes": 470.0},
        ]
        fig_lab = px.bar(
            tat_lab_data,
            x="Metric",
            y="Minutes",
            text="Minutes",
            title="Laboratory TAT Profile (N=13,175 Bounded Orders)",
            color="Minutes",
            color_continuous_scale="Reds",
        )
        fig_lab.update_traces(texttemplate="%{text:.1f} min", textposition="outside")
        fig_lab.update_layout(coloraxis_showscale=False, margin=dict(l=20, r=20, t=40, b=20), height=340)
        st.plotly_chart(fig_lab, use_container_width=True)
        st.caption("🧪 **Laboratory TAT**: Median of 2 hours 5 minutes; 4,631 orders lacked valid completion timestamps and were properly excluded.")

    with col_img:
        tat_img_data = [
            {"Metric": "Minimum", "Minutes": 0.0},
            {"Metric": "25th Percentile (Q1)", "Minutes": 1.0},
            {"Metric": "Median (P50)", "Minutes": 3.0},
            {"Metric": "Mean", "Minutes": 11.2},
            {"Metric": "75th Percentile (Q3)", "Minutes": 7.0},
            {"Metric": "90th Percentile (P90)", "Minutes": 13.0},
        ]
        fig_img = px.bar(
            tat_img_data,
            x="Metric",
            y="Minutes",
            text="Minutes",
            title="Imaging Procedure TAT (N=5,412 Bounded Exams)",
            color="Minutes",
            color_continuous_scale="Greens",
        )
        fig_img.update_traces(texttemplate="%{text:.1f} min", textposition="outside")
        fig_img.update_layout(coloraxis_showscale=False, margin=dict(l=20, r=20, t=40, b=20), height=340)
        st.plotly_chart(fig_img, use_container_width=True)
        st.caption("📷 **Imaging TAT**: Rapid turnaround with median 3.0 minutes and P90 of 13.0 minutes, reflecting prompt bedside/X-ray acquisition.")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Top Observed Transitions & Slow Bottlenecks
    # -----------------------------------------------------------------------
    st.markdown("### 🐢 Slowest Observed Pathway Transitions")
    trans_df = load_transition_times()

    if not trans_df.empty:
        cnt_col = "transition_count" if "transition_count" in trans_df.columns else "count"
        med_col = "median_duration_minutes" if "median_duration_minutes" in trans_df.columns else "median_minutes"
        p90_col = "p90_duration_minutes" if "p90_duration_minutes" in trans_df.columns else "p90_minutes"

        # Show top slowest transitions by median duration
        slowest = trans_df[trans_df[cnt_col] >= 10].sort_values(med_col, ascending=False).head(8)
        slowest["transition"] = slowest["source_activity"] + " → " + slowest["target_activity"]

        fig_slow = go.Figure()
        fig_slow.add_trace(go.Bar(
            y=slowest["transition"],
            x=slowest[med_col],
            name="Median Wait (P50)",
            orientation="h",
            marker_color="#d95f02",
            text=slowest[med_col].round(1).astype(str) + " min",
            textposition="outside",
        ))
        fig_slow.add_trace(go.Bar(
            y=slowest["transition"],
            x=slowest[p90_col],
            name="90th Percentile (P90)",
            orientation="h",
            marker_color="#1e3d59",
            opacity=0.6,
            text=slowest[p90_col].round(1).astype(str) + " min",
            textposition="outside",
        ))
        fig_slow.update_layout(
            title="Top Slowest Inter-Activity Transitions (Median vs. P90)",
            barmode="group",
            yaxis={"autorange": "reversed"},
            xaxis={"title": "Duration (Minutes)"},
            legend=dict(x=0.7, y=1.1, orientation="h"),
            margin=dict(l=20, r=20, t=50, b=20),
            height=380,
        )
        st.plotly_chart(fig_slow, use_container_width=True)

    # -----------------------------------------------------------------------
    # Data Quality & Timestamp Integrity Audit
    # -----------------------------------------------------------------------
    st.markdown("### 🛡️ Data Quality & Timestamp Integrity Audit")
    dq1, dq2, dq3, dq4 = st.columns(4)
    with dq1:
        st.metric("Negative Intervals", "0", delta="Zero Inversions", delta_color="normal")
    with dq2:
        st.metric("Simultaneous Events", "11,502", delta="0 min Delta", delta_color="off")
    with dq3:
        st.metric("Missing Lab End Times", "4,631", delta="Excluded from TAT", delta_color="off")
    with dq4:
        st.metric("Inverted Prescriptions", "49", delta="Rule 9 Blanked", delta_color="off")

    st.markdown(
        "All data quality anomalies documented during event log extraction were preserved and audited: "
        "49 inverted prescription timestamps were retained with blanked durations (Rule 9), "
        "12 missing prescription start timestamps were preserved with lifecycle='complete' (Rule 8), "
        "and 4,631 open/uncompleted lab orders were excluded strictly from turnaround metrics."
    )
