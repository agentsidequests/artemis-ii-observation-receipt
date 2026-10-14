#!/usr/bin/env python3
"""Verify Stage 10I's source-to-current-archive provenance crosswalk."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file
from stage10a_metadata_integrity import add_check, load_json
from stage10e_all_days_integrity import verify_stage10e


SERIAL_KEY = "img_surface:Instrument_Information/img_surface:instrument_serial_number"


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "source_equals_products": False, "iphone_lost": False, "nikon_lost": False,
        "cab2_lost": False, "audio_counts_equivalent": False, "all_sources_tripled": False,
        "snapshot_complete": False,
    }
    if mutation is None:
        return mutated
    mapping = {
        "equate_source_files_with_current_products": "source_equals_products",
        "declare_pending_iphone_files_lost": "iphone_lost",
        "declare_nikon_residuals_lost": "nikon_lost",
        "declare_cab2_residuals_lost": "cab2_lost",
        "equate_112_audio_products_with_115_source_files": "audio_counts_equivalent",
        "triple_every_mission_source_file": "all_sources_tripled",
        "declare_current_atlas_snapshot_complete": "snapshot_complete",
    }
    if mutation == "open_pixels_to_explain_inventory_residuals":
        mutated["source_contract"]["pixel_payload_bytes"] = 1
    elif mutation in mapping:
        mutated["mutation_state"][mapping[mutation]] = True
    else:
        raise ValueError(f"Unknown mutation: {mutation}")
    return mutated


def verify_receipt(root: Path, receipt: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for record in receipt.get("sources", []):
        path = root / record["path"]
        if not path.is_file():
            failures.append(f"missing:{record['path']}")
            continue
        if path.stat().st_size != record["bytes"]:
            failures.append(f"bytes:{record['path']}")
        if sha256_file(path) != record["sha256"]:
            failures.append(f"sha256:{record['path']}")
    return failures


def page_paths(root: Path, receipt_path: str, key: str) -> list[Path]:
    receipt = load_json(root / receipt_path)
    return [root / item[key] for item in receipt["atlas_pages"]]


def current_nikon_counts(root: Path, contract: dict[str, Any]) -> Counter[str]:
    paths = page_paths(root, contract["stage10a_receipt_path"], "response_path")
    paths += page_paths(root, contract["stage10e_receipt_path"], "response_path")
    counts: Counter[str] = Counter()
    for path in paths:
        for hit in load_json(path)["hits"]["hits"]:
            values = hit["_source"].get("pds4_label", {}).get(SERIAL_KEY, [])
            if values:
                counts[str(values[0])] += 1
    return counts


def current_orion_counts(path: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    pattern = re.compile(r"_([^_:]+)_raw")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.search(line)
        if match:
            counts[match.group(1)] += 1
    return counts


def atlas_audio_counts(payload: dict[str, Any]) -> dict[str, int]:
    for bundle in payload["aggregations"]["bundles"]["buckets"]:
        if bundle["key"] == "artemis2_mission_audio":
            return {item["key"]: int(item["doc_count"]) for item in bundle["collections"]["buckets"]}
    return {}


def verify_stage10i(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec" / "stage10i.json"), mutation)
    contract, expected = spec["source_contract"], spec["frozen_observables"]
    receipt = load_json(root / contract["receipt_path"])
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    receipt_failures = verify_receipt(root, receipt)
    add_check(checks, errors, "source_identity", receipt.get("status") == "COMPLETED" and not receipt_failures,
              error="A Stage 10I source or dependency identity changed.", failures=receipt_failures)

    upstream_e = verify_stage10e(root)
    upstream_h = load_json(root / contract["stage10h_result_path"])
    upstream_ok = upstream_e.get("pass") is True and upstream_h.get("pass") is True
    add_check(checks, errors, "verified_upstream_ledgers", upstream_ok,
              error="An upstream complete-inventory or source-volume checkpoint failed.")

    report = " ".join((root / contract["report_table_path"]).read_text(encoding="utf-8", errors="replace").split())
    report_ok = all(phrase in report for phrase in (
        "Nikon D5 (3500015) 7011", "Nikon D5 (3500017) 553", "Nikon Z9 (3920019) 2775",
        "iPhone 17 Pro 68", "Total Crew Camera 10407", "CAB Cam 2 176", "Total Orion Camera (Still) 1040 3.14",
        "Total Mission Audio 115 2.86",
    ))
    add_check(checks, errors, "official_source_type_inventory", report_ok,
              error="The official source inventory by instrument or type changed.")

    nikon = current_nikon_counts(root, contract)
    expected_nikon = {key: int(value) for key, value in expected["atlas_nikon_counts"].items()}
    source_nikon = {key: int(value) for key, value in expected["source_nikon_counts"].items()}
    residuals = {key: source_nikon[key] - nikon[key] for key in source_nikon}
    guide = " ".join((root / contract["user_guide_path"]).read_text(encoding="utf-8", errors="replace").lower().split())
    iphone_pending = all(phrase in guide for phrase in (
        "archive collection for the small number of crew captured images from the iphone 17 pro max was still being prepared",
        "an update to t he archive and th is user guide will be made upon later release",
    ))
    crew_ok = (
        dict(nikon) == expected_nikon
        and residuals == expected["nikon_residuals"]
        and sum(nikon.values()) == 10329
        and expected["source_crew_total"] - sum(nikon.values()) == 78
        and expected["source_iphone_count"] == 68
        and iphone_pending
    )
    add_check(checks, errors, "crew_source_to_current_crosswalk", crew_ok,
              error="The Nikon counts, iPhone pending state, or residual distribution changed.",
              current_nikon=dict(nikon), nikon_residuals=residuals,
              documented_pending_iphone=expected["source_iphone_count"], unexplained_nikon=sum(residuals.values()))

    orion = current_orion_counts(root / contract["orion_inventory_path"])
    expected_orion = {key: int(value) for key, value in expected["atlas_orion_still_counts"].items()}
    source_orion = {key: int(value) for key, value in expected["source_orion_still_counts"].items()}
    orion_residuals = {key: source_orion[key] - orion[key] for key in source_orion}
    orion_ok = dict(orion) == expected_orion and sum(orion.values()) == 1012 and orion_residuals == {
        "saw2": 0, "saw3": 0, "saw4": 0, "cab2": 28, "onav": 0, "dcam": 0,
    }
    add_check(checks, errors, "orion_source_to_current_crosswalk", orion_ok,
              error="The Orion current inventory or instrument-specific residual changed.",
              current_orion=dict(orion), residuals=orion_residuals)

    atlas = load_json(root / contract["atlas_response_path"])
    audio = atlas_audio_counts(atlas)
    expected_audio = {key: int(value) for key, value in expected["atlas_audio_product_counts"].items()}
    audio_rules = all(phrase in guide for phrase in (
        "voice loop audio recordings were received as mp3 and converted to m4a for pds4-compliance",
        "they were split into lengths by utc day around lunar flyby",
        "one transcript file was produced for each pcd audio (.m4a) file",
    )) and "brief transcriptions of nikon audio wav files were added to the metadata" in report.lower()
    audio_ok = audio == expected_audio and sum(audio.values()) == 112 and audio_rules
    add_check(checks, errors, "audio_non_bijective_product_mapping", audio_ok,
              error="The audio product counts or documented transformation rules changed.",
              source_audio_files=expected["source_audio_files"], current_audio_products=audio)

    state = spec["mutation_state"]
    boundary_ok = (
        not any(state.values()) and contract["pixel_payload_bytes"] == 0 and receipt["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited equivalence, loss, completeness, generalization, or pixel claim was admitted.",
              mutation_state=state, pixel_payload_bytes=contract["pixel_payload_bytes"])

    mapping_ok = report_ok and crew_ok and orion_ok and audio_ok
    evidence_state = "VERIFIED_NON_BIJECTIVE_PROVENANCE_CROSSWALK_WITH_RESIDUALS" if mapping_ok else "CROSSWALK_UNRESOLVED"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "source_crew_files": expected["source_crew_total"], "current_nikon_identities": sum(nikon.values()),
        "current_nikon_counts": dict(nikon), "documented_pending_iphone": expected["source_iphone_count"],
        "unexplained_nikon_residuals": residuals, "unexplained_nikon_total": sum(residuals.values()),
        "source_orion_stills": sum(source_orion.values()), "current_orion_stills": sum(orion.values()),
        "unexplained_orion_residuals": orion_residuals,
        "source_audio_files": expected["source_audio_files"], "current_audio_products": audio,
        "verified": spec["interpretation"]["verified"], "bounded_inference": spec["interpretation"]["bounded_inference"],
        "decision_use": spec["interpretation"]["decision_use"], "pixel_payload_bytes": receipt["pixel_payload_bytes"],
        "claim_ceiling": spec["claim_ceiling"], "next_step_logic": spec["next_step_logic"],
        "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10i(root)
    names = load_json(root / "spec" / "stage10i.json")["hard_negatives"]
    mutations = {name: verify_stage10i(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10I hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 10I — Source-to-Archive Provenance Crosswalk", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`", f"- Evidence state: `{result['evidence_state']}`",
        f"- Crew source files / current Nikon identities: `{result['source_crew_files']:,}` / `{result['current_nikon_identities']:,}`",
        f"- Documented pending iPhone / unexplained Nikon residual: `{result['documented_pending_iphone']}` / `{result['unexplained_nikon_total']}`",
        f"- Orion source stills / current Orion still products: `{result['source_orion_stills']:,}` / `{result['current_orion_stills']:,}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`", "",
        "## Verified", "", result["verified"], "", "## Bounded inference", "", result["bounded_inference"], "",
        "## Decision use", "", result["decision_use"], "", "## Claim ceiling", "", result["claim_ceiling"], "", "## Hard negatives", "",
    ]
    for name, mutation_result in result.get("hard_negatives", {}).items():
        lines.append(f"- `{name}`: {'REJECTED' if not mutation_result['pass'] else 'UNEXPECTEDLY ACCEPTED'}")
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json-output", type=Path); parser.add_argument("--markdown-output", type=Path); parser.add_argument("--mutation")
    args = parser.parse_args(argv)
    result = verify_with_mutations(args.root.resolve()) if args.command == "verify" else verify_stage10i(args.root.resolve(), args.mutation)
    if args.json_output: write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2)); return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
