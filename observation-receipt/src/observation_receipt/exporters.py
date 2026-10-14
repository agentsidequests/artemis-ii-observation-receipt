"""Portable receipt exports and the read-only local viewer."""

from __future__ import annotations

import base64
import csv
import hashlib
import html
import json
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .evaluator import parse_utc
from . import comparison_exports
from . import steward_links


def _status_family(status: str) -> str:
    if status.startswith("SUPPORTED"):
        return "supported"
    if status.startswith("REFUTED"):
        return "refuted"
    if status.startswith("BLOCKED"):
        return "blocked"
    return "other"


def _humanize(value: str) -> str:
    return value.replace("_", " ").strip().title()


def _format_value(value: Any) -> str:
    if value is None:
        return "Not provided"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        if value != 0 and (abs(value) < 0.001 or abs(value) >= 1_000_000):
            return f"{value:.6g}"
        return f"{value:,.6f}".rstrip("0").rstrip(".")
    if isinstance(value, list):
        return ", ".join(_format_value(item) for item in value) if value else "None"
    if isinstance(value, dict):
        return ", ".join(f"{_humanize(str(key))}: {_format_value(item)}" for key, item in value.items())
    return str(value)


def _finding_details(finding: dict[str, Any]) -> list[tuple[str, str]]:
    hidden = {"claim_id", "proposition", "rule_kind", "claim_ceiling", "status"}
    return [(_humanize(key), _format_value(value)) for key, value in finding.items() if key not in hidden]


def render_markdown(case: dict[str, Any], receipt: dict[str, Any]) -> str:
    lines = [
        f"# Observation Receipt: {case['title']}",
        "",
        f"State: `{receipt['state']}`",
        "",
        case.get("summary", ""),
        "",
        "## Decision summary",
        "",
        f"- Supported: **{receipt['summary']['supported']}**",
        f"- Refuted: **{receipt['summary']['refuted']}**",
        f"- Blocked: **{receipt['summary']['blocked']}**",
        f"- Local artifacts verified: **{sum(item['state'] == 'MATCH' for item in receipt['artifact_checks'])} / {sum('path' in item for item in receipt['artifact_checks'])}**",
        f"- Reference-only URLs, not byte verified: **{sum(item['state'] == 'REFERENCE_ONLY' for item in receipt['artifact_checks'])}**",
        "",
        "## Findings",
        "",
        "| Claim | Status | Claim ceiling |",
        "|---|---|---|",
    ]
    extension_text = steward_links.markdown(receipt) + comparison_exports.markdown(receipt)
    if extension_text:
        lines[-5:] = [extension_text, "", "## Findings", "", "| Claim | Status | Claim ceiling |", "|---|---|---|"]
    for finding in receipt["findings"]:
        lines.append(
            f"| {finding['proposition']} | `{finding['status']}` | {finding['claim_ceiling']} |"
        )
    lines.extend(["", "## Why each finding landed there", ""])
    for finding in receipt["findings"]:
        lines.extend([f"### {finding['proposition']}", "", f"**{finding['status']}**", ""])
        for label, value in _finding_details(finding):
            lines.append(f"- {label}: {value}")
        lines.extend(["", f"Claim ceiling: {finding['claim_ceiling']}", ""])

    lines.extend(["## Observation windows", "", "| Window | Start | Stop | Target |", "|---|---|---|---|"])
    for window in case["observation_windows"]:
        lines.append(f"| {window['label']} | {window['start_utc']} | {window['stop_utc']} | {window['target']} |")

    lines.extend(["", "## Witness marks", "", "| Candidate | Observer | Time state | Mark time | Elicitation | Independence |", "|---|---|---|---|---|---|"])
    for candidate in case["candidates"]:
        for mark in candidate["witness_marks"]:
            lines.append(
                f"| {candidate['label']} | {mark['observer']} | {mark['time_state']} | {mark.get('marked_at_utc') or 'Unknown'} | {mark['elicitation_state']} | {mark['independence_state']} |"
            )

    lines.extend(["", "## Artifact integrity", "", "| Artifact | State |", "|---|---|"])
    for artifact in receipt["artifact_checks"]:
        lines.append(f"| {artifact['id']} | `{artifact['state']}` |")

    lines.extend(["", "## Claim ceiling", "", receipt["claim_ceiling"], ""])
    if receipt.get("next_steps"):
        lines.extend(["## What would change this receipt", ""])
        for item in receipt["next_steps"]:
            lines.append(f"- {item}")
        lines.append("")
    lines.extend(
        [
            "## Reproduce",
            "",
            "This bundle was generated deterministically from the case file and hash-pinned local artifacts. Rebuild it with the command documented in the project README.",
            "",
        ]
    )
    return "\n".join(lines)


def _timeline(case: dict[str, Any]) -> str:
    windows = case["observation_windows"]
    exact_marks = [
        (candidate, mark)
        for candidate in case["candidates"]
        for mark in candidate["witness_marks"]
        if mark.get("marked_at_utc")
    ]
    points = [parse_utc(window["start_utc"]) for window in windows]
    points.extend(parse_utc(window["stop_utc"]) for window in windows)
    points.extend(parse_utc(mark["marked_at_utc"]) for _, mark in exact_marks)
    if not points:
        return "<p>No exact times are available for this case.</p>"
    minimum = min(points)
    maximum = max(points)
    span = max((maximum - minimum).total_seconds(), 1.0)

    rows: list[str] = []
    for window in windows:
        start = (parse_utc(window["start_utc"]) - minimum).total_seconds() / span * 100
        width = (parse_utc(window["stop_utc"]) - parse_utc(window["start_utc"])).total_seconds() / span * 100
        rows.append(
            '<div class="timeline-row">'
            f'<div class="timeline-label">{html.escape(window["label"])}</div>'
            '<div class="timeline-track">'
            f'<span class="window-bar" style="left:{start:.3f}%;width:{max(width, 0.6):.3f}%" title="{html.escape(window["start_utc"])} to {html.escape(window["stop_utc"])}"></span>'
            "</div></div>"
        )
    marks: list[str] = []
    for candidate, mark in exact_marks:
        position = (parse_utc(mark["marked_at_utc"]) - minimum).total_seconds() / span * 100
        label = f"{candidate['label']}: {mark['observer']} at {mark['marked_at_utc']}"
        marks.append(
            f'<span class="event-dot" style="left:{position:.3f}%" title="{html.escape(label)}"><span class="sr-only">{html.escape(label)}</span></span>'
        )
    start_label = minimum.strftime("%H:%M:%S UTC")
    stop_label = maximum.strftime("%H:%M:%S UTC")
    return (
        '<div class="timeline" role="img" aria-label="Observation windows and exact witness marks on a shared UTC timeline">'
        + "".join(rows)
        + '<div class="timeline-row event-row"><div class="timeline-label">Exact witness marks</div><div class="timeline-track">'
        + "".join(marks)
        + "</div></div>"
        + f'<div class="timeline-axis"><span>{start_label}</span><span>{stop_label}</span></div></div>'
    )


def _witness_matrix(case: dict[str, Any]) -> str:
    observers = sorted({mark["observer"] for candidate in case["candidates"] for mark in candidate["witness_marks"]})
    headings = "".join(f"<th scope=\"col\">{html.escape(observer)}</th>" for observer in observers)
    rows: list[str] = []
    for candidate in case["candidates"]:
        cells: list[str] = []
        by_observer = {mark["observer"]: mark for mark in candidate["witness_marks"]}
        for observer in observers:
            mark = by_observer.get(observer)
            if not mark:
                cells.append('<td><span class="mark none">Not marked</span></td>')
                continue
            symbol = "●" if mark["elicitation_state"] == "unprompted" else "◐" if mark["elicitation_state"] in {"prompted", "socially_cued"} else "○"
            label = f"{symbol} {_humanize(mark['elicitation_state'])}; {_humanize(mark['independence_state'])}"
            cells.append(f'<td><span class="mark">{html.escape(label)}</span></td>')
        rows.append(
            f'<tr><th scope="row">{html.escape(candidate["label"])}</th>{"".join(cells)}</tr>'
        )
    return (
        '<div class="table-wrap"><table><caption>Marks remain distinct from independent confirmations.</caption>'
        f'<thead><tr><th scope="col">Candidate</th>{headings}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
    )


def render_html(
    case: dict[str, Any],
    receipt: dict[str, Any],
    download_payloads: dict[str, str] | None = None,
) -> str:
    esc = html.escape
    summary = receipt["summary"]
    findings: list[str] = []
    for finding in receipt["findings"]:
        details = "".join(
            f"<dt>{esc(label)}</dt><dd>{esc(value)}</dd>" for label, value in _finding_details(finding)
        )
        family = _status_family(finding["status"])
        heading = finding["proposition"]
        evaluated_claim = ""
        if family in {'blocked', 'refuted'}:
            heading = 'This claim remains blocked by missing evidence.' if family == 'blocked' else 'The saved evidence refutes this evaluated claim.'
            evaluated_claim = f'<p class="evaluated-claim"><strong>Claim evaluated, not established:</strong> {esc(finding["proposition"])}</p>'
        if finding["rule_kind"] == "identity_resolution_gate":
            heading = {
                "BLOCKED_IDENTITY_UNRESOLVED": "Physical identity remains unresolved",
                "BLOCKED_IDENTITY_INTEGRITY": "Identity evidence could not be verified",
            }.get(finding["status"], "Identity assessment")
            if receipt.get('steward_links'):
                heading = 'Metadata-only proof remains insufficient' if finding['status']=='BLOCKED_IDENTITY_UNRESOLVED' else 'Historical metadata evidence could not be verified'
            evaluated_claim = f'<p><strong>Claim evaluated:</strong> {esc(finding["proposition"])}</p>'
        findings.append(
            f'<article class="finding {family}" data-claim-card="{esc(finding["claim_id"])}" data-status-family="{family}" tabindex="-1"><div class="finding-top"><span class="status {family}">{esc(finding["status"])}</span><span class="rule">{esc(_humanize(finding["rule_kind"]))}</span><a class="claim-link" href="#claim={quote(finding["claim_id"], safe="")}">Focus this claim</a></div>'
            f'<h3>{esc(heading)}</h3>{evaluated_claim}<details><summary>How this result follows from the evidence</summary><dl>{details}</dl></details>'
            f'<p class="ceiling"><strong>Claim ceiling:</strong> {esc(finding["claim_ceiling"])}</p></article>'
        )

    window_rows: list[str] = []
    for window in case["observation_windows"]:
        capabilities = "".join(
            f'<li><span class="cap-state {esc(item["state"])}">{esc(_humanize(item["state"]))}</span> {esc(_humanize(name))}</li>'
            for name, item in window["capabilities"].items()
        )
        window_rows.append(
            f'<article class="window-card"><p class="eyebrow">{esc(window["target"])}</p><h3>{esc(window["label"])}</h3>'
            f'<p class="mono">{esc(window["start_utc"])}<br>{esc(window["stop_utc"])}</p><ul class="capabilities">{capabilities}</ul></article>'
        )

    artifact_rows = "".join(
        f'<tr><th scope="row">{esc(item["id"])}</th><td><span class="status {"supported" if item["state"] == "MATCH" else "other" if item["state"] == "REFERENCE_ONLY" else "refuted"}">{esc(item["state"])}</span></td><td class="mono">{esc(str(item.get("sha256") or item.get("url") or ""))}</td></tr>'
        for item in receipt["artifact_checks"]
    )
    next_steps = "".join(f"<li>{esc(item)}</li>" for item in receipt.get("next_steps", []))
    verified = sum(item["state"] == "MATCH" for item in receipt["artifact_checks"])
    total_artifacts = sum("path" in item for item in receipt["artifact_checks"])
    references = sum(item["state"] == "REFERENCE_ONLY" for item in receipt["artifact_checks"])
    state_class = "supported" if receipt["pass"] else "refuted"
    subtitle = case.get("summary", "")
    display_title = case['title']
    links = receipt.get('steward_links', [])
    if len(links)==1 and links[0]['integrity_verified'] and links[0]['statement'] is not None:
        statement=links[0]['statement']
        display_title='One confirmed pair. Original counts preserved.'
        subtitle=f"Archive-steward confirmation links {' and '.join(statement['native_identifiers'])} to reported original {statement['reported_original_filename']}. Local NEF-byte equality remains unverified. The original and historical conditional values below are unchanged."
    context = case.get("viewer_context", {})
    distinction = context.get(
        "key_distinction",
        "A timestamp match is not evidence coverage. A null is not an exclusion unless the sensor could see the event.",
    )
    mime_types = {
        "receipt.json": "application/json",
        "receipt.md": "text/markdown",
        "witness-marks.csv": "text/csv",
    }

    def download_href(name: str) -> str:
        if not download_payloads or name not in download_payloads:
            return name
        encoded = base64.b64encode(download_payloads[name].encode("utf-8")).decode("ascii")
        return f"data:{mime_types[name]};charset=utf-8;base64,{encoded}"

    receipt_json_href = html.escape(download_href("receipt.json"), quote=True)
    receipt_markdown_href = html.escape(download_href("receipt.md"), quote=True)
    witness_csv_href = html.escape(download_href("witness-marks.csv"), quote=True)
    mime_types["comparison.csv"] = "text/csv"
    comparison_href = html.escape(download_href("comparison.csv"), quote=True)
    extra_download = f'<a class="button secondary" href="{comparison_href}" download="comparison.csv">Original / conditional CSV</a>' if receipt.get("conditional_comparisons") else ""
    witness_download = f'<a class="button secondary" href="{witness_csv_href}" download="witness-marks.csv">Witness marks CSV</a>' if any(c["witness_marks"] for c in case["candidates"]) else ""
    temporal_sections = ""
    if case["observation_windows"] or any(c["witness_marks"] for c in case["candidates"]):
        temporal_sections = f'<section id="timeline"><p class="eyebrow">Opportunity layer</p><h2>When evidence could observe the event</h2><p class="section-intro">Exact witness marks and observation windows share one UTC axis. Unknown event times remain unknown rather than being pulled toward the nearest camera frame.</p>{_timeline(case)}<div class="windows">{"".join(window_rows)}</div></section><section id="witnesses"><p class="eyebrow">Human evidence</p><h2>Who marked what, and under what conditions</h2><p class="section-intro">Filled circles are unprompted marks. Half circles are prompted or socially cued marks. Open circles preserve unknown elicitation state. None of these symbols asserts statistical independence.</p>{_witness_matrix(case)}</section>'
    supported_label = "Supported conditional predicates" if receipt.get("conditional_comparisons") else "Supported claims"

    interactive_style = Path(__file__).with_name('explorer.css').read_text(encoding='utf-8')
    interactive_script = Path(__file__).with_name('claim-explorer.js').read_text(encoding='utf-8')
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'">
<title>Observation Receipt: {esc(display_title)}</title>
<style>
:root {{ --ink:#102331; --muted:#506472; --paper:#f6f2e9; --card:#fffdf8; --line:#d8d1c3; --navy:#0b2030; --teal:#087c77; --teal-soft:#dff4ed; --coral:#b84b35; --coral-soft:#ffe6df; --amber:#9a6500; --amber-soft:#fff1c2; --blue:#316b8a; --shadow:0 18px 50px rgba(11,32,48,.10); }}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{ margin:0; color:var(--ink); background:var(--paper); font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; line-height:1.55; }}
a {{ color:#075e72; }} a:focus-visible, summary:focus-visible {{ outline:3px solid #e69720; outline-offset:3px; }}
.comparison-region:focus-visible {{ outline:3px solid #e69720; outline-offset:3px; }}
.identity-card {{ border:1px solid #dcc88b; border-left:6px solid var(--amber); border-radius:1rem; padding:1.3rem; background:#fff9e8; }}
.identity-alternatives {{ display:flex; flex-wrap:wrap; gap:.75rem 2rem; padding-left:1.25rem; }}
.comparison-note {{ background:#eaf2f2; padding:1rem 1.3rem; border:1px solid #c5d9d8; border-radius:1rem; margin-bottom:1.25rem; }}
.comparison-note p {{ margin:.45rem 0; }} .number {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
.conditional-value {{ background:#f0f7f5; }} details {{ margin-top:1rem; }} summary {{ cursor:pointer; font-weight:750; padding:.7rem 0; }}
.source-paths code,.identity-card code,.comparison-provenance code {{ overflow-wrap:anywhere; }}
.skip {{ position:absolute; left:-9999px; top:1rem; background:white; padding:.75rem 1rem; z-index:10; }} .skip:focus {{ left:1rem; }}
.hero {{ color:white; background:radial-gradient(circle at 85% 15%,rgba(34,169,157,.35),transparent 30%),linear-gradient(135deg,#081923,#12364a 68%,#17536a); padding:4.5rem max(1.25rem,calc((100vw - 1160px)/2)) 3.5rem; }}
.hero-grid {{ display:grid; grid-template-columns:minmax(0,1.6fr) minmax(260px,.7fr); gap:3rem; align-items:end; }}
.kicker,.eyebrow {{ margin:0 0 .65rem; letter-spacing:.13em; text-transform:uppercase; font-weight:800; font-size:.76rem; }} .kicker {{ color:#78ddd0; }} .eyebrow {{ color:var(--teal); }}
h1 {{ font-family:Georgia,"Times New Roman",serif; font-weight:500; font-size:clamp(2.5rem,6vw,5.7rem); line-height:.98; letter-spacing:-.035em; margin:.2rem 0 1.25rem; max-width:900px; }}
.lede {{ max-width:790px; color:#d9e8ec; font-size:1.1rem; }}
.state-panel {{ border:1px solid rgba(255,255,255,.24); background:rgba(255,255,255,.08); padding:1.25rem; border-radius:1rem; backdrop-filter:blur(8px); }} .state-panel strong {{ display:block; font-size:1.5rem; margin-top:.35rem; }}
.download-row {{ display:flex; flex-wrap:wrap; gap:.65rem; margin-top:1.5rem; }} .button {{ display:inline-block; padding:.68rem .92rem; border-radius:999px; text-decoration:none; font-weight:750; background:#e8fffb; color:#0b4f4b; }} .button.secondary {{ background:transparent; color:white; border:1px solid rgba(255,255,255,.42); }}
main {{ max-width:1160px; margin:auto; padding:2.5rem 1.25rem 5rem; }}
.principle {{ display:grid; grid-template-columns:3px 1fr; gap:1.25rem; margin:-4.2rem 0 2.5rem; position:relative; background:var(--card); border:1px solid var(--line); border-radius:1rem; padding:1.5rem 1.6rem; box-shadow:var(--shadow); }} .principle:before {{ content:""; background:linear-gradient(var(--teal),#77c8ba); border-radius:3px; }} .principle p {{ margin:.2rem 0; font-size:1.2rem; font-family:Georgia,serif; }}
.metrics {{ display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; margin:2rem 0 4rem; }} .metric {{ background:var(--card); border:1px solid var(--line); border-radius:.9rem; padding:1rem 1.1rem; }} .metric b {{ display:block; font-size:2rem; line-height:1.1; }} .metric span {{ color:var(--muted); font-size:.9rem; }}
section {{ margin:4.2rem 0; }} h2 {{ font-family:Georgia,serif; font-size:clamp(1.9rem,4vw,3rem); font-weight:500; letter-spacing:-.02em; margin:0 0 .5rem; }} .section-intro {{ color:var(--muted); max-width:760px; margin:0 0 1.5rem; }}
.findings {{ display:grid; gap:1rem; }} .finding {{ background:var(--card); border:1px solid var(--line); border-left:6px solid var(--blue); border-radius:.85rem; padding:1.2rem 1.35rem; }} .finding.supported {{ border-left-color:var(--teal); }} .finding.refuted {{ border-left-color:var(--coral); }} .finding.blocked {{ border-left-color:var(--amber); }} .finding-top {{ display:flex; gap:.6rem; align-items:center; flex-wrap:wrap; }} .finding h3 {{ font-size:1.2rem; margin:.8rem 0; }}
.status {{ display:inline-block; border-radius:999px; padding:.28rem .58rem; font-size:.72rem; font-weight:850; letter-spacing:.035em; }} .status.supported {{ color:#174f3e; background:var(--teal-soft); }} .status.refuted {{ color:#772a1c; background:var(--coral-soft); }} .status.blocked {{ color:#6c4a00; background:var(--amber-soft); }} .rule {{ color:var(--muted); font-size:.82rem; }}
dl {{ display:grid; grid-template-columns:minmax(180px,.45fr) minmax(0,1fr); gap:.35rem 1rem; margin:1rem 0; }} dt {{ color:var(--muted); }} dd {{ margin:0; overflow-wrap:anywhere; }} .ceiling {{ background:#eef2f2; border-radius:.55rem; padding:.75rem .85rem; margin-bottom:0; }}
.timeline {{ background:var(--card); border:1px solid var(--line); border-radius:1rem; padding:1.2rem; overflow:hidden; }} .timeline-row {{ display:grid; grid-template-columns:minmax(150px,230px) 1fr; gap:1rem; align-items:center; margin:.8rem 0; }} .timeline-label {{ font-weight:700; font-size:.9rem; }} .timeline-track {{ height:20px; position:relative; border-radius:999px; background:repeating-linear-gradient(90deg,#edf0ec 0,#edf0ec 1px,transparent 1px,transparent 10%); border:1px solid #d8ddd8; }} .window-bar {{ position:absolute; top:3px; bottom:3px; min-width:5px; border-radius:999px; background:linear-gradient(90deg,var(--blue),var(--teal)); }} .event-dot {{ position:absolute; width:14px; height:14px; margin-left:-7px; top:2px; border-radius:50%; background:var(--coral); border:3px solid white; box-shadow:0 0 0 2px var(--coral); }} .timeline-axis {{ display:flex; justify-content:space-between; color:var(--muted); font-size:.8rem; padding-left:calc(230px + 1rem); }}
.windows {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:1rem; margin-top:1rem; }} .window-card {{ background:var(--card); border:1px solid var(--line); border-radius:.85rem; padding:1rem; }} .window-card h3 {{ margin:.2rem 0; }} .capabilities {{ list-style:none; padding:0; margin:1rem 0 0; }} .capabilities li {{ margin:.4rem 0; }} .cap-state {{ display:inline-block; min-width:122px; font-size:.72rem; font-weight:800; text-transform:uppercase; }} .cap-state.demonstrated {{ color:#15513d; }} .cap-state.not_demonstrated {{ color:#7a4c00; }}
.table-wrap {{ overflow-x:auto; background:var(--card); border:1px solid var(--line); border-radius:1rem; }} table {{ width:100%; border-collapse:collapse; min-width:680px; }} caption {{ text-align:left; padding:1rem; color:var(--muted); }} th,td {{ text-align:left; padding:.75rem .9rem; border-top:1px solid var(--line); vertical-align:top; }} thead th {{ background:#ecf1ef; border-top:0; }} .mark {{ font-size:.82rem; }} .mark.none {{ color:var(--muted); }}
.integrity td.mono {{ max-width:520px; word-break:break-all; }} .mono {{ font-family:"SFMono-Regular",Consolas,monospace; font-size:.82rem; }}
.ceiling-panel {{ background:var(--navy); color:#eaf2f3; padding:1.5rem; border-radius:1rem; }} .ceiling-panel h2 {{ color:white; }} .next {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(240px,.45fr); gap:2rem; }} .next ol {{ padding-left:1.25rem; }} .next li {{ margin:.65rem 0; }} .note {{ background:#fff9e8; border:1px solid #e7d59a; padding:1rem; border-radius:.8rem; align-self:start; }}
footer {{ max-width:1160px; margin:auto; padding:0 1.25rem 3rem; color:var(--muted); font-size:.88rem; }} .sr-only {{ position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0; }}
@media (max-width:760px) {{ .hero-grid,.next {{ grid-template-columns:1fr; }} .metrics {{ grid-template-columns:repeat(2,1fr); }} .timeline-row {{ grid-template-columns:1fr; gap:.25rem; }} .timeline-axis {{ padding-left:0; }} dl {{ grid-template-columns:1fr; }} dt {{ margin-top:.5rem; }} }}
@media (prefers-reduced-motion:reduce) {{ html {{ scroll-behavior:auto; }} }}
@media print {{ .hero {{ background:white;color:var(--ink);padding:1rem 0; }} .hero .lede,.kicker {{ color:var(--ink); }} .download-row {{ display:none; }} .principle {{ margin:1rem 0;box-shadow:none; }} main,footer {{ max-width:none; }} .finding,.window-card,.timeline,.table-wrap,.metric {{ break-inside:avoid; }} }}
</style>
<style>{interactive_style}</style></head>
<body>
<a class="skip" href="#main">Skip to findings</a>
<header class="hero">
  <div class="hero-grid">
    <div>
      <p class="kicker">Observation Receipt / case {esc(receipt['receipt_version'])}</p>
      <h1>{esc(display_title)}</h1>
      <p class="lede">{esc(subtitle)}</p>
      <nav class="download-row" aria-label="Receipt downloads">
        <a class="button" href="{receipt_json_href}" download="receipt.json">Machine-readable receipt</a>
        <a class="button secondary" href="{receipt_markdown_href}" download="receipt.md">Markdown docket</a>
        {witness_download}{extra_download}
      </nav>
    </div>
    <aside class="state-panel" aria-label="Receipt state">
      <span class="status {state_class}">{esc(receipt['state'])}</span>
      <strong>{summary['supported']} supported, {summary['refuted']} refuted, {summary['blocked']} blocked</strong>
      <span>{verified} of {total_artifacts} local artifact identities verified</span>
      <p>{references} reference-only URLs, not byte verified.</p>
      <p>Replay integrity, not scientific acceptance.</p>
    </aside>
  </div>
</header>
<main id="main">
  <aside class="principle"><p>{esc(distinction)}</p></aside>
  <section class="metrics" aria-label="Receipt summary">
    <div class="metric"><b>{summary['supported']}</b><span>{supported_label}</span></div>
    <div class="metric"><b>{summary['refuted']}</b><span>Refuted claims</span></div>
    <div class="metric"><b>{summary['blocked']}</b><span>Blocked inferences</span></div>
    <div class="metric"><b>{verified}/{total_artifacts}</b><span>Artifacts verified</span></div>
  </section>
  {steward_links.render(receipt)}{comparison_exports.render(receipt)}
  <section id="findings"><p class="eyebrow">Decision layer</p><h2>What the evidence permits</h2><p class="section-intro">A blocked result identifies the missing condition that prevents a stronger claim. Open a proof only when you need its detail.</p><div id="claim-tools" class="claim-tools" hidden><div class="claim-toolbar"><label>Find a claim or evidence condition<input id="claim-search" type="search" placeholder="Try coverage, calibration or identity"></label><label>Finding state<select id="claim-filter"><option value="all">All saved findings</option><option value="supported">Supported</option><option value="blocked">Blocked</option><option value="refuted">Refuted</option></select></label><button id="claim-reset">Clear filters</button></div><p id="claim-count" class="claim-count" role="status"></p></div><div id="claim-empty" class="claim-empty" hidden><p>No saved finding matches these filters. Nothing has been removed from the receipt.</p><button id="claim-empty-reset">Show all findings</button></div><noscript><p>All saved findings and native proof disclosures remain available without JavaScript. Search and focus links require JavaScript; the complete receipt downloads remain the fallback.</p></noscript><div class="findings">{''.join(findings)}</div></section>
  {temporal_sections}
  <section id="integrity"><p class="eyebrow">Custody layer</p><h2>Artifact integrity</h2><p class="section-intro">Local evidence must match its recorded byte length and SHA-256 identity before the case passes.</p><div class="table-wrap integrity"><table><caption>Artifact verification results.</caption><thead><tr><th scope="col">Artifact</th><th scope="col">State</th><th scope="col">Observed identity or URL</th></tr></thead><tbody>{artifact_rows}</tbody></table></div></section>
  <section class="ceiling-panel"><p class="eyebrow">Interpretation boundary</p><h2>Claim ceiling</h2><p>{esc(receipt['claim_ceiling'])}</p></section>
  <section class="next"><div><p class="eyebrow">Recovery path</p><h2>What would change this receipt</h2><ol>{next_steps}</ol></div><aside class="note"><strong>Read-only by design</strong><p>This viewer does not modify source evidence or accept scientific, legal, operational, or institutional claims on anyone else's behalf.</p></aside></section>
</main>
<footer>Generated locally by Observation Receipt. No account, cloud service, external script, or language model is required.</footer>
<script>{interactive_script}</script></body>
</html>
'''


def _csv_text(fieldnames: list[str], rows: list[dict[str, Any]]) -> str:
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    safe_rows = [{name: "'" + value if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')) else value
                  for name, value in row.items()} for row in rows]
    writer.writerows(safe_rows)
    return stream.getvalue()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_bundle(case: dict[str, Any], receipt: dict[str, Any], output: Path) -> dict[str, Path]:
    """Write a deterministic, offline-readable receipt bundle."""

    output.mkdir(parents=True, exist_ok=True)
    candidates = [
        {
            "candidate_id": item["id"],
            "label": item["label"],
            "disposition": item["disposition"],
            "mapping_state": item.get("mapping_state", ""),
            "witness_marks": len(item["witness_marks"]),
        }
        for item in case["candidates"]
    ]
    marks = [
        {
            "candidate_id": candidate["id"],
            "mark_id": mark["id"],
            "observer": mark["observer"],
            "time_state": mark["time_state"],
            "marked_at_utc": mark.get("marked_at_utc") or "",
            "elicitation_state": mark["elicitation_state"],
            "independence_state": mark["independence_state"],
            "dependency_group": mark.get("dependency_group") or "",
            "source_artifact_id": mark["source_artifact_id"],
            "source_locator": mark.get("source_locator", ""),
        }
        for candidate in case["candidates"]
        for mark in candidate["witness_marks"]
    ]
    windows = [
        {
            "window_id": item["id"],
            "label": item["label"],
            "start_utc": item["start_utc"],
            "stop_utc": item["stop_utc"],
            "clock_domain": item.get("clock_domain", ""),
            "target": item["target"],
        }
        for item in case["observation_windows"]
    ]
    findings = [
        {
            "claim_id": item["claim_id"],
            "status": item["status"],
            "proposition": item["proposition"],
            "claim_ceiling": item["claim_ceiling"],
        }
        for item in receipt["findings"]
    ]
    content = {
        "receipt.json": json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
        "receipt.md": render_markdown(case, receipt),
        "candidates.csv": _csv_text(["candidate_id", "label", "disposition", "mapping_state", "witness_marks"], candidates),
        "witness-marks.csv": _csv_text(
            [
                "candidate_id",
                "mark_id",
                "observer",
                "time_state",
                "marked_at_utc",
                "elicitation_state",
                "independence_state",
                "dependency_group",
                "source_artifact_id",
                "source_locator",
            ],
            marks,
        ),
        "observation-windows.csv": _csv_text(["window_id", "label", "start_utc", "stop_utc", "clock_domain", "target"], windows),
        "findings.csv": _csv_text(["claim_id", "status", "proposition", "claim_ceiling"], findings),
    }
    if receipt.get("conditional_comparisons"):
        content["comparison.csv"] = _csv_text(["comparison_id","metric_id","label","unit","original","conditional","delta","delta_unit","source_artifact_id","original_pointer","conditional_pointer","scale","replaces_original"], comparison_exports.csv_rows(receipt))
    if receipt.get("identity_groups"):
        identity_rows = [{"group_id":g["id"],"status":g["status"],"alternative":alternative,"source_artifact_id":g["source_artifact_id"],"source_pointer":g["alternatives_pointer"],"representative_selected":False} for g in receipt["identity_groups"] for alternative in g["alternatives"]]
        content["identity-groups.csv"] = _csv_text(["group_id","status","alternative","source_artifact_id","source_pointer","representative_selected"],identity_rows)
    content["index.html"] = render_html(case, receipt, content)
    paths: dict[str, Path] = {}
    for name, text in content.items():
        path = output / name
        path.write_text(text, encoding="utf-8", newline="\n")
        paths[name] = path.resolve()
    manifest = {
        "bundle_version": receipt["receipt_version"],
        "case_id": receipt["case_id"],
        "files": [
            {"path": name, "bytes": paths[name].stat().st_size, "sha256": _sha256(paths[name])}
            for name in sorted(paths)
        ],
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    paths["manifest.json"] = manifest_path.resolve()
    return paths
