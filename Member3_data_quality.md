# Data Quality Report: Duplicates, Inconsistent Values, Suspicious IDs, Blank Columns

**Author:** Garima Singh (Member 3)
**Dataset:** HospitalOPD-noname.csv (62,422 rows x 25 columns)
**Appointment date range:** 2024-04-25 to 2026-04-07
**Method:** Python (pandas). Source data was not modified.
**Supporting files:** `duplicate_summary.csv`, `duplicate_by_column.csv`, `duplicate_report.py`

## 1. Summary
| # | Issue | Severity | Rows affected |
|---|-------|----------|---------------|
| 1 | Blank column (header is empty, all values missing) | Low | 62,422 (100%) |
| 2 | `lab_end_datetime` corrupted (values like `53:45.0`, date lost) | High | 4,702 (26.08% of lab rows) |
| 3 | `lab_id` / `imaging_request_id` reused across different appointments | High | 1,332 lab rows (606 IDs); 60 imaging IDs |
| 4 | Duplicate event rows (same case + ID + start time) | Medium | 4 exact duplicates; 181 lab, 102 imaging, 40 pharmacy extra rows |
| 5 | Prescription end time earlier than start time | Medium | 52 |
| 6 | Event starts before the appointment or before the prescription | Medium | Lab 457 / Imaging 295 / Prescription 5 (before appointment); Lab 1,566 / Imaging 2,004 (before prescription) |
| 7 | Impossible or extreme dates | Medium | 1 future-year typo; 14 prescriptions over 30 days after appointment |
| 8 | Missing timestamps on non-optional events | Low | 12 prescription start, 1 prescription end, 10 imaging end |
| 9 | Inconsistent text values (spacing, case, non-doctor name) | Low | See section 6 |

## 2. Duplicate Records
| Check | Result |
|-------|--------|
| `record_no` unique and sequential (1 to 62,422) | Yes, 0 duplicates |
| Exact duplicate rows (all columns) | 0 (because `record_no` is unique) |
| Exact duplicate rows excluding `record_no` | **4 extra rows** (8 rows in 4 groups) |
| Prescription event duplicates (appointment + order + start time) | 11,854 extra rows |
| Lab event duplicates (appointment + lab_id + start time) | 181 extra rows (357 rows in duplicate groups) |
| Imaging event duplicates | 102 extra rows |
| Pharmacy event duplicates | 40 extra rows |

**Evidence (4 exact duplicates, all lab rows):**
- record_no 30014 and 30015: patient 234866, appointment 326934, lab_id 136480
- record_no 30016 and 30017: patient 234866, appointment 326934, lab_id 136484
- record_no 40613 and 40614: patient 257364, appointment 333059, lab_id 142279
- record_no 40615 and 40616: patient 257364, appointment 333059, lab_id 142292

**Explanation for the large prescription number:** The table is flat. `prescription_order_id` repeats 11,854 times because the prescription is copied onto every lab, imaging, or pharmacy row of the same order. This is expected. The evidence is that no order ID ever belongs to more than one appointment, patient, or doctor. These are not errors, but they must be de-duplicated when building the event log.

**Lab and imaging duplicates:** In 307 of the 357 lab rows in duplicate groups, there is no imaging or pharmacy on the same row, so table joins do not fully explain them. These need checking against the source system.

## 3. Blank and Unnecessary Columns
- The 3rd column has an **empty header** and is **100% empty** (62,422 of 62,422). It is loaded as `Unnamed: 2`. **Recommendation: drop it.**
- Lab, imaging, and pharmacy columns are mostly empty (lab 71.12%, imaging 91.15%, pharmacy 99.52%). These are **structural blanks** (the activity did not happen), not errors. Keep them.
- Evidence that the blanks are consistent with `flow_code`: lab rows 16,434 + 1,575 + 20 = 18,029; imaging rows 3,947 + 1,575 + 1 = 5,523; pharmacy rows 281 + 20 + 1 = 302. These match the populated columns exactly.

## 4. Suspicious IDs
| Check | Result |
|-------|--------|
| `lab_id` used in more than one appointment | **606 IDs, 1,332 rows**. Always the same patient. Median gap 51 days, maximum 198 days |
| `imaging_request_id` used in more than one appointment | **60 IDs** |
| Doctor ID with more than one name, or name with more than one ID | None (98 doctors, 1:1) |
| Appointment ID with more than one patient or start time | None |
| Prescription order ID spanning appointments, patients, or doctors | None |
| IDs zero or negative | None |
| Doctor `Admin` (ID 225) | 3 rows: record_no 1, 116, 15688. Not a real doctor |

**Evidence for reused lab IDs:**
- lab_id 5319 (Complete Blood Count), patient 122401: appointment 258834 on 6/25/2025 and appointment 277820 on 7/25/2025.
- lab_id 8557 (Complete Blood Count), patient 128597: appointment 236421 on 5/17/2025 and appointment 329003 on 10/4/2025.

A lab order ID should belong to one appointment. This may be a test-type ID rather than a transaction ID, or an ID reuse problem. It must be confirmed with the data owner before it is used as a case or event key.

Note: `imaging_request_id` and `imaging_result_id` differ in all 5,523 rows, which is expected as they are different ID types. Both are blank together in the same 56,899 rows.

## 5. Inconsistent and Impossible Time Values
| Issue | Evidence |
|-------|----------|
| `lab_end_datetime` corrupted | 4,702 of 18,029 values (26.08%) look like `53:45.0`, `46:40.0`, `29:40.0`, `15:00.0`. The date part is lost and they cannot be parsed. Only 13,327 lab end times are usable. All other datetime columns are well-formed |
| Prescription end before start | 52 rows, usually about 1 day earlier. Example: record_no 2826 starts 9/16/2025 8:08, ends 9/12/2025 8:17 |
| Future-year typo | record_no 28837: appointment 7/23/2025, prescription start 7/23/2026 16:43, end 7/23/2025 16:50 |
| Prescription long after appointment | 14 rows over 30 days. Example: appointment 756 on 4/27/2024, prescription on 8/23/2025 |
| Prescription start before appointment | 5 rows |
| Lab start before appointment start | 457 rows |
| Imaging start before appointment start | 295 rows |
| Lab start before prescription start | 1,566 rows (flow says Appointment, Prescription, then Lab) |
| Imaging start before prescription start | 2,004 rows |
| Very long durations | Prescription over 1 day: 65 rows (21 over 7 days). Lab over 1 day: 732 rows (among parseable). Imaging over 1 day: 26 rows |
| Missing timestamps | `prescription_start_datetime` 12, `prescription_end_datetime` 1, `imaging_end_datetime` 10 (start present, end missing) |

The dataset has no events dated after the last appointment (2026-04-07) except the typo above.

## 6. Inconsistent Text Values
- Doctor names: 84 use the `Dr.` prefix, but 3 use uppercase `DR.` (example: `DR. AHMAD TAMIM BARYALAI`, record_no 6). One non-doctor value `Admin`.
- Leading or trailing spaces: `lab_name` 3, `imaging_name` 6, `medicine_name` 8.
- Double spaces: `imaging_name` 15, `medicine_name` 248.
- Variant of the same value: `Soft Tissue` and ` Soft Tissue` (leading space) in `imaging_name`.
- `medicine_name` is free text with 154 distinct values and includes dosage, pack size, and location codes (for example `MTH`, `OP`), so the same medicine can appear under different names.

## 7. Recommended Actions
1. Drop the blank header column.
2. Repair or exclude `lab_end_datetime` (26% corrupted). Ask the data owner for the original values.
3. Remove the 4 exact duplicate rows after confirming with the source.
4. De-duplicate events by (appointment, ID, start time) when building the event log.
5. Confirm with the data owner why `lab_id` and `imaging_request_id` repeat across appointments.
6. Fix or flag the 52 rows where prescription end is before start, and the future-year typo.
7. Trim whitespace and standardize name formatting. Exclude or flag `Admin`.
8. Agree as a team on handling of events that start before the appointment or prescription.
