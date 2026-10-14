#!/usr/bin/env python3
"""Verify Stage 10H's source-volume versus archive-footprint reconciliation."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

from artemis_testbed import sha256_file
from stage10a_metadata_integrity import add_check, load_json


def apply_mutation(spec: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    mutated = copy.deepcopy(spec)
    mutated["mutation_state"] = {
        "headline_basis": "source_table_814_51_gb",
        "source_volume_bytes": False,
        "source_volume_current_download": False,
        "products_independent": False,
        "video_difference_missing": False,
        "representations_waste": False,
        "release_completeness_inferred": False,
    }
    if mutation is None:
        return mutated
    state = mutated["mutation_state"]
    if mutation == "claim_833gb_is_documented_headline_basis":
        state["headline_basis"] = "stage10d_833_9_gb_subtotal"
    elif mutation == "claim_2527tb_is_source_data_volume":
        state["source_volume_bytes"] = True
    elif mutation == "claim_815gb_is_current_download_footprint":
        state["source_volume_current_download"] = True
    elif mutation == "treat_archive_products_as_independent_observations":
        state["products_independent"] = True
    elif mutation == "call_video_size_difference_missing_data":
        state["video_difference_missing"] = True
    elif mutation == "call_format_conversions_wasteful_duplicates":
        state["representations_waste"] = True
    elif mutation == "infer_current_release_completeness_from_count_difference":
        state["release_completeness_inferred"] = True
    elif mutation == "open_pixels_to_reconcile_ledger_units":
        mutated["source_contract"]["pixel_payload_bytes"] = 1
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


def atlas_values(payload: dict[str, Any]) -> dict[str, int]:
    bundles = payload["aggregations"]["bundles"]["buckets"]
    values = {
        "products": int(payload["hits"]["total"]["value"]),
        "bytes": int(sum(item["bytes"]["value"] for item in bundles)),
        "video_products": 0,
        "video_bytes": 0,
    }
    for bundle in bundles:
        for collection in bundle["collections"]["buckets"]:
            if collection["key"] == "data_video":
                values["video_products"] = int(collection["doc_count"])
                values["video_bytes"] = int(collection["bytes"]["value"])
    return values


def verify_stage10h(root: Path, mutation: str | None = None) -> dict[str, Any]:
    spec = apply_mutation(load_json(root / "spec" / "stage10h.json"), mutation)
    contract = spec["source_contract"]
    expected = spec["frozen_observables"]
    receipt = load_json(root / contract["receipt_path"])
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    receipt_failures = verify_receipt(root, receipt)
    parent = receipt.get("external_parent_sources", [{}])[0]
    source_ok = (
        receipt.get("status") == "COMPLETED"
        and not receipt_failures
        and parent.get("bytes") == 143769154
        and parent.get("sha256") == "edf4a22f7451b404c7eb85210e357bd5809a34aff79b07ccf8d57a9ca53748fa"
    )
    add_check(checks, errors, "source_identity", source_ok,
              error="A focused source, dependency, or parent-report identity changed.",
              failures=receipt_failures)

    report = " ".join((root / contract["report_page_text_path"]).read_text(
        encoding="utf-8", errors="replace").split())
    table_phrases = (
        "Table 4.1: Science Data Summary",
        "Total Mission Science Data File Count Volume (GB)",
        "11591 814.51",
        "Total Crew Camera 10407 210.29",
        "Total Orion Camera (Still) 1040 3.14",
        "Total Orion Camera (Video) 22 598.20",
        "Total Mission Audio 115 2.86",
        "Total Mission (Other) 7 0.02",
    )
    table_ok = all(phrase in report for phrase in table_phrases)
    add_check(checks, errors, "official_source_data_ledger", table_ok,
              error="NASA Table 4.1's source-data counts or volumes did not reproduce.",
              files=expected["source_file_count"], volume_gb=expected["source_volume_gb"])

    release = (root / contract["nasa_release_path"]).read_text(
        encoding="utf-8", errors="replace")
    headline_ok = bool(re.search(r"More than 800 gigabytes of .*?Artemis II lunar science data", release, re.I | re.S))
    add_check(checks, errors, "official_release_wording", headline_ok,
              error="NASA's more-than-800-GB release wording did not reproduce.")

    atlas = atlas_values(load_json(root / contract["atlas_response_path"]))
    atlas_ok = (
        atlas["products"] == expected["atlas_product_count"]
        and atlas["bytes"] == expected["atlas_archive_bytes"]
        and atlas["video_products"] == expected["atlas_video_products"]
        and atlas["video_bytes"] == expected["atlas_video_bytes"]
    )
    add_check(checks, errors, "atlas_archive_product_ledger", atlas_ok,
              error="The preserved Atlas product or archive-size ledger changed.", **atlas)

    guide = " ".join((root / contract["user_guide_text_path"]).read_text(
        encoding="utf-8", errors="replace").lower().split())
    conversion_ok = all(phrase in guide for phrase in (
        "source image files, raw files that have been converted to pds4- compliant array image format, processed images",
        "substantial reductions in the size of files during conversion to mp4 format for archiving",
        "converted to mp4 (.mp4) with h.264 codec",
    ))
    add_check(checks, errors, "official_representation_and_video_bridge", conversion_ok,
              error="The official representation or MXF-to-MP4 conversion explanation changed.",
              source_video_gb=expected["source_orion_video_volume_gb"],
              atlas_video_bytes=atlas["video_bytes"])

    stage10d = load_json(root / contract["stage10d_result_path"])
    prior = stage10d["mission_bytes_excluding_processed_crew_collection"] / 1_000_000_000
    falsification_ok = (
        stage10d.get("pass") is True
        and abs(prior - expected["prior_subtotal_gb"]) < 1e-12
        and table_ok
        and abs(prior - expected["source_volume_gb"]) > 1.0
    )
    add_check(checks, errors, "stage10d_hypothesis_superseded", falsification_ok,
              error="The prior subtotal or its decisive official counterevidence did not reproduce.",
              prior_subtotal_gb=prior, documented_source_volume_gb=expected["source_volume_gb"])

    state = spec["mutation_state"]
    boundary_ok = (
        state["headline_basis"] == "source_table_814_51_gb"
        and not any(state[key] for key in (
            "source_volume_bytes", "source_volume_current_download", "products_independent",
            "video_difference_missing", "representations_waste", "release_completeness_inferred",
        ))
        and contract["pixel_payload_bytes"] == 0
        and receipt["pixel_payload_bytes"] == 0
    )
    add_check(checks, errors, "claim_and_access_boundaries", boundary_ok,
              error="A prohibited accounting, independence, loss, waste, completeness, or pixel claim was admitted.",
              mutation_state=state, pixel_payload_bytes=contract["pixel_payload_bytes"])

    reconciliation_ok = table_ok and headline_ok and atlas_ok and conversion_ok and falsification_ok
    evidence_state = "VERIFIED_SOURCE_VOLUME_VS_ARCHIVE_PRODUCT_FOOTPRINT" if reconciliation_ok else "UNRESOLVED_LEDGER_RECONCILIATION"
    return {
        "testbed_id": spec["testbed_id"], "mutation": mutation, "pass": not errors,
        "evidence_state": evidence_state if not errors else "REJECTED",
        "source_file_count": expected["source_file_count"],
        "source_volume_gb": expected["source_volume_gb"],
        "atlas_product_count": atlas["products"], "atlas_archive_bytes": atlas["bytes"],
        "atlas_archive_decimal_tb": atlas["bytes"] / 1_000_000_000_000,
        "source_video_files": expected["source_orion_video_files"],
        "source_video_volume_gb": expected["source_orion_video_volume_gb"],
        "atlas_video_products": atlas["video_products"], "atlas_video_bytes": atlas["video_bytes"],
        "prior_subtotal_gb": prior, "prior_hypothesis_superseded": falsification_ok,
        "verified": spec["interpretation"]["verified"],
        "falsification": spec["interpretation"]["falsification"],
        "video_bridge": spec["interpretation"]["video_bridge"],
        "decision_use": spec["interpretation"]["decision_use"],
        "pixel_payload_bytes": receipt["pixel_payload_bytes"],
        "claim_ceiling": spec["claim_ceiling"], "next_step_logic": spec["next_step_logic"],
        "checks": checks, "errors": errors,
    }


def verify_with_mutations(root: Path) -> dict[str, Any]:
    baseline = verify_stage10h(root)
    names = load_json(root / "spec" / "stage10h.json")["hard_negatives"]
    mutations = {name: verify_stage10h(root, name) for name in names}
    hard_negatives_pass = all(not result["pass"] for result in mutations.values())
    return {**baseline, "hard_negatives": mutations, "hard_negatives_pass": hard_negatives_pass,
            "pass": baseline["pass"] and hard_negatives_pass,
            "errors": baseline["errors"] + ([] if hard_negatives_pass else ["At least one Stage 10H hard negative was accepted."])}


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Stage 10H — Source Volume / Archive Footprint Reconciliation", "",
        f"- Verification: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Evidence state: `{result['evidence_state']}`",
        f"- Official source ledger: `{result['source_file_count']:,}` files / `{result['source_volume_gb']:.2f} GB`",
        f"- Preserved Atlas ledger: `{result['atlas_product_count']:,}` products / `{result['atlas_archive_decimal_tb']:.12f} TB`",
        f"- Source video / Atlas video: `{result['source_video_volume_gb']:.2f} GB` MXF / `{result['atlas_video_bytes'] / 1_000_000_000:.9f} GB` MP4",
        f"- Prior 833.9-GB hypothesis superseded: `{result['prior_hypothesis_superseded']}`",
        f"- Pixel payload bytes opened: `{result['pixel_payload_bytes']}`", "",
        "## Verified", "", result["verified"], "", "## Successful falsification", "", result["falsification"], "",
        "## Video bridge", "", result["video_bridge"], "", "## Decision use", "", result["decision_use"], "",
        "## Claim ceiling", "", result["claim_ceiling"], "", "## Hard negatives", "",
    ]
    for name, mutation_result in result.get("hard_negatives", {}).items():
        verdict = "REJECTED" if not mutation_result["pass"] else "UNEXPECTEDLY ACCEPTED"
        lines.append(f"- `{name}`: {verdict}")
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--mutation")
    args = parser.parse_args(argv)
    if args.command == "verify":
        if args.mutation:
            parser.error("--mutation is valid only with run")
        result = verify_with_mutations(args.root.resolve())
    else:
        result = verify_stage10h(args.root.resolve(), args.mutation)
    if args.json_output:
        write_json(args.json_output, result)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result) if args.command == "verify" else json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
