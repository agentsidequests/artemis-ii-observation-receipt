from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class Stage11POverlapPixelScreenTests(unittest.TestCase):
    def test_saved_screen_preserves_contextual_claim_ceiling(self) -> None:
        path = ROOT / "results/stage11p-overlap-pixel-screen.json"
        if not path.exists():
            self.skipTest("Stage 11P screen has not been rendered yet.")
        result = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(result["pass"], result["checks"])
        self.assertEqual("VERIFIED_CONTEXTUAL_PIXEL_SCREEN", result["evidence_state"])
        self.assertEqual(900, result["video"]["frames_decoded"])
        self.assertFalse(any(result["claim_boundaries"].values()))
        self.assertIn("does not exclude", result["pulse_screen"]["interpretation"])

    def test_screen_source_names_transcode_limit(self) -> None:
        source = (ROOT / "src/stage11p_overlap_pixel_screen.py").read_text(encoding="utf-8")
        spec = json.loads((ROOT / "spec/stage11p.json").read_text(encoding="utf-8"))
        self.assertIn("values are not source-pixel photometry", spec["source"]["transcode_note"])
        self.assertIn("not an optical-resolution", source)
        self.assertNotIn("—", source)


if __name__ == "__main__":
    unittest.main()
