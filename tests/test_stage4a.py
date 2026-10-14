from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from artemis_testbed import run_testbed  # noqa: E402
from stage1_boundary_equivalence import verify_stage1  # noqa: E402
from stage2a_earthrise_coverage import verify_stage2a  # noqa: E402
from stage3_attention_allocation import verify_stage3a  # noqa: E402
from stage4a_product_canary import verify_stage4a, verify_with_mutations  # noqa: E402


class Stage4AProductCanaryTests(unittest.TestCase):
    def test_label_only_canary_is_replayable(self) -> None:
        result = verify_stage4a(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual("VERIFIED_CAPTURE_AVAILABLE", result["evidence_state"])
        self.assertEqual("UNVALIDATED_CAPTURE_CANDIDATE", result["flash_state"])
        self.assertEqual("NOMINATE_TINY_STAGE5_SUBSET", result["disposition"])

    def test_exactly_seven_canonical_products_are_admitted(self) -> None:
        result = verify_stage4a(ROOT)
        videos = [item for item in result["products"] if item["kind"] == "continuous_video"]
        images = [item for item in result["products"] if item["kind"] == "raw_image"]
        self.assertEqual(7, len(result["products"]))
        self.assertEqual(2, len(videos))
        self.assertEqual(5, len(images))
        self.assertTrue(all(item["timing_rule_pass"] for item in result["products"]))
        self.assertEqual(10, result["atlas_summary"]["derivative_records_excluded"])
        self.assertEqual(4, result["atlas_summary"]["unrelated_records_excluded"])

    def test_video_spans_report_interval_but_does_not_validate_flash(self) -> None:
        result = verify_stage4a(ROOT)
        videos = [item for item in result["products"] if item["kind"] == "continuous_video"]
        self.assertEqual({"2026-04-06T23:38:11Z"}, {item["start_utc"] for item in videos})
        self.assertEqual(
            {"2026-04-07T01:37:45Z", "2026-04-07T01:37:57Z"},
            {item["stop_utc"] for item in videos},
        )
        self.assertIn("do not show that a flash is visible", result["claim_ceiling"])

    def test_image_burst_preserves_activity_tag_contradiction(self) -> None:
        result = verify_stage4a(ROOT)
        self.assertEqual(
            {
                "24_Sunset": 4,
                "25_Discussion #6: Forward Look": 1,
                "Other": 2,
            },
            result["metadata_friction"]["activity_tag_counts"],
        )
        self.assertIn("not evidence of pointing", result["metadata_friction"]["bounded_interpretation"])

    def test_full_payload_burden_is_explicit_without_media(self) -> None:
        result = verify_stage4a(ROOT)
        self.assertEqual(6339176275, result["payload_burden"]["full_product_bytes"])
        self.assertEqual(6.339, result["payload_burden"]["decimal_gigabytes"])
        source_suffixes = {path.suffix.lower() for path in (ROOT / "evidence" / "stage4a").rglob("*") if path.is_file()}
        self.assertTrue(source_suffixes <= {".json", ".xml", ".csv"})

    def test_all_stage4a_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"])
        self.assertTrue(result["hard_negatives_pass"])
        self.assertTrue(all(not item["pass"] for item in result["hard_negatives"].values()))

    def test_earlier_stages_remain_replayable(self) -> None:
        self.assertTrue(run_testbed(ROOT)["pass"])
        self.assertTrue(verify_stage1(ROOT)["pass"])
        self.assertTrue(verify_stage2a(ROOT)["pass"])
        self.assertTrue(verify_stage3a(ROOT)["pass"])


if __name__ == "__main__":
    unittest.main()
