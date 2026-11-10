"""Unit tests for CareFlow Streamlit Dashboard.

Tests data loaders, aggregate metrics accuracy, privacy protections,
page component imports, and Power BI dataset export integrity.
"""

import os
import sys
import unittest
import pandas as pd

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dashboard.components import data_loader
from dashboard.components import (
    page_executive,
    page_patient_eda,
    page_process_discovery,
    page_bottleneck,
    page_conformance,
)


class TestCareFlowDashboard(unittest.TestCase):
    """Test suite for CareFlow interactive dashboard and components."""

    def test_kpi_constants(self):
        """Test executive KPI metrics accuracy."""
        kpis = data_loader.load_kpis()
        self.assertEqual(kpis["unique_patients"], 39_442)
        self.assertEqual(kpis["unique_appointments"], 49_912)
        self.assertEqual(kpis["total_events"], 123_969)
        self.assertEqual(kpis["activity_categories"], 5)
        self.assertEqual(kpis["process_variants"], 287)
        self.assertEqual(kpis["tbr_fitness"], 1.0)
        self.assertAlmostEqual(kpis["tbr_precision"], 0.7914, places=3)
        self.assertAlmostEqual(kpis["tbr_f_measure"], 0.8836, places=3)

    def test_temporal_monthly_data(self):
        """Test monthly trend data loader."""
        df = data_loader.load_temporal_monthly()
        self.assertFalse(df.empty)
        self.assertIn("month", df.columns)
        self.assertIn("appointment_count", df.columns)
        self.assertEqual(df["appointment_count"].sum(), 49_912)

    def test_temporal_weekday_data(self):
        """Test weekday distribution data loader."""
        df = data_loader.load_temporal_weekday()
        self.assertEqual(len(df), 7)
        self.assertEqual(df["appointment_count"].sum(), 49_912)
        mon = df[df["weekday"] == "Monday"].iloc[0]
        self.assertEqual(mon["appointment_count"], 10_042)

    def test_patient_visit_distribution(self):
        """Test patient visit frequency data loader."""
        df = data_loader.load_patient_visits()
        self.assertFalse(df.empty)
        self.assertEqual(df["patient_count"].sum(), 39_442)
        v1 = df[df["visits_count"] == 1].iloc[0]
        self.assertEqual(v1["patient_count"], 32_322)
        self.assertAlmostEqual(v1["percentage"], 81.95, places=1)

    def test_activity_frequencies(self):
        """Test activity frequencies data loader."""
        df = data_loader.load_activity_frequencies()
        self.assertEqual(len(df), 5)
        self.assertIn("activity", df.columns)
        count_col = "event_count" if "event_count" in df.columns else "absolute_frequency"
        self.assertIn(count_col, df.columns)
        self.assertEqual(df[count_col].sum(), 123_969)

    def test_process_variants_data(self):
        """Test process variants data loader."""
        df = data_loader.load_process_variants()
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 287)
        top = df.iloc[0]
        self.assertEqual(top["variant_id"], "VAR_001")
        self.assertEqual(top["case_count"], 39_197)

    def test_transition_times_data(self):
        """Test transition times data loader."""
        df = data_loader.load_transition_times()
        self.assertEqual(len(df), 20)
        med_col = "median_duration_minutes" if "median_duration_minutes" in df.columns else "median_minutes"
        p90_col = "p90_duration_minutes" if "p90_duration_minutes" in df.columns else "p90_minutes"
        cnt_col = "transition_count" if "transition_count" in df.columns else "count"
        self.assertIn(med_col, df.columns)
        self.assertIn(p90_col, df.columns)
        self.assertEqual(df[cnt_col].sum(), 74_057)

    def test_clinical_flows_data(self):
        """Test clinical flows data loader."""
        df = data_loader.load_clinical_flows()
        self.assertEqual(len(df), 7)
        self.assertEqual(df["Total_Cases"].sum(), 49_912)

    def test_conformance_and_deviations_data(self):
        """Test conformance summary and deviation analysis loaders."""
        summary = data_loader.load_conformance_summary()
        self.assertFalse(summary.empty)
        devs = data_loader.load_deviation_analysis()
        self.assertGreaterEqual(len(devs), 18)

    def test_strict_privacy_protections(self):
        """Verify that NO loaded dataframe contains patient or case identifiers."""
        loaders = [
            data_loader.load_temporal_monthly,
            data_loader.load_temporal_weekday,
            data_loader.load_temporal_hourly,
            data_loader.load_patient_visits,
            data_loader.load_activity_frequencies,
            data_loader.load_start_end_activities,
            data_loader.load_process_variants,
            data_loader.load_transition_times,
            data_loader.load_conformance_summary,
            data_loader.load_deviation_analysis,
            data_loader.load_clinical_flows,
        ]
        for loader in loaders:
            df = loader()
            if not df.empty:
                for col in df.columns:
                    self.assertNotIn("patient_id", col.lower())
                    self.assertNotIn("case_id", col.lower())

                # Check string contents
                str_rep = df.to_string()
                self.assertNotIn("PAT_", str_rep)
                self.assertNotIn("ENC_", str_rep)

    def test_power_bi_datasets_exist_and_clean(self):
        """Verify all 9 Power BI datasets exist and contain zero private identifiers."""
        pbi_dir = data_loader.resolve_data_path("outputs/power_bi")
        self.assertTrue(os.path.exists(pbi_dir))

        expected_files = [
            "CareFlow_PowerBI_KPIs.csv",
            "CareFlow_PowerBI_Monthly_Trends.csv",
            "CareFlow_PowerBI_Weekday_Distribution.csv",
            "CareFlow_PowerBI_Patient_Visits.csv",
            "CareFlow_PowerBI_Activities.csv",
            "CareFlow_PowerBI_Transitions.csv",
            "CareFlow_PowerBI_Variants.csv",
            "CareFlow_PowerBI_Deviations.csv",
            "CareFlow_PowerBI_Clinical_Flows.csv",
        ]
        for f in expected_files:
            file_path = os.path.join(pbi_dir, f)
            self.assertTrue(os.path.exists(file_path), f"Missing Power BI file: {f}")
            self.assertGreater(os.path.getsize(file_path), 50, f"File {f} is empty")

            with open(file_path, "r", encoding="utf-8") as fp:
                txt = fp.read()
                self.assertNotIn("PAT_", txt)
                self.assertNotIn("ENC_", txt)
                self.assertNotIn("patient_id", txt.lower())
                self.assertNotIn("case_id", txt.lower())


if __name__ == "__main__":
    unittest.main()
