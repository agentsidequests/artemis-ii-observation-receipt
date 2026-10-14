from __future__ import annotations

import csv
import io
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage11n_flash_exposure_audit import (  # noqa: E402
    audit_stage11n,
    render_event_receipt,
    verify_hard_negatives,
)


class Stage11NFlashExposureAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = audit_stage11n(ROOT)

    def test_baseline_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_FLASH_EXPOSURE_RECEIPT", self.result["evidence_state"])
        self.assertEqual("UNAVAILABLE_FROM_PUBLIC_RECORD", self.result["calibrated_flux_state"])

    def test_witness_pattern(self) -> None:
        metrics = self.result["witness_metrics"]
        self.assertEqual(5, metrics["annotated_events"])
        self.assertEqual(8, metrics["witness_marks"])
        self.assertEqual(3, metrics["distinct_observers"])
        self.assertEqual(3, metrics["single_witness_events"])
        self.assertEqual(2, metrics["multi_witness_events"])
        self.assertEqual(1, metrics["triple_witness_events"])

    def test_high_rate_video_is_later_null_window(self) -> None:
        camera = self.result["camera_window"]
        self.assertEqual(913, camera["starts_after_ledger_seconds"])
        self.assertEqual(30.0, camera["acquisition_frame_rate_fps"])
        self.assertEqual(130, camera["duration_seconds"])
        self.assertFalse(camera["simultaneous_with_any_ledgered_event"])

    def test_distance_geometry_is_illustrative_not_photometry(self) -> None:
        geometry = self.result["geometry"]
        self.assertAlmostEqual(26.96, geometry["inverse_square_received_flux_advantage"], places=1)
        self.assertAlmostEqual(3.58, geometry["magnitude_advantage"], places=2)
        self.assertFalse(geometry["rate_values_are_valid_flux_estimates"])
        self.assertIn("not photometric calibration", geometry["interpretation"].casefold())

    def test_conservative_count_floor_is_not_promoted_to_calibrated_flux(self) -> None:
        geometry = self.result["geometry"]
        self.assertAlmostEqual(
            1.31e-7,
            geometry["all_lunar_one_hour_detected_count_floor_km2_hour"],
            delta=0.01e-7,
        )
        self.assertEqual("CONSERVATIVE_OBSERVED_COUNT_DENSITY_ONLY", geometry["count_floor_status"])
        self.assertFalse(self.result["claim_boundaries"]["conservative_count_floor_is_promoted_to_completeness_corrected_flux"])
        self.assertEqual("UNAVAILABLE_FROM_PUBLIC_RECORD", self.result["calibrated_flux_state"])

    def test_every_claim_mutation_is_rejected(self) -> None:
        result = verify_hard_negatives(ROOT)
        self.assertTrue(result["pass"])
        self.assertEqual(10, len(result["hard_negatives"]))
        for outcome in result["hard_negatives"].values():
            self.assertTrue(outcome["rejected"])
            self.assertIn("claim_and_method_boundaries", outcome["failed_checks"])

    def test_event_receipt_does_not_invent_exact_mapping(self) -> None:
        payload = render_event_receipt(self.result).decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(payload)))
        self.assertEqual(5, len(rows))
        for row in rows:
            self.assertEqual("not independently resolved", row["exact_event_utc"])
            self.assertEqual("not assigned one-to-one", row["transcript_mapping"])
            self.assertEqual("not established", row["overlapping_30fps_event_frame"])

    def test_overlap_clip_is_context_not_exclusion(self) -> None:
        overlap = self.result["overlap_camera"]
        self.assertEqual("VERIFIED_BOUNDED_EXTRACTION", overlap["transport_state"])
        self.assertEqual(900, overlap["frames_screened"])
        self.assertEqual(10, overlap["apparent_lunar_diameter_pixels"])
        self.assertEqual(0, overlap["screened_pulse_candidates"])
        self.assertFalse(overlap["screen_excludes_crew_event"])
        self.assertFalse(overlap["source_pixel_photometry"])

    def test_ground_candidate_is_not_promoted_to_match(self) -> None:
        state = self.result["ground_correlation_state"].casefold()
        self.assertIn("candidate", state)
        self.assertIn("did not identify it as a confirmed match", state)
        self.assertFalse(self.result["claim_boundaries"]["citizen_candidate_is_confirmed_ground_match"])

    def test_recommendations_are_explicit_and_testable(self) -> None:
        recommendations = self.result["recommendations"]
        self.assertEqual(8, len(recommendations))
        for item in recommendations:
            self.assertTrue(item["requirement"])
            self.assertTrue(item["acceptance"])

    def test_claim_ceiling_names_key_limits(self) -> None:
        ceiling = self.result["claim_ceiling"].casefold()
        for phrase in (
            "independently measured impact rate",
            "exact one-to-one timing",
            "simultaneous camera non-detection",
            "ground match to a crew event",
            "nasa acceptance",
            "global novelty",
            "event exclusion",
        ):
            self.assertIn(phrase, ceiling)

    def test_saved_result_matches_when_present(self) -> None:
        path = ROOT / "results/stage11n-result.json"
        if not path.exists():
            self.skipTest("Stage 11N result has not been rendered yet.")
        saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(saved["pass"])
        self.assertEqual(self.result["witness_metrics"], saved["witness_metrics"])
        self.assertEqual(self.result["camera_window"], saved["camera_window"])


if __name__ == "__main__":
    unittest.main()
