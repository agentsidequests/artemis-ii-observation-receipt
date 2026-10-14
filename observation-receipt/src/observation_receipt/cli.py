"""Command-line entrypoint for Observation Receipt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .evaluator import evaluate_case
from .exporters import write_bundle
from .model import CaseValidationError
from . import robustness


APP_ROOT = Path(__file__).resolve().parents[2]


def _load_case(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(case_path: Path, root: Path, output: Path | None) -> int:
    try:
        case = _load_case(case_path)
        is_robustness = case.get("case_kind") == "tag_weight_robustness"
        receipt = robustness.evaluate(case, root) if is_robustness else evaluate_case(case, root)
    except (OSError, json.JSONDecodeError, CaseValidationError, KeyError, TypeError, ValueError) as error:
        print(f"Observation Receipt could not evaluate the case:\n{error}", file=sys.stderr)
        return 2
    if output is not None:
        written = robustness.write_bundle(receipt, output) if is_robustness else write_bundle(case, receipt, output)
        print(f"Built {case['title']}")
        print(f"Viewer: {written['index.html']}")
        print(f"Receipt: {written['receipt.json']}")
    else:
        print(json.dumps(receipt, indent=2))
    return 0 if receipt["pass"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="observation-receipt",
        description="Show whether evidence had the opportunity and capability to support a claim.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate and evaluate one case without writing files.")
    validate.add_argument("case", type=Path)
    validate.add_argument("--root", type=Path, default=Path.cwd(), help="Root used to resolve local artifact paths.")

    build = subparsers.add_parser("build", help="Build a portable receipt bundle and local viewer.")
    build.add_argument("case", type=Path)
    build.add_argument("--root", type=Path, default=Path.cwd(), help="Root used to resolve local artifact paths.")
    build.add_argument("--output", type=Path, required=True)

    demo = subparsers.add_parser("demo", help="Build the included Artemis II demonstration.")
    demo.add_argument("--case", choices=["flashes", "identity", "identity-confirmed", "robustness"], default="flashes", help="Choose flash evidence, historical identity comparison, current steward-confirmed pair or hypothetical target-weight robustness.")
    demo.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        name = {"flashes": "artemis-ii-flashes", "identity": "artemis-ii-identity", "identity-confirmed": "artemis-ii-identity-confirmed", "robustness": "artemis-ii-robustness"}[args.case]
        output = args.output if args.output is not None else APP_ROOT / "build" / name
        return _run(APP_ROOT / "cases" / name / "case.json", APP_ROOT, output.resolve())
    case_path = args.case.resolve()
    output = args.output.resolve() if args.command == "build" else None
    return _run(case_path, args.root.resolve(), output)
