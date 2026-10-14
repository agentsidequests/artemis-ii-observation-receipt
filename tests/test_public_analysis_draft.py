from __future__ import annotations

import re
import json
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "PUBLIC-ANALYSIS-DRAFT.md"
REVIEW_PACKET = ROOT / "ARTEMIS-II-CLAIM-AND-PILOT-REVIEW-PACKET.md"
CHARTS = (
    "Artemis-II-Chart-1-One-Sunset.png",
    "Artemis-II-Chart-2-Hidden-Weight.png",
    "Artemis-II-Chart-3-Rank-Reversal.png",
    "Artemis-II-Chart-4-Split-Hazard.png",
    "Artemis-II-Chart-5-Archive-vs-Analysis.png",
    "Artemis-II-Chart-6-Task-Readiness.png",
    "Artemis-II-Chart-7-Opportunity-Concentration.png",
    "Artemis-II-Chart-8-Attention-Conditioned-Detection.png",
    "Artemis-II-Chart-9-Selection-Weighting-Cascade.png",
)
COVER = "Artemis-II-Cover-4290-One-Sunset.png"


class PublicAnalysisDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = DRAFT.read_text(encoding="utf-8")
        cls.folded = cls.text.casefold()
        cls.renderer = (ROOT / "src" / "render_public_analysis_charts.py").read_text(
            encoding="utf-8"
        )

    def test_title_opening_and_four_function_promise(self) -> None:
        self.assertTrue(self.text.startswith("# 4,290 Data Products, One Sunset\n"))
        for phrase in (
            "archive is also a hidden experimental design",
            "4,290 rows. one scheduled sunset.",
            "**relationship:**",
            "**selection:**",
            "**weighting:**",
            "**detection:**",
        ):
            self.assertIn(phrase, self.folded)

    def test_relationship_results_are_exact(self) -> None:
        for phrase in (
            "2,535 products, 845 exposures, and 169 camera actions",
            "4,290 products, 1,430 exposures, and 286 actions",
            "1 connected context × 286 camera actions × 5 exposures per action × 3 products per exposure = 4,290 archive products",
            "4,307 share an exact capture identity with training",
            "remaining 204 share a reconstructed complete camera action",
            "Zero are isolated from training at the complete-action layer",
            "89.111 percent",
            "52.911 percent",
            "1,937 of 2,166 camera actions",
            "157 of 816 conditional five-second groups still crossed",
            "placing 1,216 actions inside a crossed outer group",
        ):
            self.assertIn(phrase, self.text)

    def test_selection_results_and_limits_are_exact(self) -> None:
        for phrase in (
            "7,606 source exposures",
            "3,413 have a target tag",
            "44.872 percent coverage",
            "17 have no target-tag coverage",
            "eight have complete coverage",
            "20 are partial",
            "87.484 percent",
            "55.128 percent",
            "1,553 exposures, or 45.502 percent",
            "empty target field does not mean",
            "camera-only metadata model",
        ):
            self.assertIn(phrase, self.text)

    def test_weighting_and_concentration_results_are_exact(self) -> None:
        for phrase in (
            "target_id IS NOT NULL",
            "1,553 of all 7,606 source-exposure target fields",
            "20.418 percent",
            "33.989 percent",
            "52.413 percent",
            "409,399,017,151 of 781,104,206,358 bytes",
            "51.495 percent",
            "49.188 percent",
            "52.720 percent",
            "52.734 percent",
            "1,294 of the 1,553 Sunset-tagged exposures",
            "12.223 percent",
            "21.554 percent",
            "all 23 nonblank target-tag values",
            "5.064 tag values",
            "3.823",
            "3.191",
            "13.204 percent of the reconstructed camera actions",
            "18.801 percent of the archive products",
            "22.785 percent of the bytes",
            "15 ÷ 9 = 1.67 times",
            "Product-weight multiplier = 18.801% ÷ 13.204% = 1.424×",
            "38 reverse rank",
            "Among 222 comparable pairs with the same product rate, none reverses",
            "35 persist under byte totals",
            "24 additional byte-only reversals",
            "The total rises to 59",
            "36 active planned windows",
            "19.000 equivalent windows",
            "16.824",
            "14.703",
            "18.040 action-equivalent",
            "15.815 product-equivalent",
            "13.595 byte-equivalent",
            "17.332, 15.318, and 13.181",
            "at least 12 additional windows",
            "reaching three would require 27",
        ):
            self.assertIn(phrase, self.text)

    def test_detection_timeline_and_limits_are_exact(self) -> None:
        for phrase in (
            "00:41:00.680 UTC",
            "138.865 seconds later",
            "376.526 seconds",
            "12.462 seconds",
            "1,324.226 seconds",
            "Raw eclipse clock time is a composite, unsegmented human observation opportunity",
            "does not estimate per-state detection probability",
            "prove prompt causation",
            "show physical clustering",
            "900 frames at about 59.94 frames per second",
            "10 by 9 pixels",
            "1,458 clip-native synthetic injection trials",
            "only 5.6 percent",
            "local null is non-exclusionary",
        ):
            self.assertIn(phrase, self.text)

    def test_nasa_practice_is_credited_before_recommendation(self) -> None:
        for phrase in (
            "NASA already has a family tree",
            "PDS4 Data Provider’s Handbook",
            "model-driven archive",
            "unique identifiers and structured labels",
            "Machine Learning Analysis dictionary",
            "Planetary Data Ecosystem review",
            "TrainingDML-AI standard",
            "Open Science and Data Management Plan",
            "Data User Guide",
            "That mature archive practice changes the criticism.",
            "Those models operate at different levels.",
            "already enumerate member products",
            "Equivalent relationships may exist in mission-specific products or workflows not inspected here.",
            "NASA’s [preliminary lunar-science report]",
        ):
            self.assertIn(phrase, self.text)
        self.assertLess(
            self.text.index("## NASA already has a family tree"),
            self.text.index("## What NASA could publish next"),
        )

    def test_recommendations_are_explicit_and_bounded(self) -> None:
        for phrase in (
            "one bounded pilot",
            "four linked receipts",
            "**Relationship**",
            "**Selection**",
            "**Weighting**",
            "**Detection**",
            "explicit unknowns",
            "camera-only baseline",
            "concentration table",
            "injection-recovery curve",
            "content-hashed record",
            "responsible specialists accept the semantics",
            "The unit has to follow the question.",
            "A terabyte can be a download. It cannot, by itself, be a sample size.",
        ):
            self.assertIn(phrase, self.text)

    def test_current_primary_sources_are_linked(self) -> None:
        for url in (
            "https://pds.nasa.gov/data/pds4/documents/document_pds4_standards/1.26.0.0/PDS4_DPH_1.26.0.pdf",
            "https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/document/artemis2_osdmp.pdf",
            "https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/document/artemis2_data_user_guide.pdf",
            "https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/",
            "https://science.nasa.gov/researchers/science-information-policy_faq/",
            "https://pds.nasa.gov/pds4/ml/v1/PDS4_ML_1P00_1211.JSON",
            "https://docs.ogc.org/is/23-008r5/23-008r5.html",
            "https://arxiv.org/abs/2609.13277",
            "https://arxiv.org/abs/2509.08027",
            "https://www.aanda.org/articles/aa/pdf/2018/11/aa33499-18.pdf",
        ):
            self.assertIn(url, self.text)

    def test_nine_substack_charts_are_linked_and_valid(self) -> None:
        for filename in CHARTS:
            path = ROOT / filename
            self.assertTrue(path.is_file(), filename)
            payload = path.read_bytes()
            self.assertEqual(payload[:8], b"\x89PNG\r\n\x1a\n")
            width, height = struct.unpack(">II", payload[16:24])
            self.assertEqual((width, height), (1600, 1000))
            self.assertGreater(len(payload), 40_000)
            values=json.loads((ROOT/'presentation/figure-reading-values.json').read_text(encoding='utf-8'))
            spec=next(f for f in values['figures'] if f['filename']==filename)
            current=f"presentation/editorial/figures/figure-{spec['number']:02}-desktop.png"
            self.assertIn(f"]({current})", self.text)
            self.assertEqual((ROOT/current).read_bytes()[:8],b'\x89PNG\r\n\x1a\n')

    def test_new_visuals_preserve_claim_boundaries(self) -> None:
        for phrase in (
            "Thirty-six windows do not carry thirty-six equal votes",
            "Concentration-equivalent window units, not effective sample size or independent scientific events.",
            "The human detector changed after the first flash",
            "A nonstationary observation process. No prompt causation, event mapping, or physical clustering is inferred.",
            "A filter and a unit can compound",
            "Frozen metadata accounting only. Not physical prevalence, actual pipeline behavior, or model bias.",
            "BY LAYER",
        ):
            self.assertIn(phrase, self.renderer)

    def test_substack_cover_is_valid(self) -> None:
        path = ROOT / COVER
        self.assertTrue(path.is_file(), COVER)
        payload = path.read_bytes()
        self.assertEqual(payload[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", payload[16:24]), (1400, 1000))
        self.assertGreater(len(payload), 35_000)

    def test_claim_boundaries_are_visible_once_they_matter(self) -> None:
        for phrase in (
            "no model was tested",
            "a mathematical hazard model, not evidence of leakage",
            "not an oracle for the exact visual event",
            "does not establish observed leakage, model bias, scientific importance, a defect in nasa’s archive",
            "does not carry nasa, pds, ogc, or specialist acceptance",
        ):
            self.assertIn(phrase, self.folded)

    def test_public_copy_exposes_no_private_system_vocabulary(self) -> None:
        for term in ("private workspace", "testbed", "stage 11", "claim ledger", "private-system-name"):
            self.assertIsNone(re.search(rf"\b{re.escape(term)}\b", self.folded))

    def test_reconstruction_scope_precedes_dependent_selection_results(self) -> None:
        scope = self.text.index("## Our reconstruction needed the same scrutiny")
        selection = self.text.index("## Selection: a blank label is not a negative example")
        self.assertLess(scope, selection)
        for phrase in (
            "not independently validated physical counts",
            "2,134 sequences and 7,502 keys",
            "source order and algorithm",
            "eight tested input orders",
            "candidate was not adopted",
            "4,305 + 204 + 0",
            "52.545%",
            "not eight independent replications",
            "Physical identity remains unresolved",
            "Figures and main quantities retain the original cohort",
            "20.418 to 75.546 percent",
            "not a confidence interval or image-content prevalence",
            "An observing objective is not an image-level answer key",
        ):
            self.assertIn(phrase, self.text)

    def test_public_copy_and_visual_text_use_no_em_dashes(self) -> None:
        self.assertNotIn("\u2014", self.text)
        self.assertNotIn("\u2014", self.renderer)

    def test_length_and_sources_fit_a_substack_essay(self) -> None:
        # Measure displayed prose, not destination URLs or longer asset paths.
        prose = re.sub(r'\]\([^)]+\)',']',self.text)
        words = re.findall(r"\b[\w’'-]+\b", prose)
        self.assertGreaterEqual(len(words), 2600)
        self.assertLessEqual(len(words), 4500)
        urls = re.findall(r"\]\((https://[^)]+)\)", self.text)
        self.assertGreaterEqual(len(set(urls)), 12)

    def test_specialist_review_packet_remains_available(self) -> None:
        self.assertTrue(REVIEW_PACKET.is_file())
        packet = REVIEW_PACKET.read_text(encoding="utf-8")
        for phrase in (
            "Neither artifact is PDS-certified, OGC-conformant, or specialist-approved",
            "content-hashed receipt",
            "fail closed on six conditions",
            "Passing proves only that declared relationships were preserved.",
            "Data Design Working Group",
            "Questions a specialist should answer",
        ):
            self.assertIn(phrase, packet)
        self.assertNotIn("\u2014", packet)


if __name__ == "__main__":
    unittest.main()
