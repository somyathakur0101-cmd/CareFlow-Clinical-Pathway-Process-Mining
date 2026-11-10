# CareFlow Power BI Implementation Guide

## Executive Overview
This guide provides complete instructions for importing the CareFlow Clinical Pathway Process Mining dataset into **Microsoft Power BI Desktop**, configuring relationships, creating DAX measures, and authoring interactive reports.

> [!NOTE]
> **Deployment Status**: 
> - **Data Preparation**: Completed. 9 clean, pre-aggregated, privacy-safe CSV files are generated in `outputs/power_bi/`.
> - **Privacy Assurance**: 100% compliant. Zero patient IDs or encounter-level records exist in the Power BI dataset.
> - **Power BI Service Deployment**: Not deployed to Power BI Cloud Service (requires Microsoft 365 organization tenant credentials and gateway configuration).

---

## 1. Prepared Dataset Files (`outputs/power_bi/`)

| File Name | Purpose | Records | Key Columns |
|---|---|---|---|
| `CareFlow_PowerBI_KPIs.csv` | Executive benchmark cards | 16 | `Metric`, `Value`, `Category`, `Format` |
| `CareFlow_PowerBI_Monthly_Trends.csv` | 24-month longitudinal volume trend | 23 | `month`, `appointment_count` |
| `CareFlow_PowerBI_Weekday_Distribution.csv` | Day-of-week arrival volume | 7 | `weekday`, `appointment_count` |
| `CareFlow_PowerBI_Patient_Visits.csv` | Single vs repeat visit distribution | 11 | `visits_count`, `patient_count`, `percentage` |
| `CareFlow_PowerBI_Activities.csv` | Clinical service demand & reach | 5 | `activity`, `absolute_frequency`, `case_frequency`, `percentage` |
| `CareFlow_PowerBI_Transitions.csv` | Inter-activity wait times & bottlenecks | 20 | `source_activity`, `target_activity`, `count`, `median_minutes`, `p90_minutes` |
| `CareFlow_PowerBI_Variants.csv` | 287 process pathways & Pareto coverage | 287 | `variant_id`, `activity_sequence`, `case_count`, `case_percentage`, `cumulative_percentage` |
| `CareFlow_PowerBI_Deviations.csv` | 18 clinical sequence deviations | 18 | `deviation_category`, `deviation_pattern`, `affected_cases`, `case_percentage` |
| `CareFlow_PowerBI_Clinical_Flows.csv` | Cross-flow compliance & loop breakdown | 7 | `Flow_Code`, `Flow_Name`, `Total_Cases`, `Start_Conforming_Pct`, `Pre_Consult_Diag_Pct` |

---

## 2. Power BI Data Model Architecture (Star Schema)

In Power BI Desktop:
1. Open Power BI Desktop and select **Get Data** → **Text/CSV**.
2. Navigate to `outputs/power_bi/` and import all 9 CSV files.
3. In **Model View**, establish the following relationships:
   - `CareFlow_PowerBI_Activities[activity]` (1) $\rightarrow$ ($\infty$) `CareFlow_PowerBI_Transitions[source_activity]`
   - `CareFlow_PowerBI_Clinical_Flows[Flow_Code]` (1) $\rightarrow$ ($\infty$) `CareFlow_PowerBI_KPIs` (Inactive / Slicer)

---

## 3. Recommended DAX Measures

Create a dedicated measures table `_CareFlow_Measures`:

```dax
// 1. Total Encounters
Total_Appointments = 
SUM('CareFlow_PowerBI_Clinical_Flows'[Total_Cases])

// 2. Average Trace Length
Weighted_Avg_Trace_Length = 
DIVIDE(
    SUMX('CareFlow_PowerBI_Clinical_Flows', 'CareFlow_PowerBI_Clinical_Flows'[Total_Cases] * 'CareFlow_PowerBI_Clinical_Flows'[Avg_Trace_Length]),
    [Total_Appointments],
    0
)

// 3. Pre-Consultation Diagnostic Cases
Pre_Consult_Diagnostic_Cases = 
SUMX(
    'CareFlow_PowerBI_Clinical_Flows', 
    'CareFlow_PowerBI_Clinical_Flows'[Total_Cases] * ('CareFlow_PowerBI_Clinical_Flows'[Pre_Consult_Diag_Pct] / 100)
)

// 4. Activity Loop Rate
Overall_Loop_Rate = 
DIVIDE(
    SUMX('CareFlow_PowerBI_Clinical_Flows', 'CareFlow_PowerBI_Clinical_Flows'[Total_Cases] * ('CareFlow_PowerBI_Clinical_Flows'[Loop_Repetition_Pct] / 100)),
    [Total_Appointments],
    0
)

// 5. Registration Compliance Rate
Registration_Compliance_Rate = 
DIVIDE(
    SUMX('CareFlow_PowerBI_Clinical_Flows', 'CareFlow_PowerBI_Clinical_Flows'[Total_Cases] * ('CareFlow_PowerBI_Clinical_Flows'[Start_Conforming_Pct] / 100)),
    [Total_Appointments],
    0
)
```

---

## 4. Visual Dashboard Construction (5 Report Tabs)

### Tab 1: Executive Overview
- **Card Visuals**: Total Appointments (`49,912`), Unique Patients (`39,442`), Total Events (`123,969`), Model Fitness (`100.0%`).
- **Line and Clustered Column Chart**: Monthly trends (`CareFlow_PowerBI_Monthly_Trends.csv`).
- **Clustered Bar Chart**: Weekday appointment volume (`CareFlow_PowerBI_Weekday_Distribution.csv`).

### Tab 2: Patient & Appointment Analysis
- **Donut Chart**: Patient return frequency (`visits_count` vs `patient_count`).
- **Bar Chart**: Patient volume by number of completed visits.
- **Funnel Chart**: Clinical service cascading reach (`CareFlow_PowerBI_Activities.csv`).

### Tab 3: Process Discovery
- **Decomposition Tree / Matrix**: Source Activity $\rightarrow$ Target Activity $\rightarrow$ Transition Count.
- **Pareto Chart**: Top 10 process variants by volume with cumulative percentage line (`CareFlow_PowerBI_Variants.csv`).
- **Table Visual**: Searchable variants explorer.

### Tab 4: Bottleneck Analysis
- **Clustered Bar Chart**: Slowest transitions by Median Wait vs 90th Percentile (`CareFlow_PowerBI_Transitions.csv`).
- **KPI Cards**: Laboratory Median TAT (`125.0 min`), Imaging Median TAT (`3.0 min`), Intake Wait (`48.0 min`).
- **Table Visual**: Data quality anomalies and timestamp audit metrics.

### Tab 5: Conformance Checking
- **Grouped Bar Chart**: Clinical flow comparison (Start Compliance % vs Pre-Consult Diagnostics % vs Loop % across Flows 1–7).
- **Horizontal Bar Chart**: Top empirical sequence deviations (`CareFlow_PowerBI_Deviations.csv`).
- **Callout Card**: Prominent disclaimer highlighting that the Petri net is an empirical reference model and not an approved medical guideline.

