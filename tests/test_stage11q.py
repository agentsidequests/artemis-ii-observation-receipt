from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class Stage11QInjectionRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        path = ROOT / "results/stage11q-injection-recovery.json"
        if not path.exists():
            raise unittest.SkipTest("Stage 11Q result has not been generated yet.")
        cls.result = json.loads(path.read_text(encoding="utf-8"))

    def test_saved_result_verifies_frozen_trial_grid(self) -> None:
        self.assertTrue(self.result["pass"], self.result["checks"])
        self.assertEqual("VERIFIED_TRANSCODED_INJECTION_RECOVERY", self.result["evidence_state"])
        self.assertEqual(1458, self.result["injection_model"]["trial_count"])
        self.assertEqual(0, self.result["baseline"]["candidate_frames"])

    def test_curve_is_monotonic_and_has_all_amplitudes(self) -> None:
        curve = self.result["recovery_curve"]
        self.assertEqual([250, 500, 1000, 2000, 4000, 6000, 8000, 12000, 16000], [row["requested_integrated_dn_per_frame"] for row in curve])
        fractions = [row["recovery_fraction"] for row in curve]
        self.assertTrue(all(a <= b for a, b in zip(fractions, fractions[1:])))

    def test_physical_and_event_claims_remain_blocked(self) -> None:
        self.assertFalse(any(self.result["claim_boundaries"].values()))
        interpretation = self.result["interpretation"].casefold()
        for phrase in ("not a physical brightness limit", "source-pixel", "flight-sensor", "event exclusion"):
            self.assertIn(phrase, interpretation)

    def test_source_uses_no_em_dash(self) -> None:
        source = (ROOT / "src/stage11q_injection_recovery.py").read_text(encoding="utf-8")
        self.assertNotIn("—", source)


if __name__ == "__main__":
    unittest.main()
