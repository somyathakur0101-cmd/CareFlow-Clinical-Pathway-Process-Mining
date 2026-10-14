# Member 3 – Duplicate Records and Data Quality Check

## 1. Objective
To identify duplicate records and data quality issues in the HospitalOPD dataset. This is a findings report only. No data was changed or deleted.

## 2. Duplicate Records Check
- First check (Power Query): grouped records using all columns, excluding the temporary Index column. The `Duplicates Only` query returned an empty table. This check included `record_no`, which is unique on every row, so it could not find duplicates.
- Second check (Python, full file): excluding `record_no`, 4 groups of exact duplicate rows were found (8 rows, 4 extra copies).
- Repeated appointment IDs are not duplicates, because one appointment can have several process activities.
- Records that share the same IDs but differ in lab time or medicine name are not exact duplicates and should not be deleted (see `Duplicate_Check_Results.xlsx`).

## 3. Data Quality Observations (full file: 62,422 rows, 25 columns)
- One column (`Unnamed: 2`) is 100% empty.
- Lab (71%), imaging (91%) and pharmacy (99.5%) columns are mostly empty. This is expected, because the patient did not go to that step.
- 52 prescriptions end before they start.
- 5 prescriptions start before the appointment.
- 4,702 values in `lab_end_datetime` are in a broken format (for example `53:45.0`).
- 12 prescription start times are missing.
- Full details with row counts: `docs/data_quality_issues.md`.

## 4. Important Notes
- Power Query's column quality preview used only the first 1,000 rows, so its percentages should not be treated as final.
- Power Query errors only show data type problems. They do not show wrong dates or times.
- No data was deleted during this check.

## 5. Recommended Next Steps
- Team to agree on a decision for each issue before cleaning.
- Clean a separate copy of the data and keep a cleaning log.
- Check the broken `lab_end_datetime` values with the data source.
