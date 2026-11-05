"""Unit and Integration Tests for CareFlow Process Discovery Module.

Tests are structured in four groups:
  1. TestEventLogLoad           - PM4Py load and format correctness.
  2. TestDFGDiscovery           - DFG edge set, transition counts, timing stats.
  3. TestVariantDiscovery       - Variant coverage, ordering, known top variants.
  4. TestPetriNetDiscovery      - Structural integrity of Inductive Miner net.
  5. TestActivityStats          - Per-activity frequency calculations.
  6. TestCSVExports             - Aggregate CSV file content correctness.
  7. TestRenderOutputs          - Process map PNG/SVG file generation.

Run with:
    python -m unittest tests.test_process_discovery -v
"""

import csv
import os
import sys
import tempfile
import unittest

os.environ["MPLCONFIGDIR"] = tempfile.gettempdir()

# Ensure project root in path regardless of working directory
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(
    0,
    os.path.abspath("CareFlow-Clinical-Pathway-Process-Mining-giricharan525-debug"),
)

from process_mining.process_discovery import CareFlowProcessDiscovery


# ---------------------------------------------------------------------------
# Shared fixture – run discovery once for the full test session.
# ---------------------------------------------------------------------------

class _SharedDiscovery:
    """Singleton fixture: loads and discovers once; shared across all test classes."""
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            d = CareFlowProcessDiscovery()
            d.load_event_log()
            d.discover_dfg()
            d.discover_variants()
            d.calculate_activity_stats()
            d.discover_petri_net()
            cls._instance = d
        return cls._instance


# ---------------------------------------------------------------------------
# 1. Event log load
# ---------------------------------------------------------------------------

class TestEventLogLoad(unittest.TestCase):
    """Verify PM4Py event log load produces the expected structure."""

    @classmethod
    def setUpClass(cls):
        cls.d = _SharedDiscovery.get()
        cls.df = cls.d.df

    def test_event_count(self):
        """123,969 events must be loaded."""
        self.assertEqual(len(self.df), 123_969)

    def test_case_count(self):
        """49,912 unique cases must be present."""
        self.assertEqual(self.df["case_id"].nunique(), 49_912)

    def test_pm4py_standard_columns_added(self):
        """PM4Py format_dataframe must add XES standard alias columns."""
        self.assertIn("case:concept:name", self.df.columns)
        self.assertIn("concept:name", self.df.columns)
        self.assertIn("time:timestamp", self.df.columns)

    def test_activities_set(self):
        """Event log must contain exactly the five known clinical activities."""
        actual = set(self.df["activity"].unique())
        expected = CareFlowProcessDiscovery.KNOWN_ACTIVITIES
        self.assertEqual(actual, expected)

    def test_activity_event_counts(self):
        """Per-activity event counts must match validated event log specification."""
        counts = self.df["activity"].value_counts().to_dict()
        self.assertEqual(counts["Appointment Registration"], 49_912)
        self.assertEqual(counts["Doctor Consultation & Prescription"], 50_568)
        self.assertEqual(counts["Laboratory Examination"], 17_806)
        self.assertEqual(counts["Imaging Procedure"], 5_421)
        self.assertEqual(counts["Pharmacy Dispensing"], 262)

    def test_no_null_case_ids(self):
        """No case_id values may be null."""
        self.assertEqual(self.df["case_id"].isna().sum(), 0)

    def test_timestamp_dtype(self):
        """'time:timestamp' column must be datetime after PM4Py formatting."""
        import pandas as pd
        self.assertTrue(
            pd.api.types.is_datetime64_any_dtype(self.df["time:timestamp"])
        )


# ---------------------------------------------------------------------------
# 2. DFG discovery
# ---------------------------------------------------------------------------

class TestDFGDiscovery(unittest.TestCase):
    """Verify Directly-Follows Graph correctness."""

    @classmethod
    def setUpClass(cls):
        cls.d = _SharedDiscovery.get()
        cls.dfg = cls.d.dfg
        cls.sa = cls.d.start_activities
        cls.ea = cls.d.end_activities
        cls.stats = cls.d.transition_stats

    def test_dfg_edge_count(self):
        """DFG must have exactly 20 distinct edges."""
        self.assertEqual(len(self.dfg), 20)

    def test_dfg_total_transitions(self):
        """Sum of all DFG edge counts must equal Events - Cases = 74,057."""
        expected = 123_969 - 49_912   # = 74,057
        self.assertEqual(sum(self.dfg.values()), expected)

    def test_start_activities_sum(self):
        """Sum of start_activities counts must equal total case count."""
        self.assertEqual(sum(self.sa.values()), 49_912)

    def test_end_activities_sum(self):
        """Sum of end_activities counts must equal total case count."""
        self.assertEqual(sum(self.ea.values()), 49_912)

    def test_appointment_registration_is_dominant_start(self):
        """Appointment Registration must be the dominant start activity."""
        self.assertIn("Appointment Registration", self.sa)
        self.assertGreater(self.sa["Appointment Registration"], 49_000)

    def test_doctor_consultation_is_dominant_end(self):
        """Doctor Consultation & Prescription must be the most common end activity."""
        self.assertIn("Doctor Consultation & Prescription", self.ea)
        end_counts = dict(self.ea)
        most_common_end = max(end_counts, key=end_counts.get)
        self.assertEqual(most_common_end, "Doctor Consultation & Prescription")

    def test_top_transition_is_appointment_to_doctor(self):
        """Top DFG edge must be Appointment Registration -> Doctor Consultation."""
        top = self.stats[0]
        self.assertEqual(top["source_activity"], "Appointment Registration")
        self.assertEqual(top["target_activity"], "Doctor Consultation & Prescription")
        self.assertGreater(top["transition_count"], 47_000)

    def test_lab_self_loop_present(self):
        """Lab -> Lab self-loop must exist (multiple lab tests per encounter)."""
        self.assertIn(
            ("Laboratory Examination", "Laboratory Examination"),
            self.dfg,
        )

    def test_no_negative_transition_counts(self):
        """All DFG edge counts must be positive integers."""
        for (src, tgt), cnt in self.dfg.items():
            self.assertGreater(cnt, 0, f"Non-positive count for edge ({src}, {tgt})")

    def test_transition_stats_cover_all_edges(self):
        """transition_stats must have one row per DFG edge."""
        self.assertEqual(len(self.stats), len(self.dfg))

    def test_transition_percentages_sum_to_100(self):
        """Sum of transition percentage values must round to 100%."""
        total_pct = sum(
            float(s["transition_percentage"].rstrip("%")) for s in self.stats
        )
        self.assertAlmostEqual(total_pct, 100.0, delta=0.1)

    def test_known_edges_present(self):
        """Several clinically expected DFG edges must be present."""
        expected_edges = [
            ("Appointment Registration", "Doctor Consultation & Prescription"),
            ("Doctor Consultation & Prescription", "Laboratory Examination"),
            ("Doctor Consultation & Prescription", "Imaging Procedure"),
            ("Doctor Consultation & Prescription", "Pharmacy Dispensing"),
            ("Imaging Procedure", "Doctor Consultation & Prescription"),
            ("Laboratory Examination", "Doctor Consultation & Prescription"),
        ]
        for edge in expected_edges:
            self.assertIn(edge, self.dfg, f"Expected DFG edge missing: {edge}")

    def test_transition_stats_sorted_descending(self):
        """transition_stats must be sorted by transition_count descending."""
        counts = [s["transition_count"] for s in self.stats]
        self.assertEqual(counts, sorted(counts, reverse=True))


# ---------------------------------------------------------------------------
# 3. Variant discovery
# ---------------------------------------------------------------------------

class TestVariantDiscovery(unittest.TestCase):
    """Verify process variant discovery completeness and ordering."""

    @classmethod
    def setUpClass(cls):
        cls.d = _SharedDiscovery.get()
        cls.variants = cls.d.variants

    def test_variant_count(self):
        """Must discover exactly 287 distinct process variants."""
        self.assertEqual(len(self.variants), 287)

    def test_all_cases_covered(self):
        """Sum of variant case_count must equal total case count (49,912)."""
        total = sum(v["case_count"] for v in self.variants)
        self.assertEqual(total, 49_912)

    def test_variants_sorted_descending(self):
        """Variants must be sorted by case_count descending."""
        counts = [v["case_count"] for v in self.variants]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_top_variant_sequence(self):
        """VAR_001 must be Appointment Registration -> Doctor Consultation."""
        self.assertEqual(
            self.variants[0]["activity_sequence"],
            "Appointment Registration -> Doctor Consultation & Prescription",
        )

    def test_top_variant_dominance(self):
        """VAR_001 must account for more than 39,000 cases (>78% of encounters)."""
        self.assertGreater(self.variants[0]["case_count"], 39_000)

    def test_variant_id_format(self):
        """variant_id values must follow VAR_NNN format."""
        for i, v in enumerate(self.variants, start=1):
            self.assertEqual(v["variant_id"], f"VAR_{i:03d}")

    def test_cumulative_percentage_monotone(self):
        """Cumulative percentage must be non-decreasing across all variants."""
        cum_pcts = [
            float(v["cumulative_percentage"].rstrip("%")) for v in self.variants
        ]
        for i in range(1, len(cum_pcts)):
            self.assertGreaterEqual(
                cum_pcts[i], cum_pcts[i - 1],
                f"Cumulative pct decreased at variant {i + 1}",
            )

    def test_final_cumulative_percentage_is_100(self):
        """Final variant's cumulative_percentage must be 100.00%."""
        self.assertEqual(self.variants[-1]["cumulative_percentage"], "100.0%")

    def test_activities_length_field(self):
        """activities_length must equal actual count of activities in sequence."""
        for v in self.variants[:20]:
            seq_len = len(v["activity_sequence"].split(" -> "))
            self.assertEqual(v["activities_length"], seq_len)

    def test_top10_cumulative_exceeds_90_pct(self):
        """Top 10 variants must collectively cover >90% of cases."""
        cum = float(self.variants[9]["cumulative_percentage"].rstrip("%"))
        self.assertGreater(cum, 90.0)

    def test_no_empty_activity_sequences(self):
        """No variant may have an empty activity_sequence."""
        for v in self.variants:
            self.assertTrue(bool(v["activity_sequence"].strip()))

    def test_all_activities_in_variants_are_known(self):
        """Every activity label in variant sequences must be from the known set."""
        known = CareFlowProcessDiscovery.KNOWN_ACTIVITIES
        for v in self.variants:
            for act in v["activity_sequence"].split(" -> "):
                self.assertIn(act, known, f"Unknown activity in variant: {act!r}")


# ---------------------------------------------------------------------------
# 4. Petri net discovery
# ---------------------------------------------------------------------------

class TestPetriNetDiscovery(unittest.TestCase):
    """Verify Inductive Miner Petri net structural integrity."""

    @classmethod
    def setUpClass(cls):
        cls.d = _SharedDiscovery.get()
        cls.net = cls.d.petri_net
        cls.im = cls.d.initial_marking
        cls.fm = cls.d.final_marking

    def test_places_count(self):
        """Petri net must have exactly 17 places."""
        self.assertEqual(len(self.net.places), 17)

    def test_transitions_count(self):
        """Petri net must have exactly 21 transitions (5 visible + 16 silent)."""
        self.assertEqual(len(self.net.transitions), 21)

    def test_arcs_count(self):
        """Petri net must have exactly 48 arcs."""
        self.assertEqual(len(self.net.arcs), 48)

    def test_initial_marking_not_empty(self):
        """Initial marking must not be empty."""
        self.assertTrue(bool(self.im))

    def test_final_marking_not_empty(self):
        """Final marking must not be empty."""
        self.assertTrue(bool(self.fm))

    def test_visible_transitions_match_activities(self):
        """Visible transitions must correspond to the five known activities."""
        visible_labels = {t.label for t in self.net.transitions if t.label}
        self.assertEqual(visible_labels, CareFlowProcessDiscovery.KNOWN_ACTIVITIES)

    def test_silent_transitions_count(self):
        """Must have exactly 16 silent (tau) transitions."""
        silent = [t for t in self.net.transitions if not t.label]
        self.assertEqual(len(silent), 16)

    def test_every_place_has_arcs(self):
        """Every place must be connected by at least one arc."""
        place_names = {p.name for p in self.net.places}
        connected = set()
        for arc in self.net.arcs:
            connected.add(arc.source.name)
            connected.add(arc.target.name)
        for pname in place_names:
            self.assertIn(pname, connected, f"Place {pname} has no arcs")

    def test_every_transition_has_arcs(self):
        """Every transition must be connected by at least one arc."""
        trans_names = {t.name for t in self.net.transitions}
        connected = set()
        for arc in self.net.arcs:
            connected.add(arc.source.name)
            connected.add(arc.target.name)
        for tname in trans_names:
            self.assertIn(tname, connected, f"Transition {tname} has no arcs")


# ---------------------------------------------------------------------------
# 5. Activity statistics
# ---------------------------------------------------------------------------

class TestActivityStats(unittest.TestCase):
    """Verify per-activity frequency statistics."""

    @classmethod
    def setUpClass(cls):
        cls.d = _SharedDiscovery.get()
        cls.stats = cls.d.activity_stats

    def test_exactly_five_activities(self):
        """Must produce statistics for exactly 5 activities."""
        self.assertEqual(len(self.stats), 5)

    def test_sorted_by_event_count_descending(self):
        """Stats must be sorted by event_count descending."""
        counts = [s["event_count"] for s in self.stats]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_total_event_count_sums_correctly(self):
        """Sum of per-activity event_count must equal 123,969."""
        total = sum(s["event_count"] for s in self.stats)
        self.assertEqual(total, 123_969)

    def test_appointment_registration_full_case_coverage(self):
        """Appointment Registration must cover 100% of cases."""
        appt = next(s for s in self.stats if s["activity"] == "Appointment Registration")
        self.assertEqual(appt["unique_cases"], 49_912)
        self.assertEqual(appt["case_coverage_percent"], "100.0%")

    def test_pharmacy_dispensing_low_coverage(self):
        """Pharmacy Dispensing is an optional step covering <1% of cases."""
        pharm = next(s for s in self.stats if s["activity"] == "Pharmacy Dispensing")
        cov = float(pharm["case_coverage_percent"].rstrip("%"))
        self.assertLess(cov, 1.0)

    def test_all_activities_present(self):
        """All five activities must appear in the stats."""
        activity_names = {s["activity"] for s in self.stats}
        self.assertEqual(activity_names, CareFlowProcessDiscovery.KNOWN_ACTIVITIES)


# ---------------------------------------------------------------------------
# 6. CSV export correctness
# ---------------------------------------------------------------------------

class TestCSVExports(unittest.TestCase):
    """Verify exported aggregate CSV files for content correctness."""

    @classmethod
    def setUpClass(cls):
        cls.d = _SharedDiscovery.get()
        cls.tmp = tempfile.mkdtemp()
        cls.d.export_csvs(output_dir=cls.tmp)

    def _read_csv(self, filename):
        path = os.path.join(self.tmp, filename)
        self.assertTrue(os.path.exists(path), f"Expected CSV not found: {path}")
        with open(path, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def test_transition_frequencies_row_count(self):
        """transition_frequencies.csv must have one row per DFG edge (20)."""
        rows = self._read_csv("transition_frequencies.csv")
        self.assertEqual(len(rows), 20)

    def test_transition_frequencies_required_columns(self):
        """transition_frequencies.csv must have all required columns."""
        rows = self._read_csv("transition_frequencies.csv")
        required = {
            "source_activity", "target_activity", "transition_count",
            "transition_percentage", "mean_transition_minutes",
            "median_transition_minutes",
        }
        self.assertTrue(required.issubset(set(rows[0].keys())))

    def test_transition_frequencies_total(self):
        """Sum of transition_count column must equal 74,057."""
        rows = self._read_csv("transition_frequencies.csv")
        total = sum(int(r["transition_count"]) for r in rows)
        self.assertEqual(total, 74_057)

    def test_process_variants_row_count(self):
        """process_variants.csv must have exactly 287 rows."""
        rows = self._read_csv("process_variants.csv")
        self.assertEqual(len(rows), 287)

    def test_process_variants_case_count_sum(self):
        """Sum of case_count in process_variants.csv must equal 49,912."""
        rows = self._read_csv("process_variants.csv")
        total = sum(int(r["case_count"]) for r in rows)
        self.assertEqual(total, 49_912)

    def test_process_variants_top_row(self):
        """First row of process_variants.csv must be VAR_001 with ~39k cases."""
        rows = self._read_csv("process_variants.csv")
        self.assertEqual(rows[0]["variant_id"], "VAR_001")
        self.assertGreater(int(rows[0]["case_count"]), 39_000)

    def test_start_end_activities_row_count(self):
        """start_end_activities.csv must have exactly 5 rows (one per activity)."""
        rows = self._read_csv("start_end_activities.csv")
        self.assertEqual(len(rows), 5)

    def test_start_activities_total_in_csv(self):
        """Sum of start_count in start_end_activities.csv must equal 49,912."""
        rows = self._read_csv("start_end_activities.csv")
        total = sum(int(r["start_count"]) for r in rows)
        self.assertEqual(total, 49_912)

    def test_end_activities_total_in_csv(self):
        """Sum of end_count in start_end_activities.csv must equal 49,912."""
        rows = self._read_csv("start_end_activities.csv")
        total = sum(int(r["end_count"]) for r in rows)
        self.assertEqual(total, 49_912)

    def test_no_patient_identifiers_in_exports(self):
        """Exported aggregate CSVs must NOT contain 'patient_id' or 'case_id'."""
        for filename in [
            "transition_frequencies.csv",
            "process_variants.csv",
            "start_end_activities.csv",
        ]:
            rows = self._read_csv(filename)
            if rows:
                for forbidden in ("patient_id", "case_id"):
                    self.assertNotIn(
                        forbidden, rows[0].keys(),
                        f"{filename} must not expose column '{forbidden}'",
                    )


# ---------------------------------------------------------------------------
# 7. Process map file generation
# ---------------------------------------------------------------------------

class TestRenderOutputs(unittest.TestCase):
    """Verify that process map rendering produces non-empty PNG and SVG files."""

    @classmethod
    def setUpClass(cls):
        cls.d = _SharedDiscovery.get()
        cls.tmp = tempfile.mkdtemp()
        cls.dfg_paths = cls.d.render_dfg_map(output_dir=cls.tmp)
        cls.pn_paths = cls.d.render_petri_net_map(output_dir=cls.tmp)
        cls.var_paths = cls.d.render_variants_chart(output_dir=cls.tmp)

    def _assert_file_exists_and_nonempty(self, path, min_bytes=1000):
        self.assertTrue(os.path.exists(path), f"File not generated: {path}")
        size = os.path.getsize(path)
        self.assertGreater(
            size, min_bytes,
            f"File too small ({size} bytes), likely empty: {path}",
        )

    def test_dfg_png_generated(self):
        self._assert_file_exists_and_nonempty(self.dfg_paths["png"])

    def test_dfg_svg_generated(self):
        self._assert_file_exists_and_nonempty(self.dfg_paths["svg"], min_bytes=500)

    def test_petri_net_png_generated(self):
        self._assert_file_exists_and_nonempty(self.pn_paths["png"])

    def test_petri_net_svg_generated(self):
        self._assert_file_exists_and_nonempty(self.pn_paths["svg"], min_bytes=500)

    def test_variants_chart_png_generated(self):
        self._assert_file_exists_and_nonempty(self.var_paths["png"])

    def test_variants_chart_svg_generated(self):
        self._assert_file_exists_and_nonempty(self.var_paths["svg"], min_bytes=500)

    def test_dfg_png_is_valid_png(self):
        """DFG PNG file must start with PNG magic bytes."""
        with open(self.dfg_paths["png"], "rb") as f:
            header = f.read(8)
        self.assertEqual(header[:4], b"\x89PNG")

    def test_petri_net_png_is_valid_png(self):
        """Petri net PNG file must start with PNG magic bytes."""
        with open(self.pn_paths["png"], "rb") as f:
            header = f.read(8)
        self.assertEqual(header[:4], b"\x89PNG")

    def test_variants_chart_png_is_valid_png(self):
        """Variants chart PNG file must start with PNG magic bytes."""
        with open(self.var_paths["png"], "rb") as f:
            header = f.read(8)
        self.assertEqual(header[:4], b"\x89PNG")

    def test_dfg_svg_contains_svg_tag(self):
        """DFG SVG must contain <svg element."""
        with open(self.dfg_paths["svg"], encoding="utf-8") as f:
            content = f.read(500)
        self.assertIn("<svg", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
