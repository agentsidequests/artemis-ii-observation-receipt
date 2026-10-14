"""Run bounded offline checks; report omissions instead of silently calling them passes."""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUICK = {
    'test_fcorona_range_reconciliation.py', 'test_observation_receipt_identity.py',
    'test_observation_receipt_app.py', 'test_public_analysis_draft.py',
    'test_two_gate_specialist_review_packet.py', 'test_evidence_accounting_brief.py',
    'test_flash_measurement_acceptance_spec.py', 'test_claim_ledger.py',
    'test_observation_receipt_prototype.py', 'test_flash_analysis_brief.py',
    'test_flash_analysis_charts.py', 'test_withdrawn_visual_guard.py',
    'test_presentation.py', 'test_tag_weight_robustness.py',
    'test_observation_receipt_robustness.py', 'test_public_refresh.py',
}
WITHHELD = ROOT / 'evidence/stage11n/source/neliota-wide-field-high-cadence.txt'
PIN = 'c147cc0d0a28ba5e347a3bd6c6406dfb80272efaa8762d59a843d12ffc8936d4'


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument('--quick', action='store_true')
    choice.add_argument('--suite', action='store_true')
    choice.add_argument('--historical-full', action='store_true')
    args = parser.parse_args()
    full_text_ready = WITHHELD.is_file() and WITHHELD.stat().st_size == 76776 and hashlib.sha256(WITHHELD.read_bytes()).hexdigest() == PIN
    if args.historical_full and not full_text_ready:
        print('STOP: exact NELIOTA full-text extract is unavailable. See REPRODUCIBILITY.md. No full historical pass is claimed.', file=sys.stderr)
        return 2
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / 'src'))
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    selected, omitted = [], []
    for path in sorted((ROOT / 'tests').glob('test_*.py')):
        if not (args.suite or args.historical_full) and path.name not in QUICK:
            continue
        if path.name == 'test_stage11n.py' and not full_text_ready:
            omitted.append({'module': path.name, 'reason': 'Exact journal full-text source not redistributed; not a pass.'})
            continue
        if path.name == 'test_observation_receipt_archive.py' and not (ROOT / '.git').exists():
            omitted.append({'module': path.name, 'reason': 'Git-only archive test requires a Git checkout, not a source ZIP.'})
            continue
        module_spec = importlib.util.spec_from_file_location('public_replay_' + path.stem, path)
        module = importlib.util.module_from_spec(module_spec)
        sys.modules[module_spec.name] = module
        module_spec.loader.exec_module(module)
        suite.addTests(loader.loadTestsFromModule(module))
        selected.append(path.name)
    print(json.dumps({'root_test_modules': len(selected), 'omitted_modules': omitted, 'network_requested': False}), flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    app = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=ROOT / 'observation-receipt', check=False)
    return app.returncode


if __name__ == '__main__':
    raise SystemExit(main())
