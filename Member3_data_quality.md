# Member 3 – Duplicate Records and Data Quality Check

## 1. Objective
To identify exact duplicate records and potential data quality issues in the HospitalOPD dataset.

## 2. Duplicate Records Check
- Checked for exact duplicate rows using Power Query.
- Grouped records using all columns, excluding the temporary Index column.
- The `Duplicates Only` query returned an empty table.
- No exact duplicate rows were identified in the current check.
- Repeated appointment IDs are not necessarily duplicates because different process activities may belong to the same appointment.

## 3. Data Quality Observations
- A blank-name column was observed with 100% empty values in the preview.
- Lab-related columns showed a high proportion of empty values.
- Imaging-related columns showed a high proportion of empty values.
- Pharmacy-related columns showed a high proportion of empty values.
- No errors were visible in the columns checked during the initial review.

## 4. Important Notes
- The column-quality preview was based on the first 1,000 rows, so these observations should not be treated as final percentages for the entire dataset.
- Empty lab, imaging, and pharmacy values may indicate that these activities were not performed.
- No data was deleted during this initial check.

## 5. Recommended Next Steps
- Verify data quality across the complete dataset.
- Investigate the blank-name column before removing it.
- Review missing values and errors before deciding on cleaning actions.
