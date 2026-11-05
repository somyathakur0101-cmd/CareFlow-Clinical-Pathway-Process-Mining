"""Unit and Validation Tests for CareFlow Event-Log Generator."""

import os
import sys
import unittest
import datetime

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(
    0,
    os.path.abspath(
        "CareFlow-Clinical-Pathway-Process-Mining-giricharan525-debug"
    ),
)

from process_mining.event_log import CareFlowEventLogGenerator


class TestCareFlowEventLog(unittest.TestCase):
    """Automated validation tests for CareFlow event log generation."""

    @classmethod
    def setUpClass(cls):
        """Generate event log once for all tests."""
        cls.generator = CareFlowEventLogGenerator()
        cls.events = cls.generator.extract_events()
        cls.cases = cls.generator.cases

    def test_total_event_count(self):
        """Verify total event count exactly matches reconciled expectations."""
        self.assertEqual(
            len(self.events),
            123969,
            f"Expected 123,969 total events, got {len(self.events)}",
        )

    def test_activity_breakdown_counts(self):
        """Verify individual activity counts match deduplicated entity totals."""
        from collections import Counter

        counts = Counter([e["activity"] for e in self.events])
        self.assertEqual(
            counts["Appointment Registration"],
            49912,
            "Appointment Registration count mismatch",
        )
        self.assertEqual(
            counts["Doctor Consultation & Prescription"],
            50568,
            "Doctor Consultation count mismatch",
        )
        self.assertEqual(
            counts["Laboratory Examination"],
            17806,
            "Laboratory Examination count mismatch",
        )
        self.assertEqual(
            counts["Imaging Procedure"],
            5421,
            "Imaging Procedure count mismatch",
        )
        self.assertEqual(
            counts["Pharmacy Dispensing"], 262, "Pharmacy Dispensing count mismatch"
        )

    def test_unique_event_ids(self):
        """Verify 100% uniqueness of all event IDs with 0 duplicates."""
        event_ids = [e["event_id"] for e in self.events]
        self.assertEqual(
            len(event_ids),
            len(set(event_ids)),
            f"Found {len(event_ids) - len(set(event_ids))} duplicate event IDs!",
        )

    def test_no_missing_case_or_patient_ids(self):
        """Verify that every event has a non-empty case_id and patient_id."""
        for e in self.events:
            self.assertTrue(
                bool(e["case_id"]), f"Event {e['event_id']} has empty case_id"
            )
            self.assertTrue(
                bool(e["patient_id"]),
                f"Event {e['event_id']} has empty patient_id",
            )

    def test_timestamp_validity(self):
        """Verify that all timestamp strings parse to valid datetime objects."""
        for e in self.events:
            ts = e["timestamp"]
            self.assertTrue(
                bool(ts), f"Event {e['event_id']} has missing timestamp"
            )
            try:
                dt = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                self.assertIsInstance(dt, datetime.datetime)
            except ValueError as ex:
                self.fail(
                    f"Timestamp '{ts}' in event {e['event_id']} is invalid: {ex}"
                )

    def test_case_chronological_ordering(self):
        """Verify that events within every case are sorted in non-decreasing chronological order."""
        for case_id, case_evs in self.cases.items():
            for i in range(len(case_evs) - 1):
                t1 = datetime.datetime.strptime(
                    case_evs[i]["timestamp"], "%Y-%m-%d %H:%M:%S"
                )
                t2 = datetime.datetime.strptime(
                    case_evs[i + 1]["timestamp"], "%Y-%m-%d %H:%M:%S"
                )
                self.assertLessEqual(
                    t1,
                    t2,
                    f"Chronological inversion in Case {case_id}: {case_evs[i]['activity']} ({t1}) > {case_evs[i+1]['activity']} ({t2})",
                )

    def test_missing_start_timestamp_rule(self):
        """Verify Rule 8: Missing start timestamp orders do not fabricate start, mark lifecycle=complete."""
        missing_start_events = [
            e
            for e in self.events
            if "flag_prescription_start_missing" in e["data_quality_flags"]
        ]
        self.assertEqual(
            len(missing_start_events),
            12,
            f"Expected 12 events with flag_prescription_start_missing, found {len(missing_start_events)}",
        )
        for e in missing_start_events:
            self.assertEqual(
                e["activity"], "Doctor Consultation & Prescription"
            )
            self.assertEqual(
                e["start_timestamp"],
                "",
                "Start timestamp must remain empty when missing in source",
            )
            self.assertTrue(
                bool(e["complete_timestamp"]),
                "Complete timestamp should be populated",
            )
            self.assertEqual(
                e["lifecycle"],
                "complete",
                "Lifecycle must be 'complete' for completion-only event",
            )

    def test_inverted_prescription_timestamp_rule(self):
        """Verify Rule 9: Inverted timestamps preserve source, blank duration, retain audit flag."""
        inverted_events = [
            e
            for e in self.events
            if "flag_prescription_end_before_start" in e["data_quality_flags"]
        ]
        self.assertEqual(
            len(inverted_events),
            49,
            f"Expected 49 deduplicated events with flag_prescription_end_before_start, found {len(inverted_events)}",
        )
        for e in inverted_events:
            self.assertEqual(
                e["activity"], "Doctor Consultation & Prescription"
            )
            self.assertEqual(
                e["duration_minutes"],
                "",
                "Duration must be empty/null for inverted timestamps",
            )

    def test_reconciliation_numbers(self):
        """Verify documented count definitions from workbook."""
        stats = self.generator.reconciliation_stats
        self.assertEqual(stats["raw_lab_rows_missing_end"], 4702)
        self.assertEqual(stats["dedup_labs_missing_end"], 4631)
        self.assertEqual(stats["raw_lab_rows_with_end"], 13327)
        self.assertEqual(stats["dedup_labs_with_end"], 13175)
        self.assertEqual(stats["raw_pharmacy_rows"], 302)
        self.assertEqual(stats["dedup_pharmacy_events"], 262)
        self.assertEqual(stats["raw_rx_end_before_start"], 52)
        self.assertEqual(stats["dedup_rx_end_before_start"], 49)
        self.assertEqual(stats["raw_rx_start_missing"], 12)
        self.assertEqual(stats["dedup_rx_start_missing"], 12)


if __name__ == "__main__":
    unittest.main()
