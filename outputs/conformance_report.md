# CareFlow Clinical Pathway Conformance Checking Report

## Executive Summary

This report documents the conformance checking analysis performed on the **CareFlow Outpatient Department (OPD) Dataset** (49,912 clinical encounter cases, 123,969 recorded events) using Python and PM4Py. Actual hospital event sequences were compared against two process references:
1. **Data-Derived Reference Model**: The discovered Inductive Miner Petri Net (`outputs/careflow_petri_net.pnml`), representing a sound mathematical abstraction of all observed event sequences in the hospital log.
2. **Normative Clinical Pathway Standards**: Clinical domain rules requiring administrative registration as the primary point of entry, physician consultation preceding diagnostic orders/prescriptions, and sequential service completion.

> [!IMPORTANT]
> **Medical Context & Reference Model Scope**: The reference Petri net was discovered directly from recorded historical hospital data. It represents an *empirical data-derived model*, NOT an approved clinical practice guideline or institutional standard of care. Full fitness against the data-derived Petri net confirms that the discovered model faithfully captures observed hospital pathways, while sequence deviation analysis against normative clinical standards reveals operational variations, out-of-order diagnostic execution, and re-testing patterns.

---

## 1. Reference Model & Activity Alignment

- **Model Format**: Inductive Miner Petri Net (PNML)
- **Places**: 17
- **Transitions**: 21 (5 visible clinical activities, 16 silent $\tau$ routing transitions)
- **Arcs**: 48
- **Initial Marking**: `['source:1']`
- **Final Marking**: `['sink:1']`
- **Model Soundness**: Mathematically sound workflow net (proper completion, option to complete, no dead transitions).

### Activity Label Consistency Verification
All 5 unique clinical activities recorded in the validated event log match the visible transitions in the Petri net exactly:

| # | Activity Name in Event Log | Petri Net Visible Transition | Alignment Status |
|---|---|---|---|
| 1 | Appointment Registration | Appointment Registration | MATCHED (100%) |
| 2 | Doctor Consultation & Prescription | Doctor Consultation & Prescription | MATCHED (100%) |
| 3 | Laboratory Examination | Laboratory Examination | MATCHED (100%) |
| 4 | Imaging Procedure | Imaging Procedure | MATCHED (100%) |
| 5 | Pharmacy Dispensing | Pharmacy Dispensing | MATCHED (100%) |

---

## 2. PM4Py Token-Based Replay (TBR) Metrics

Token-based replay was executed across all **49,912 cases** using `pm4py.conformance_diagnostics_token_based_replay` and `pm4py.fitness_token_based_replay`:

| Metric Name | Value | Unit / Scale | Clinical Interpretation |
|---|---|---|---|
| **Log Fitness** | **1.0000** | 0.0 - 1.0 (100.0%) | Perfect replay fitness; the model reproduces all observed sequences. |
| **Average Trace Fitness** | **1.0000** | 0.0 - 1.0 (100.0%) | Every single encounter trace achieves 1.0 fitness. |
| **Percentage of Fitting Traces** | **100.00%** | Percentage | 49,912 / 49,912 cases fit without token artificial forcing. |
| **TBR Precision** | **0.7914** | 0.0 - 1.0 (79.14%) | High precision; model avoids excessive over-generalization. |
| **TBR F-Measure** | **0.8836** | 0.0 - 1.0 (88.36%) | Balanced harmonic score of fitness and precision. |
| **Total Cases Replayed** | **49,912** | Cases | Full OPD cohort evaluated. |
| **Produced Tokens** | **552,840** | Tokens | Total tokens generated during replay firings. |
| **Consumed Tokens** | **552,840** | Tokens | Total tokens consumed by enabled transitions. |
| **Missing Tokens** | **0** | Tokens | Zero missing tokens (no forced firings required). |
| **Remaining Tokens** | **0** | Tokens | Zero stranded tokens (all tokens reached final sink place). |
| **Traces with Problem Transitions** | **0** | Cases | Zero trace execution failures. |

---

## 3. Conformance Across Clinical Flows

Comparing observed pathways across the seven clinical flow categories reveals distinct operational compliance profiles:

| Flow Code | Clinical Flow Name | Total Cases | Log Share | Start Conf (%) | Activity Match (%) | Out-of-Order Diag (%) | Loops / Repetition (%) | Mean Length |
|---|---|---|---|---|---|---|---|---|
| 1 | Appointment -> Prescription | 39,667 | 79.47% | 99.99% | 99.98% | 0.0% | 1.17% | 2.01 |
| 2 | Appointment -> Prescription -> Lab | 4,834 | 9.69% | 98.22% | 99.73% | 7.43% | 61.09% | 4.51 |
| 3 | Appointment -> Prescription -> Imaging | 3,785 | 7.58% | 93.92% | 100.0% | 38.84% | 3.54% | 3.04 |
| 4 | Appointment -> Prescription -> Pharmacy | 93 | 0.19% | 100.0% | 100.0% | 0.0% | 72.04% | 4.4 |
| 5 | Appointment -> Prescription -> Lab + Imaging | 1,518 | 3.04% | 93.54% | 100.0% | 32.61% | 78.13% | 6.83 |
| 6 | Appointment -> Prescription -> Lab + Pharmacy | 14 | 0.03% | 100.0% | 100.0% | 0.0% | 92.86% | 6.36 |
| 7 | Appointment -> Prescription -> Imaging + Pharmacy | 1 | 0.0% | 100.0% | 100.0% | 0.0% | 0.0% | 4.0 |

### Clinical Flow Insights
1. **Flow 1 (Appointment -> Prescription, N=39,667, 79.47%)**: Highly standardized consultation pathway. 99.98% activity-conforming, 99.99% start-conforming. 466 cases (1.17%) experienced re-consultation (repeat Doctor Consultation events).
2. **Flow 2 (Appointment -> Prescription -> Lab, N=4,834, 9.69%)**: 61.09% of cases had repeated laboratory activities (multiple laboratory tests performed in one visit). In 359 cases (7.43%), laboratory blood draw was recorded before physician consultation (fasting morning draws).
3. **Flow 3 (Appointment -> Prescription -> Imaging, N=3,785, 7.58%)**: Shows the highest rate of pre-consultation diagnostic execution: **1,470 cases (38.84%)** had imaging performed before recorded consultation. This reflects routine walk-in imaging or triage X-rays completed prior to clinician review.
4. **Flow 4 (Appointment -> Prescription -> Pharmacy, N=93, 0.19%)**: High rate of repeated pharmacy dispensing (72.04% loop execution), representing split-batch medication fulfillment.
5. **Flow 5 (Appointment -> Prescription -> Lab + Imaging, N=1,518, 3.04%)**: Complex multi-service visits. 78.13% loop execution (multiple tests) and 32.61% pre-consultation diagnostic orders.
6. **Flows 6 & 7 (Comprehensive Pathways, N=15)**: Infrequent complex pathways with high activity repetition (up to 92.86%).

---

## 4. Empirical Clinical Sequence Deviations

The table below details all observed empirical deviations categorized by operational type:

| Category | Deviation Pattern | Affected Cases | Case Share (%) | Clinical & Operational Significance |
|---|---|---|---|---|
| Rework & Complexity | Any Activity Repetition (Loop Execution) | 4,819 | 9.65% | Encounter contains two or more events of the same activity type within the same visit. |
| Rework & Complexity | Activity Repetition: Laboratory Examination (>=2x) | 4,107 | 8.23% | Patient underwent multiple laboratory examinations during a single OPD encounter. |
| Clinical Precedence | Diagnostic Precedence Deviation: Any Diagnostic Before Consultation | 2,324 | 4.66% | Diagnostic service occurred prior to physician consultation; indicates walk-in diagnostic, standing pre-visit order, or direct radiology/lab arrival before clinical review. |
| Clinical Precedence | Sequence Inversion: Imaging Procedure Before Consultation | 1,915 | 3.84% | Patient completed X-ray or ultrasound before seeing the consulting physician. |
| Rework & Complexity | Activity Repetition: Doctor Consultation & Prescription (>=2x) | 640 | 1.28% | Patient had multiple physician consultation events in one encounter. |
| Clinical Precedence | Sequence Inversion: Laboratory Examination Before Consultation | 498 | 1.00% | Blood or specimen collection occurred prior to physician consultation. |
| Administrative Flow | Registration Not First Activity | 418 | 0.84% | Encounter record shows a clinical activity timestamp preceding the recorded registration time. |
| Administrative Flow | Start Activity Deviation: First is 'Imaging Procedure' | 282 | 0.56% | Initial recorded encounter event is imaging; registration entered later in EMR. |
| Administrative Flow | Start Activity Deviation: First is 'Laboratory Examination' | 131 | 0.26% | Initial recorded encounter event is phlebotomy/lab draw. |
| Rework & Complexity | Activity Repetition: Imaging Procedure (>=2x) | 98 | 0.20% | Patient underwent multiple imaging examinations (e.g. multi-view X-ray or ultrasound). |
| Rework & Complexity | Activity Repetition: Pharmacy Dispensing (>=2x) | 79 | 0.16% | Prescription items dispensed in multiple separate fulfillment batches. |
| Data Quality & Classification | Flow Designation Mismatch: Activity Set vs Flow Code | 22 | 0.04% | Case contains activities that deviate from the standard activity set of its clinical flow code. |
| Data Quality & Classification | Flow 2 with Unexpected Activity: Imaging Procedure | 13 | 0.03% | Encounter classified as Flow 2 (Appointment -> Prescription -> Lab) also received Imaging. |
| Data Quality & Classification | Flow 1 with Unexpected Activity: Imaging Procedure | 5 | 0.01% | Encounter classified as Flow 1 (Consultation only) received an ad-hoc Imaging Procedure. |
| Administrative Flow | Start Activity Deviation: First is 'Doctor Consultation & Prescription' | 5 | 0.01% | Immediate physician evaluation recorded before clerk registration entry. |

---

## 5. Top Process Variant Conformance

Analysis of the top process variants demonstrates how specific clinical sequences align with normative standards:

| Variant ID | Case Count | Share (%) | Trace Length | Classification | Activity Sequence |
|---|---|---|---|---|---|
| VAR_001 | 39,197 | 78.53% | 2 | Standard Linear Conformant | `Appointment Registration -> Doctor Consultation & Prescription` |
| VAR_002 | 2,219 | 4.45% | 3 | Standard Linear Conformant | `Appointment Registration -> Doctor Consultation & Prescription -> Imaging Procedure` |
| VAR_003 | 1,775 | 3.56% | 3 | Standard Linear Conformant | `Appointment Registration -> Doctor Consultation & Prescription -> Laboratory Examination` |
| VAR_004 | 1,209 | 2.42% | 3 | Pre-Consultation Diagnostic Variant | `Appointment Registration -> Imaging Procedure -> Doctor Consultation & Prescription` |
| VAR_005 | 1,175 | 2.35% | 4 | Standard with Activity Repetition (Loop) | `Appointment Registration -> Doctor Consultation & Prescription -> Laboratory Examination -> Laboratory Examination` |
| VAR_006 | 598 | 1.20% | 5 | Standard with Activity Repetition (Loop) | `Appointment Registration -> Doctor Consultation & Prescription -> Laboratory Examination -> Laboratory Examination -> Laboratory Examination` |
| VAR_007 | 447 | 0.90% | 3 | Standard with Activity Repetition (Loop) | `Appointment Registration -> Doctor Consultation & Prescription -> Doctor Consultation & Prescription` |
| VAR_008 | 339 | 0.68% | 6 | Standard with Activity Repetition (Loop) | `Appointment Registration -> Doctor Consultation & Prescription -> Laboratory Examination -> Laboratory Examination -> Laboratory Examination -> Laboratory Examination` |
| VAR_009 | 222 | 0.44% | 3 | Pre-Consultation Diagnostic Variant | `Imaging Procedure -> Appointment Registration -> Doctor Consultation & Prescription` |
| VAR_010 | 189 | 0.38% | 7 | Standard with Activity Repetition (Loop) | `Appointment Registration -> Doctor Consultation & Prescription -> Laboratory Examination -> Laboratory Examination -> Laboratory Examination -> Laboratory Examination -> Laboratory Examination` |

---

## 6. Key Findings & Clinical Recommendations

### Finding 1: Perfect Model Replay vs Operational Sequence Variation
- The data-derived Inductive Miner Petri Net achieves **100% trace fitness** and **79.14% precision** across all 49,912 cases.
- This confirms that the discovered model is mathematically sound and capable of replaying every hospital encounter.
- However, conformance against strict normative guidelines reveals that **4.66% of encounters (2,324 cases)** had diagnostic procedures recorded prior to doctor consultation, driven primarily by Imaging in Flow 3 (38.84%) and Flow 5 (32.61%).

### Finding 2: High Activity Repetition Reflects Diagnostic Panels, Not Clinical Failure
- Overall, **4,819 encounters (9.65%)** exhibited repeated activities, with laboratory tests accounting for the vast majority (up to 26 lab events per encounter).
- In hospital OPD process mining, self-loop transitions for Laboratory Examination represent multi-component diagnostic panels (e.g. CBC, Liver Function, Lipid Profile) ordered and performed concurrently, rather than medical re-testing or clinical error.

### Finding 3: Start Activity Integrity and Administrative Delays
- **99.16% of encounters (49,494 cases)** correctly initiated at Appointment Registration.
- The remaining **418 cases (0.84%)** had initial events at Imaging (282 cases) or Laboratory (131 cases). These instances reflect direct walk-in arrivals or urgent triage routing where physical care preceded clerical EMR registration desk processing.

### Finding 4: Encounter Completeness
- **Zero single-event traces were observed** (0.00% incomplete traces). Every recorded appointment case successfully completed both administrative intake and clinician consultation.

---

## 7. Methodological Limitations

1. **Data-Derived Reference Nature**: The Petri net model reflects historical operational practice, including existing hospital bottlenecks, batch order entries, and workflow quirks.
2. **Timestamp Granularity & Simultaneous Events**: When multiple diagnostic tests share identical timestamps, event ordering is governed by index tie-breaking rather than physical clinical succession.
3. **Absence of Negative Clinical Outcome Data**: Process deviations (such as pre-consultation X-rays) cannot be labeled as clinically erroneous without clinical outcome metrics (e.g., diagnostic yield, patient safety incidents).

---

*Report generated automatically by CareFlow Conformance Checking Module.*