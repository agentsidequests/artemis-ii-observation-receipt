from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage8b_stimulus_recoverability import verify_sources  # noqa: E402


class Stage8BStimulusRecoverabilityTests(unittest.TestCase):
    def test_archive_supports_camera_proxy_not_human_stimulus_reconstruction(self) -> None:
        result = verify_sources(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(
            "CAMERA_NATIVE_STIMULUS_PROXY_AVAILABLE", result["evidence_state"]
        )
        self.assertEqual("ADMIT_SEPARATE_CAMERA_NATIVE_CANARY", result["disposition"])
        self.assertTrue(all(result["dimensions"][key]["satisfied"] for key in "ABCD"))
        self.assertFalse(result["dimensions"]["E"]["satisfied"])
        self.assertFalse(result["dimensions"]["F"]["satisfied"])

    def test_selected_labels_bind_time_targets_settings_and_dense_control_points(self) -> None:
        result = verify_sources(ROOT)
        by_id = {item["id"]: item for item in result["checks"]}
        self.assertTrue(by_id["selected_pds4_label_contracts"]["pass"])
        self.assertTrue(by_id["official_coordinate_control_points"]["pass"])
        self.assertEqual(
            976,
            by_id["selected_pds4_label_contracts"]["products"][
                "art002e012219_nkd5015_prc_v01"
            ]["pixel_intercept_count"],
        )
        self.assertEqual(
            1408,
            by_id["selected_pds4_label_contracts"]["products"][
                "art002e012252_nkd5015_prc_v01"
            ]["pixel_intercept_count"],
        )

    def test_three_images_and_one_calendar_stay_inside_budget(self) -> None:
        result = verify_sources(ROOT)
        by_id = {item["id"]: item for item in result["checks"]}
        self.assertTrue(by_id["bounded_three_scene_acquisition"]["pass"])
        self.assertTrue(by_id["decoded_visible_browse_images"]["pass"])
        self.assertTrue(by_id["dated_artemis_spice_release_state"]["pass"])
        self.assertEqual(30724440, result["total_network_bytes"])
        self.assertEqual(0, result["verification_network_bytes"])

    def test_source_hash_tamper_fails_closed(self) -> None:
        result = verify_sources(ROOT, "tamper_source_manifest_hash")
        self.assertFalse(result["pass"])
        self.assertEqual(
            "INDETERMINATE_SOURCE_IDENTITY_OR_INSPECTION", result["evidence_state"]
        )


if __name__ == "__main__":
    unittest.main()
