from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "ARTEMIS-II-FLASH-MEASUREMENT-ACCEPTANCE-SPEC.md"


class FlashMeasurementAcceptanceSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SPEC.read_text(encoding="utf-8")
        cls.folded = cls.text.casefold()

    def test_nasa_baseline_and_added_contract_are_separate(self) -> None:
        self.assertIn("Baseline NASA already owns", self.text)
        self.assertIn("does not claim those ideas as new", self.folded)
        for phrase in (
            "simultaneous detection in both",
            "stated completeness to magnitude +9",
            "synchronized dual-band validation",
            "does not claim those mechanisms as new either",
            "The added proposal is an integrated acceptance and release contract",
            "one independently replayable evidence chain",
        ):
            self.assertIn(phrase.casefold(), self.folded)

    def test_eight_required_system_sections_are_present(self) -> None:
        headings = re.findall(r"^### ([1-8])\. ", self.text, flags=re.MULTILINE)
        self.assertEqual([str(index) for index in range(1, 9)], headings)

    def test_human_dependence_and_null_boundaries_are_explicit(self) -> None:
        for phrase in (
            "unprompted first marks, prompted confirmations, silence while exposed, and not exposed",
            "a gap is not a null",
            "pixel count, or a visible lunar disk alone does not establish detectability",
            "human and instrument detection functions separately",
            "do not tune the pulse, threshold, locations, or timing after viewing the recovery curve",
        ):
            self.assertIn(phrase, self.folded)

    def test_reproducibility_and_authority_gates_are_visible(self) -> None:
        for phrase in (
            "independent implementation",
            "recompute any published flux",
            "NASA owns mission design",
            "does not establish that every requirement is operationally optimal",
        ):
            self.assertIn(phrase.casefold(), self.folded)

    def test_terrain_dependent_recovery_is_preserved(self) -> None:
        for phrase in (
            "terrain-conditioned families",
            "mare, highland, border, and uncertain terrain states",
            "terrain class, source, and uncertainty",
            "terrain-conditioned detection terms",
            "10.1051/0004-6361/202660978",
        ):
            self.assertIn(phrase.casefold(), self.folded)

    def test_public_spec_uses_no_em_dash_or_private_vocabulary(self) -> None:
        self.assertNotIn("—", self.text)
        for phrase in ("private-system-name",):
            self.assertNotIn(phrase, self.folded)


if __name__ == "__main__":
    unittest.main()
