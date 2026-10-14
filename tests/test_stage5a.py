from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from artemis_testbed import verify_with_mutations as verify_stage0  # noqa: E402
from stage1_boundary_equivalence import verify_with_mutations as verify_stage1  # noqa: E402
from stage2a_earthrise_coverage import verify_with_mutations as verify_stage2a  # noqa: E402
from stage3_attention_allocation import verify_with_mutations as verify_stage3a  # noqa: E402
from stage4a_product_canary import verify_with_mutations as verify_stage4a  # noqa: E402
from stage5a_transport_verification import verify_stage5a, verify_with_mutations  # noqa: E402


class Stage5ATransportVerificationTests(unittest.TestCase):
    def test_budget_stop_is_replayable_offline(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result)
        self.assertEqual(result["evidence_state"], "VERIFIED_BUDGET_STOP")

    def test_exact_range_transport_is_verified_without_a_clip(self) -> None:
        result = verify_stage5a(ROOT)
        self.assertTrue(result["range_transport_verified"])
        self.assertFalse(result["clip_materialized"])
        self.assertEqual(result["accepted_media_body_bytes"], 67_108_864)

    def test_tail_moov_geometry_is_explicit(self) -> None:
        result = verify_stage5a(ROOT)
        atoms = {item["type"]: item for item in result["top_level_atoms"]}
        self.assertEqual(atoms["moov"]["offset"], 2_929_948_257)
        self.assertEqual(atoms["moov"]["size"], 30_289_940)

    def test_all_stage5a_hard_negatives_are_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["hard_negatives_pass"], result["hard_negatives"])

    def test_earlier_stages_remain_replayable(self) -> None:
        self.assertTrue(verify_stage0(ROOT)["pass"])
        self.assertTrue(verify_stage1(ROOT)["pass"])
        self.assertTrue(verify_stage2a(ROOT)["pass"])
        self.assertTrue(verify_stage3a(ROOT)["pass"])
        self.assertTrue(verify_stage4a(ROOT)["pass"])


if __name__ == "__main__":
    unittest.main()
