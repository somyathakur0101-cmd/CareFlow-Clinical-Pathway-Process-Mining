# CareFlow Interactive Clinical Pathway Dashboard

A comprehensive, interactive web dashboard built with **Python**, **Streamlit**, and **Plotly** for exploring outpatient healthcare process mining results, clinical pathway variants, operational bottlenecks, and conformance checking.

---

## Architecture & Page Overview

The dashboard is structured into five dedicated analytical modules accessible via the sidebar navigation:

1. **Page 1: Executive Overview (`dashboard/components/page_executive.py`)**
   - High-level KPI metric cards: 39,442 unique patients, 49,912 appointments, 123,969 recorded events, 5 clinical activities.
   - Interactive monthly volume trend (April 2024 to April 2026) with peak month callouts.
   - Weekday appointment volume distribution (Monday surge: 20.12%, Sunday urgent care: 4.43%).
   - Hourly registration profile highlighting early morning intake peaks (05:00–08:00 AM).

2. **Page 2: Patient & Appointment Analysis (`dashboard/components/page_patient_eda.py`)**
   - Anonymized patient visit frequency analysis (81.95% single-visit vs 18.05% multi-visit cohort).
   - Diurnal and weekly scheduling dynamics.
   - Clinical service demand cascade: Consultation (100%), Lab (19.8%), Imaging (10.7%), Pharmacy (3.2%).
   - Detailed operational findings on patient return behavior.

3. **Page 3: Process Discovery (`dashboard/components/page_process_discovery.py`)**
   - High-resolution Directly-Follows Graph (DFG) and Inductive Miner Petri Net model views.
   - Interactive transition frequency table with volume and wait-time filtering.
   - Pareto analysis of the top process variants (VAR_001 = 78.53%; Top 10 variants = 93.4%).
   - Start and end activity distributions (99.16% start at Registration; 83.37% exit at Consultation).

4. **Page 4: Bottleneck Analysis (`dashboard/components/page_bottleneck.py`)**
   - Departmental turnaround times: Laboratory (median 125.0 min, bounded N=13,175) vs. Imaging (median 3.0 min, bounded N=5,412).
   - Slowest observed inter-event transitions with Median and 90th percentile comparisons.
   - Data quality audit summary (0 negative intervals, 11,502 simultaneous events, 4,631 missing lab completion times, 49 inverted prescriptions).
   - Clear clinical distinction between observed waiting time and active treatment delay.

5. **Page 5: Conformance Checking (`dashboard/components/page_conformance.py`)**
   - **Crucial Clinical Interpretation Notice**: Explicit documentation that the Petri net is an empirical, data-derived reference model, not an approved medical guideline.
   - PM4Py Token-Based Replay metrics: 100.0% replay fitness, 79.14% precision, 88.36% F-measure.
   - Cross-flow compliance comparison across Clinical Flows 1 through 7.
   - Interactive sequence deviation explorer (2,324 pre-consultation diagnostics, 4,819 activity loops, 418 delayed registrations).

---

## Privacy & Security Compliance

- **Zero Patient Identifiers**: The dashboard operates **exclusively** on pre-computed aggregate tables and summary files.
- No patient IDs (`patient_id`), encounter numbers (`case_id`), or identifiable clinical records are ever loaded or rendered in the web interface.
- Fully compliant with healthcare data minimization and HIPAA de-identification principles.

---

## Quick Start & Execution

### 1. Install Dependencies
```bash
pip install -r dashboard/requirements.txt
```

### 2. Launch the Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```

The application will start locally at `http://localhost:8501`.

### 3. Run Automated Dashboard Tests
```bash
python -m unittest tests.test_dashboard -v
```

---

## Power BI Integration

For Microsoft Power BI Desktop users, 9 pre-aggregated CSV datasets and a comprehensive implementation guide are provided in `outputs/power_bi/` and `dashboard/POWER_BI_GUIDE.md`.

