# CareFlow – Member 1: Dataset Understanding

## 1. Dataset overview
- **File:** `HospitalOPD-noname (1).csv`
- **Rows:** 62,422
- **Columns:** 25
- **Dataset context:** Hospital outpatient department (OPD) workflow data, with appointment, prescription, laboratory, imaging, pharmacy, and flow information.

## 2. Column names, data types, and meanings

| Column | Pandas data type | Non-missing values | Missing values | Meaning (inferred from column name) |
|---|---:|---:|---:|---|
| `record_no` | `int64` | 62422 | 0 | Record/row identifier |
| `patient_id` | `int64` | 62422 | 0 | Identifier for the patient |
| `Unnamed: 2` | `float64` | 0 | 62422 | Unnamed column; all values are missing in this dataset |
| `appointment_id` | `int64` | 62422 | 0 | Identifier for the appointment |
| `appointment_start_datetime` | `object` | 62422 | 0 | Appointment start date and time |
| `prescription_doctor_id` | `int64` | 62422 | 0 | Identifier for the prescribing doctor |
| `prescription_doctor_name` | `object` | 62422 | 0 | Name of the prescribing doctor |
| `prescription_order_id` | `int64` | 62422 | 0 | Identifier for the prescription order |
| `prescription_start_datetime` | `object` | 62410 | 12 | Prescription start date and time |
| `prescription_end_datetime` | `object` | 62421 | 1 | Prescription end date and time |
| `lab_id` | `float64` | 18029 | 44393 | Identifier for a laboratory event/test |
| `lab_name` | `object` | 18029 | 44393 | Name of the laboratory test |
| `lab_start_datetime` | `object` | 18029 | 44393 | Laboratory event start date and time |
| `lab_end_datetime` | `object` | 18029 | 44393 | Laboratory event end date and time |
| `imaging_request_id` | `float64` | 5523 | 56899 | Identifier for an imaging request |
| `imaging_result_id` | `float64` | 5523 | 56899 | Identifier for an imaging result |
| `imaging_name` | `object` | 5523 | 56899 | Name/type of imaging |
| `imaging_start_datetime` | `object` | 5523 | 56899 | Imaging event start date and time |
| `imaging_end_datetime` | `object` | 5513 | 56909 | Imaging event end date and time |
| `pharmacy_sale_line_id` | `float64` | 302 | 62120 | Identifier for a pharmacy sale line |
| `medicine_name` | `object` | 302 | 62120 | Name of the medicine |
| `pharmacy_start_datetime` | `object` | 302 | 62120 | Pharmacy event start date and time |
| `pharmacy_end_datetime` | `object` | 302 | 62120 | Pharmacy event end date and time |
| `flow_code` | `int64` | 62422 | 0 | Numeric code for the recorded process flow |
| `flow_name` | `object` | 62422 | 0 | Name/description of the recorded process flow |

## 3. Main observations
1. The dataset contains 62,422 records and 25 columns.
2. Six columns are `int64`, five are `float64`, and fourteen are `object`.
3. Date/time-like columns are currently stored as `object` and should be checked and parsed as datetime values during preprocessing.
4. `Unnamed: 2` contains no populated values in the inspected file; confirm whether it can be excluded.
5. Lab, imaging, and pharmacy fields have many missing values. These may represent events that did not occur for every record, rather than automatically indicating bad data. Review with the team before imputing or deleting.
6. Column meanings above are inferred from names; confirm them against project documentation or the dataset provider's data dictionary where available.

## 4. Conclusion
The initial structure and data types have been reviewed. The next step is for the team to combine this schema review with missing-value analysis and data-quality checks, then agree on cleaning rules before modifying the dataset.

## 5. Reproducible Python code
```python
import pandas as pd

df = pd.read_csv("HospitalOPD-noname (1).csv")

print("Dataset shape:", df.shape)
print("\nColumn names:")
print(df.columns.tolist())

print("\nData types:")
print(df.dtypes)

print("\nDataset information:")
df.info()

schema = pd.DataFrame({
    "column_name": df.columns,
    "data_type": [str(df[col].dtype) for col in df.columns],
    "non_null_count": [df[col].notna().sum() for col in df.columns],
    "missing_count": [df[col].isna().sum() for col in df.columns],
    "missing_percentage": [(df[col].isna().mean() * 100).round(2) for col in df.columns]
})
print(schema.to_string(index=False))
```
