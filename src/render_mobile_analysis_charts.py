"""Source-bound phone figures. No resampling of the desktop raster or science inputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import ImageDraw

from render_public_analysis_charts import (
    ROOT, AMBER, BLUE, CORAL, GRID, MUTED, PANEL_DEEP, TEAL, TEXT,
    TEXT_SOFT, TRACK, VIOLET, font, gradient_background, load_json, wrap_text,
)

WIDTH = 720
MARGIN = 44
BODY_SIZE = 32
SOURCE_FILES = ["stage11e-result.json", "stage11g-result.json", "stage11l-result.json",
                "stage10x-result.json", "stage11s-result.json", "stage11t-result.json",
                "stage11u-selection-weighting-cascade.json"]


def row(label, value=None, unit="", color=TEAL, maximum=None, detail=""):
    return dict(label=label, value=value, unit=unit, color=color, maximum=maximum, detail=detail)


def figure(filename, number, title, note, rows, kind="rows", scale=""):
    return dict(filename=filename, number=number, title=title, note=note,
                rows=rows, kind=kind, scale=scale)


def specifications():
    e, g, l, readiness, s, t, u = [load_json(n) for n in SOURCE_FILES]
    if not all(x.get("pass") for x in (e, g, l, readiness, s, t, u)):
        raise ValueError("Refusing a failed source receipt")
    c, m, rank = e["context"], e["measures"], g["product_reversal_examples"][0]
    selection, weight = u["metrics"]["selection_panel"], u["metrics"]["strict_tagged_weighting_panel"]
    figures = [figure("Artemis-II-Chart-1-One-Sunset.png", 1, "One Sunset. Four counts.",
        "Original frozen reconstruction, not certified physical counts or independent samples.", [
            row("Scheduled connected context", 1, "context", AMBER),
            row("Camera actions", c["actions"], "actions", TEAL, detail="Five exposure keys per action"),
            row("Capture keys", c["exposures"], "keys", BLUE, detail="Three archive products per key"),
            row("Archive products", c["products"], "products", CORAL),
        ], "flow"),
        figure("Artemis-II-Chart-9-Selection-Weighting-Cascade.png", 2, "Same tag. Different share.",
            "Frozen metadata accounting. Not physical prevalence, model bias or observed pipeline behavior. Layer and action-carried sensitivities remain in the article.", [
            row("All source-exposure fields", selection["sunset_tag_occupancy_all_source_exposures"]*100, "%", BLUE, 100,
                f"{selection['sunset_tagged_source_exposures']:,} / {u['metrics']['all_cohort']['source_exposures']:,}"),
            row("Keep nonblank target fields", selection["sunset_share_of_tagged_source_exposures"]*100, "%", TEAL, 100,
                f"{selection['sunset_tagged_source_exposures']:,} / {selection['tagged_source_exposures']:,}"),
            row("Selected actions", weight["sunset_share_of_selected_actions"]*100, "%", TEAL, 100),
            row("Tagged exposures", weight["sunset_share_of_tagged_exposures"]*100, "%", BLUE, 100),
            row("Derived products", weight["sunset_share_of_tagged_products"]*100, "%", VIOLET, 100),
            row("Attached bytes", weight["sunset_share_of_tagged_bytes"]*100, "%", AMBER, 100),
        ], scale="All tracks 0–100%; marker 50%. Filter: target_id IS NOT NULL AND target_id <> ''."),
        figure("Artemis-II-Chart-2-Hidden-Weight.png", 3, "The context stays fixed.",
            "Action-count reference, not an independence baseline. Descriptive shares, not a sampler or model effect.", [
            row("Camera actions", m["action_share"]*100, "%", BLUE, 25, "Action-count reference"),
            row("Archive products", m["product_share"]*100, "%", AMBER, 25, f"{m['product_weight_vs_action_weight']:.3f}× action share"),
            row("Archive bytes", m["total_byte_share"]*100, "%", TEAL, 25, f"{m['byte_weight_vs_action_weight']:.3f}× action share"),
        ], scale="Every track 0–25%; values are shares of the whole cohort."),
        figure("Artemis-II-Chart-3-Rank-Reversal.png", 4, "Change the unit. Change the winner.",
            "Archive prominence, not scientific importance. The windows are the same; the units are not.", [
            row("ACTIONS: Guided Discussion", rank["more_actions_actions"], "actions", AMBER, 80),
            row("ACTIONS: Earthset", rank["more_products_actions"], "actions", TEAL, 80),
            row("PRODUCTS: Guided Discussion", rank["more_actions_products"], "products", AMBER, 1000),
            row("PRODUCTS: Earthset", rank["more_products_products"], "products", TEAL, 1000),
        ], scale="Action tracks 0–80. Product tracks 0–1,000. Compare within each unit."),
    ]
    rows = []
    for label, key in [("Raw memberships", "raw_concentration_equivalent_windows"),
                       ("Fractional overlaps", "fractional_concentration_equivalent_windows"),
                       ("Collapsed same-name overlaps", "collapsed_fractional_concentration_equivalent_windows")]:
        for unit, field, color in [("actions", "actions", TEAL), ("products", "products", AMBER), ("bytes", "archive_size_bytes", CORAL)]:
            rows.append(row(label + ": " + unit, t["metrics"][key][field], "units", color, 20))
    figures.append(figure("Artemis-II-Chart-7-Opportunity-Concentration.png", 5,
        "Thirty-six windows. Unequal weight.",
        "Nconcentration = 1 / sum(pᵢ²). Not effective sample size, independent events or a flight recommendation.",
        rows, scale="All index tracks 0–20 concentration-equivalent window units. Equal original memberships would give 36."))
    rows = []
    for label, key, color in [("Product-ID split", "product_key", CORAL), ("Action-ID split", "action_key", AMBER),
                               ("Five-second-group split", "temporal_5s_key", TEAL)]:
        policy = l["policies"][key]
        rows.append(row(label, detail=f"Action groups crossing: {policy['crossing_action_groups']:,} / 2,166.\nFive-second groups crossing: {policy['crossing_temporal_5s_groups']:,} / 816.", color=color))
    figures.append(figure("Artemis-II-Chart-4-Split-Hazard.png", 6, "A clean split can split an observation.",
        "Deterministic metadata canary, not an observed NASA sampler. Five seconds is a conditional relation, not a scene boundary. Zero crossings is only a declared-layer pass.", rows))
    ordered = [("first_pre_explicit_search_report", "First report"), ("explicit_search_intent", "Search intent"),
               ("display_dimming", "Display dimmed"), ("dedicated_watch_start", "Dedicated watch"),
               ("shared_report", "Shared report"), ("timeline_return", "Timeline return"),
               ("ground_prompt_end", "Ground query ends"), ("prompt_proximate_candidate", "Prompt-proximate candidate"),
               ("last_clear_report", "Last clear report")]
    anchors = {r["id"]: r for r in s["timeline"]}
    figures.append(figure("Artemis-II-Chart-8-Attention-Conditioned-Detection.png", 7,
        "The observing process changed.",
        "Nonstationary opportunity. No prompt causation, one-to-one event mapping, detection probability or physical clustering is inferred.",
        [row(label, detail=anchors[key]["utc"][11:-1] + " UTC", color=AMBER if "report" in key else TEAL) for key, label in ordered],
        "timeline", "Ordered anchors on 7 April 2026. Vertical spacing shows order, not elapsed time."))
    figures.append(figure("Artemis-II-Chart-5-Archive-vs-Analysis.png", 8, "Keep identity. Add dependence.",
        "Illustrative pilot, not an accepted PDS or OGC carrier. Membership can be zero, one or many; unmatched is an alternative, not a simultaneous mapped state.", [
        row("PDS4 archive", detail="Stable product identifiers and source lineage", color=BLUE),
        row("OGC training-data concepts", detail="Task, sample, split role, provenance and quality", color=VIOLET),
        row("Task companion", detail="Product → capture → action; declare protected relationships", color=AMBER),
        row("Window memberships", detail="Preserve zero, one or many links. Do not force one owner.", color=TEAL),
    ], "flow"))
    labels = [("Retrieval audit", "Supported now", "Products, identities, bytes"),
              ("Representation study", "Supported with limit", "Keep sibling views together"),
              ("Within-event model", "Conditional", "Freeze a deployment-shaped protocol"),
              ("Target classifier", "Label audit needed", "44.872% tagged; camera associated with tags"),
              ("New-Sunset test", "Second event needed", "One scheduled event cannot test another"),
              ("Color / photometry", "Calibration needed", "Archived tiers alone are insufficient")]
    expected = ["SUPPORTED_NOW", "SUPPORTED_NOW_WITH_CLAIM_LIMIT", "CONDITIONALLY_SUPPORTABLE", "NOT_YET_SUPPORTABLE",
                "NOT_INTERNALLY_IDENTIFIABLE", "NOT_SUPPORTED_BY_ARCHIVED_TIERS_ALONE"]
    assert [r["status"] for r in readiness["task_matrix"]] == expected
    figures.append(figure("Artemis-II-Chart-6-Task-Readiness.png", 9, "Readiness belongs to a task.",
        "Six bounded task states. No global ready/unusable verdict or specialist approval.",
        [row(label, detail=status + ". " + detail, color=color) for (label, status, detail), color in zip(labels, [TEAL, TEAL, AMBER, CORAL, VIOLET, BLUE])]))
    return sorted(figures, key=lambda f:f["number"])


def wrapped(draw, text, size=BODY_SIZE, width=WIDTH-2*MARGIN, face="sans"):
    result = wrap_text(draw, text, font(size, face), width)
    if any(draw.textlength(line, font=font(size, face)) > width for line in result.splitlines()):
        raise ValueError("Unbreakable figure text exceeds its declared width")
    return result


def render(spec):
    # Layout by measured lines, not assumed label lengths. Never shrink data labels.
    scratch = ImageDraw.Draw(gradient_background(WIDTH, 1))
    title = wrapped(scratch, spec["title"], 46, face="serif-bold")
    y = 95 + len(title.splitlines())*56 + 24
    scale = wrapped(scratch, spec["scale"], 28) if spec["scale"] else ""
    if scale:
        y += len(scale.splitlines())*38 + 35
    layouts = []
    for r in spec["rows"]:
        label = wrapped(scratch, r["label"], 32, WIDTH-2*MARGIN-44, face="sans-semibold")
        detail = "\n".join(wrapped(scratch, line, 30, WIDTH-2*MARGIN-44) for line in r["detail"].splitlines())
        height = 50 + len(label.splitlines())*43 + (83 if r["value"] is not None else 0)
        height += 40 if r["maximum"] is not None else 0
        height += (len(detail.splitlines())*39+15) if detail else 0
        layouts.append((r, label, detail, y, height))
        y += height+28
    note = wrapped(scratch, spec["note"], 28)
    height = y + 38 + len(note.splitlines())*38 + 48
    image = gradient_background(WIDTH, height)
    draw = ImageDraw.Draw(image)
    draw.text((MARGIN, 30), f"FIGURE {spec['number']:02} / ARTEMIS II", font=font(27, "sans-bold"), fill=AMBER)
    draw.multiline_text((MARGIN, 84), title, font=font(46, "serif-bold"), fill=TEXT, spacing=10)
    if scale:
        draw.multiline_text((MARGIN, 95+len(title.splitlines())*56+24), scale, font=font(28), fill=TEXT_SOFT, spacing=8)
    for r, label, detail, top, h in layouts:
        draw.rounded_rectangle((MARGIN, top, WIDTH-MARGIN, top+h), radius=20, fill=PANEL_DEEP, outline=GRID, width=2)
        draw.line((MARGIN, top+22, MARGIN, top+h-22), fill=r["color"], width=6)
        draw.multiline_text((MARGIN+22, top+20), label, font=font(32, "sans-semibold"), fill=r["color"], spacing=9)
        cursor = top+25+len(label.splitlines())*43
        if r["value"] is not None:
            v = r["value"]
            value = f"{v:,}" if isinstance(v, int) else f"{v:.3f}"
            draw.text((MARGIN+22, cursor), value + ("%" if r["unit"]=="%" else " "+r["unit"]), font=font(47, "serif-bold"), fill=TEXT)
            cursor += 83
        if r["maximum"] is not None:
            left, right = MARGIN+22, WIDTH-MARGIN-22
            draw.rounded_rectangle((left, cursor, right, cursor+21), radius=10, fill=TRACK)
            end = left+(right-left)*r["value"]/r["maximum"]
            draw.rounded_rectangle((left, cursor, end, cursor+21), radius=10, fill=r["color"])
            if r["maximum"]==100:
                mid=(left+right)//2
                draw.line((mid,cursor-7,mid,cursor+28),fill=TEXT,width=2)
            cursor += 40
        if detail:
            draw.multiline_text((MARGIN+22,cursor),detail,font=font(30),fill=TEXT_SOFT,spacing=9)
        if spec["kind"] in ("flow", "timeline") and r is not layouts[-1][0]:
            draw.line((WIDTH//2,top+h+3,WIDTH//2,top+h+25),fill=MUTED,width=3)
    draw.line((MARGIN,y+8,WIDTH-MARGIN,y+8),fill=GRID,width=2)
    draw.multiline_text((MARGIN,y+29),note,font=font(28),fill=TEXT_SOFT,spacing=10)
    target = ROOT/"presentation"/"mobile"/spec["filename"]
    target.parent.mkdir(parents=True,exist_ok=True)
    image.save(target,format="PNG",optimize=True,dpi=(144,144))


def main():
    specs=specifications()
    for spec in specs:
        render(spec)
    sources=[dict(path="results/"+n,sha256=hashlib.sha256((ROOT/"results"/n).read_bytes()).hexdigest()) for n in SOURCE_FILES]
    payload=dict(schema_version=1,new_science=False,width=WIDTH,minimum_data_label_size=BODY_SIZE,
                 sources=sources,figures=specs)
    (ROOT/"presentation"/"figure-reading-values.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(dict(pass_=True,figures=len(specs),source_files=len(sources))))


if __name__ == "__main__":
    main()
