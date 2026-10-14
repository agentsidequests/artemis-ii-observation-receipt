from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stage8c_camera_native_canary import (  # noqa: E402
    histogram_auc,
    render_markdown,
    unfilter_indexed_scanlines,
    verify_sources,
    write_json,
)


class Stage8CCameraNativeCanaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = verify_sources(ROOT)

    def test_png_unfilter_handles_all_five_standard_filters(self) -> None:
        encoded = bytes(
            [
                0, 10, 20, 30,
                1, 11, 12, 13,
                2, 4, 6, 9,
                3, 13, 11, 10,
                4, 5, 5, 5,
            ]
        )
        expected = bytes(
            [
                10, 20, 30,
                11, 23, 36,
                15, 29, 45,
                20, 35, 50,
                25, 40, 55,
            ]
        )
        self.assertEqual(expected, unfilter_indexed_scanlines(encoded, 3, 5))

    def test_histogram_auc_counts_wins_and_ties_exactly(self) -> None:
        inner = [0] * 256
        outer = [0] * 256
        inner[2] = 1
        inner[3] = 1
        outer[1] = 1
        outer[2] = 1
        self.assertEqual(0.875, histogram_auc(inner, outer))

    def test_frozen_camera_run_is_replayable_offline(self) -> None:
        result = self.result
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(
            "NO_CAMERA_NATIVE_ORDINAL_CONCORDANCE", result["evidence_state"]
        )
        self.assertEqual("CLOSE_CAMERA_NATIVE_GLUSHKO_OHM_LANE", result["disposition"])
        self.assertEqual(0, result["verification_network_bytes"])
        self.assertEqual(
            {"joint_same_frame", "matched_400mm_pair"}, set(result["views"])
        )
        self.assertTrue(all(len(view["cells"]) == 3 for view in result["views"].values()))
        self.assertTrue(all(not view["pass"] for view in result["views"].values()))
        self.assertTrue(all(view["passing_cells"] == 0 for view in result["views"].values()))

    def test_direction_recurs_but_signal_and_similarity_do_not(self) -> None:
        cells = [
            cell
            for view in self.result["views"].values()
            for cell in view["cells"].values()
        ]
        self.assertEqual(6, len(cells))
        self.assertTrue(all(cell["direction_pass"] for cell in cells))
        self.assertTrue(all(not cell["signal_pass"] for cell in cells))
        self.assertTrue(all(not cell["similarity_pass"] for cell in cells))
        joint_primary = self.result["views"]["joint_same_frame"]["cells"][
            "inner_1p50_3p00_outer_3p00_4p00"
        ]
        self.assertAlmostEqual(0.5379767319625725, joint_primary["glushko"]["auc"])
        self.assertAlmostEqual(0.49791524133603815, joint_primary["ohm"]["auc"])

    def test_result_writers_preserve_the_verified_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            write_json(output, self.result)
            self.assertIn(
                '"evidence_state": "NO_CAMERA_NATIVE_ORDINAL_CONCORDANCE"',
                output.read_text(encoding="utf-8"),
            )
        rendered = render_markdown(self.result)
        self.assertIn("`NO_CAMERA_NATIVE_ORDINAL_CONCORDANCE`", rendered)
        self.assertIn("Passing robustness cells: `0 / 3`", rendered)

    def test_saved_receipt_matches_the_current_replay(self) -> None:
        saved = json.loads(
            (ROOT / "results" / "stage8c-verification.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(self.result["evidence_state"], saved["evidence_state"])
        self.assertEqual(self.result["disposition"], saved["disposition"])
        self.assertEqual(self.result["views"], saved["views"])

    def test_source_hash_tamper_fails_before_pixel_scoring(self) -> None:
        result = verify_sources(ROOT, "tamper_joint_image_hash")
        self.assertFalse(result["pass"])
        self.assertEqual(
            "INDETERMINATE_CAMERA_SOURCE_GEOMETRY_OR_DECODER",
            result["evidence_state"],
        )
        self.assertEqual({}, result["views"])


if __name__ == "__main__":
    unittest.main()
