from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "ARTEMIS-II-FLASH-ANALYSIS-BRIEF.md"
APP = ROOT / "OBSERVATION-RECEIPT-OPEN-SOURCE-APP-CONCEPT.md"


class FlashAnalysisBriefTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.brief = BRIEF.read_text(encoding="utf-8")
        cls.app = APP.read_text(encoding="utf-8")
        cls.folded = cls.brief.casefold()

    def test_exact_flash_receipts_are_visible(self) -> None:
        for phrase in (
            "five accepted events and eight witness marks",
            "1.31 x 10^-7 km^-2 h^-1",
            "begins 913 seconds after",
            "10 by 9 pixels",
            "1,458 trials",
            "5.6 percent",
            "fifty percent recovery was not reached",
            "about 27 times more received flux",
            "7.4 meteoroids per hour",
        ):
            self.assertIn(phrase, self.folded)

    def test_claim_boundaries_are_explicit(self) -> None:
        self.assertIn("Historical distance illustration, physical interpretation withdrawn", self.brief)
        self.assertIn("Do not replace this with a larger physical ratio", self.brief)
        self.assertIn("paper-review/range-geometry/RANGE-RECONCILIATION.md", self.brief)
        self.assertIn("WITHDRAWN as an established Artemis observing advantage", self.brief)
        self.assertIn("UNESTABLISHED; background-photo timing does not bound all accepted events", self.brief)
        self.assertNotIn("Refuted by label timing", self.brief)
        self.assertNotIn("Supported as an approximation", self.brief)
        self.assertIn("withdrawn and must not be reused, including in an appendix", self.brief)
        self.assertNotIn("distance-advantage chart, and injection-recovery chart work", self.brief)
        for phrase in (
            "not a calibrated flux estimate",
            "cannot exclude the crew event",
            "not physical brightness",
            "not a validated flash model",
            "not establish that a confirmed crew event failed to appear on camera",
            "ten-pixel footprint does not by itself prove that a flash was invisible",
            "poisson significance calculation that treats the two thresholds as identical",
        ):
            self.assertIn(phrase, self.folded)

    def test_nasa_baseline_is_separate_from_extensions(self) -> None:
        self.assertIn("Those are NASA's recommendations", self.brief)
        self.assertIn("extends them into acceptance criteria", self.brief)
        for heading in (
            "Continuous event-window coverage",
            "Target-scale sampling requirement",
            "Injection-recovery completeness",
            "Effective area-time release",
            "unprompted first marks separately from prompted confirmations",
        ):
            self.assertIn(heading, self.brief)

    def test_sources_include_primary_and_specialist_methods(self) -> None:
        urls = re.findall(r"https://[^\s)]+", self.brief)
        for host in ("science.nasa.gov", "ntrs.nasa.gov", "arxiv.org"):
            self.assertTrue(any(host in url for url in urls), host)

    def test_terrain_dependent_light_curve_implication_is_bounded(self) -> None:
        for phrase in (
            "across 124 multi-frame flashes",
            "highland decay timescale was about 0.11 seconds",
            "about 0.038 seconds for mare flashes",
            "terrain-conditioned light-curve families",
            "rough locations, not the event localization and calibrated light curves",
            "10.1051/0004-6361/202660978",
        ):
            self.assertIn(phrase, self.folded)

    def test_public_deliverables_use_no_em_dash_or_private_vocabulary(self) -> None:
        combined = f"{self.brief}\n{self.app}"
        self.assertNotIn("—", combined)
        folded = combined.casefold()
        self.assertNotIn("private-system-name", folded)
        self.assertIsNone(re.search(r"\bprivate-system-name\b", folded))

    def test_app_positioning_and_private_gate_are_visible(self) -> None:
        folded = self.app.casefold()
        for phrase in (
            "did this evidence have the opportunity and capability to test this claim?",
            "do not start as a generic knowledge graph",
            "keep the application local and private for one more gate",
            "extract the clean subtree into its own public github repository",
            "50 percent recovery was not reached",
            "blocked_insufficient_capability",
            "version 0.2 closes the flat-witness gap",
            "structured witness marks",
        ):
            self.assertIn(phrase, folded)


if __name__ == "__main__":
    unittest.main()
