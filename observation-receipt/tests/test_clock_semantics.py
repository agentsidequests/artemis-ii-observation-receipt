"""A background-photo time cannot certify when a retrospective ledger was assembled."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from observation_receipt.evaluator import evaluate_case


class ClockSemanticsTests(unittest.TestCase):
    def test_current_negative_timing_claim_is_metadata_only(self):
        case = json.loads((ROOT / 'cases/artemis-ii-flashes/case.json').read_text(encoding='utf-8'))
        self.assertNotIn('annotation_ledger_utc', case['facts'])
        self.assertEqual('2026-04-07T01:04:00Z', case['facts']['annotation_base_image_utc'])
        claim = case['claims'][1]
        self.assertIn('background-photo epoch', claim['proposition'])
        self.assertIn('not ledger creation', claim['claim_ceiling'])
        receipt = evaluate_case(case, ROOT)
        self.assertTrue(receipt['pass'])
        finding = next(row for row in receipt['findings'] if row['claim_id'] == claim['id'])
        self.assertEqual('REFUTED_NONOVERLAP', finding['status'])
        self.assertEqual(913.0, finding['gap_seconds'])
        self.assertIn('every accepted event', case['claim_ceiling'])


if __name__ == '__main__':
    unittest.main()
