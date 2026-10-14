from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage10o_relationship_manifest import verify_stage10o, verify_with_mutations  # noqa: E402


class Stage10ORelationshipManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_stage10o(ROOT)

    def test_manifest_verifies(self) -> None:
        self.assertTrue(self.result["pass"], self.result["errors"])
        self.assertEqual("VERIFIED_PRODUCT_ACTION_RELATIONSHIP_MANIFEST", self.result["evidence_state"])

    def test_exact_hierarchy(self) -> None:
        self.assertEqual((22818, 7606, 2166), (
            self.result["products"], self.result["capture_identities"], self.result["complete_actions"],
        ))
        self.assertEqual(1625281365343, self.result["total_bytes"])

    def test_temporal_group_keys_replay_stage10n(self) -> None:
        self.assertEqual({"1": 2051, "2": 1377, "5": 816, "10": 538, "30": 254}, self.result["temporal_cluster_counts"])

    def test_claim_ceiling_prevents_partition_and_semantic_inflation(self) -> None:
        ceiling = self.result["claim_ceiling"].lower()
        for phrase in ("train/test partition", "official pds identifiers", "semantic scenes", "pixel similarity", "observed leakage", "global novelty or priority"):
            self.assertIn(phrase, ceiling)

    def test_no_pixels_are_opened(self) -> None:
        self.assertEqual(0, self.result["pixel_payload_bytes"])

    def test_every_hard_negative_is_rejected(self) -> None:
        result = verify_with_mutations(ROOT)
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(result["hard_negatives_pass"])


if __name__ == "__main__":
    unittest.main()
