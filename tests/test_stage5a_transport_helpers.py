from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from stage5a_transport_canary import (  # noqa: E402
    Budget,
    is_client_disconnect,
    parse_atom_header,
    parse_content_range,
    parse_range_header,
)


class Stage5ATransportHelperTests(unittest.TestCase):
    def test_open_ended_range_is_admitted_but_not_expanded(self) -> None:
        self.assertEqual(parse_range_header("bytes=100-", 1000), (100, None))

    def test_multiple_or_suffix_ranges_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_range_header("bytes=0-9,20-29", 1000)
        with self.assertRaises(ValueError):
            parse_range_header("bytes=-50", 1000)

    def test_content_range_binds_total_identity(self) -> None:
        self.assertEqual(parse_content_range("bytes 10-19/1000"), (10, 19, 1000))
        with self.assertRaises(ValueError):
            parse_content_range("bytes */1000")

    def test_standard_and_extended_atom_headers(self) -> None:
        standard = (24).to_bytes(4, "big") + b"ftyp" + b"\0" * 8
        self.assertEqual(parse_atom_header(standard, 0)["size"], 24)
        extended = (1).to_bytes(4, "big") + b"mdat" + (5000).to_bytes(8, "big")
        parsed = parse_atom_header(extended, 24)
        self.assertEqual(parsed["size"], 5000)
        self.assertEqual(parsed["header_bytes"], 16)

    def test_budget_fails_closed(self) -> None:
        budget = Budget(10)
        budget.add(10)
        self.assertEqual(budget.remaining, 0)
        with self.assertRaises(RuntimeError):
            budget.add(1)

    def test_windows_connection_abort_is_a_client_disconnect(self) -> None:
        self.assertTrue(
            is_client_disconnect(
                ConnectionAbortedError(10053, "An established connection was aborted")
            )
        )
        self.assertFalse(is_client_disconnect(OSError(5, "Unrelated I/O failure")))


if __name__ == "__main__":
    unittest.main()
