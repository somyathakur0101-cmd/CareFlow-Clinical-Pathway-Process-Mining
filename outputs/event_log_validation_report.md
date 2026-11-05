# CareFlow – Event-Log Validation & Reconciliation Report

**Execution Timestamp:** 2026-11-04 17:33:49  
**Source Dataset:** `CareFlow-Clinical-Pathway-Process-Mining-giricharan525-debug\data\HospitalOPD_CareFlow_cleaned_v4.xlsx` (`Cleaned_Data`)  
**Total Source Rows Evaluated:** 62,422  
**Total Validated Events Generated:** 123,969  
**Total Distinct Encounter Cases:** 49,912  

---

## 1. Discrepancy Reconciliation & Exact Definitions

The source workbook `HospitalOPD_CareFlow_cleaned_v4.xlsx` contains a denormalized table where multiple tests (labs, imaging, prescriptions) within a single outpatient encounter (`appointment_id`) are represented across multiple table rows. This creates distinct numerical totals when counting **raw table rows** versus **deduplicated clinical entities**:

### A. Lab End Timestamps: 4,702 vs. 4,631
* **4,702 (Raw Row Count):** Total rows in `Cleaned_Data` where `lab_start_datetime` is populated but `lab_end_datetime` is empty/blanked (matching the 4,702 entries cataloged in the `Invalid_lab_end` sheet).
* **4,631 (Deduplicated Entity Count):** Total distinct laboratory test orders identified by `(appointment_id, lab_id)` lacking an end timestamp.
* **Exact Difference ($4,702 - 4,631 = 71$):** 71 redundant rows where the same lab order was repeated across multi-item appointments (e.g., patient receiving multiple prescriptions or imaging scans within the same visit).

### B. Fully Bounded Lab Tests: 13,327 vs. 13,175
* **13,327 (Raw Row Count):** Total rows in `Cleaned_Data` where both `lab_start_datetime` and `lab_end_datetime` are populated ($18,029 - 4,702 = 13,327$).
* **13,175 (Deduplicated Entity Count):** Total distinct laboratory test orders identified by `(appointment_id, lab_id)` with confirmed start and completion timestamps ($17,806 - 4,631 = 13,175$).
* **Exact Difference ($13,327 - 13,175 = 152$):** 152 duplicate rows of bounded lab tests repeated across multi-item encounter rows.

### C. Pharmacy Events: 302 vs. 262
* **302 (Raw Row Count):** Total rows in `Cleaned_Data` where pharmacy dispensing columns (`pharmacy_sale_line_id`, `pharmacy_start_datetime`) are populated.
* **262 (Deduplicated Entity Count):** Total distinct pharmacy sale line items identified by `(appointment_id, pharmacy_sale_line_id)`.
* **Exact Difference ($302 - 262 = 40$):** 40 duplicate pharmacy rows repeated across multi-test appointments.

### D. Prescription Start Missing: 12 vs. 12
* **12 (Raw Row Count) & 12 (Deduplicated Order Count):** Exactly 12 orders lack `prescription_start_datetime`. Handled under Rule 8 by setting `lifecycle=complete`, retaining valid end time, and leaving `start_timestamp` empty.

### E. Prescription Inverted Timestamps: 52 vs. 49
* **52 (Raw Row Count):** 52 rows in `Cleaned_Data` with `flag_prescription_end_before_start` set.
* **49 (Deduplicated Order Count):** 49 unique prescription orders identified by `(appointment_id, prescription_order_id)` have `prescription_start > prescription_end`. 3 of these orders were repeated across multi-test rows ($49 + 3 = 52$).

---

## 2. Event Extraction Summary

| Clinical Activity Name | Deduplication Entity Key | Generated Events | Unique Cases | Case Coverage % |
|---|---|---:|---:|---:|
| **Appointment Registration** | `appointment_id` | 49,912 | 49,912 | 100.00% |
| **Doctor Consultation & Prescription** | `appointment_id` + `prescription_order_id` | 50,568 | 49,912 | 100.00% |
| **Laboratory Examination** | `appointment_id` + `lab_id` | 17,806 | 12,969 | 25.98% |
| **Imaging Procedure** | `appointment_id` + `imaging_request_id` | 5,421 | 4,772 | 9.56% |
| **Pharmacy Dispensing** | `appointment_id` + `pharmacy_sale_line_id` | 262 | 261 | 0.52% |
| **TOTAL EVENT LOG** | | **123,969** | **49,912** | **100.00%** |

---

## 3. Automated Validation Test Results

| Validation Check | Target Specification | Actual Result | Status |
|---|---|---|---|
| **Event Count Verification** | 123,969 events | 123,969 | **PASSED** |
| **Unique Event IDs** | 100% unique (0 duplicates) | 123,969 unique IDs | **PASSED** |
| **Missing Case IDs (`appointment_id`)** | 0 nulls | 0 | **PASSED** |
| **Missing Patient IDs (`patient_id`)** | 0 nulls | 0 | **PASSED** |
| **Chronological Ordering within Cases** | 0 inversions | 0 violations | **PASSED** |
| **Missing Start Time Rule (Rule 8)** | Keep valid end time, lifecycle=`complete` | 12 orders handled | **PASSED** |
| **Inverted Timestamps (Rule 9)** | Duration=`null`, flagged transparently | 49 deduplicated orders handled | **PASSED** |

---

## 4. Clinical Pathway Process Mining Compatibility

* **PM4Py Compatibility:** All event timestamps conform strictly to `%Y-%m-%d %H:%M:%S` and ISO 8601 formatting.
* **XES Standard Export:** Standard IEEE 1849-2016 compliant XES output available at `outputs/careflow_event_log.xes`.
* **Privacy Assurance:** Patient identifiers and individual records remain exclusively in local outputs protected by `.gitignore`.
