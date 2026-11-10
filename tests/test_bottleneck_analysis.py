"""Unit and Integration Tests for CareFlow Bottleneck and Waiting-Time Analysis Module.

Tests are structured into 7 validation classes:
  1. TestEventLogLoad           - Verify event log dimensions and timestamp parsing.
  2. TestTransitionAnalysis     - Inter-event durations, 0 negative values, exact 74,057 total.
  3. TestActivityTurnaroundTimes- Laboratory TAT (13,175 bounded), Imaging TAT, Rx duration.
  4. TestClinicalFlowDurations  - 7 clinical flow categories, case coverage, duration rankings.
  5. TestDataQualityAudit       - Missing lab ends, missing Rx starts, inverted timestamps.
  6. TestCSVExportsAndPrivacy   - Aggregate CSVs structure, 0 patient identifiers.
  7. TestVisualizationsAndReport- PNG/SVG charts and comprehensive markdown report.

Run with:
    python -m unittest tests.test_bottleneck_analysis -v
"""

import csv
import os
import sys
import tempfile
import unittest

os.environ["MPLCONFIGDIR"] = tempfile.gettempdir()

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(
    0,
    os.path.abspath("CareFlow-Clinical-Pathway-Process-Mining-giricharan525-debug"),
)

from process_mining.bottleneck_analysis import CareFlowBottleneckAnalysis


# ---------------------------------------------------------------------------
# Shared fixture – run analysis once for all test suites
# ---------------------------------------------------------------------------

class _SharedBottleneckAnalysis:
    """Singleton fixture to run bottleneck analysis once across all test cases."""
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            analyzer = CareFlowBottleneckAnalysis()
            analyzer.load_event_log()
            analyzer.analyze_transitions()
            analyzer.analyze_activity_durations()
            analyzer.analyze_clinical_flows()
            analyzer.audit_data_quality_durations()
            cls._instance = analyzer
        return cls._instance


# ---------------------------------------------------------------------------
# 1. Event Log Load
# ---------------------------------------------------------------------------

class TestEventLogLoad(unittest.TestCase):
    """Verify event log load and timestamp preprocessing."""

    @classmethod
    def setUpClass(cls):
        cls.analyzer = _SharedBottleneckAnalysis.get()
        cls.df = cls.analyzer.df

    def test_total_events_loaded(self):
        """Must load exactly 123,969 validated events."""
        self.assertEqual(len(self.df), 123_969)

    def test_unique_cases_loaded(self):
        """Must load exactly 49,912 unique encounter cases."""
        self.assertEqual(self.df["case_id"].nunique(), 49_912)

    def test_timestamp_datetime_parsed(self):
        """timestamp_dt must be populated datetime objects with zero nulls."""
        self.assertIn("timestamp_dt", self.df.columns)
        self.assertEqual(self.df["timestamp_dt"].isna().sum(), 0)

    def test_chronological_sorting_integrity(self):
        """Events within each case must be strictly sorted by timestamp_dt and event_index."""
        # Sample test 100 cases
        cases = self.df["case_id"].unique()[:100]
        subset = self.df[self.df["case_id"].isin(cases)]
        for _, group in subset.groupby("case_id"):
            timestamps = list(group["timestamp_dt"])
            for i in range(len(timestamps) - 1):
                self.assertLessEqual(timestamps[i], timestamps[i + 1])


# ---------------------------------------------------------------------------
# 2. Inter-Event Transition & Waiting Time Analysis
# ---------------------------------------------------------------------------

class TestTransitionAnalysis(unittest.TestCase):
    """Verify inter-event transition calculations and duration statistics."""

    @classmethod
    def setUpClass(cls):
        cls.analyzer = _SharedBottleneckAnalysis.get()
        cls.trans_df = cls.analyzer.transitions_df
        cls.trans_stats = cls.analyzer.transition_stats

    def test_total_transitions_count(self):
        """Total intra-case transitions must equal (Total Events - Total Cases) = 74,057."""
        expected = 123_969 - 49_912
        self.assertEqual(len(self.trans_df), expected)
        self.assertEqual(sum(t["transition_count"] for t in self.trans_stats), expected)

    def test_zero_negative_transitions(self):
        """No transition duration may be negative (0 inversions within cases)."""
        negative_count = (self.trans_df["duration_minutes"] < 0).sum()
        self.assertEqual(negative_count, 0)

    def test_distinct_transition_pairs_count(self):
        """Must discover exactly 20 distinct (source, target) transition pairs."""
        self.assertEqual(len(self.trans_stats), 20)

    def test_top_transition_is_appointment_to_doctor(self):
        """Top transition by count must be Appointment Registration -> Doctor Consultation."""
        top = self.trans_stats[0]
        self.assertEqual(top["source_activity"], "Appointment Registration")
        self.assertEqual(top["target_activity"], "Doctor Consultation & Prescription")
        self.assertEqual(top["transition_count"], 47_964)
        self.assertEqual(top["median_duration_minutes"], 25.0)

    def test_self_loops_identified(self):
        """Must correctly flag self-loop transitions (Lab->Lab, Rx->Rx, Pharmacy->Pharmacy, Imaging->Imaging)."""
        self_loops = [t for t in self.trans_stats if t["is_self_loop"]]
        self.assertEqual(len(self_loops), 4)
        self_loop_activities = {t["source_activity"] for t in self_loops}
        expected = {
            "Laboratory Examination",
            "Doctor Consultation & Prescription",
            "Pharmacy Dispensing",
            "Imaging Procedure"
        }
        self.assertEqual(self_loop_activities, expected)

    def test_lab_self_loop_characteristics(self):
        """Lab->Lab self-loop has 11,395 occurrences and median of 0.0 minutes (batch digital entry)."""
        lab_loop = next(t for t in self.trans_stats if t["source_activity"] == "Laboratory Examination" and t["target_activity"] == "Laboratory Examination")
        self.assertEqual(lab_loop["transition_count"], 11_395)
        self.assertEqual(lab_loop["median_duration_minutes"], 0.0)

    def test_doctor_to_imaging_bottleneck(self):
        """Doctor Consultation -> Imaging Procedure must identify significant waiting time (mean > 400m)."""
        rx_img = next(t for t in self.trans_stats if t["source_activity"] == "Doctor Consultation & Prescription" and t["target_activity"] == "Imaging Procedure")
        self.assertEqual(rx_img["transition_count"], 2_981)
        self.assertEqual(rx_img["median_duration_minutes"], 35.0)
        self.assertGreater(rx_img["mean_duration_minutes"], 400.0)
        self.assertEqual(rx_img["p90_duration_minutes"], 110.0)

    def test_zero_duration_transitions_volume(self):
        """Total simultaneous transitions (duration = 0 min) must equal 11,502."""
        zero_total = sum(t["zero_duration_count"] for t in self.trans_stats)
        self.assertEqual(zero_total, 11_502)


# ---------------------------------------------------------------------------
# 3. Diagnostic & Service Turnaround Times (TAT)
# ---------------------------------------------------------------------------

class TestActivityTurnaroundTimes(unittest.TestCase):
    """Verify activity execution and turnaround time calculations."""

    @classmethod
    def setUpClass(cls):
        cls.analyzer = _SharedBottleneckAnalysis.get()
        cls.tat_stats = cls.analyzer.activity_tat_stats

    def _get_metric(self, activity_name):
        return next(r for r in self.tat_stats if r["activity_name"] == activity_name)

    def test_five_activities_evaluated(self):
        """All 5 clinical activities must be evaluated."""
        self.assertEqual(len(self.tat_stats), 5)

    def test_lab_tat_bounded_records_count(self):
        """Laboratory TAT must be calculated strictly on 13,175 verified bounded lab events."""
        lab = self._get_metric("Laboratory Examination")
        self.assertEqual(lab["total_events"], 17_806)
        self.assertEqual(lab["valid_bounded_events"], 13_175)
        self.assertEqual(lab["unbounded_missing_events"], 4_631)

    def test_lab_tat_median_and_p90(self):
        """Laboratory median TAT must be 125.0 minutes and P90 must be 470.0 minutes."""
        lab = self._get_metric("Laboratory Examination")
        self.assertEqual(lab["median_minutes"], 125.0)
        self.assertEqual(lab["p90_minutes"], 470.0)
        self.assertAlmostEqual(lab["mean_minutes"], 469.39, places=1)

    def test_imaging_tat_bounded_records_count(self):
        """Imaging TAT must be calculated on 5,412 bounded radiology procedures."""
        img = self._get_metric("Imaging Procedure")
        self.assertEqual(img["total_events"], 5_421)
        self.assertEqual(img["valid_bounded_events"], 5_412)
        self.assertEqual(img["unbounded_missing_events"], 9)
        self.assertEqual(img["median_minutes"], 3.0)
        self.assertEqual(img["p90_minutes"], 9.0)

    def test_doctor_consultation_duration_and_exclusions(self):
        """Doctor Consultation duration must be calculated on 50,506 valid orders, excluding 61 anomalies."""
        rx = self._get_metric("Doctor Consultation & Prescription")
        self.assertEqual(rx["total_events"], 50_568)
        self.assertEqual(rx["valid_bounded_events"], 50_506)
        # Excludes 12 missing start (Rule 8) + 49 inverted start>end (Rule 9) + 1 missing end = 62
        self.assertEqual(rx["unbounded_missing_events"], 62)
        self.assertEqual(rx["median_minutes"], 0.0)
        self.assertEqual(rx["p90_minutes"], 7.0)

    def test_pharmacy_dispensing_duration(self):
        """Pharmacy dispensing must have 262 valid bounded line items."""
        pharm = self._get_metric("Pharmacy Dispensing")
        self.assertEqual(pharm["total_events"], 262)
        self.assertEqual(pharm["valid_bounded_events"], 262)
        self.assertEqual(pharm["median_minutes"], 1.0)
        self.assertEqual(pharm["p90_minutes"], 2.0)

    def test_appointment_registration_point_event(self):
        """Appointment Registration is a point event with 0.0 duration."""
        reg = self._get_metric("Appointment Registration")
        self.assertEqual(reg["total_events"], 49_912)
        self.assertEqual(reg["mean_minutes"], 0.0)
        self.assertEqual(reg["median_minutes"], 0.0)


# ---------------------------------------------------------------------------
# 4. Clinical Flow Pathway Durations
# ---------------------------------------------------------------------------

class TestClinicalFlowDurations(unittest.TestCase):
    """Verify encounter throughput durations across all 7 clinical flows."""

    @classmethod
    def setUpClass(cls):
        cls.analyzer = _SharedBottleneckAnalysis.get()
        cls.flows = cls.analyzer.clinical_flow_stats

    def test_seven_clinical_flows_present(self):
        """All 7 clinical flow codes (1 through 7) must be present."""
        self.assertEqual(len(self.flows), 7)
        codes = [f["clinical_flow_code"] for f in self.flows]
        self.assertEqual(codes, [1, 2, 3, 4, 5, 6, 7])

    def test_total_cases_across_flows_equals_49912(self):
        """Sum of case counts across all clinical flows must equal 49,912."""
        total_cases = sum(f["case_count"] for f in self.flows)
        self.assertEqual(total_cases, 49_912)

    def test_dominant_flow1_metrics(self):
        """Flow 1 (Appointment -> Prescription) must have the highest volume (>39k cases) and lowest median duration."""
        flow1 = next(f for f in self.flows if f["clinical_flow_code"] == 1)
        self.assertGreater(flow1["case_count"], 39_000)
        self.assertEqual(flow1["median_duration_minutes"], 26.0)
        self.assertEqual(flow1["p90_duration_minutes"], 94.0)

    def test_multi_test_flow5_longest_median_duration(self):
        """Flow 5 (Lab + Imaging) must have the longest median duration among major flows (> 100 min)."""
        flow5 = next(f for f in self.flows if f["clinical_flow_code"] == 5)
        self.assertEqual(flow5["case_count"], 1_518)
        self.assertEqual(flow5["median_duration_minutes"], 115.5)
        self.assertEqual(flow5["p90_duration_minutes"], 438.3)


# ---------------------------------------------------------------------------
# 5. Data Quality, Missing & Suspicious Durations Audit
# ---------------------------------------------------------------------------

class TestDataQualityAudit(unittest.TestCase):
    """Verify data quality anomaly categorization and counts."""

    @classmethod
    def setUpClass(cls):
        cls.analyzer = _SharedBottleneckAnalysis.get()
        cls.dq = cls.analyzer.data_quality_stats

    def test_zero_negative_transitions(self):
        """Zero negative transition intervals."""
        self.assertEqual(self.dq["negative_transitions_count"], 0)

    def test_missing_lab_end_timestamps_reconciliation(self):
        """Missing lab end timestamps count must equal 4,631."""
        self.assertEqual(self.dq["missing_lab_end_timestamps"], 4_631)

    def test_missing_prescription_start_timestamps_count(self):
        """Missing prescription start timestamps count must equal 12 (Rule 8)."""
        self.assertEqual(self.dq["missing_prescription_start_timestamps"], 12)

    def test_inverted_prescription_timestamps_count(self):
        """Inverted prescription timestamps count must equal 49 (Rule 9)."""
        self.assertEqual(self.dq["inverted_prescription_timestamps"], 49)

    def test_zero_duration_transitions_count(self):
        """Simultaneous transitions must equal 11,502."""
        self.assertEqual(self.dq["zero_duration_transitions_count"], 11_502)

    def test_cases_exceeding_24h_percentage(self):
        """Cases exceeding 24 hours must be between 1% and 2% (low outlier frequency)."""
        pct = float(self.dq["cases_gt_24h_percent"].rstrip("%"))
        self.assertGreater(pct, 1.0)
        self.assertLess(pct, 2.0)


# ---------------------------------------------------------------------------
# 6. CSV Exports and Privacy Checks
# ---------------------------------------------------------------------------

class TestCSVExportsAndPrivacy(unittest.TestCase):
    """Verify exported aggregate CSV files for accuracy and HIPAA compliance."""

    @classmethod
    def setUpClass(cls):
        cls.analyzer = _SharedBottleneckAnalysis.get()
        cls.tmp_dir = tempfile.mkdtemp()
        cls.exported = cls.analyzer.export_csvs(output_dir=cls.tmp_dir)

    def _read_csv(self, filename):
        path = os.path.join(self.tmp_dir, filename)
        self.assertTrue(os.path.exists(path), f"File {filename} not exported")
        with open(path, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def test_transition_time_analysis_csv_rows(self):
        """transition_time_analysis.csv must have exactly 20 rows (one per DFG edge)."""
        rows = self._read_csv("transition_time_analysis.csv")
        self.assertEqual(len(rows), 20)

    def test_transition_time_analysis_required_columns(self):
        """transition_time_analysis.csv must contain all statistical columns."""
        rows = self._read_csv("transition_time_analysis.csv")
        required = {
            "source_activity", "target_activity", "transition_count",
            "mean_duration_minutes", "median_duration_minutes", "p90_duration_minutes",
            "min_duration_minutes", "max_duration_minutes", "zero_duration_count",
            "outliers_gt_24h_count", "is_self_loop"
        }
        self.assertTrue(required.issubset(set(rows[0].keys())))

    def test_bottleneck_summary_csv_rows_and_categories(self):
        """bottleneck_summary.csv must contain sections for Activity TAT, Clinical Flows, and Slow Transitions."""
        rows = self._read_csv("bottleneck_summary.csv")
        categories = {r["analysis_category"] for r in rows}
        self.assertIn("Activity Turnaround Time", categories)
        self.assertIn("Clinical Flow Case Duration", categories)
        self.assertIn("Slow Inter-Activity Transition", categories)

    def test_zero_patient_identifiers_in_csv_exports(self):
        """CRITICAL PRIVACY CHECK: Exported CSVs must NOT contain patient_id or case_id."""
        for filename in ["transition_time_analysis.csv", "bottleneck_summary.csv"]:
            rows = self._read_csv(filename)
            for r in rows:
                for forbidden in ("patient_id", "case_id", "patient_name", "doctor_name"):
                    self.assertNotIn(forbidden, r.keys())


# ---------------------------------------------------------------------------
# 7. Visualizations and Markdown Report Generation
# ---------------------------------------------------------------------------

class TestVisualizationsAndReport(unittest.TestCase):
    """Verify that all required charts (PNG + SVG) and markdown reports are generated."""

    @classmethod
    def setUpClass(cls):
        cls.analyzer = _SharedBottleneckAnalysis.get()
        cls.tmp_dir = tempfile.mkdtemp()
        cls.charts = cls.analyzer.generate_visualizations(output_dir=cls.tmp_dir)
        cls.report_path = cls.analyzer.generate_markdown_report(output_dir=cls.tmp_dir)

    def _assert_file_exists_and_valid(self, path, min_bytes=1000):
        self.assertTrue(os.path.exists(path), f"File {path} does not exist")
        self.assertGreater(os.path.getsize(path), min_bytes, f"File {path} is suspiciously small")

    def test_five_png_charts_generated_and_valid(self):
        """All 5 PNG charts must exist and have PNG magic bytes."""
        png_keys = [
            "transition_times_png", "lab_turnaround_png", "imaging_turnaround_png",
            "activity_durations_png", "slow_transitions_png"
        ]
        for k in png_keys:
            path = self.charts[k]
            self._assert_file_exists_and_valid(path)
            with open(path, "rb") as f:
                header = f.read(4)
            self.assertEqual(header, b"\x89PNG")

    def test_five_svg_charts_generated_and_valid(self):
        """All 5 SVG charts must exist and contain valid <svg root tag."""
        svg_keys = [
            "transition_times_svg", "lab_turnaround_svg", "imaging_turnaround_svg",
            "activity_durations_svg", "slow_transitions_svg"
        ]
        for k in svg_keys:
            path = self.charts[k]
            self._assert_file_exists_and_valid(path, min_bytes=500)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read(500)
            self.assertIn("<svg", content)

    def test_markdown_report_comprehensive(self):
        """bottleneck_analysis_report.md must exist, be > 5KB, and contain key analytical headings."""
        self._assert_file_exists_and_valid(self.report_path, min_bytes=5000)
        with open(self.report_path, "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn("Laboratory Examination", text)
        self.assertIn("Turnaround Time (TAT)", text)
        self.assertIn("Doctor Consultation", text)
        self.assertIn("Imaging Procedure", text)
        self.assertIn("Clinical Pathway Category", text)
        self.assertIn("Operational Recommendations for Hospital Management", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
