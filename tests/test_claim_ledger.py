from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "CLAIM-LEDGER.md"


class ClaimLedgerTests(unittest.TestCase):
    def test_claim_ids_are_complete_and_unique(self) -> None:
        text = LEDGER.read_text(encoding="utf-8")
        ids = re.findall(r"\| (C\d{2}) \|", text)
        self.assertEqual([f"C{index:02d}" for index in range(1, 25)], ids)

    def test_every_relative_link_resolves(self) -> None:
        text = LEDGER.read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
        self.assertGreaterEqual(len(links), 19)
        for link in links:
            self.assertFalse(link.startswith(("http://", "https://")))
            self.assertTrue((ROOT / link).is_file(), link)

    def test_global_ceiling_is_visible(self) -> None:
        text = LEDGER.read_text(encoding="utf-8").casefold()
        for phrase in (
            "new lunar-science discovery",
            "formal informative cluster size",
            "observed model leakage or bias",
            "archive defect",
            "global novelty",
            "nasa owns the source archive",
        ):
            self.assertIn(phrase, text)

    def test_independence_influence_burden_and_detectability_are_separated(self) -> None:
        text = LEDGER.read_text(encoding="utf-8").casefold()
        for phrase in (
            "independence:",
            "influence:",
            "burden:",
            "detectability:",
            "bytes = actions × (exposures / actions) × (products / exposures) × (bytes / products)",
            "products / exposures` is constant at three",
            "bytes / products` adds a separate file-size layer",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
