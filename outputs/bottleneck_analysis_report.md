# CareFlow – Clinical Pathway Bottleneck & Waiting-Time Analysis Report

**Analysis Engine:** CareFlow Bottleneck Analysis Module (`process_mining/bottleneck_analysis.py`)  
**Data Evaluated:** Validated CareFlow Outpatient Event Log (`outputs/careflow_event_log.csv`)  
**Total Patient Encounters:** 49,912 cases  
**Total Validated Events:** 123,969 events  
**Total Inter-Event Transitions:** 74,057 transitions  

---

## 1. Executive Summary & Core Operational Findings

1. **Overall Encounter Duration:**
   - **Median Encounter Length:** **33.0 minutes** across all 49,912 outpatient visits.
   - **90th Percentile Duration:** **120.0 minutes (2.0 hours)**.
   - **Mean Encounter Length:** **191.52 minutes (3.19 hours)**, strongly influenced by a long tail of 609 multi-day encounters (1.22% of cases) extending beyond 24 hours.

2. **Primary Clinical Bottlenecks (Waiting Times):**
   - **Doctor Consultation → Imaging Procedure:** Observed mean waiting time of **441.32 minutes (~7.4 hours)**, median of **35.0 minutes**, and 90th percentile of **110.0 minutes**. In 2,981 encounters, patients faced substantial waiting intervals between consultation completion and radiology execution.
   - **Laboratory Examination → Imaging Procedure:** Cross-diagnostic transfer in multi-investigation visits (Flow 5) averaged **1,613.24 minutes (~26.9 hours)** with a median of **60.0 minutes** and P90 of **3,246.6 minutes (~54 hours)**, indicating cross-day staged diagnostics.
   - **Appointment Registration → Doctor Consultation:** Primary waiting room interval averaging **130.22 minutes**, median of **25.0 minutes**, and P90 of **92.0 minutes** across 47,964 encounters.

3. **Diagnostic Service Turnaround Times (TAT):**
   - **Laboratory Examination:** Median turnaround time of **125.0 minutes (2.1 hours)**; Mean of **469.39 minutes (7.8 hours)**; 90th percentile of **470.0 minutes**.
   - **Imaging Procedure:** Rapid technical scan execution with a median of **3.0 minutes** and 90th percentile of **9.0 minutes** (Mean: **98.41 minutes**).
   - **Physician Consultation & Prescription:** Median of **0.0 minutes** (simultaneous EMR sign-off) with 90th percentile of **7.0 minutes** (Mean: **7.58 minutes**).

---

## 2. Activity Turnaround & Service Duration Analysis

Durations calculated strictly on validated, bounded timestamps:

| Clinical Activity | Metric Evaluated | Total Events | Bounded Valid Events | Unbounded / Excluded | Mean (min) | Median (min) | P90 (min) | Max (min) |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|
| **Laboratory Examination** | Turnaround Time (TAT) | 17,806 | 13,175 | 4,631 | 469.39 | 125.0 | 470.0 | 76,200.0 |
| **Imaging Procedure** | Turnaround Time (TAT) | 5,421 | 5,412 | 9 | 98.41 | 3.0 | 9.0 | 101,753.0 |
| **Doctor Consultation & Rx** | Consultation & Order Duration | 50,568 | 50,506 | 62 | 7.58 | 0.0 | 7.0 | 40,391.0 |
| **Pharmacy Dispensing** | Dispensing & Sale Duration | 262 | 262 | 0 | 6.08 | 1.0 | 2.0 | 707.0 |
| **Appointment Registration** | Reception Check-in (Point) | 49,912 | 49,912 | 0 | 0.00 | 0.0 | 0.0 | 0.0 |

> [!NOTE]
> **Data Quality Exclusion Transparency:**
> - **Laboratory Tests:** 4,631 orders (26.0%) lacked valid completion timestamps (matching the 4,702 raw row count in the workbook's `Invalid_lab_end` catalog after deduplicating multi-test rows) and were excluded from turnaround duration calculations to avoid distorting medical metrics.
> - **Prescriptions:** 12 orders lacking start timestamps (Rule 8) and 49 orders with inverted timestamps where start > end (Rule 9) had durations blanked and were audited separately.

---

## 3. Inter-Event Transition & Waiting-Time Analysis

Detailed breakdown of all 20 discovered transitions between consecutive clinical events (74,057 total transitions):

| Source Activity | Target Activity | Count | % Transitions | Mean (min) | Median (min) | P90 (min) | Zero Spans | Outliers >24h |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|
| Appointment Registration | Doctor Consultation & Prescription | 47,964 | 64.77% | 130.22 | 25.0 | 92.0 | 34 | 309 |
| Laboratory Examination | Laboratory Examination | 11,395 | 15.39% | 1.86 | 0.0 | 0.0 | 11,275 | 1 |
| Doctor Consultation & Prescription | Laboratory Examination | 5,302 | 7.16% | 35.69 | 19.0 | 65.0 | 7 | 1 |
| Doctor Consultation & Prescription | Imaging Procedure | 2,981 | 4.03% | 441.32 | 35.0 | 110.0 | 8 | 124 |
| Imaging Procedure | Doctor Consultation & Prescription | 1,658 | 2.24% | 41.58 | 25.0 | 71.0 | 0 | 2 |
| Appointment Registration | Imaging Procedure | 1,592 | 2.15% | 72.20 | 47.0 | 183.9 | 2 | 1 |
| Imaging Procedure | Laboratory Examination | 614 | 0.83% | 44.89 | 29.0 | 69.7 | 0 | 0 |
| Doctor Consultation & Prescription | Doctor Consultation & Prescription | 562 | 0.76% | 1054.00 | 15.0 | 1420.7 | 20 | 55 |
| Laboratory Examination | Imaging Procedure | 483 | 0.65% | 1613.24 | 60.0 | 3246.6 | 0 | 73 |
| Laboratory Examination | Doctor Consultation & Prescription | 379 | 0.51% | 254.78 | 37.0 | 331.2 | 0 | 16 |
| Appointment Registration | Laboratory Examination | 352 | 0.48% | 110.79 | 30.0 | 92.0 | 3 | 4 |
| Imaging Procedure | Appointment Registration | 288 | 0.39% | 55.14 | 18.0 | 135.3 | 0 | 0 |
| Pharmacy Dispensing | Pharmacy Dispensing | 154 | 0.21% | 3.62 | 0.0 | 0.0 | 150 | 0 |
| Laboratory Examination | Appointment Registration | 125 | 0.17% | 192.80 | 158.0 | 456.2 | 0 | 0 |
| Doctor Consultation & Prescription | Pharmacy Dispensing | 106 | 0.14% | 10.59 | 7.0 | 19.0 | 0 | 0 |
| Imaging Procedure | Imaging Procedure | 82 | 0.11% | 197.51 | 10.0 | 80.7 | 3 | 1 |
| Pharmacy Dispensing | Laboratory Examination | 12 | 0.02% | 17.67 | 11.0 | 42.8 | 0 | 0 |
| Doctor Consultation & Prescription | Appointment Registration | 5 | 0.01% | 2107.40 | 1439.0 | 4555.2 | 0 | 2 |
| Laboratory Examination | Pharmacy Dispensing | 2 | 0.0% | 45.00 | 45.0 | 46.6 | 0 | 0 |
| Pharmacy Dispensing | Imaging Procedure | 1 | 0.0% | 245.00 | 245.0 | 245.0 | 0 | 0 |

---

## 4. Encounter Durations Across Clinical Flow Pathways

Comparison of patient throughput duration across the 7 distinct OPD clinical flows:

| Code | Clinical Pathway Category | Cases | Events | Median (min) | Mean (min) | P90 (min) | Cases >24h |
|:---:|:---|---:|---:|---:|---:|---:|---:|
| 1 | Appointment → Prescription | 39,667 | 79,823 | 26.0 | 164.37 | 94.0 | 0.89% |
| 2 | Appointment → Prescription → Lab | 4,834 | 21,788 | 50.0 | 103.81 | 153.0 | 0.72% |
| 3 | Appointment → Prescription → Imaging | 3,785 | 11,495 | 78.0 | 383.67 | 261.0 | 3.25% |
| 4 | Appointment → Prescription → Pharmacy | 93 | 409 | 29.0 | 42.91 | 86.4 | 0.0% |
| 5 | Appointment → Prescription → Lab + Imaging | 1,518 | 10,361 | 115.5 | 711.39 | 438.3 | 6.39% |
| 6 | Appointment → Prescription → Lab + Pharmacy | 14 | 89 | 48.5 | 51.21 | 82.5 | 0.0% |
| 7 | Appointment → Prescription → Imaging + Pharmacy | 1 | 4 | 322.0 | 322.00 | 322.0 | 0.0% |

---

## 5. Frequently Repeated Activities (Self-Loops)

Self-loops represent multiple line items of the same activity type ordered in a single encounter:

1. **Laboratory Examination → Laboratory Examination (11,395 occurrences):**
   - **Median Duration:** **0.0 minutes**; Mean: **1.86 minutes**.
   - **Interpretation:** Multiple blood/urine test panels requested simultaneously in a single laboratory order form. Zero-minute intervals reflect batch digital order entry rather than instant physical testing.
2. **Doctor Consultation → Doctor Consultation (562 occurrences):**
   - **Median Duration:** **15.0 minutes**; Mean: **1,054.0 minutes**; P90: **1,420.7 minutes**.
   - **Interpretation:** Multiple medications prescribed or follow-up consultations within a multi-day visit episode.
3. **Pharmacy Dispensing → Pharmacy Dispensing (154 occurrences):**
   - **Median Duration:** **0.0 minutes**; Mean: **3.62 minutes**.
   - **Interpretation:** Multi-item pharmaceutical prescription fulfillment at the hospital pharmacy counter.
4. **Imaging Procedure → Imaging Procedure (82 occurrences):**
   - **Median Duration:** **10.0 minutes**; Mean: **197.51 minutes**.
   - **Interpretation:** Multi-view or multi-anatomical region diagnostic scans.

---

## 6. Data Quality, Missing, and Suspicious Durations Audit

Comprehensive reconciliation of timestamp integrity and operational anomalies:

| Quality / Anomaly Dimension | Observed Count | Percentage / Rate | Operational Explanation |
|:---|---:|---:|:---|
| **Negative Transitions (t < 0)** | **0** | 0.00% | Full chronological ordering verified within all cases. |
| **Simultaneous Transitions (t = 0)** | **11,502** | 15.53% | Batch order entries sharing identical appointment timestamps. |
| **Transitions Exceeding 24 Hours** | **589** | 0.8% | Cross-day diagnostic appointments and deferred follow-ups. |
| **Missing Lab End Timestamps** | **4,631** | 26.01% | Unparseable/unrecorded end times in source (Rule 1 & 2). |
| **Missing Prescription Start Timestamps** | **12** | 0.02% | Retained completion time; lifecycle marked complete (Rule 8). |
| **Inverted Prescription Timestamps** | **49** | 0.10% | Start > End; duration blanked, audit flag retained (Rule 9). |
| **Encounters Exceeding 24 Hours** | **609** | 1.22% | Outpatient episodes spanning multiple days (Max: 483.1 days). |

---

## 7. Clinical & Methodological Discussion

### A. Distinguishing Observed Waiting Time from Medical Delay
- **Administrative vs. Clinical Spans:** An observed transition duration between `Doctor Consultation` and `Imaging Procedure` of 441.3 minutes does **not** signify that a patient physically sat in a waiting room for 7.4 hours. In OPD settings, non-urgent imaging requests (e.g., routine ultrasounds or elective MRIs) are frequently scheduled for later in the day or deferred to subsequent dates.
- **Timestamp Granularity & Simultaneous Entries:** 11,502 transitions exhibit a duration of exactly 0.0 minutes. Treating these as zero-duration clinical acts would be erroneous; they represent simultaneous digital documentation by medical staff in the hospital information system.

### B. Impact of Outliers on Mean vs. Median
- Across almost all transitions, the **mean significantly exceeds the median** (e.g., Consultation → Imaging: Mean 441 min vs. Median 35 min; Appointment → Doctor: Mean 130 min vs. Median 25 min).
- The **median** provides the most accurate reflection of the standard patient experience, while the **mean** and **90th percentile** expose the operational long tail that strains hospital scheduling.

---

## 8. Operational Recommendations for Hospital Management

1. **Establish Dedicated Imaging Scheduling Slots:**
   - Mitigate the Consultation-to-Imaging bottleneck (P90: 110 min) by implementing fast-track imaging protocols for acute outpatient evaluations.
2. **Standardize Laboratory Result Sign-off:**
   - Address the 4,631 lab orders lacking completion timestamps by enforcing mandatory digital closure in the Laboratory Information System (LIS).
3. **Queue Balancing During Peak Registration Hours:**
   - With an appointment-to-consultation waiting time reaching 92.0 minutes at the 90th percentile, deploy dynamic registration queuing to smooth morning patient influx.
