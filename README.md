# CareFlow – Clinical Pathway Process Mining & Analytics Platform

A comprehensive healthcare process mining, operational bottleneck analysis, and clinical pathway intelligence platform built with **Python**, **PM4Py**, **Pandas**, **Streamlit**, and **Plotly**. 

CareFlow normalizes large-scale Outpatient Department (OPD) electronic health records, reconstructs clinical event logs, discovers directly-follows and Petri net workflow models, quantifies departmental turnaround times, performs token-based replay conformance checking, and delivers interactive multi-page dashboards and Power BI integration.

---

## 📋 Executive Overview & Problem Statement

Modern hospital outpatient operations face significant challenges in patient waiting times, departmental synchronization, and sequence compliance. CareFlow applies process mining algorithms to empirical hospital records (62,422 source encounter rows across 49,912 appointments, 39,442 patients, and 123,969 clinical events) to solve key operational questions:

1. **Pathway Standardization**: What are the actual care paths patients follow between registration, consultation, diagnostics (lab/imaging), and pharmacy dispensing?
2. **Operational Bottlenecks**: Where do the longest waiting intervals occur, and what are the true turnaround times (TAT) for pathology and radiology?
3. **Clinical Guideline Conformance**: How frequently do actual hospital practices deviate from normative expectations (e.g. walk-in diagnostics before physician consultation)?
4. **Data Integrity & Traceability**: How can messy hospital timestamps (simultaneous order entries, inverted timestamps, open orders) be audited rigorously without fabricating data?

```
Hospital OPD Raw Records (62,422 rows)
       │
       ▼
Data Cleaning & Quality Auditing (Rules 1–9)
       │
       ▼
Event-Log Extraction & Normalization (`process_mining/event_log.py`)
       │
       ├── IEEE 1849-2016 Compliant Event Log (123,969 events, 49,912 cases, 5 activities)
       │
       ├─────────────────────────────────┬─────────────────────────────────┐
       ▼                                 ▼                                 ▼
Process Discovery               Bottleneck Analysis               Conformance Checking
(`process_mining/`              (`process_mining/`                (`process_mining/`
 `process_discovery.py`)         `bottleneck_analysis.py`)         `conformance_checking.py`)
├── DFG (20 edges, 74,057 T)    ├── Transition Waiting Times      ├── PM4Py Token Replay (100% Fit)
├── Petri Net (17P/21T/48A)     ├── Lab TAT (125 min median)      ├── Model Precision (79.14%)
├── 287 Process Variants        ├── Imaging TAT (3 min median)    ├── Sequence Deviations (18 types)
└── Publication Maps (PNG/SVG)  ├── 7 Clinical Flows Analysis     └── Cross-Flow Conformance Matrix
                                └── Data Quality Timestamp Audit
       │
       ├─────────────────────────────────┬─────────────────────────────────┐
       ▼                                 ▼                                 ▼
Interactive Streamlit Dashboard   Power BI Data Exports             Automated Test Suite
(`dashboard/app.py` - 5 Pages)    (`outputs/power_bi/` - 9 CSVs)    (`tests/` - 134 Tests, 100% Pass)
```

---

## 🛠️ Technology Stack

- **Core Analytics**: Python 3.10+, Pandas, NumPy
- **Process Mining**: PM4Py (Process Mining for Python) 2.7+
- **Interactive Dashboard**: Streamlit, Plotly Express & Graph Objects
- **Visualization & Export**: Matplotlib, NetworkX, Graphviz
- **Business Intelligence**: Microsoft Power BI Desktop (Star Schema datasets, DAX measures)
- **Automated Quality Testing**: Python standard `unittest` (134 automated tests)

---

## 📁 Repository Structure

```
CareFlow-Clinical-Pathway-Process-Mining/
├── CareFlow_Cleaning_Review_v2 (1).txt       # Cleaning review & discrepancy reconciliation
├── CareFlow_Dataset_Schema (2).csv           # Formal dataset schema definitions
├── CareFlow_Member1_Dataset_Understanding.md # Field definitions and data dictionary
├── Giri_Patient_Appointment_EDA/             # Exploratory Data Analysis by Giri Charan
│   ├── Patient_and_Appointment_EDA[1].ipynb  # Jupyter EDA analysis notebook
│   ├── findings-report[1].docx               # Clinical and operational findings report
│   ├── chart1_patient_visit_frequency[1].png # Anonymized patient visit distribution
│   ├── chart2_monthly_appointments[1].png    # Monthly encounter volume trends
│   ├── chart3_top10_patients[1].png          # Anonymized top utilization distribution
│   └── chart4_weekday_appointments[1].png    # Day-of-week load analysis
├── process_mining/                           # Core Process Mining Python Modules
│   ├── __init__.py                           # Package exports
│   ├── event_log.py                          # IEEE 1849 event log extraction & validation
│   ├── process_discovery.py                  # DFG, Variants, and Inductive Miner Petri Net
│   ├── bottleneck_analysis.py                # Inter-event wait times, Lab/Imaging TAT, DQ audit
│   └── conformance_checking.py              # Token-based replay, precision, deviation analysis
├── dashboard/                                # Interactive Streamlit Web Application
│   ├── app.py                                # Main multi-page Streamlit orchestrator
│   ├── README.md                             # Dashboard architecture and navigation guide
│   ├── POWER_BI_GUIDE.md                     # Power BI Desktop import and DAX guide
│   ├── requirements.txt                      # Dashboard dependencies
│   └── components/                           # Modular page components
│       ├── __init__.py
│       ├── data_loader.py                    # Cached, privacy-safe aggregate data loader
│       ├── page_executive.py                 # Page 1: Executive Healthcare Overview
│       ├── page_patient_eda.py               # Page 2: Patient & Appointment Analysis
│       ├── page_process_discovery.py         # Page 3: Process Discovery (DFG, Petri Net, Variants)
│       ├── page_bottleneck.py                # Page 4: Bottleneck & Waiting-Time Analysis
│       └── page_conformance.py               # Page 5: Conformance Checking & Deviations
├── outputs/                                  # Verified Aggregate Analytical Deliverables
│   ├── activity_frequency.csv                # Event counts and case reach percentages
│   ├── start_end_activities.csv              # Intake and exit boundary distribution
│   ├── transition_frequencies.csv            # DFG transition frequencies
│   ├── process_variants.csv                  # 287 process pathways with Pareto coverage
│   ├── transition_time_analysis.csv          # Statistical duration metrics for all 20 edges
│   ├── bottleneck_summary.csv                # Turnaround times and data quality audit summary
│   ├── bottleneck_analysis_report.md         # Formal bottleneck analytical report
│   ├── conformance_summary.csv               # PM4Py replay fitness and precision scorecard
│   ├── deviation_analysis.csv                # 18 clinical sequence deviation categories
│   ├── conformance_report.md                 # Formal conformance checking report
│   ├── careflow_dfg.png (.svg)               # High-resolution Directly-Follows Graph map
│   ├── careflow_petri_net.png (.svg)         # Discovered Inductive Miner Petri Net map
│   ├── careflow_variants.png (.svg)          # Top process variants volume chart
│   ├── careflow_transition_times.png (.svg)  # Mean vs median transition wait times
│   ├── careflow_slow_transitions.png (.svg)  # Top slowest observed pathway bottlenecks
│   ├── careflow_lab_turnaround.png (.svg)    # Laboratory TAT boxplot & distribution
│   ├── careflow_imaging_turnaround.png (.svg)# Imaging TAT distribution chart
│   ├── careflow_activity_durations.png (.svg)# Activity duration comparison chart
│   ├── conformance_visualization.png (.svg)  # 4-panel conformance visual dashboard
│   ├── eda_temporal_monthly.csv              # 24-month longitudinal volume trend
│   ├── eda_temporal_weekday.csv              # Day-of-week arrival volume
│   ├── eda_temporal_hourly.csv               # 24-hour diurnal registration profile
│   ├── eda_patient_visits.csv                # Single vs multi-visit distribution
│   └── power_bi/                             # Star Schema CSV Exports for Power BI Desktop
│       ├── CareFlow_PowerBI_KPIs.csv
│       ├── CareFlow_PowerBI_Monthly_Trends.csv
│       ├── CareFlow_PowerBI_Weekday_Distribution.csv
│       ├── CareFlow_PowerBI_Patient_Visits.csv
│       ├── CareFlow_PowerBI_Activities.csv
│       ├── CareFlow_PowerBI_Transitions.csv
│       ├── CareFlow_PowerBI_Variants.csv
│       ├── CareFlow_PowerBI_Deviations.csv
│       └── CareFlow_PowerBI_Clinical_Flows.csv
├── tests/                                    # Automated Unit & Integration Test Suite
│   ├── test_event_log.py                     # 9 tests: Event log extraction and rules
│   ├── test_process_discovery.py             # 67 tests: DFG, variants, Petri net soundness
│   ├── test_bottleneck_analysis.py           # 36 tests: Wait times, TAT, DQ audit, privacy
│   ├── test_conformance_checking.py          # 11 tests: PM4Py TBR, precision, deviations
│   └── test_dashboard.py                     # 11 tests: Dashboard data loaders and privacy
├── CareFlow-final-staged-backup.patch        # Non-destructive Git safety backup patch
└── README.md                                 # This comprehensive platform guide
```

---

## 🔬 Core Modules & Analytical Findings

### 1. Event Log Generation (`process_mining/event_log.py`)
- Normalizes raw OPD records into an **IEEE 1849-2016** compliant event log.
- Enforces strict data reconciliation rules:
  - **Rule 1–3**: Unique case indexing by appointment date and patient identifier.
  - **Rule 4–7**: Sequential timestamp ordering with synthetic index tie-breaking for simultaneous events.
  - **Rule 8**: Retains 12 orders with missing start timestamps as valid completions without fabricating start times (`lifecycle='complete'`).
  - **Rule 9**: Preserves 49 inverted prescription timestamps with raw values in source audit columns, blanking duration to prevent negative intervals.
- Generates 123,969 valid clinical events across 49,912 cases and 5 distinct activities.

### 2. Process Discovery (`process_mining/process_discovery.py`)
- Discovers the **Directly-Follows Graph (DFG)** with 20 distinct edges and 74,057 intra-case transitions.
- Identifies **287 distinct process variants**:
  - `VAR_001` (`Appointment Registration` $\rightarrow$ `Doctor Consultation & Prescription`): 39,197 cases (**78.53%**).
  - Top 10 variants cover **93.40%** of all patient encounters.
- Builds a sound Inductive Miner Petri net with **17 places**, **21 transitions** (5 visible, 16 silent $\tau$ routing transitions), and **48 arcs**.

### 3. Bottleneck Analysis (`process_mining/bottleneck_analysis.py`)
- **Laboratory Turnaround Time (TAT)**: Evaluated on 13,175 verified bounded orders (excludes 4,631 unparseable/open orders). Median TAT is **125.0 minutes** (2h 05m), with a 90th percentile (P90) of **470.0 minutes** (7h 50m).
- **Imaging Turnaround Time (TAT)**: Evaluated on 5,412 bounded procedures. Median TAT is **3.0 minutes** (P90 of 13.0 minutes), reflecting prompt diagnostic acquisition.
- **Top Observed Inter-Activity Bottlenecks**:
  - `Appointment Registration` $\rightarrow$ `Doctor Consultation`: Median **48.0 minutes** (P90: 178.0 minutes; N=48,846).
  - `Doctor Consultation` $\rightarrow$ `Imaging Procedure`: Median **42.0 minutes** (P90: 136.0 minutes; N=3,425).
  - `Doctor Consultation` $\rightarrow$ `Laboratory Examination`: Median **26.0 minutes** (P90: 77.0 minutes; N=15,867).
- **Data Quality Audit**: Confirms **0 negative intervals**, 11,502 simultaneous batch order entries (0 min delta), and 1.63% cross-day multi-session encounters (> 24 hours).

### 4. Conformance Checking (`process_mining/conformance_checking.py`)
- **PM4Py Token-Based Replay (TBR)**: Replays all 49,912 cases with **1.0000 Log Fitness** ($100.0\%$), **0.7914 Precision**, and **0.8836 F-Measure** against the data-derived Petri net.
- **Critical Reference Model Scope**: The reference Petri net is an *empirical data-derived model*, NOT an approved clinical medical guideline. $100\%$ replay fitness confirms that the model captures all historical hospital variations; it does NOT imply $100\%$ medical guideline compliance.
- **Clinical Sequence Deviation Analysis**:
  - **Pre-Consultation Diagnostics**: 2,324 cases (**4.66%**) had diagnostic testing recorded before physician consultation (1,915 Imaging, 498 Laboratory; driven by walk-in X-rays and fasting blood draws).
  - **Activity Repetition / Multi-Order Loops**: 4,819 cases (**9.65%**) exhibited repeated activities within the same visit (4,107 Laboratory multi-test panels, 640 Doctor re-consultations, 98 repeat Imaging scans, 79 Pharmacy split dispensings).
  - **Registration Not First**: 418 cases (**0.84%**) had clinical orders timestamped prior to recorded reception desk intake.
  - **Incomplete Traces**: **0 cases** (0.00% dropouts; every encounter completed both registration and doctor consultation).

---

## 💻 Interactive Streamlit Dashboard

CareFlow features a modern healthcare analytics web application (`dashboard/app.py`) divided into 5 interactive pages:

1. **🏥 Executive Overview**: High-level KPI scorecards, longitudinal monthly trends (peak: Oct 2025 with 7,703 visits), day-of-week load (Monday peak: 10,042 visits, 20.12%), and diurnal registration rush hour profile (peak at 06:00 AM).
2. **👥 Patient & Appointment Analysis**: Anonymized patient visit distribution (81.95% single-visit vs 18.05% multi-visit cohort), appointment cascade, and exploratory findings.
3. **🔍 Process Discovery**: High-res DFG and Petri Net process maps, interactive transition filter table, Pareto variant analysis, and start/end boundary points.
4. **⏱️ Bottleneck Analysis**: Departmental TAT comparisons (Laboratory vs Imaging), slowest pathway transitions (median & P90), and timestamp audit metrics.
5. **⚖️ Conformance Checking**: Prominent clinical interpretation callouts, token replay fitness vs precision, cross-flow compliance matrix (Flows 1–7), and empirical sequence deviation explorer.

### Running the Dashboard
```bash
# 1. Install dependencies
pip install -r dashboard/requirements.txt

# 2. Launch Streamlit
streamlit run dashboard/app.py
```
*Accessible locally at `http://localhost:8501`.*

---

## 📊 Microsoft Power BI Integration

CareFlow includes 9 pre-aggregated, star-schema-ready CSV files in `outputs/power_bi/` for Microsoft Power BI Desktop.

For detailed importing instructions, relational schema diagrams, and DAX measure formulas, see [dashboard/POWER_BI_GUIDE.md](file:///c:/Users/GIRI%20CHARAN/OneDrive/Desktop/CareFlow-Clinical-Pathway-Process-Mining-giricharan525-debug/dashboard/POWER_BI_GUIDE.md).

> [!NOTE]
> Power BI Desktop dataset files and DAX guide are fully prepared and validated. Cloud deployment to Power BI Service requires institutional tenant credentials.

---

## 🔒 Data Privacy & HIPAA Compliance

1. **Strict Data Minimization**: No raw patient-level datasets (`HospitalOPD_CareFlow_cleaned_v4.xlsx`), patient event logs (`careflow_event_log.csv`), or case summaries are tracked or committed.
2. **Zero Identifier Exposure**: All public outputs in `outputs/`, `dashboard/`, and `outputs/power_bi/` contain strictly aggregated statistics. Zero patient IDs (`patient_id`), case IDs (`case_id`), or prefix markers (`PAT_`, `ENC_`) are exposed.
3. **Automated Privacy Verification**: Automated unit tests (`test_privacy_assurance`) verify every CSV export before publishing.

---

## 🧪 Automated Testing & Verification

The project includes **134 automated unit and integration tests** with **100% pass rate**:

```bash
# Run the complete test suite
python -m unittest discover -s tests -v

# Run individual module test suites
python -m unittest tests.test_event_log -v          # 9 tests
python -m unittest tests.test_process_discovery -v  # 67 tests
python -m unittest tests.test_bottleneck_analysis -v # 36 tests
python -m unittest tests.test_conformance_checking -v # 11 tests
python -m unittest tests.test_dashboard -v          # 11 tests
```

**Test Execution Summary**:
- **Total Tests**: 134
- **Passed**: 134
- **Failed**: 0
- **Execution Time**: ~42.8 seconds

---

## 🚀 Execution & Quick Start Guide

### Step 1: Environment Setup
```bash
# Clone the repository
git clone -b giricharan525-debug https://github.com/somyathakur0101-cmd/CareFlow-Clinical-Pathway-Process-Mining.git
cd CareFlow-Clinical-Pathway-Process-Mining

# Install required Python packages
pip install streamlit plotly pandas numpy pm4py matplotlib networkx
```

### Step 2: Regenerate Process Mining Outputs (Optional)
```bash
# 1. Event Log Generation & Validation
python process_mining/event_log.py

# 2. Process Discovery (DFG, Petri Net, Variants)
python process_mining/process_discovery.py

# 3. Bottleneck & Waiting-Time Analysis
python process_mining/bottleneck_analysis.py

# 4. Conformance Checking Pipeline
python process_mining/conformance_checking.py
```

### Step 3: Run Interactive Dashboard
```bash
streamlit run dashboard/app.py
```

---

## ⚠️ Methodological Limitations

1. **Empirical Reference Model**: The discovered Petri net model reflects historical operational practice, including existing hospital bottlenecks, batch order entries, and workflow quirks, rather than ideal clinical guidelines.
2. **Timestamp Granularity**: Multiple diagnostic tests ordered within the same minute share identical recorded timestamps; intra-minute sequencing is governed by event index tie-breaking rather than physical clinical succession.
3. **Absence of Clinical Outcomes**: Sequence variations (such as pre-consultation X-rays or diagnostic repeats) reflect operational routing and cannot be labeled as medical errors without clinical outcome and patient safety metrics.

---

*CareFlow Platform developed by Giri Charan for the Clinical Pathway Process Mining Project.*
