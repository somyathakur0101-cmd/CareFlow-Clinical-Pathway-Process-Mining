"""Unit tests for CareFlow Conformance Checking Module.

Tests PM4Py token-based replay, activity-model alignment, precision,
clinical flow-level conformance, deviation detection, variant analysis,
privacy assurance, and visualization generation.
"""

import os
import sys
import unittest
import pandas as pd
import pm4py

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from process_mining.conformance_checking import CareFlowConformanceChecking, resolve_file_path


class TestCareFlowConformanceChecking(unittest.TestCase):
    """Test suite for CareFlowConformanceChecking class."""

    @classmethod
    def setUpClass(cls):
        """Initialize checker and load data once for read-only tests."""
        cls.checker = CareFlowConformanceChecking()
        cls.checker.load_event_log()
        cls.checker.load_petri_net()

    def test_load_event_log(self):
        """Test event log loading and PM4Py formatting."""
        self.assertIsNotNone(self.checker.df)
        self.assertIsNotNone(self.checker.df_pm)
        self.assertEqual(len(self.checker.df), 123_969)
        self.assertEqual(self.checker.df["case_id"].nunique(), 49_912)

        # Check PM4Py required columns
        for col in ["case:concept:name", "concept:name", "time:timestamp"]:
            self.assertIn(col, self.checker.df_pm.columns)

    def test_load_petri_net(self):
        """Test Petri net loading and structure."""
        self.assertIsNotNone(self.checker.net)
        self.assertIsNotNone(self.checker.initial_marking)
        self.assertIsNotNone(self.checker.final_marking)

        # Petri net structural invariants
        self.assertEqual(len(self.checker.net.places), 17)
        self.assertEqual(len(self.checker.net.transitions), 21)
        self.assertEqual(len(self.checker.net.arcs), 48)

        # Check initial and final markings
        im_places = [p.name for p in self.checker.initial_marking]
        fm_places = [p.name for p in self.checker.final_marking]
        self.assertIn("source:1", str(self.checker.initial_marking))
        self.assertIn("sink:1", str(self.checker.final_marking))

    def test_activity_model_alignment(self):
        """Verify that event log activities match model visible transitions exactly."""
        verification = self.checker.verify_activity_model_alignment()
        self.assertTrue(verification["is_consistent"])
        self.assertEqual(len(verification["missing_in_model"]), 0)
        self.assertEqual(len(verification["extra_in_model"]), 0)
        self.assertEqual(len(verification["log_activities"]), 5)
        self.assertEqual(len(verification["visible_model_labels"]), 5)
        self.assertEqual(verification["silent_transition_count"], 16)

    def test_token_based_replay_execution(self):
        """Test token-based replay execution and metric correctness."""
        metrics = self.checker.run_token_based_replay()
        self.assertEqual(metrics["total_cases_replayed"], 49_912)
        self.assertEqual(metrics["fit_cases"], 49_912)
        self.assertAlmostEqual(metrics["percentage_fit_traces"], 100.0, places=1)
        self.assertAlmostEqual(metrics["log_fitness"], 1.0, places=4)
        self.assertAlmostEqual(metrics["average_trace_fitness"], 1.0, places=4)
        self.assertEqual(metrics["missing_tokens"], 0)
        self.assertEqual(metrics["remaining_tokens"], 0)
        self.assertEqual(metrics["traces_with_problems"], 0)
        self.assertGreater(metrics["produced_tokens"], 500_000)
        self.assertEqual(metrics["produced_tokens"], metrics["consumed_tokens"])

    def test_precision_and_f_measure(self):
        """Test precision score and harmonic F-measure."""
        prec = self.checker.calculate_precision()
        self.assertGreater(prec, 0.70)
        self.assertLessEqual(prec, 1.0)

        f_meas = self.checker.f_measure
        self.assertIsNotNone(f_meas)
        self.assertGreater(f_meas, 0.80)
        self.assertLessEqual(f_meas, 1.0)

    def test_clinical_flow_conformance(self):
        """Test clinical flow-level breakdown and compliance statistics."""
        flow_df = self.checker.analyze_clinical_flows()
        self.assertEqual(len(flow_df), 7)
        self.assertEqual(flow_df["total_cases"].sum(), 49_912)

        # Flow 1 should be the largest
        f1 = flow_df[flow_df["clinical_flow_code"] == 1].iloc[0]
        self.assertEqual(f1["total_cases"], 39_667)
        self.assertGreater(f1["start_conforming_pct"], 99.9)

        # Flow 3 should exhibit the highest pre-consultation imaging
        f3 = flow_df[flow_df["clinical_flow_code"] == 3].iloc[0]
        self.assertEqual(f3["total_cases"], 3_785)
        self.assertGreater(f3["out_of_order_diagnostic_pct"], 35.0)

        # Flow 2 should exhibit high lab repetition
        f2 = flow_df[flow_df["clinical_flow_code"] == 2].iloc[0]
        self.assertEqual(f2["total_cases"], 4_834)
        self.assertGreater(f2["repeated_activity_pct"], 50.0)

    def test_deviation_analysis_counts(self):
        """Test that deviation analysis identifies known clinical patterns accurately."""
        dev_df = self.checker.analyze_deviations()
        self.assertGreater(len(dev_df), 10)

        # Check required columns
        for col in ["deviation_category", "deviation_pattern", "affected_cases", "case_percentage", "clinical_interpretation"]:
            self.assertIn(col, dev_df.columns)

        # Convert to dictionary for easy lookup
        dev_dict = dict(zip(dev_df["deviation_pattern"], dev_df["affected_cases"]))

        # Specific known counts
        self.assertEqual(dev_dict.get("Registration Not First Activity"), 418)
        self.assertEqual(dev_dict.get("Sequence Inversion: Imaging Procedure Before Consultation"), 1_915)
        self.assertEqual(dev_dict.get("Sequence Inversion: Laboratory Examination Before Consultation"), 498)
        self.assertEqual(dev_dict.get("Diagnostic Precedence Deviation: Any Diagnostic Before Consultation"), 2_324)
        self.assertEqual(dev_dict.get("Sequence Inversion: Consultation Before Registration"), 5)
        self.assertEqual(dev_dict.get("Any Activity Repetition (Loop Execution)"), 4_819)
        self.assertEqual(dev_dict.get("Activity Repetition: Laboratory Examination (>=2x)"), 4_107)
        self.assertEqual(dev_dict.get("Activity Repetition: Doctor Consultation & Prescription (>=2x)"), 640)
        self.assertEqual(dev_dict.get("Flow Designation Mismatch: Activity Set vs Flow Code"), 22)
        self.assertEqual(dev_dict.get("Incomplete Trace: Single Event Encounter", 0), 0)

    def test_synthetic_trace_deviations(self):
        """Test deviation detection on synthetic mock traces."""
        # Create a small mock checker
        checker = CareFlowConformanceChecking()
        mock_data = pd.DataFrame([
            # Case 1: Standard conformant
            {"case_id": "SYNTH_01", "clinical_flow_code": 1, "activity": "Appointment Registration", "timestamp": "2026-01-01 08:00"},
            {"case_id": "SYNTH_01", "clinical_flow_code": 1, "activity": "Doctor Consultation & Prescription", "timestamp": "2026-01-01 08:30"},
            # Case 2: Imaging before registration and before consultation
            {"case_id": "SYNTH_02", "clinical_flow_code": 3, "activity": "Imaging Procedure", "timestamp": "2026-01-01 08:00"},
            {"case_id": "SYNTH_02", "clinical_flow_code": 3, "activity": "Appointment Registration", "timestamp": "2026-01-01 08:30"},
            {"case_id": "SYNTH_02", "clinical_flow_code": 3, "activity": "Doctor Consultation & Prescription", "timestamp": "2026-01-01 09:00"},
            # Case 3: Repeated lab (loop)
            {"case_id": "SYNTH_03", "clinical_flow_code": 2, "activity": "Appointment Registration", "timestamp": "2026-01-01 08:00"},
            {"case_id": "SYNTH_03", "clinical_flow_code": 2, "activity": "Doctor Consultation & Prescription", "timestamp": "2026-01-01 08:30"},
            {"case_id": "SYNTH_03", "clinical_flow_code": 2, "activity": "Laboratory Examination", "timestamp": "2026-01-01 09:00"},
            {"case_id": "SYNTH_03", "clinical_flow_code": 2, "activity": "Laboratory Examination", "timestamp": "2026-01-01 09:15"},
        ])
        checker.df = mock_data
        dev_df = checker.analyze_deviations()
        dev_dict = dict(zip(dev_df["deviation_pattern"], dev_df["affected_cases"]))

        self.assertEqual(dev_dict.get("Start Activity Deviation: First is 'Imaging Procedure'"), 1)
        self.assertEqual(dev_dict.get("Sequence Inversion: Imaging Procedure Before Consultation"), 1)
        self.assertEqual(dev_dict.get("Activity Repetition: Laboratory Examination (>=2x)"), 1)

    def test_variant_conformance(self):
        """Test process variant conformance analysis."""
        var_df = self.checker.analyze_variant_conformance(top_n=10)
        self.assertEqual(len(var_df), 10)
        self.assertIn("conformance_classification", var_df.columns)
        self.assertTrue(var_df["tbr_model_fit"].all())

        # Top variant VAR_001 should be Standard Linear Conformant
        v1 = var_df.iloc[0]
        self.assertEqual(v1["variant_id"], "VAR_001")
        self.assertEqual(v1["conformance_classification"], "Standard Linear Conformant")

        # Top variant VAR_004 should be Pre-Consultation Diagnostic Variant
        v4 = var_df[var_df["variant_id"] == "VAR_004"].iloc[0]
        self.assertEqual(v4["conformance_classification"], "Pre-Consultation Diagnostic Variant")

    def test_privacy_assurance(self):
        """Verify that exported CSVs contain zero patient-level or encounter-level identifiers."""
        summary_csv = resolve_file_path("outputs/conformance_summary.csv")
        dev_csv = resolve_file_path("outputs/deviation_analysis.csv")

        self.assertTrue(os.path.exists(summary_csv))
        self.assertTrue(os.path.exists(dev_csv))

        for path in [summary_csv, dev_csv]:
            df = pd.read_csv(path)
            for col in df.columns:
                self.assertNotIn("patient_id", col.lower())
                self.assertNotIn("case_id", col.lower())

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertNotIn("PAT_", content)
                self.assertNotIn("ENC_", content)

    def test_visualization_generation(self):
        """Verify that visualization files exist, are non-empty, and valid."""
        png_path = resolve_file_path("outputs/conformance_visualization.png")
        svg_path = resolve_file_path("outputs/conformance_visualization.svg")

        self.assertTrue(os.path.exists(png_path))
        self.assertTrue(os.path.exists(svg_path))

        png_size = os.path.getsize(png_path)
        svg_size = os.path.getsize(svg_path)

        self.assertGreater(png_size, 50_000, "PNG file is too small.")
        self.assertGreater(svg_size, 20_000, "SVG file is too small.")

        # Verify PNG magic bytes
        with open(png_path, "rb") as f:
            header = f.read(8)
            self.assertEqual(header, b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
