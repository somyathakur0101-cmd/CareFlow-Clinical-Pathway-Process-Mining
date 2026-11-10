# CareFlow – Clinical Pathway Process Mining
# Final Project Completion Report

**Project Title**: CareFlow – Clinical Pathway Process Mining & Bottleneck Analysis  
**Repository**: `https://github.com/somyathakur0101-cmd/CareFlow-Clinical-Pathway-Process-Mining.git`  
**Target Branch**: `giricharan525-debug`  
**Author**: Giri Charan  
**Completion Date**: November 10, 2026  
**Status**: Completed, Fully Integrated, Verified & Submission-Ready  

---

## 1. Executive Summary

This report documents the final completion, end-to-end integration, verification, and automated testing of the **CareFlow – Clinical Pathway Process Mining** internship project.

All core analytical stages—from raw Outpatient Department (OPD) data understanding and IEEE 1849 event log extraction to PM4Py process discovery, operational bottleneck analysis, token-based replay conformance checking, and an interactive 5-page Streamlit web dashboard—have been implemented, empirically validated, and tested.

All **134 automated unit and integration tests** pass with a $100\%$ success rate. Strict privacy guarantees have been enforced: zero patient-level identifiers or sensitive records exist in public outputs or dashboard datasets.

---

## 2. Completed Modules & Deliverables

| # | Development Stage | Module Path | Core Functionality | Status |
|---|---|---|---|---|
| **1** | **Dataset Understanding & Cleaning Review** | `CareFlow_Member1_Dataset_Understanding.md`, `CareFlow_Cleaning_Review_v2 (1).txt` | 62,422 source rows audited; 9 reconciliation rules established; schema and field dictionaries documented. | Completed |
| **2** | **Patient & Appointment EDA** | `Giri_Patient_Appointment_EDA/` | Anonymized patient return analysis (81.95% single-visit vs 18.05% repeat); longitudinal volume trends; weekday load (Monday peak 20.12%); 4 publication charts. | Completed |
| **3** | **Event Log Generation** | `process_mining/event_log.py` | IEEE 1849-2016 compliant event log extraction; 123,969 events across 49,912 appointments and 5 activities; Rule 8/9 timestamp integrity handling. | Completed |
| **4** | **Process Discovery (PM4Py)** | `process_mining/process_discovery.py` | Directly-Follows Graph (DFG – 20 edges, 74,057 transitions); 287 process variants; Inductive Miner Petri Net (17 places, 21 transitions, 48 arcs); PNML export. | Completed |
| **5** | **Bottleneck Analysis** | `process_mining/bottleneck_analysis.py` | Turnaround time (TAT) quantification: Laboratory TAT (median 125.0 min on 13,175 bounded orders), Imaging TAT (median 3.0 min on 5,412 bounded scans); 20 DFG waiting times; DQ audit. | Completed |
| **6** | **Conformance Checking** | `process_mining/conformance_checking.py` | Token-based replay (100% replay fitness); precision (79.14%); harmonic F-measure (88.36%); 18 empirical clinical sequence deviation patterns; cross-flow matrix. | Completed |
| **7** | **Interactive Web Dashboard** | `dashboard/app.py` & `dashboard/components/` | Streamlit + Plotly 5-page dashboard: Executive Overview, Patient EDA, Process Discovery, Bottlenecks, and Conformance Checking with filters and KPI cards. | Completed |
| **8** | **Power BI Integration** | `dashboard/POWER_BI_GUIDE.md`, `outputs/power_bi/` | 9 pre-aggregated Star Schema CSV datasets ready for Power BI Desktop; complete DAX measure formulas and tab visual guide. | Completed |
| **9** | **Automated Testing Suite** | `tests/` | 134 automated unit and integration tests across 5 test suites covering all modules, rules, metrics, and privacy constraints. | Completed |

---

## 3. Implemented Features by Analytical Stage

### A. Data Engineering & Event Log Normalization
- Extracted 123,969 clinical events across 49,912 unique outpatient cases from 62,422 raw records.
- Standardized 5 clinical activities: `Appointment Registration`, `Doctor Consultation & Prescription`, `Laboratory Examination`, `Imaging Procedure`, and `Pharmacy Dispensing`.
- Implemented **Rule 8**: Preserves 12 orders with unrecorded start times as valid completions (`lifecycle='complete'`) without fabricating start times.
- Implemented **Rule 9**: Preserves 49 inverted prescription timestamps with raw values in source audit columns, blanking duration to prevent negative intervals.
- Sorted events chronologically within cases with synthetic event index tie-breaking for simultaneous timestamps.

### B. Process Discovery (PM4Py)
- Discovered Directly-Follows Graph with 20 distinct edges and 74,057 transitions.
- Mined 287 distinct process variants:
  - Top variant `VAR_001` (`Appointment Registration` $\rightarrow$ `Doctor Consultation & Prescription`) represents **39,197 cases (78.53%)**.
  - Top 10 variants collectively account for **93.40%** of all patient encounters.
- Mined sound Inductive Miner Petri Net with 17 places, 21 transitions (5 visible activities, 16 silent $\tau$ routing transitions), and 48 arcs.
- Exported publication-ready maps in PNG and SVG vector formats.

### C. Operational Bottleneck & Turnaround Time Analysis
- **Laboratory Turnaround Time**: Evaluated on 13,175 verified bounded orders (excludes 4,631 unparseable/open orders). Median TAT = **125.0 minutes** (2h 05m), P90 = **470.0 minutes** (7h 50m).
- **Imaging Turnaround Time**: Evaluated on 5,412 bounded procedures. Median TAT = **3.0 minutes**, P90 = **13.0 minutes**.
- **Inter-Event Waiting Times**:
  - `Appointment Registration` $\rightarrow$ `Doctor Consultation`: Median **48.0 min** (P90: 178.0 min; N=48,846).
  - `Doctor Consultation` $\rightarrow$ `Imaging Procedure`: Median **42.0 min** (P90: 136.0 min; N=3,425).
  - `Doctor Consultation` $\rightarrow$ `Laboratory Examination`: Median **26.0 min** (P90: 77.0 min; N=15,867).
- **Data Quality & Timestamp Integrity Audit**: Confirmed **0 negative intervals**, 11,502 simultaneous batch order entries (0 min delta), and 1.63% cross-day multi-session encounters (> 24 hours).
- **Clinical Principle**: Strictly differentiated between elapsed EMR timestamp intervals and active medical treatment delay.

### D. Conformance Checking & Sequence Deviation Analysis
- **Token-Based Replay (TBR)**: Replayed all 49,912 cases with **1.0000 Log Fitness** ($100.0\%$), **0.7914 Precision**, and **0.8836 F-Measure** against the data-derived Petri net.
- **Reference Model Interpretation Notice**: Documented that the reference Petri net is an empirical *data-derived model*, not an approved medical practice guideline. Replay fitness confirms model accuracy; it does not indicate clinical guideline adherence.
- **Clinical Sequence Deviation Analysis**:
  - **Pre-Consultation Diagnostics**: 2,324 cases (**4.66%**) had diagnostic testing recorded before physician consultation (1,915 Imaging, 498 Laboratory; walk-in X-rays and fasting blood draws).
  - **Activity Repetition / Multi-Order Loops**: 4,819 cases (**9.65%**) exhibited repeated activities (4,107 Laboratory multi-test panels, 640 Doctor re-consultations, 98 repeat Imaging scans, 79 Pharmacy split dispensings).
  - **Registration Not First**: 418 cases (**0.84%**) had clinical orders timestamped prior to recorded reception desk intake.
  - **Encounter Completeness**: **0 cases** (0.00% single-event dropouts; every encounter completed both registration and doctor consultation).

### E. Interactive Streamlit Dashboard (`dashboard/app.py`)
- **Page 1: Executive Overview**: High-level KPI cards, longitudinal monthly volume trend (peak: Oct 2025 with 7,703 visits), weekday distribution (Monday peak 20.12%), and diurnal registration rush hour profile (peak at 06:00 AM).
- **Page 2: Patient & Appointment Analysis**: Anonymized patient visit distribution (81.95% single-visit vs 18.05% multi-visit cohort), appointment cascade, and exploratory findings.
- **Page 3: Process Discovery**: High-res DFG and Petri Net process maps, interactive transition filter table, Pareto variant analysis, and start/end boundary points.
- **Page 4: Bottleneck Analysis**: Departmental TAT comparisons (Laboratory vs Imaging), slowest pathway transitions (median & P90), and timestamp audit metrics.
- **Page 5: Conformance Checking**: Prominent clinical interpretation callouts, token replay fitness vs precision, cross-flow compliance matrix (Flows 1–7), and empirical sequence deviation explorer.
- **Design & UX**: Healthcare-themed navy/teal styling, sidebar navigation, responsive metric cards, interactive Plotly charts, and global clinical flow filters.

### F. Power BI Integration
- Prepared 9 star-schema CSV tables in `outputs/power_bi/`.
- Authored `dashboard/POWER_BI_GUIDE.md` with complete relational schema architecture and 5 production-ready DAX measure formulas.

---

## 4. Automated Test Results

The entire project was tested via Python's standard `unittest` framework:

```
Ran 134 tests in 42.804s

OK (100% Pass Rate)
```

### Test Breakdown by Module:

| Test Suite File | Module Under Test | Tests | Status | Execution Time |
|---|---|---|---|---|
| `tests/test_event_log.py` | Event Log Generation & Reconciliation Rules | 9 | **PASS** | ~2.1s |
| `tests/test_process_discovery.py` | DFG, Process Variants, Petri Net Soundness | 67 | **PASS** | ~18.4s |
| `tests/test_bottleneck_analysis.py` | Wait Times, TAT, DQ Audit, Privacy | 36 | **PASS** | ~1.8s |
| `tests/test_conformance_checking.py` | PM4Py TBR, Precision, Deviations, Privacy | 11 | **PASS** | ~18.9s |
| `tests/test_dashboard.py` | Dashboard Data Loaders, Privacy, Power BI | 11 | **PASS** | ~0.1s |
| **Total Automated Tests** | **Full System Regression Suite** | **134** | **100% PASS** | **42.8s** |

---

## 5. Verified Output Files

### Process Discovery & Process Maps:
- `outputs/careflow_dfg.png` & `outputs/careflow_dfg.svg` (601 KB PNG, 93 KB SVG)
- `outputs/careflow_petri_net.png` & `outputs/careflow_petri_net.svg` (954 KB PNG, 78 KB SVG)
- `outputs/careflow_petri_net.pnml` (10 KB XML)
- `outputs/careflow_variants.png` & `outputs/careflow_variants.svg` (405 KB PNG, 170 KB SVG)
- `outputs/process_variants.csv` (76 KB)
- `outputs/activity_frequency.csv` (469 bytes)
- `outputs/start_end_activities.csv` (291 bytes)
- `outputs/transition_frequencies.csv` (1.5 KB)

### Bottleneck Analysis & Charts:
- `outputs/bottleneck_summary.csv` (3.3 KB)
- `outputs/transition_time_analysis.csv` (2.7 KB)
- `outputs/bottleneck_analysis_report.md` (11.4 KB)
- `outputs/careflow_transition_times.png` & `.svg` (302 KB PNG, 108 KB SVG)
- `outputs/careflow_slow_transitions.png` & `.svg` (298 KB PNG, 110 KB SVG)
- `outputs/careflow_lab_turnaround.png` & `.svg` (180 KB PNG, 162 KB SVG)
- `outputs/careflow_imaging_turnaround.png` & `.svg` (143 KB PNG, 71 KB SVG)
- `outputs/careflow_activity_durations.png` & `.svg` (167 KB PNG, 76 KB SVG)

### Conformance Checking & Scorecards:
- `outputs/conformance_summary.csv` (2.5 KB)
- `outputs/deviation_analysis.csv` (4.8 KB)
- `outputs/conformance_report.md` (14.2 KB)
- `outputs/conformance_visualization.png` & `.svg` (510 KB PNG, 273 KB SVG)

### Aggregate EDA & Power BI Datasets:
- `outputs/eda_temporal_monthly.csv`, `outputs/eda_temporal_weekday.csv`, `outputs/eda_temporal_hourly.csv`, `outputs/eda_patient_visits.csv`
- `outputs/power_bi/CareFlow_PowerBI_KPIs.csv`
- `outputs/power_bi/CareFlow_PowerBI_Monthly_Trends.csv`
- `outputs/power_bi/CareFlow_PowerBI_Weekday_Distribution.csv`
- `outputs/power_bi/CareFlow_PowerBI_Patient_Visits.csv`
- `outputs/power_bi/CareFlow_PowerBI_Activities.csv`
- `outputs/power_bi/CareFlow_PowerBI_Transitions.csv`
- `outputs/power_bi/CareFlow_PowerBI_Variants.csv`
- `outputs/power_bi/CareFlow_PowerBI_Deviations.csv`
- `outputs/power_bi/CareFlow_PowerBI_Clinical_Flows.csv`

---

## 6. Dashboard Status & Execution

- **Technology**: Streamlit 1.67.0, Plotly 7.1.0, Pandas 3.1.0.
- **Verification**: All 5 pages (`page_executive`, `page_patient_eda`, `page_process_discovery`, `page_bottleneck`, `page_conformance`) tested in bare execution mode and verified exception-free.
- **Privacy Enforcement**: The dashboard loads strictly pre-computed aggregate files. No patient IDs, case IDs, or raw tables are loaded into memory.

---

## 7. Known Methodological Limitations

1. **Empirical Reference Model**: The discovered Petri net reflects historical operational practices (including existing hospital delays, batch ordering patterns, and administrative habits) rather than an idealized clinical standard.
2. **Timestamp Granularity**: Diagnostic orders entered within the same minute share identical timestamps; sequencing is established by stable synthetic index ordering rather than physical clinical succession.
3. **Absence of Clinical Outcome Data**: Process variations (such as pre-consultation X-rays or repeat laboratory panels) represent operational routing choices and cannot be characterized as clinical errors without linked clinical outcome data.

---

## 8. Exact Commands to Run the Project

### A. Run Automated Unit & Integration Tests:
```powershell
python -m unittest discover -s tests -v
```

### B. Launch the Interactive Streamlit Dashboard:
```powershell
streamlit run dashboard/app.py
```

### C. Regenerate Specific Process Mining Modules:
```powershell
# Event Log Extraction & IEEE 1849 Validation
python process_mining/event_log.py

# Process Discovery (DFG, Petri Net, Variants)
python process_mining/process_discovery.py

# Bottleneck & Turnaround Time Analysis
python process_mining/bottleneck_analysis.py

# Conformance Checking Pipeline
python process_mining/conformance_checking.py
```

---

## 9. Remaining Tasks / Blockers

- **Code & Analytical Modules**: **Zero remaining tasks**. 100% complete and verified.
- **Git & Push Safety**: As requested, changes are staged cleanly. The backup patch `CareFlow-final-staged-backup.patch` is preserved. Manual instructions for committing and pushing to `giricharan525-debug` are provided below.
