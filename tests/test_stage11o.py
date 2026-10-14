from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class Stage11OOverlapVideoCanaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.receipt = json.loads(
            (ROOT / "evidence/stage11o/acquisition-receipt.json").read_text(encoding="utf-8")
        )

    def test_bounded_extraction_succeeded(self) -> None:
        self.assertEqual("VERIFIED_BOUNDED_EXTRACTION", self.receipt["state"])
        self.assertLess(
            self.receipt["accepted_media_body_bytes"],
            self.receipt["budget_limit_bytes"],
        )
        self.assertEqual(666376, self.receipt["clip"]["bytes"])
        self.assertEqual(
            "a2dc14c6060de9bb8858d4d9d49b207c99d6dacdd5943fb84bb3448f67762eec",
            self.receipt["clip"]["sha256"],
        )

    def test_every_upstream_media_request_was_bounded(self) -> None:
        media_requests = [item for item in self.receipt["requests"] if item.get("method") == "GET"]
        self.assertTrue(media_requests)
        for item in media_requests:
            self.assertIsNotNone(item.get("requested_range"))
            self.assertEqual(206, item.get("status"))
            self.assertLessEqual(item.get("media_body_bytes", 0), 1048576)

    def test_claim_ceiling_preserves_pixel_boundary(self) -> None:
        ceiling = self.receipt["claim_ceiling"].casefold()
        for phrase in ("timing overlap", "visible transient", "impact causation", "photometry"):
            self.assertIn(phrase, ceiling)


if __name__ == "__main__":
    unittest.main()
