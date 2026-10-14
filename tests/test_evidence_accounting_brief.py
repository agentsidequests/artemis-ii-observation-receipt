from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "ARTEMIS-II-EVIDENCE-ACCOUNTING-BRIEF.md"


class EvidenceAccountingBriefTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = BRIEF.read_text(encoding="utf-8")
        cls.folded = cls.text.casefold()

    def test_two_gate_thesis_is_explicit(self) -> None:
        for phrase in (
            "data abundance can hide a shortage of evidential opportunities",
            "gate 1: independence",
            "gate 2: detectability",
            "one discipline, two mathematical objects",
        ):
            self.assertIn(phrase, self.folded)

    def test_exact_split_decomposition_and_flash_recovery_are_visible(self) -> None:
        for phrase in (
            "4,511 test products = 4,307 capture-linked + 204 action-only-linked + 0 action-isolated",
            "4,511 test files -> 3,679 test-visible captures -> 68 capture-isolated groups -> 1,937 test-visible actions -> 0 action-isolated groups",
            "20,601 of the 22,818 product rows",
            "1,458-trial injection grid",
            "9 of 162 trials, or 5.6 percent",
        ):
            self.assertIn(phrase, self.text)

    def test_claim_ceiling_blocks_the_decision_changing_overclaims(self) -> None:
        for phrase in (
            "observed leakage",
            "model-performance effect",
            "physical camera detection threshold",
            "calibrated impact rate",
            "defect in nasa's archive or standards",
            "global novelty or priority",
        ):
            self.assertIn(phrase, self.folded)

    def test_existing_practice_is_credited_before_the_recommendation(self) -> None:
        practice = self.folded.index("## what nasa and the field already do")
        recommendation = self.folded.index("## explicit recommendation")
        self.assertLess(practice, recommendation)
        for phrase in ("pds4", "trainingdml-ai", "sombench", "neliota"):
            self.assertIn(phrase, self.folded)

    def test_public_brief_uses_no_em_dash_and_local_links_resolve(self) -> None:
        self.assertNotIn(chr(0x2014), self.text)
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", self.text)
        for link in links:
            if link.startswith(("http://", "https://")):
                continue
            self.assertTrue((ROOT / link).is_file(), link)


if __name__ == "__main__":
    unittest.main()
