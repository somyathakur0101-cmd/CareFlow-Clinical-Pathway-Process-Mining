"""Page 2: Patient and Appointment Analysis (EDA).

Presents patient visit frequency distribution using anonymized labels,
appointment volume trends, arrival patterns, and key exploratory findings.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from .data_loader import (
    load_patient_visits,
    load_temporal_monthly,
    load_temporal_weekday,
    load_temporal_hourly,
)


def render():
    """Render Patient and Appointment Analysis Page."""
    st.markdown("## 👥 Patient & Appointment Exploratory Analysis")
    st.markdown(
        "Explores patient return patterns, encounter volume trends, and scheduling dynamics. "
        "All data is strictly anonymized and aggregated in compliance with clinical privacy standards."
    )

    # -----------------------------------------------------------------------
    # Top Demographics Summary
    # -----------------------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Patients", "39,442", help="Unique individuals evaluated.")
    with c2:
        st.metric("Total Appointments", "49,912", help="Outpatient encounters completed.")
    with c3:
        st.metric("Mean Visits / Patient", "1.27", help="Average outpatient visits per patient.")
    with c4:
        st.metric("Repeat Visit Rate", "18.05%", help="Patients with 2 or more outpatient appointments.")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Finding 1: Patient Visit Frequency Distribution
    # -----------------------------------------------------------------------
    st.markdown("### 🔍 Finding 1: Single vs. Repeat Visit Cohort Structure")
    st.markdown(
        "Analysis of patient return frequency reveals a predominantly single-encounter outpatient service model, "
        "accompanied by an active chronic disease / return consultation segment."
    )

    pv_df = load_patient_visits()

    col_pie, col_bar = st.columns([5, 5])
    with col_pie:
        # Group 5+ visits for clean pie chart
        pie_labels = [f"{row['visits_count']} Visit" if row['visits_count'] == 1 else f"{row['visits_count']} Visits" for _, row in pv_df.head(4).iterrows()]
        pie_values = [row['patient_count'] for _, row in pv_df.head(4).iterrows()]
        other_sum = pv_df.iloc[4:]['patient_count'].sum()
        pie_labels.append("5+ Visits (Chronic/Frequent)")
        pie_values.append(other_sum)

        fig_pie = px.pie(
            names=pie_labels,
            values=pie_values,
            title="Patient Visit Frequency Breakdown",
            color_discrete_sequence=["#1e3d59", "#17b978", "#386cb0", "#e7298a", "#e6ab02"],
            hole=0.45,
        )
        fig_pie.update_traces(textinfo="percent+label", textposition="outside")
        fig_pie.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20), height=350)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        fig_pv = px.bar(
            pv_df.head(6),
            x="visits_count",
            y="patient_count",
            text="patient_count",
            title="Patient Count by Number of Visits (Anonymized)",
            labels={"visits_count": "Visits Completed", "patient_count": "Patient Count"},
            color="patient_count",
            color_continuous_scale="Viridis",
        )
        fig_pv.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_pv.update_layout(coloraxis_showscale=False, margin=dict(l=20, r=20, t=40, b=20), height=350)
        st.plotly_chart(fig_pv, use_container_width=True)

    st.caption(
        "📊 **Cohort Finding 1 Breakdown**: "
        "**32,322 patients (81.95%)** visited exactly once. **7,120 patients (18.05%)** returned for multiple visits: "
        "5,067 returned twice (12.85%), 1,317 returned three times (3.34%), and 736 patients had 4 to 11 visits."
    )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Finding 2: Temporal Arrival Patterns
    # -----------------------------------------------------------------------
    st.markdown("### 🔍 Finding 2: Weekly & Diurnal Arrival Clustering")
    col_day, col_hour = st.columns([5, 5])

    with col_day:
        weekday_df = load_temporal_weekday()
        weekday_df["percentage"] = (weekday_df["appointment_count"] / weekday_df["appointment_count"].sum() * 100).round(2)
        fig_w = px.bar(
            weekday_df,
            x="weekday",
            y="appointment_count",
            text="percentage",
            title="Appointment Encounters by Day of Week",
            labels={"weekday": "Weekday", "appointment_count": "Appointments"},
            color="appointment_count",
            color_continuous_scale="Purples",
        )
        fig_w.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_w.update_layout(coloraxis_showscale=False, margin=dict(l=20, r=20, t=40, b=20), height=340)
        st.plotly_chart(fig_w, use_container_width=True)

    with col_hour:
        hourly_df = load_temporal_hourly()
        fig_h = px.line(
            hourly_df,
            x="hour_of_day",
            y="appointment_count",
            markers=True,
            title="Hourly Registration Curve (00:00 – 23:00)",
            labels={"hour_of_day": "Arrival Hour", "appointment_count": "Registrations"},
            color_discrete_sequence=["#d95f02"],
        )
        fig_h.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=340)
        fig_h.add_vrect(x0=5, x1=8, fillcolor="rgba(217, 95, 2, 0.15)", line_width=0, annotation_text="Morning Surge (38%)", annotation_position="top left")
        st.plotly_chart(fig_h, use_container_width=True)

    st.caption(
        "📊 **Cohort Finding 2 Breakdown**: "
        "**Mondays represent the highest workload (10,042 visits, 20.12%)**, followed by Tuesday (17.11%). "
        "Volume declines steadily toward Friday (14.66%) and weekend urgent sessions (Sunday: 4.43%). "
        "Diurnally, the registration desks encounter severe queue congestion between 05:00 AM and 08:00 AM."
    )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Finding 3: Diagnostic and Therapeutic Service Mix
    # -----------------------------------------------------------------------
    st.markdown("### 🔍 Finding 3: Clinical Diagnostic & Dispensing Pathways")
    st.markdown(
        "Every patient encounter begins with administrative intake and proceeds to physician consultation. "
        "Downstream clinical routing diverges into diagnostic and therapeutic branches."
    )

    serv_data = [
        {"Service": "Doctor Consultation & Prescription", "Cases": 49912, "Percentage": 100.0, "Role": "Mandatory Primary Evaluation"},
        {"Service": "Laboratory Examination", "Cases": 9866, "Percentage": 19.77, "Role": "Diagnostic Pathology (Blood, Urine)"},
        {"Service": "Imaging Procedure", "Cases": 5351, "Percentage": 10.72, "Role": "Diagnostic Radiology (X-Ray, USG)"},
        {"Service": "Pharmacy Dispensing", "Cases": 1608, "Percentage": 3.22, "Role": "Medication Fulfillment"},
    ]
    serv_df = pd.DataFrame(serv_data)

    fig_serv = px.funnel(
        serv_df,
        y="Service",
        x="Cases",
        title="Clinical Service Cascade (Encounter Reach)",
        color="Service",
        color_discrete_sequence=["#1e3d59", "#17b978", "#386cb0", "#e7298a"],
    )
    fig_serv.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=300)
    st.plotly_chart(fig_serv, use_container_width=True)

    st.caption(
        "📊 **Cohort Finding 3 Breakdown**: "
        "While 100% of cases receive doctor evaluation, only 19.77% require laboratory tests and 10.72% require imaging. "
        "Only 3.22% of visits recorded on-site pharmacy dispensing, reflecting either outside pharmacy fulfillment "
        "or paper prescription hand-offs."
    )

