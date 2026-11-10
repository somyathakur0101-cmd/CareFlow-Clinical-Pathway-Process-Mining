"""Page 1: Executive Overview.

Presents high-level outpatient KPIs, monthly appointment trends,
weekday distribution, hourly arrival patterns, and service demand breakdown.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from .data_loader import (
    load_kpis,
    load_temporal_monthly,
    load_temporal_weekday,
    load_temporal_hourly,
    load_activity_frequencies,
)


def render():
    """Render Executive Overview Page."""
    kpis = load_kpis()

    st.markdown("## 🏥 Executive Healthcare Overview")
    st.markdown(
        "High-level process mining and clinical operational intelligence across the "
        "**CareFlow Outpatient Department (OPD)** cohort."
    )

    # -----------------------------------------------------------------------
    # Top KPI Row
    # -----------------------------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Unique Patients",
            value=f"{kpis['unique_patients']:,}",
            help="Total distinct individuals treated in the OPD cohort.",
        )
    with col2:
        st.metric(
            label="Unique Appointments",
            value=f"{kpis['unique_appointments']:,}",
            help="Total completed appointment encounters (cases).",
        )
    with col3:
        st.metric(
            label="Recorded Events",
            value=f"{kpis['total_events']:,}",
            help="Total timestamped clinical service events recorded across all encounters.",
        )
    with col4:
        st.metric(
            label="Clinical Activities",
            value=kpis["activity_categories"],
            help="Distinct clinical activity types (Registration, Consultation, Lab, Imaging, Pharmacy).",
        )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Secondary Metric Row
    # -----------------------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            label="Process Variants",
            value=kpis["process_variants"],
            help="Distinct sequence pathways observed across 49,912 appointments.",
        )
    with c2:
        st.metric(
            label="Petri Net Replay Fitness",
            value=f"{kpis['tbr_fitness'] * 100:.1f}%",
            help="Data-derived Petri net token-based replay fitness (PM4Py Inductive Miner).",
        )
    with c3:
        st.metric(
            label="Model Precision",
            value=f"{kpis['tbr_precision'] * 100:.1f}%",
            help="Exactness vs over-generalization score.",
        )
    with c4:
        st.metric(
            label="Registration First",
            value=f"{kpis['registration_compliance'] * 100:.2f}%",
            help="Proportion of encounters beginning with administrative registration (49,494 cases).",
        )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Monthly Appointment Trend & Weekday Distribution
    # -----------------------------------------------------------------------
    st.markdown("### 📈 Operational Volume & Arrival Dynamics")
    row2_left, row2_right = st.columns([6, 4])

    with row2_left:
        monthly_df = load_temporal_monthly()
        fig_monthly = px.area(
            monthly_df,
            x="month",
            y="appointment_count",
            title="Monthly Appointment Encounters (April 2024 – April 2026)",
            labels={"month": "Month", "appointment_count": "Appointments"},
            color_discrete_sequence=["#1e3d59"],
        )
        fig_monthly.update_traces(mode="lines+markers", fill="tozeroy", fillcolor="rgba(30, 61, 89, 0.15)")
        fig_monthly.update_layout(
            hovermode="x unified",
            xaxis_tickangle=-45,
            margin=dict(l=20, r=20, t=40, b=20),
            height=360,
        )
        # Highlight peak month
        max_row = monthly_df.loc[monthly_df["appointment_count"].idxmax()]
        fig_monthly.add_annotation(
            x=max_row["month"],
            y=max_row["appointment_count"],
            text=f"Peak: {max_row['month']} ({max_row['appointment_count']:,})",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#d95f02",
            font=dict(color="#d95f02", size=11, family="Arial Black"),
        )
        st.plotly_chart(fig_monthly, use_container_width=True)

    with row2_right:
        weekday_df = load_temporal_weekday()
        colors = ["#17b978" if w == "Monday" else "#386cb0" if w != "Sunday" else "#e7298a" for w in weekday_df["weekday"]]
        fig_weekday = px.bar(
            weekday_df,
            x="weekday",
            y="appointment_count",
            title="Weekday Appointment Distribution",
            labels={"weekday": "Day of Week", "appointment_count": "Appointments"},
            color="weekday",
            color_discrete_sequence=colors,
        )
        fig_weekday.update_layout(
            showlegend=False,
            margin=dict(l=20, r=20, t=40, b=20),
            height=360,
        )
        st.plotly_chart(fig_weekday, use_container_width=True)

    # -----------------------------------------------------------------------
    # Hourly Registration Rush & Activity Volume Breakdown
    # -----------------------------------------------------------------------
    st.markdown("### ⏰ Daily Registration Rush & Service Utilization")
    row3_left, row3_right = st.columns([5, 5])

    with row3_left:
        hourly_df = load_temporal_hourly()
        fig_hourly = px.bar(
            hourly_df,
            x="hour_of_day",
            y="appointment_count",
            title="Hourly Registration Pattern (24-Hour Profile)",
            labels={"hour_of_day": "Hour of Arrival (24h)", "appointment_count": "Registrations"},
            color="appointment_count",
            color_continuous_scale="Teal",
        )
        fig_hourly.update_layout(
            coloraxis_showscale=False,
            margin=dict(l=20, r=20, t=40, b=20),
            height=340,
        )
        st.plotly_chart(fig_hourly, use_container_width=True)
        st.caption(
            "💡 **Early Morning Intake Peak**: Over 38% of daily registrations occur between "
            "05:00 AM and 08:00 AM, with peak arrival at 06:00 AM (6,208 patients)."
        )

    with row3_right:
        act_df = load_activity_frequencies()
        count_col = "event_count" if "event_count" in act_df.columns else "absolute_frequency"
        pct_col = "case_coverage_percent" if "case_coverage_percent" in act_df.columns else "case_percentage"
        fig_act = px.bar(
            act_df,
            x=pct_col,
            y="activity",
            orientation="h",
            title="Clinical Service Case Coverage (%)",
            labels={pct_col: "Case Coverage (%)", "activity": "Activity"},
            color=pct_col,
            color_continuous_scale="Blues",
            text=pct_col,
        )
        fig_act.update_traces(texttemplate="%{text:.1f}%", textposition="inside")
        fig_act.update_layout(
            coloraxis_showscale=False,
            yaxis={"autorange": "reversed"},
            margin=dict(l=20, r=20, t=40, b=20),
            height=340,
        )
        st.plotly_chart(fig_act, use_container_width=True)
        st.caption(
            "💡 **Service Mix**: 100% of visits completed Doctor Consultation; 19.8% ordered Laboratory, "
            "10.7% ordered Imaging, and 3.2% fulfilled Pharmacy Dispensing."
        )

    # -----------------------------------------------------------------------
    # Executive Summary Card
    # -----------------------------------------------------------------------
    st.info(
        "**Executive Takeaway**: Outpatient operations demonstrate high standardisation, "
        "with **78.53%** of all encounters following the linear two-step consultation pathway "
        "(`Appointment Registration` → `Doctor Consultation & Prescription`). Peak demand is concentrated "
        "on Mondays (20.1%) and during early morning hours (05:00–08:00 AM), indicating opportunities for "
        "staggered queue management and digital pre-registration."
    )
