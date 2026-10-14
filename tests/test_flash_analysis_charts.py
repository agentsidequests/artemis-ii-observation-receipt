from __future__ import annotations

import unittest
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHARTS = [
    "Artemis-II-Flash-Chart-2-Witness-Matrix.png",
    "Artemis-II-Flash-Chart-3-Count-To-Flux.png",
    "Artemis-II-Flash-Chart-5-Overlap-Limit.png",
    "Artemis-II-Flash-Chart-6-Injection-Recovery.png",
]


class FlashAnalysisChartTests(unittest.TestCase):
    def test_withdrawn_distance_chart_is_not_distributed(self) -> None:
        self.assertFalse((ROOT / "Artemis-II-Flash-Chart-4-Distance-Advantage.png").exists())
        self.assertFalse((ROOT / "Artemis-II-Flash-Chart-1-Timeline.png").exists())

    def test_renderer_uses_verified_stage11n_result(self) -> None:
        source = (ROOT / "src/render_flash_analysis_charts.py").read_text(encoding="utf-8")
        self.assertIn('load_json("stage11n-result.json")', source)
        self.assertIn('if not result.get("pass")', source)

    def test_renderer_preserves_claim_limits(self) -> None:
        source = (ROOT / "src/render_flash_analysis_charts.py").read_text(encoding="utf-8")
        for phrase in (
            "VOICE ANCHORS ARE NOT ASSIGNED ONE-TO-ONE",
            "NOT SURVEY-COMPARABLE",
            "NOT FLASH PHOTOMETRY OR AN IMPACT-SIZE MEASUREMENT",
            "NO SCREENED PULSE  •  NOT AN EXCLUSION",
            "10⁻⁷",
            "50% RECOVERY NOT REACHED",
        ):
            self.assertIn(phrase, source)
        self.assertNotIn("—", source)

    def test_rendered_charts_have_expected_size_when_present(self) -> None:
        for name in CHARTS:
            path = ROOT / name
            if not path.exists():
                self.skipTest("Flash charts have not been rendered yet.")
            data = path.read_bytes()
            self.assertEqual(b"\x89PNG\r\n\x1a\n", data[:8])
            self.assertEqual(b"IHDR", data[12:16])
            self.assertEqual((1600, 1000), struct.unpack(">II", data[16:24]))
            self.assertEqual(8, data[24])
            self.assertEqual(2, data[25])


if __name__ == "__main__":
    unittest.main()
