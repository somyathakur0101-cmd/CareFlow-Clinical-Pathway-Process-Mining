"""CareFlow Clinical Pathway Process Mining Dashboard.

Main Streamlit Application.
Provides interactive visual analytics across 5 comprehensive clinical pages:
1. Executive Overview
2. Patient and Appointment Analysis
3. Process Discovery (DFG, Petri Net, Variants)
4. Bottleneck and Waiting-Time Analysis
5. Conformance Checking and Sequence Deviations

PRIVACY GUARANTEE:
Loads strictly aggregated, anonymized metrics. Zero patient IDs or case IDs.
"""

import os
import sys
import streamlit as st

# Ensure project root is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dashboard.components import (
    page_executive,
    page_patient_eda,
    page_process_discovery,
    page_bottleneck,
    page_conformance,
)

# ---------------------------------------------------------------------------
# Streamlit App Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CareFlow – Clinical Pathway Process Mining",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Healthcare Analytics Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Global layout & typography */
    .main .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
    }
    
    /* Healthcare Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 1rem 1.2rem;
        border-radius: 0.6rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetric"]:hover {
        border-color: #cbd5e1;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    div[data-testid="stMetricLabel"] > div {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    div[data-testid="stMetricValue"] > div {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #1e3d59 !important;
    }
    
    /* Header decoration */
    .careflow-header {
        background: linear-gradient(135deg, #1e3d59 0%, #17b978 100%);
        color: white;
        padding: 1.2rem 1.5rem;
        border-radius: 0.6rem;
        margin-bottom: 1.5rem;
    }
    .careflow-header h1 {
        color: white !important;
        margin: 0;
        font-size: 1.9rem;
        font-weight: 700;
    }
    .careflow-header p {
        color: #e2e8f0;
        margin: 0.3rem 0 0 0;
        font-size: 0.95rem;
    }

    /* Sidebar polish */
    section[data-testid="stSidebar"] {
        background-color: #f1f5f9;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Privacy badge */
    .privacy-badge {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 0.5rem 0.8rem;
        border-radius: 0.4rem;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid #bae6fd;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar Navigation & Filter Controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏥 CareFlow Analytics")
    st.markdown("**Clinical Pathway Process Mining**")
    st.markdown("---")

    page_selection = st.radio(
        "Navigation Menu:",
        [
            "1. Executive Overview",
            "2. Patient & Appointment EDA",
            "3. Process Discovery",
            "4. Bottleneck Analysis",
            "5. Conformance Checking",
        ],
        index=0,
    )

    st.markdown("---")
    st.markdown("#### ⚙️ Global Pathway Filter")
    flow_filter = st.selectbox(
        "Clinical Flow Filter:",
        [
            "All Flows (Full Cohort N=49,912)",
            "Flow 1: Appointment -> Prescription (79.47%)",
            "Flow 2: Appointment -> Prescription -> Lab (9.69%)",
            "Flow 3: Appointment -> Prescription -> Imaging (7.58%)",
            "Flow 4: Appointment -> Prescription -> Pharmacy (0.19%)",
            "Flow 5: Appointment -> Prescription -> Lab + Imaging (3.04%)",
            "Flow 6: Appointment -> Prescription -> Lab + Pharmacy (0.03%)",
            "Flow 7: Appointment -> Prescription -> Imaging + Pharmacy (0.00%)",
        ]
    )

    st.markdown("---")
    st.markdown("#### 🔒 Privacy & Compliance")
    st.markdown(
        "<div class='privacy-badge'>"
        "🛡️ <b>HIPAA & Anonymity Safe</b><br>"
        "Operating strictly on aggregated analytical outputs. "
        "Zero patient-level identifiers or encounter records are accessible."
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.caption("CareFlow Process Mining System v1.0\nAuthor: Giri Charan")

# ---------------------------------------------------------------------------
# Main Page Router
# ---------------------------------------------------------------------------
if page_selection == "1. Executive Overview":
    page_executive.render()
elif page_selection == "2. Patient & Appointment EDA":
    page_patient_eda.render()
elif page_selection == "3. Process Discovery":
    page_process_discovery.render()
elif page_selection == "4. Bottleneck Analysis":
    page_bottleneck.render()
elif page_selection == "5. Conformance Checking":
    page_conformance.render()

