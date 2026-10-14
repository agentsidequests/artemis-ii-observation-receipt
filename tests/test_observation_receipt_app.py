from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_PATH = ROOT / "observation-receipt" / "tests" / "test_observation_receipt.py"
SPEC = importlib.util.spec_from_file_location("observation_receipt_standalone_tests", TEST_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None) -> unittest.TestSuite:
    return loader.loadTestsFromModule(MODULE)
