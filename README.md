# CareFlow – Clinical Pathway Process Mining

A comprehensive data engineering and process mining platform for analyzing clinical outpatient department (OPD) care pathways, identifying bottlenecks, discovering workflow models, and evaluating healthcare operational efficiency using PM4Py and Python.

---

## 📋 Project Overview & Architecture

CareFlow analyzes large-scale hospital OPD data across appointments, physician consultations, laboratory testing, imaging diagnostics, and pharmacy dispensing.

```
Hospital OPD Raw Records (62,422 rows)
       │
       ▼
Data Cleaning & Quality Auditing (Rules 1–9)
       │
       ▼
Event-Log Extraction & Normalization (`process_mining/event_log.py`)
       │
       ├── IEEE 1849-2016 Compliant Event Log (123,969 events, 49,912 cases)
       │
       ▼
Process Discovery & Modeling (`process_mining/process_discovery.py`)
       ├── Directly-Follows Graph (DFG) – 20 distinct edges, 74,057 transitions
       ├── Process Variant Mining – 287 distinct variants (Top 10 cover 94.91% of cases)
       ├── Inductive Miner Petri Net – 17 places, 21 transitions, 48 arcs (Sound Workflow Net)
       └── High-Resolution Maps (PNG & SVG) + Aggregate Reporting CSVs
```

---

## 📁 Repository Structure

```
├── CareFlow_Cleaning_Review_v2 (1).txt       # Cleaning review & discrepancy reconciliation documentation
├── CareFlow_Dataset_Schema (2).csv           # Formal dataset schema definitions
├── CareFlow_Member1_Dataset_Understanding.md # Dataset understanding report & field analysis
├── Giri_Patient_Appointment_EDA/             # Exploratory Data Analysis by Giri
│   ├── Patient_and_Appointment_EDA[1].ipynb  # Full exploratory analysis notebook
│   ├── findings-report[1].docx               # Key clinical and operational findings
│   ├── chart1_patient_visit_frequency[1].png # Anonymized patient visit distribution
│   ├── chart2_monthly_appointments[1].png    # Monthly encounter volume trends
│   ├── chart3_top10_patients[1].png          # Anonymized top utilization distribution
│   ├── chart4_weekday_appointments[1].png    # Day-of-week load analysis
│   └── *.csv                                 # Aggregate appointment EDA tables
├── process_mining/                           # Core Process Mining Python Modules
│   ├── __init__.py                           # Package exports
│   ├── event_log.py                          # Event-log generation and validation engine
│   └── process_discovery.py                  # DFG, Variants, Petri net discovery & rendering
├── tests/                                    # Automated Test Suite (76 passing tests)
│   ├── test_event_log.py                     # 9 validation tests for event-log integrity
│   └── test_process_discovery.py             # 67 tests for discovery, DFG, variants, Petri net
├── outputs/                                  # Discovered Models & Aggregate Reports
│   ├── careflow_dfg.png / .svg               # Directly-Follows Graph (DFG) process maps
│   ├── careflow_petri_net.png / .svg / .pnml # Inductive Miner Petri Net model & XML
│   ├── careflow_variants.png / .svg          # Top process variants chart
│   ├── activity_frequency.csv                # Per-activity counts, coverage, and durations
│   ├── transition_frequencies.csv            # 20 DFG transitions with mean/median durations
│   ├── process_variants.csv                  # 287 variants with cumulative case percentages
│   ├── start_end_activities.csv              # Start and end activity distributions
│   └── event_log_validation_report.md        # Event-log reconciliation report
└── .gitignore                                # HIPAA & patient privacy protection rules
```

---

## 🔍 Key Discovered Clinical Pathways

1. **Dominant Pathway (78.53% of encounters, 39,197 cases):**  
   `Appointment Registration -> Doctor Consultation & Prescription`  
   Standard routine outpatient consultation requiring no additional diagnostics.

2. **Post-Consultation Diagnostic Pathways (8.01% combined):**  
   - Post-consultation imaging: 2,219 cases (4.45%)  
   - Post-consultation single laboratory test: 1,775 cases (3.56%)

3. **Multi-Test Diagnostic Panels (VAR_005–011+):**  
   Encounters with multiple laboratory orders (2 to 8+ tests). Laboratory self-loops account for 15.39% of all transition events in the DFG (11,395 transitions).

4. **Pre-Consultation Investigations (2.42%, 1,209 cases):**  
   `Appointment Registration -> Imaging Procedure -> Doctor Consultation & Prescription`  
   Walk-in or pre-ordered diagnostic radiology prior to specialist consultation.

---

## 🧪 Testing & Validation

Run the automated test suite using Python's standard `unittest` module:

```bash
# Run all process discovery tests (67 tests)
python -m unittest tests.test_process_discovery -v

# Run event-log generation tests (9 tests)
python -m unittest tests.test_event_log -v
```

All 76 validation checks enforce:
- Exact reconciliation to 123,969 events and 49,912 cases
- Chronological consistency within cases
- Sound workflow Petri net verification (places, transitions, markings)
- Privacy enforcement: 0 patient identifiers in aggregate exports

---

## 🔒 Privacy & HIPAA Compliance

In strict compliance with healthcare data privacy and HIPAA standards:
- Patient-level event logs (`careflow_event_log.csv`, `careflow_event_log.xes`), case summaries (`case_summary.csv`), and raw medical workbooks (`*.xlsx`, `HospitalOPD*.csv`) are maintained exclusively in local secure storage.
- All files tracked in version control are anonymized or aggregated.
