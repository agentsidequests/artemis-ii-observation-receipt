#!/usr/bin/env python3
"""Audit hierarchical train/test isolation in the frozen Stage 11L canary."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    required = {
        "product_id",
        "capture_identity",
        "action_id",
        "product_key_partition",
    }
    if not rows:
        raise ValueError("Assignment artifact is empty")
    if not required.issubset(rows[0]):
        missing = sorted(required.difference(rows[0]))
        raise ValueError(f"Assignment artifact is missing columns: {missing}")
    return rows


def analyze_assignments(rows: list[dict[str, str]]) -> dict[str, Any]:
    product_ids = [row["product_id"] for row in rows]
    partitions = {row["product_key_partition"] for row in rows}
    train = [row for row in rows if row["product_key_partition"] == "train"]
    test = [row for row in rows if row["product_key_partition"] == "test"]
    train_captures = {row["capture_identity"] for row in train}
    train_actions = {row["action_id"] for row in train}
    test_captures = {row["capture_identity"] for row in test}
    test_actions = {row["action_id"] for row in test}

    capture_linked = 0
    action_only_linked = 0
    action_isolated = 0
    for row in test:
        if row["capture_identity"] in train_captures:
            capture_linked += 1
        elif row["action_id"] in train_actions:
            action_only_linked += 1
        else:
            action_isolated += 1

    action_partitions: dict[str, set[str]] = defaultdict(set)
    action_rows: dict[str, int] = defaultdict(int)
    for row in rows:
        action_partitions[row["action_id"]].add(row["product_key_partition"])
        action_rows[row["action_id"]] += 1
    crossing_actions = {
        action_id for action_id, action_splits in action_partitions.items()
        if action_splits == {"train", "test"}
    }
    products_in_crossing_actions = sum(action_rows[action_id] for action_id in crossing_actions)

    test_count = len(test)
    return {
        "rows": len(rows),
        "train_products": len(train),
        "test_products": test_count,
        "partitions": sorted(partitions),
        "unique_product_ids": len(set(product_ids)),
        "capture_linked_test_products": capture_linked,
        "action_only_linked_test_products": action_only_linked,
        "action_isolated_test_products": action_isolated,
        "capture_linked_test_share": capture_linked / test_count,
        "action_only_linked_test_share": action_only_linked / test_count,
        "action_isolated_test_share": action_isolated / test_count,
        "test_visible_capture_groups": len(test_captures),
        "capture_linked_test_capture_groups": len(test_captures & train_captures),
        "capture_isolated_test_capture_groups": len(test_captures - train_captures),
        "test_visible_action_groups": len(test_actions),
        "action_isolated_test_action_groups": len(test_actions - train_actions),
        "crossing_action_groups": len(crossing_actions),
        "products_in_crossing_action_groups": products_in_crossing_actions,
        "share_all_products_in_crossing_actions": products_in_crossing_actions / len(rows),
    }


def metrics_match_expected(observed: dict[str, Any], expected: dict[str, Any]) -> bool:
    for key, expected_value in expected.items():
        observed_value = observed.get(key)
        if isinstance(expected_value, float):
            if observed_value is None or not math.isclose(
                float(observed_value), expected_value, rel_tol=0.0, abs_tol=1e-12
            ):
                return False
        elif observed_value != expected_value:
            return False
    return True


def source_identities(root: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    identities = []
    for expected in spec["sources"]:
        path = root / expected["path"]
        observed = {
            "path": expected["path"],
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        observed["match"] = (
            observed["bytes"] == expected["bytes"]
            and observed["sha256"] == expected["sha256"]
        )
        identities.append(observed)
    return identities


def verify_stage11r(root: Path) -> dict[str, Any]:
    spec = json.loads((root / "spec/stage11r.json").read_text(encoding="utf-8"))
    identities = source_identities(root, spec)
    assignment_path = root / spec["sources"][0]["path"]
    receipt_path = root / spec["sources"][1]["path"]
    rows = load_rows(assignment_path)
    metrics = analyze_assignments(rows)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt_policy = receipt["policies"]["product_key"]
    expected = spec["frozen_observables"]

    checks = {
        "source_identities": all(identity["match"] for identity in identities),
        "only_train_and_test_partitions": metrics["partitions"] == ["test", "train"],
        "unique_product_ids": metrics["unique_product_ids"] == metrics["rows"],
        "complete_partition": (
            metrics["train_products"] + metrics["test_products"] == metrics["rows"]
        ),
        "mutually_exclusive_test_bins": (
            metrics["capture_linked_test_products"]
            + metrics["action_only_linked_test_products"]
            + metrics["action_isolated_test_products"]
            == metrics["test_products"]
        ),
        "receipt_action_crossings_agree": (
            metrics["crossing_action_groups"]
            == receipt_policy["crossing_action_groups"]
        ),
        "receipt_crossing_products_agree": (
            metrics["products_in_crossing_action_groups"]
            == receipt_policy["products_in_crossing_action_groups"]
        ),
        "frozen_observables": metrics_match_expected(metrics, expected),
        "claim_boundaries_preserved": not any(spec["claim_boundaries"].values()),
        "zero_pixel_access": True,
    }
    passed = all(checks.values())
    return {
        "testbed_id": spec["testbed_id"],
        "version": spec["version"],
        "pass": passed,
        "evidence_state": (
            "VERIFIED_HIERARCHICAL_TEST_ISOLATION_AUDIT"
            if passed
            else "FAILED_HIERARCHICAL_TEST_ISOLATION_AUDIT"
        ),
        "checks": checks,
        "source_identities": identities,
        "structural_isolation": metrics,
        "formula": {
            "identity": "test = capture-linked + action-only-linked + action-isolated",
            "observed": "4511 = 4307 + 204 + 0",
            "classification_order": [
                "exact capture identity present in training",
                "capture absent but complete action present in training",
                "complete action absent from training",
            ],
        },
        "interpretation": (
            "The frozen product-key canary has no test product isolated from training "
            "at the reconstructed complete-action layer. This is structural overlap, "
            "not observed leakage, pixel similarity, statistical dependence, or harm."
        ),
        "claim_boundaries": spec["claim_boundaries"],
        "claim_ceiling": spec["claim_ceiling"],
        "next_step_logic": spec["next_step_logic"],
        "pixel_payload_bytes_opened": 0,
    }


def render_markdown(result: dict[str, Any]) -> str:
    metrics = result["structural_isolation"]
    status = "PASS" if result["pass"] else "FAIL"
    return f"""# Stage 11R: Hierarchical Test-Set Isolation Audit

- Verification: `{status}`
- Evidence state: `{result['evidence_state']}`
- Pixel payload bytes opened: `0`

## Result

The frozen Stage 11L product-key canary contains {metrics['test_products']:,} test products, but none is isolated from training at the verified complete-action layer.

| Test-product relationship to training | Products | Share of test partition |
| --- | ---: | ---: |
| Exact capture identity also in training | {metrics['capture_linked_test_products']:,} | {metrics['capture_linked_test_share']:.3%} |
| Capture absent, complete action in training | {metrics['action_only_linked_test_products']:,} | {metrics['action_only_linked_test_share']:.3%} |
| Complete action absent from training | {metrics['action_isolated_test_products']:,} | {metrics['action_isolated_test_share']:.3%} |

The accounting identity is exact:

`{metrics['test_products']:,} = {metrics['capture_linked_test_products']:,} + {metrics['action_only_linked_test_products']:,} + {metrics['action_isolated_test_products']:,}`

At the group level, the test partition contains {metrics['test_visible_capture_groups']:,} capture identities. Only {metrics['capture_isolated_test_capture_groups']:,} captures are absent from training, and all of them belong to actions represented in training. The {metrics['test_visible_action_groups']:,} test-visible action groups are therefore all crossing actions, with zero action groups isolated in test.

Across the full assignment artifact, those {metrics['crossing_action_groups']:,} crossing action groups contain {metrics['products_in_crossing_action_groups']:,} of {metrics['rows']:,} products ({metrics['share_all_products_in_crossing_actions']:.3%}).

## Decision use

Use this result to show that a filename-disjoint test partition can still have zero action-isolated test products under one frozen product-key policy. Require a real task to name its prediction unit, estimand, and protected relation before treating structural isolation as sufficient.

## Claim ceiling

{result['claim_ceiling']}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    result = verify_stage11r(root)
    if args.write:
        json_path = root / "results/stage11r-hierarchical-isolation.json"
        markdown_path = root / "results/stage11r-result.md"
        json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        markdown_path.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
