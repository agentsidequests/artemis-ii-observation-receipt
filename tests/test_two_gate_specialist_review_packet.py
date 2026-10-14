import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "ARTEMIS-II-TWO-GATE-SPECIALIST-REVIEW-PACKET.md"


class TwoGateSpecialistReviewPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = PACKET.read_text(encoding="utf-8")
        cls.folded = cls.text.casefold()

    def test_exact_independence_funnel_and_replay_identity_are_present(self) -> None:
        for phrase in (
            "4,511 test products = 4,307 capture-linked + 204 action-only-linked + 0 action-isolated",
            "4,511 test files -> 3,679 test-visible captures -> 68 captures absent from training -> 1,937 test-visible actions -> 0 actions absent from training",
            "20,601 of all 22,818 product rows, or 90.284 percent",
            "4,573,289",
            "2a372b95bc2897ee2d27400f7467d9d8ceb7c7410ed6fee7dab7aad0b1ed20d1",
            "4,216",
            "9fb6f1d180e66cffb83b19924b3c25650b7c144712eff97053bfdf0043a97b2a",
        ):
            self.assertIn(phrase, self.text)

    def test_exact_flash_counts_and_recovery_ceiling_are_present(self) -> None:
        for phrase in (
            "five accepted crew-reported impact-flash events, eight witness marks, and three observers",
            "15 minutes 13 seconds",
            "900 decoded frames",
            "10 by 9 pixels",
            "1,458 deterministic point-like synthetic trials",
            "9 of 162 trials, or 5.6 percent",
            "Fifty percent recovery was not reached",
            "1.31e-7 km^-2 h^-1",
            "not a completeness-corrected or brightness-threshold flux",
        ):
            self.assertIn(phrase, self.text)

    def test_four_function_orientation_and_selection_result_are_present(self) -> None:
        for phrase in (
            "# Artemis II four-function specialist review packet",
            "**Relationship:**",
            "**Selection:**",
            "**Weighting:**",
            "**Detection:**",
            "3,413 of 7,606",
            "44.872%",
            "17** have zero coverage",
            "8** have complete coverage",
            "20** have partial coverage",
            "87.484%",
            "55.128%",
            "0.820465",
        ):
            self.assertIn(phrase, self.text)

    def test_weighting_sensitivities_and_claim_ceiling_are_present(self) -> None:
        for phrase in (
            "20.418%",
            "45.502%",
            "33.989%",
            "52.413%",
            "409,399,017,151",
            "781,104,206,358",
            "51.495 percent",
            "49.188 percent",
            "52.720 percent",
            "52.734 percent",
            "1,294 of 1,553 Sunset-tagged exposures",
            "12.223 percent",
            "21.554 percent",
            "all 23 nonblank target-tag values",
            "5.064 tag values",
            "3.823",
            "3.191",
            "36 active scheduled-window memberships",
            "19.000",
            "16.824",
            "14.703",
            "18.040",
            "15.815",
            "13.595",
            "17.332",
            "15.318",
            "13.181",
            "not effective sample sizes or independent-event counts",
            "does not show that NASA or a researcher used this query or weighting scheme",
        ):
            self.assertIn(phrase, self.text)

    def test_attention_timeline_and_detection_boundaries_are_present(self) -> None:
        for phrase in (
            "138.865 s after the first report",
            "376.526 s after dedicated watching begins",
            "500.143 s",
            "12.462 s after the query",
            "1,324.226 s after the first clear report",
            "state-segmented exposure ledger",
            "does not estimate how detection probability changed",
            "show that prompting caused a report",
        ):
            self.assertIn(phrase, self.text)

    def test_reviewers_and_questions_remain_separate(self) -> None:
        self.assertIn("Questions for the archive and ML reviewer", self.text)
        self.assertIn("Questions for the lunar-impact reviewer", self.text)
        archive = self.text.split("## Questions for the archive and ML reviewer", 1)[1].split(
            "## Questions for the lunar-impact reviewer", 1
        )[0]
        science = self.text.split("## Questions for the lunar-impact reviewer", 1)[1].split(
            "## Low-burden response format", 1
        )[0]
        for section, expected in ((archive, 4), (science, 3)):
            questions = re.findall(r"^\d+\. .+", section, flags=re.MULTILINE)
            self.assertEqual(expected, len(questions))

    def test_existing_practice_is_credited_before_the_recommendation(self) -> None:
        prior = self.text.index("## Existing practice the proposal must credit")
        proposal = self.text.index("## Proposed linked experimental receipts")
        self.assertLess(prior, proposal)
        for phrase in (
            "PDS4",
            "PDS Machine Learning Analysis dictionary",
            "OGC TrainingDML-AI",
            "SomBench",
            "NELIOTA detection study",
            "Artemis II preliminary report",
        ):
            self.assertIn(phrase, self.text)

    def test_local_evidence_map_targets_resolve(self) -> None:
        evidence_section = self.text.split("## Evidence map", 1)[1].split("## Present acceptance state", 1)[0]
        paths = re.findall(r"`([^`]+)`", evidence_section)
        self.assertGreaterEqual(len(paths), 10)
        missing = [path for path in paths if not (ROOT / path).exists()]
        self.assertEqual([], missing)

    def test_acceptance_remains_unverified(self) -> None:
        for phrase in (
            "This packet has not been sent",
            "the maintainer's earlier archive inquiry received the scoped JPL response",
            "not endorsement",
            "have not been accepted by a qualified specialist",
            "remain `NOT VERIFIED`",
        ):
            self.assertIn(phrase, self.text)
        self.assertNotIn("No contact has been made", self.text)

    def test_identity_failure_conditional_scope_and_task_gates_are_visible(self) -> None:
        self.assertLess(self.text.index("**Leading archive question:**"), self.text.index("## Decision summary"))
        self.assertLess(self.text.index("## Reconstruction qualification"), self.text.index("## Function 1:"))
        for phrase in (
            "source-order sensitive",
            "2,134 and 7,502",
            "Zero pairs have both IDs in the counted cohort",
            "candidate is not adopted",
            "a2-action-1c22cc639e2f4792a76b8ca4",
            "art002e009301",
            "art002e015991",
            "Do not rebuild clusters, resplit",
            "22,803 / 7,601 / 2,165",
            "4,305 / 204 / 0",
            "0.132627 percentage points",
            "not eight independent replications or all-ambiguity robustness",
            "Original receipts, counts and sources are unchanged",
            "not statistical sample-size recommendations",
            "24 purposeful calibration IDs and 24 reserved confirmation IDs",
            "No panel pixels or content labels were produced",
            "Do not send the steward crosswalk",
            "not reinstated here or replaced with photometry",
        ):
            self.assertIn(phrase, self.text)

    def test_conditional_replay_result_identity_matches_current_bytes(self) -> None:
        import hashlib
        path = ROOT / "paper-review/downstream-sensitivity/result.json"
        data = path.read_bytes()
        self.assertEqual(152230, len(data))
        self.assertIn(hashlib.sha256(data).hexdigest(), self.text)
        for name in ("comparison.csv", "withheld-products.csv"):
            digest = hashlib.sha256((path.parent / name).read_bytes()).hexdigest()
            self.assertIn(digest, self.text)

    def test_public_copy_uses_no_em_dash_or_private_vocabulary(self) -> None:
        self.assertNotIn("\u2014", self.text)
        for term in ("private-system-name", "private workspace", "bounded research pass"):
            self.assertIsNone(re.search(rf"\b{re.escape(term)}\b", self.folded))


if __name__ == "__main__":
    unittest.main()
