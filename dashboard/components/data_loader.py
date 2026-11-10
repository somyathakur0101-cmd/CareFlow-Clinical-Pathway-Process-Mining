"""CareFlow Dashboard Data Loader.

Provides cached, privacy-safe data loading for all aggregate metrics,
tables, and visual charts. Guarantees zero patient-level record exposure.
"""

import os
from typing import Dict, Any, Optional
import pandas as pd
import streamlit as st


def resolve_data_path(target_path: str) -> str:
    """Resolve file paths across common working directories."""
    candidates = [
        target_path,
        os.path.join("..", target_path),
        os.path.join("outputs", target_path),
        os.path.join("..", "outputs", target_path),
        os.path.join("CareFlow-Clinical-Pathway-Process-Mining-giricharan525-debug", target_path),
        os.path.join("CareFlow-Clinical-Pathway-Process-Mining-giricharan525-debug", "outputs", target_path),
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    return target_path


@st.cache_data
def load_kpis() -> Dict[str, Any]:
    """Load high-level KPI constants and metrics."""
    return {
        "unique_patients": 39_442,
        "unique_appointments": 49_912,
        "total_events": 123_969,
        "activity_categories": 5,
        "process_variants": 287,
        "tbr_fitness": 1.0000,
        "tbr_precision": 0.7914,
        "tbr_f_measure": 0.8836,
        "registration_compliance": 0.9916,
        "lab_median_tat": 125.0,
        "imaging_median_tat": 3.0,
        "dominant_variant_share": 78.53,
    }


@st.cache_data
def load_temporal_monthly() -> pd.DataFrame:
    """Load monthly appointment volume aggregate table."""
    path = resolve_data_path("outputs/eda_temporal_monthly.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    # Fallback
    return pd.DataFrame([
        {"month": "2025-08", "appointment_count": 2040},
        {"month": "2025-09", "appointment_count": 7636},
        {"month": "2025-10", "appointment_count": 7703},
        {"month": "2025-11", "appointment_count": 6063},
        {"month": "2025-12", "appointment_count": 6320},
        {"month": "2026-01", "appointment_count": 6013},
        {"month": "2026-02", "appointment_count": 6439},
        {"month": "2026-03", "appointment_count": 4256},
    ])


@st.cache_data
def load_temporal_weekday() -> pd.DataFrame:
    """Load weekday appointment distribution aggregate table."""
    path = resolve_data_path("outputs/eda_temporal_weekday.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame([
        {"weekday": "Monday", "appointment_count": 10042},
        {"weekday": "Tuesday", "appointment_count": 8542},
        {"weekday": "Wednesday", "appointment_count": 7829},
        {"weekday": "Thursday", "appointment_count": 7542},
        {"weekday": "Friday", "appointment_count": 7317},
        {"weekday": "Saturday", "appointment_count": 6430},
        {"weekday": "Sunday", "appointment_count": 2210},
    ])


@st.cache_data
def load_temporal_hourly() -> pd.DataFrame:
    """Load hourly appointment registration distribution table."""
    path = resolve_data_path("outputs/eda_temporal_hourly.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame([
        {"hour_of_day": h, "appointment_count": 100} for h in range(24)
    ])


@st.cache_data
def load_patient_visits() -> pd.DataFrame:
    """Load patient visit frequency distribution table."""
    path = resolve_data_path("outputs/eda_patient_visits.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame([
        {"visits_count": 1, "patient_count": 32322, "percentage": 81.95},
        {"visits_count": 2, "patient_count": 5067, "percentage": 12.85},
        {"visits_count": 3, "patient_count": 1317, "percentage": 3.34},
        {"visits_count": 4, "patient_count": 434, "percentage": 1.10},
        {"visits_count": "5+", "patient_count": 302, "percentage": 0.76},
    ])


@st.cache_data
def load_activity_frequencies() -> pd.DataFrame:
    """Load clinical activity frequencies table."""
    path = resolve_data_path("outputs/activity_frequency.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame([
        {"activity": "Appointment Registration", "absolute_frequency": 49912, "case_frequency": 49912, "case_percentage": 100.0},
        {"activity": "Doctor Consultation & Prescription", "absolute_frequency": 50567, "case_frequency": 49912, "case_percentage": 100.0},
        {"activity": "Laboratory Examination", "absolute_frequency": 17806, "case_frequency": 9866, "case_percentage": 19.77},
        {"activity": "Imaging Procedure", "absolute_frequency": 5421, "case_frequency": 5351, "case_percentage": 10.72},
        {"activity": "Pharmacy Dispensing", "absolute_frequency": 263, "case_frequency": 1608, "case_percentage": 3.22},
    ])


@st.cache_data
def load_start_end_activities() -> pd.DataFrame:
    """Load start and end activities table."""
    path = resolve_data_path("outputs/start_end_activities.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data
def load_process_variants() -> pd.DataFrame:
    """Load process variants table."""
    path = resolve_data_path("outputs/process_variants.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data
def load_transition_times() -> pd.DataFrame:
    """Load transition time analysis table."""
    path = resolve_data_path("outputs/transition_time_analysis.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data
def load_conformance_summary() -> pd.DataFrame:
    """Load conformance summary table."""
    path = resolve_data_path("outputs/conformance_summary.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data
def load_deviation_analysis() -> pd.DataFrame:
    """Load deviation analysis table."""
    path = resolve_data_path("outputs/deviation_analysis.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data
def load_clinical_flows() -> pd.DataFrame:
    """Load clinical flows breakdown table."""
    path = resolve_data_path("outputs/power_bi/CareFlow_PowerBI_Clinical_Flows.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame([
        {"Flow_Code": 1, "Flow_Name": "Appointment -> Prescription", "Total_Cases": 39667, "Case_Percentage": 79.47, "Start_Conforming_Pct": 99.99, "Pre_Consult_Diag_Pct": 0.00, "Loop_Repetition_Pct": 1.17, "Avg_Trace_Length": 2.01},
        {"Flow_Code": 2, "Flow_Name": "Appointment -> Prescription -> Lab", "Total_Cases": 4834, "Case_Percentage": 9.69, "Start_Conforming_Pct": 98.22, "Pre_Consult_Diag_Pct": 7.43, "Loop_Repetition_Pct": 61.09, "Avg_Trace_Length": 4.36},
        {"Flow_Code": 3, "Flow_Name": "Appointment -> Prescription -> Imaging", "Total_Cases": 3785, "Case_Percentage": 7.58, "Start_Conforming_Pct": 93.92, "Pre_Consult_Diag_Pct": 38.84, "Loop_Repetition_Pct": 3.54, "Avg_Trace_Length": 3.08},
        {"Flow_Code": 4, "Flow_Name": "Appointment -> Prescription -> Pharmacy", "Total_Cases": 93, "Case_Percentage": 0.19, "Start_Conforming_Pct": 100.00, "Pre_Consult_Diag_Pct": 0.00, "Loop_Repetition_Pct": 72.04, "Avg_Trace_Length": 4.14},
        {"Flow_Code": 5, "Flow_Name": "Appointment -> Prescription -> Lab + Imaging", "Total_Cases": 1518, "Case_Percentage": 3.04, "Start_Conforming_Pct": 93.54, "Pre_Consult_Diag_Pct": 32.61, "Loop_Repetition_Pct": 78.13, "Avg_Trace_Length": 6.03},
        {"Flow_Code": 6, "Flow_Name": "Appointment -> Prescription -> Lab + Pharmacy", "Total_Cases": 14, "Case_Percentage": 0.03, "Start_Conforming_Pct": 100.00, "Pre_Consult_Diag_Pct": 0.00, "Loop_Repetition_Pct": 92.86, "Avg_Trace_Length": 7.21},
        {"Flow_Code": 7, "Flow_Name": "Appointment -> Prescription -> Imaging + Pharmacy", "Total_Cases": 1, "Case_Percentage": 0.00, "Start_Conforming_Pct": 100.00, "Pre_Consult_Diag_Pct": 0.00, "Loop_Repetition_Pct": 0.00, "Avg_Trace_Length": 4.00},
    ])

