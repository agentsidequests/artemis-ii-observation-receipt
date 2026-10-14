from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
CHART_W = 1600
CHART_H = 1000
COVER_W = 1400
COVER_H = 1000

SPACE_TOP = (4, 13, 28)
SPACE_BOTTOM = (10, 32, 54)
PANEL = "#102A46"
PANEL_DEEP = "#0B2139"
PANEL_LIGHT = "#173856"
TEXT = "#F8F2E7"
TEXT_SOFT = "#B8C6D6"
MUTED = "#8296AB"
GRID = "#29445F"
TRACK = "#1A3A56"
AMBER = "#FFB84D"
AMBER_LIGHT = "#F8D79A"
TEAL = "#59D7CA"
CORAL = "#FF776D"
BLUE = "#7CA8FF"
VIOLET = "#BDA0FF"
GREEN = "#84D99B"
MOON = "#D6D8D5"
NAVY = "#07172E"

FONT_DIR = Path("C:/Windows/Fonts")


def font(size: int, face: str = "sans") -> ImageFont.FreeTypeFont:
    names = {
        "sans": "segoeui.ttf",
        "sans-semibold": "seguisb.ttf",
        "sans-bold": "segoeuib.ttf",
        "serif": "georgia.ttf",
        "serif-bold": "georgiab.ttf",
        "serif-italic": "georgiai.ttf",
        "mono": "consola.ttf",
    }
    return ImageFont.truetype(str(FONT_DIR / names[face]), size=size)


def fitted_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    start_size: int,
    face: str,
    minimum: int = 22,
) -> ImageFont.FreeTypeFont:
    size = start_size
    candidate = font(size, face)
    while draw.textbbox((0, 0), text, font=candidate)[2] > max_width and size > minimum:
        size -= 2
        candidate = font(size, face)
    return candidate


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    text_font: ImageFont.FreeTypeFont,
    max_width: int,
) -> str:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and draw.textlength(candidate, font=text_font) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines)


def load_json(name: str) -> dict[str, Any]:
    return json.loads((ROOT / "results" / name).read_text(encoding="utf-8"))


def gradient_background(width: int, height: int) -> Image.Image:
    image = Image.new("RGB", (width, height), SPACE_TOP)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / max(1, height - 1)
        color = tuple(
            round(SPACE_TOP[channel] * (1 - ratio) + SPACE_BOTTOM[channel] * ratio)
            for channel in range(3)
        )
        draw.line((0, y, width, y), fill=color)

    for index in range(72):
        x = (index * 239 + 71) % width
        y = (index * index * 19 + index * 41 + 53) % max(1, height - 80)
        radius = 1 if index % 5 else 2
        color = "#71869A" if index % 3 else "#A7B5C2"
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    return image


def chart_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = gradient_background(CHART_W, CHART_H)
    draw = ImageDraw.Draw(image)
    draw.arc((1260, -170, 1730, 300), 25, 220, fill="#274560", width=3)
    draw.arc((1300, -130, 1690, 260), 30, 210, fill="#5E512F", width=2)
    draw.ellipse((1490, 94, 1502, 106), fill=AMBER)
    return image, draw


def tracked_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    text_font: ImageFont.FreeTypeFont,
    fill: str,
    spacing: int = 4,
) -> None:
    x, y = xy
    for character in text:
        draw.text((x, y), character, font=text_font, fill=fill)
        x += int(draw.textlength(character, font=text_font)) + spacing


def chart_header(
    draw: ImageDraw.ImageDraw,
    figure_number: str,
    title: str,
    subtitle: str,
) -> None:
    tracked_text(
        draw,
        (84, 50),
        f"FIGURE {figure_number}  /  ARTEMIS II DATA NOTE",
        font(18, "sans-semibold"),
        AMBER,
        3,
    )
    title_font = fitted_font(draw, title, 1390, 57, "serif-bold", 40)
    draw.text((82, 92), title, fill=TEXT, font=title_font)
    draw.text((84, 169), subtitle, fill=TEXT_SOFT, font=font(24, "sans"))


def chart_footer(draw: ImageDraw.ImageDraw, note: str) -> None:
    draw.line((84, 910, 1516, 910), fill=GRID, width=2)
    draw.text((84, 930), note, fill=MUTED, font=font(19, "sans"))


def save_chart(image: Image.Image, filename: str) -> None:
    image.save(ROOT / filename, format="PNG", optimize=True, dpi=(144, 144))


def glass_panel(
    draw: ImageDraw.ImageDraw,
    bounds: tuple[int, int, int, int],
    accent: str | None = None,
    radius: int = 26,
    fill: str = PANEL,
) -> None:
    draw.rounded_rectangle(bounds, radius=radius, fill=fill, outline=GRID, width=2)
    if accent:
        left, top, right, _ = bounds
        draw.rounded_rectangle((left, top, right, top + 7), radius=radius, fill=accent)


def glow_disc(
    image: Image.Image,
    center: tuple[int, int],
    radius: int,
    color: tuple[int, int, int],
    alpha: int = 105,
) -> None:
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer)
    x, y = center
    layer_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(max(8, radius // 2)))
    composite = Image.alpha_composite(image.convert("RGBA"), layer).convert("RGB")
    image.paste(composite)


def draw_arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    color: str = GRID,
    width: int = 4,
) -> None:
    draw.line((*start, *end), fill=color, width=width)
    x, y = end
    if abs(end[0] - start[0]) >= abs(end[1] - start[1]):
        direction = 1 if end[0] >= start[0] else -1
        draw.polygon([(x, y), (x - 12 * direction, y - 7), (x - 12 * direction, y + 7)], fill=color)
    else:
        direction = 1 if end[1] >= start[1] else -1
        draw.polygon([(x, y), (x - 7, y - 12 * direction), (x + 7, y - 12 * direction)], fill=color)


def render_cover() -> None:
    image = gradient_background(COVER_W, COVER_H)
    glow_disc(image, (1120, 505), 250, (255, 184, 77), 95)
    draw = ImageDraw.Draw(image)

    draw.ellipse((895, 265, 1395, 765), fill=MOON)
    draw.ellipse((835, 220, 1348, 733), fill=NAVY)
    draw.arc((805, 175, 1425, 795), 18, 172, fill="#486685", width=3)
    draw.arc((845, 215, 1385, 755), 18, 172, fill="#294969", width=2)
    draw.ellipse((1327, 486, 1359, 518), fill=AMBER)
    draw.line((1359, 502, 1395, 502), fill=AMBER, width=3)

    tracked_text(draw, (72, 66), "ARTEMIS II  /  PUBLIC DATA NOTE", font(18, "sans-semibold"), AMBER_LIGHT, 4)
    draw.line((72, 107, 592, 107), fill="#395673", width=2)
    draw.text((70, 156), "4,290", fill=AMBER, font=font(168, "serif-bold"))
    tracked_text(draw, (82, 340), "DATA PRODUCTS", font(28, "sans-semibold"), TEXT, 5)
    draw.line((72, 414, 626, 414), fill="#395673", width=2)
    draw.ellipse((613, 402, 637, 426), fill=AMBER)
    draw.text((70, 443), "ONE", fill=TEXT, font=font(142, "serif-bold"))
    tracked_text(draw, (82, 610), "SCHEDULED SUNSET", font(28, "sans-semibold"), TEXT, 5)
    draw.text((74, 740), "Why a file count is not a sample size", fill=TEXT, font=font(38, "serif-italic"))
    draw.text((76, 811), "An observation graph hidden inside NASA’s lunar archive", fill=TEXT_SOFT, font=font(24, "sans"))
    draw.line((72, 900, 1328, 900), fill="#395673", width=2)
    draw.text((72, 921), "OCTOBER 2026", fill=TEXT_SOFT, font=font(19, "sans"))
    draw.text((1328, 921), "BOB", fill=TEXT_SOFT, font=font(19, "sans-semibold"), anchor="ra")

    image.save(ROOT / "Artemis-II-Cover-4290-One-Sunset.png", format="PNG", optimize=True, dpi=(144, 144))


def render_observation_collapse(context: dict[str, Any]) -> None:
    image, draw = chart_canvas()
    chart_header(draw, "01", "One Sunset, four correct counts", "The archive expands through four legitimate relationship layers.")

    nodes = [
        (f"{context['products']:,}", "ARCHIVE PRODUCTS", "three views per exposure", AMBER, (255, 184, 77)),
        (f"{context['exposures']:,}", "EXPOSURES", "five per camera action", TEAL, (89, 215, 202)),
        (f"{context['actions']:,}", "CAMERA ACTIONS", "connected context", CORAL, (255, 119, 109)),
        ("1", "SCHEDULED EVENT", "the Sunset plan", BLUE, (124, 168, 255)),
    ]
    xs = [215, 605, 995, 1385]
    center_y = 485
    draw.line((215, center_y, 1385, center_y), fill=GRID, width=5)

    for index, ((number, label, detail, color, rgb), x) in enumerate(zip(nodes, xs)):
        glow_disc(image, (x, center_y), 76, rgb, 75)
        draw = ImageDraw.Draw(image)
        draw.ellipse((x - 70, center_y - 70, x + 70, center_y + 70), fill=PANEL_DEEP, outline=color, width=5)
        draw.text((x, center_y - 14), number, fill=TEXT, font=font(49 if index < 3 else 61, "serif-bold"), anchor="mm")
        draw.text((x, center_y + 44), label, fill=color, font=font(17, "sans-bold"), anchor="mm")
        draw.text((x, 605), detail, fill=TEXT_SOFT, font=font(19, "sans"), anchor="mm")
        if index < 3:
            draw.text(((x + xs[index + 1]) // 2, center_y - 2), "›", fill=TEXT_SOFT, font=font(38, "sans"), anchor="mm")

    glass_panel(draw, (145, 700, 1455, 815), AMBER, fill=PANEL_DEEP)
    draw.text((800, 758), "1 × 286 × 5 × 3 = 4,290", fill=TEXT, font=font(44, "mono"), anchor="mm")
    draw.text((800, 794), "context     actions     exposures     products", fill=TEXT_SOFT, font=font(17, "sans"), anchor="mm")
    chart_footer(draw, "Scope: conservative connected Sunset context within the verified complete-action cohort.")
    save_chart(image, "Artemis-II-Chart-1-One-Sunset.png")


def render_weight_shift(measures: dict[str, Any]) -> None:
    image, draw = chart_canvas()
    chart_header(draw, "03", "The context stays fixed. Its weight does not.", "The same context occupies a different share under each denominator.")

    rows = [
        ("CAMERA ACTIONS", "action-count reference", measures["action_share"] * 100, 1.0, BLUE),
        ("ARCHIVE PRODUCTS", "protocol and representation weight", measures["product_share"] * 100, measures["product_weight_vs_action_weight"], AMBER),
        ("ARCHIVE BYTES", "retrieval and processing weight", measures["total_byte_share"] * 100, measures["byte_weight_vs_action_weight"], TEAL),
    ]
    ys = [285, 505, 725]
    x0, x1 = 530, 1435
    max_value = 25.0
    baseline_x = x0 + (x1 - x0) * rows[0][2] / max_value
    draw.line((baseline_x, 260, baseline_x, 860), fill="#66798D", width=2)
    draw.text((baseline_x, 245), "13.2% action reference; tracks 0–25%", fill=TEXT_SOFT, font=font(17, "sans-semibold"), anchor="ms")

    for (label, detail, value, multiplier, color), y in zip(rows, ys):
        glass_panel(draw, (84, y, 1516, y + 165), color, fill=PANEL_DEEP)
        draw.text((118, y + 49), label, fill=TEXT, font=font(22, "sans-bold"))
        draw.text((118, y + 88), detail, fill=TEXT_SOFT, font=font(18, "sans"))
        draw.rounded_rectangle((x0, y + 56, x1, y + 104), radius=24, fill=TRACK)
        end = x0 + (x1 - x0) * value / max_value
        draw.rounded_rectangle((x0, y + 56, end, y + 104), radius=24, fill=color)
        draw.text((x1, y + 38), f"{value:.1f}%", fill=TEXT, font=font(39, "serif-bold"), anchor="ra")
        label_text = "ACTION REFERENCE" if multiplier == 1.0 else f"{multiplier:.2f}× ACTION WEIGHT"
        draw.text((x1, y + 126), label_text, fill=color, font=font(18, "sans-bold"), anchor="ra")

    chart_footer(draw, "Descriptive shares only. They do not establish a sampler, model bias, or performance effect.")
    save_chart(image, "Artemis-II-Chart-2-Hidden-Weight.png")


def render_selection_weighting_cascade(stage11u: dict[str, Any]) -> None:
    image, draw = chart_canvas()
    chart_header(
        draw,
        "02",
        "A filter and a unit can compound",
        "The target stays Sunset. The selected population and influence rule change.",
    )

    metrics = stage11u["metrics"]
    selection = metrics["selection_panel"]
    weighting = metrics["strict_tagged_weighting_panel"]
    sensitivity = metrics["action_carried_sensitivity"]
    collection_sensitivity = metrics["collection_byte_sensitivity"]

    glass_panel(draw, (84, 245, 750, 810), TEAL, fill=PANEL_DEEP)
    draw.text((118, 285), "1  SELECTION", fill=TEAL, font=font(20, "sans-bold"))
    draw.text((118, 326), "Which target fields enter?", fill=TEXT, font=font(27, "serif-bold"))

    selection_rows = [
        (
            "ALL SOURCE-EXPOSURE FIELDS",
            selection["sunset_tag_occupancy_all_source_exposures"] * 100,
            f"{selection['sunset_tagged_source_exposures']:,} / {metrics['all_cohort']['source_exposures']:,}",
            BLUE,
        ),
        (
            "NONBLANK TARGET FIELDS",
            selection["sunset_share_of_tagged_source_exposures"] * 100,
            f"{selection['sunset_tagged_source_exposures']:,} / {selection['tagged_source_exposures']:,}",
            TEAL,
        ),
    ]
    for index, (label, value, fraction, color) in enumerate(selection_rows):
        top = 370 + index * 220
        draw.text((120, top), label, fill=TEXT_SOFT, font=font(17, "sans-bold"))
        draw.text((120, top + 48), f"{value:.1f}%", fill=color, font=font(62, "serif-bold"))
        draw.text((390, top + 70), fraction, fill=MUTED, font=font(18, "mono"))
        draw.rounded_rectangle((120, top + 112, 690, top + 138), radius=13, fill=TRACK)
        draw.rounded_rectangle((120, top + 112, 120 + int(570 * value / 100.0), top + 138), radius=13, fill=color)
        draw.line((405, top + 108, 405, top + 142), fill=TEXT_SOFT, width=2)
        draw.text((690, top + 150), "0–100% track; marker 50%", fill=MUTED, font=font(16, "sans"), anchor="ra")

    draw.rounded_rectangle((112, 550, 718, 582), radius=16, fill=PANEL_LIGHT, outline=AMBER, width=2)
    draw.text((415, 566), "target_id IS NOT NULL AND target_id <> ''", fill=AMBER_LIGHT, font=font(17, "mono"), anchor="mm")

    glass_panel(draw, (790, 245, 1516, 810), AMBER, fill=PANEL_DEEP)
    draw.text((824, 285), "2  WEIGHTING", fill=AMBER, font=font(20, "sans-bold"))
    draw.text((824, 326), "How much influence does Sunset get?", fill=TEXT, font=font(27, "serif-bold"))

    weighting_rows = [
        ("SELECTED ACTIONS", weighting["sunset_share_of_selected_actions"] * 100, TEAL),
        ("TAGGED EXPOSURES", weighting["sunset_share_of_tagged_exposures"] * 100, BLUE),
        ("DERIVED PRODUCTS", weighting["sunset_share_of_tagged_products"] * 100, VIOLET),
        ("ATTACHED BYTES", weighting["sunset_share_of_tagged_bytes"] * 100, AMBER),
    ]
    x0, x1 = 1028, 1360
    for index, (label, value, color) in enumerate(weighting_rows):
        y = 398 + index * 92
        draw.text((824, y), label, fill=TEXT_SOFT, font=font(16, "sans-bold"), anchor="lm")
        draw.rounded_rectangle((x0, y - 14, x1, y + 16), radius=15, fill=TRACK)
        bar_right = x0 + int((x1 - x0) * value / 100.0)
        draw.rounded_rectangle((x0, y - 14, bar_right, y + 16), radius=15, fill=color)
        draw.line(((x0+x1)//2, y-19, (x0+x1)//2, y+21), fill=TEXT_SOFT, width=2)
        draw.text((1480, y), f"{value:.1f}%", fill=color, font=font(28, "serif-bold"), anchor="rm")

    draw.text((1480, 690), "0–100% tracks; markers 50%", fill=MUTED, font=font(16, "sans"), anchor="ra")
    draw.rounded_rectangle((828, 710, 1478, 746), radius=18, fill=PANEL_LIGHT, outline=GRID, width=2)
    draw.text(
        (1153, 728),
        "BY LAYER  "
        f"SOURCE {collection_sensitivity['data_source']['sunset_share']:.1%}  /  "
        f"RAW {collection_sensitivity['data_raw']['sunset_share']:.1%}  /  "
        f"PROCESSED {collection_sensitivity['data_processed']['sunset_share']:.1%}",
        fill=TEXT_SOFT,
        font=font(14, "sans-bold"),
        anchor="mm",
    )
    draw.rounded_rectangle((828, 754, 1478, 790), radius=18, fill=PANEL_LIGHT, outline=GRID, width=2)
    draw.text(
        (1153, 772),
        f"ACTION-CARRIED BYTE SENSITIVITY  {sensitivity['sunset_share_of_selected_action_bytes']:.1%}",
        fill=TEXT,
        font=font(15, "sans-bold"),
        anchor="mm",
    )

    chart_footer(draw, "Frozen metadata accounting only. Not physical prevalence, actual pipeline behavior, or model bias.")
    save_chart(image, "Artemis-II-Chart-9-Selection-Weighting-Cascade.png")


def rank_marker(draw: ImageDraw.ImageDraw, x: int, y: int, color: str, shape: str) -> None:
    if shape == "circle":
        draw.ellipse((x - 17, y - 17, x + 17, y + 17), fill=PANEL_DEEP, outline=color, width=7)
    else:
        draw.rounded_rectangle((x - 16, y - 16, x + 16, y + 16), radius=5, fill=PANEL_DEEP, outline=color, width=7)


def render_rank_reversal(example: dict[str, Any], total_reversals: int, pairs: int) -> None:
    image, draw = chart_canvas()
    chart_header(draw, "04", "Change the unit, change the winner", "Two planned windows reverse rank when products replace camera actions.")

    glass_panel(draw, (120, 245, 1480, 805), BLUE, fill=PANEL_DEEP)
    left_x, right_x = 430, 1170
    top_y, bottom_y = 385, 685
    draw.text((left_x, 300), "CAMERA ACTIONS", fill=BLUE, font=font(20, "sans-bold"), anchor="mm")
    draw.text((right_x, 300), "ARCHIVE PRODUCTS", fill=AMBER, font=font(20, "sans-bold"), anchor="mm")
    draw.line((left_x, 335, left_x, 735), fill=GRID, width=3)
    draw.line((right_x, 335, right_x, 735), fill=GRID, width=3)

    lines = [
        (example["more_actions_name"], example["more_actions_actions"], example["more_actions_products"], top_y, bottom_y, AMBER, "circle"),
        (example["more_products_name"], example["more_products_actions"], example["more_products_products"], bottom_y, top_y, TEAL, "square"),
    ]
    for name, left_value, right_value, left_y, right_y, color, shape in lines:
        draw.line((left_x, left_y, right_x, right_y), fill=color, width=8)
        rank_marker(draw, left_x, left_y, color, shape)
        rank_marker(draw, right_x, right_y, color, shape)
        draw.text((left_x - 42, left_y - 18), name, fill=TEXT, font=font(23, "sans-semibold"), anchor="rs")
        draw.text((left_x - 42, left_y + 31), f"{left_value} actions", fill=color, font=font(29, "serif-bold"), anchor="ra")
        draw.text((right_x + 42, right_y - 18), name, fill=TEXT, font=font(23, "sans-semibold"), anchor="ls")
        draw.text((right_x + 42, right_y + 31), f"{right_value} products", fill=color, font=font(29, "serif-bold"), anchor="la")

    draw.ellipse((756, 478, 844, 566), fill=PANEL, outline=TEXT_SOFT, width=2)
    draw.text((800, 510), "UNIT", fill=TEXT, font=font(16, "sans-bold"), anchor="mm")
    draw.text((800, 536), "CHANGE", fill=TEXT, font=font(16, "sans-bold"), anchor="mm")
    draw.rounded_rectangle((550, 820, 1050, 878), radius=29, fill=PANEL_LIGHT, outline=GRID, width=2)
    draw.text((800, 849), f"{total_reversals} reversals  /  {pairs} comparable pairs", fill=TEXT, font=font(25, "serif-italic"), anchor="mm")
    chart_footer(draw, "A reversal describes archive prominence under different units, not scientific importance.")
    save_chart(image, "Artemis-II-Chart-3-Rank-Reversal.png")


def render_split_receipt(stage11l: dict[str, Any]) -> None:
    image, draw = chart_canvas()
    chart_header(
        draw,
        "06",
        "One seed. Three policies. Two protected relationships.",
        "A content-bound receipt distinguishes filename disjointness from declared group integrity.",
    )

    columns = [
        (84, 545, "PARTITION KEY"),
        (570, 1004, "ACTION GROUPS CROSSING"),
        (1029, 1516, "5-SECOND GROUPS CROSSING"),
    ]
    for left, right, label in columns:
        draw.text(((left + right) // 2, 247), label, fill=TEXT_SOFT, font=font(17, "sans-bold"), anchor="mm")

    policies = stage11l["policies"]
    rows = [
        ("PRODUCT ID", "row-level", "product_key", CORAL),
        ("ACTION ID", "measured minimum", "action_key", AMBER),
        ("5-SECOND GROUP ID", "conditional outer key", "temporal_5s_key", TEAL),
    ]
    y_values = [285, 485, 685]
    for (title, subtitle, policy_name, color), top in zip(rows, y_values):
        item = policies[policy_name]
        glass_panel(draw, (84, top, 1516, top + 165), color, fill=PANEL_DEEP)
        draw.text((116, top + 36), title, fill=color, font=font(22, "sans-bold"))
        draw.text((116, top + 74), subtitle, fill=TEXT_SOFT, font=font(18, "sans"))
        draw.text(
            (116, top + 120),
            f"{item['test_product_share']:.1%} of products in test",
            fill=TEXT,
            font=font(19, "serif-bold"),
        )

        action_count = item["crossing_action_groups"]
        temporal_count = item["crossing_temporal_5s_groups"]
        action_color = TEAL if action_count == 0 else CORAL
        temporal_color = TEAL if temporal_count == 0 else CORAL
        for center_x, count, denominator, status_color in (
            (787, action_count, 2166, action_color),
            (1272, temporal_count, 816, temporal_color),
        ):
            draw.rounded_rectangle(
                (center_x - 172, top + 42, center_x + 172, top + 123),
                radius=31,
                fill=PANEL_LIGHT,
                outline=status_color,
                width=3,
            )
            status = "PASS" if count == 0 else "FAIL"
            draw.text((center_x - 122, top + 82), status, fill=status_color, font=font(18, "sans-bold"), anchor="lm")
            draw.text(
                (center_x + 145, top + 82),
                f"{count:,} / {denominator:,}",
                fill=TEXT,
                font=font(28, "serif-bold"),
                anchor="rm",
            )

        if policy_name == "action_key":
            draw.text(
                (1272, top + 141),
                "1,216 actions sit inside crossed outer groups",
                fill=AMBER_LIGHT,
                font=font(16, "sans-semibold"),
                anchor="mm",
            )

    chart_footer(draw, "Deterministic metadata canary only. Five seconds is conditional, not a semantic scene rule or a leakage finding.")
    save_chart(image, "Artemis-II-Chart-4-Split-Hazard.png")


def small_node(
    draw: ImageDraw.ImageDraw,
    bounds: tuple[int, int, int, int],
    title: str,
    detail: str,
    color: str,
) -> None:
    left, top, right, bottom = bounds
    draw.rounded_rectangle(bounds, radius=18, fill=PANEL_DEEP, outline=color, width=3)
    draw.text(((left + right) // 2, top + 27), title, fill=TEXT, font=font(17, "sans-bold"), anchor="mm")
    draw.text(((left + right) // 2, bottom - 21), detail, fill=TEXT_SOFT, font=font(15, "sans"), anchor="mm")


def render_archive_analysis_layers() -> None:
    image, draw = chart_canvas()
    chart_header(draw, "08", "A practical bridge: membership plus dependence", "PDS4 and OGC already cover identity, samples, tasks, and provenance. Evaluation can add one declared relationship layer.")

    cards = [
        ((84, 245, 532, 430), "PDS4 ARCHIVE", "What is this product?", "stable IDs, source lineage, supplemental tables", BLUE),
        ((576, 245, 1024, 430), "OGC TRAINING DATA", "How is the sample used?", "task, split role, provenance, quality, changes", VIOLET),
        ((1068, 245, 1516, 430), "TASK COMPANION", "What must stay together?", "parent groups, protected keys, split receipt", AMBER),
    ]
    for bounds, kicker, question, detail, color in cards:
        glass_panel(draw, bounds, color, fill=PANEL_DEEP)
        left, top, right, _ = bounds
        draw.text((left + 28, top + 35), kicker, fill=color, font=font(17, "sans-bold"))
        draw.text((left + 28, top + 77), question, fill=TEXT, font=font(27, "serif-bold"))
        wrapped = wrap_text(draw, detail, font(18, "sans"), right - left - 56)
        draw.multiline_text((left + 28, top + 124), wrapped, fill=TEXT_SOFT, font=font(18, "sans"), spacing=4)

    draw_arrow(draw, (532, 338), (570, 338), VIOLET, 4)
    draw_arrow(draw, (1024, 338), (1062, 338), AMBER, 4)
    draw.text((84, 475), "THE COMPANION PRESERVES A GRAPH, NOT A SINGLE OWNER", fill=TEAL, font=font(18, "sans-bold"))
    small_node(draw, (92, 535, 280, 635), "PDS PRODUCTS", "stable LIDVIDs", BLUE)
    small_node(draw, (360, 535, 548, 635), "EXPOSURE", "one capture", TEAL)
    small_node(draw, (628, 535, 816, 635), "ACTION GROUP", "derived or official key", CORAL)
    draw_arrow(draw, (280, 585), (354, 585), BLUE, 4)
    draw_arrow(draw, (548, 585), (622, 585), TEAL, 4)

    episode_nodes = [
        ((1045, 485, 1260, 565), "WINDOW A", "planned membership", AMBER),
        ((1045, 590, 1260, 670), "WINDOW B", "overlapping membership", VIOLET),
        ((1045, 695, 1260, 775), "UNMATCHED", "preserved explicitly", MUTED),
    ]
    for bounds, title, detail, color in episode_nodes:
        small_node(draw, bounds, title, detail, color)

    branch_x = 930
    draw.line((816, 585, branch_x, 585), fill=CORAL, width=4)
    draw.line((branch_x, 525, branch_x, 735), fill=CORAL, width=4)
    for y in (525, 630, 735):
        draw_arrow(draw, (branch_x, y), (1039, y), CORAL, 4)
    draw.ellipse((920, 575, 940, 595), fill=CORAL)

    glass_panel(draw, (1325, 485, 1516, 775), TEAL, fill=PANEL_DEEP)
    draw.text((1420, 530), "REAL LEDGER", fill=TEAL, font=font(17, "sans-bold"), anchor="mm")
    draw.text((1420, 586), "626", fill=TEXT, font=font(38, "serif-bold"), anchor="mm")
    draw.text((1420, 620), "unmatched", fill=TEXT_SOFT, font=font(16, "sans"), anchor="mm")
    draw.text((1420, 681), "58", fill=TEXT, font=font(38, "serif-bold"), anchor="mm")
    draw.text((1420, 715), "multi-member", fill=TEXT_SOFT, font=font(16, "sans"), anchor="mm")
    draw.text((1420, 751), "of 2,166 actions", fill=MUTED, font=font(15, "sans"), anchor="mm")
    draw.rounded_rectangle((250, 820, 1350, 875), radius=27, fill=PANEL_LIGHT, outline=GRID, width=2)
    draw.text((800, 847), "SAME IDENTIFIERS  •  EXPLICIT MEMBERS  •  DECLARED GROUPS KEPT INTACT", fill=TEXT, font=font(22, "sans-bold"), anchor="mm")
    chart_footer(draw, "Illustrative pilot design. PDS and OGC reviewers would choose its formal home and conformance target.")
    save_chart(image, "Artemis-II-Chart-5-Archive-vs-Analysis.png")


def render_task_readiness(readiness: dict[str, Any]) -> None:
    image, draw = chart_canvas()
    chart_header(draw, "09", "One archive, six different readiness answers", "Keeping declared groups intact fixes measured crossings. It cannot create labels, another event, or calibration.")

    cards = [
        ("RETRIEVAL AUDIT", "SUPPORTED NOW", "Products, identities, bytes", GREEN),
        ("REPRESENTATION STUDY", "SUPPORTED WITH LIMIT", "Keep sibling views together", TEAL),
        ("WITHIN-EVENT MODEL", "CONDITIONAL", "Freeze a deployment-shaped protocol", AMBER),
        ("TARGET CLASSIFIER", "LABEL AUDIT NEEDED", "44.872% tagged, camera predictive", CORAL),
        ("NEW-SUNSET TEST", "SECOND EVENT NEEDED", "One scheduled event cannot test another", VIOLET),
        ("COLOR / PHOTOMETRY", "CALIBRATION NEEDED", "Archived tiers are not physical truth", BLUE),
    ]
    actual_statuses = [row["status"] for row in readiness["task_matrix"]]
    expected_statuses = [
        "SUPPORTED_NOW",
        "SUPPORTED_NOW_WITH_CLAIM_LIMIT",
        "CONDITIONALLY_SUPPORTABLE",
        "NOT_YET_SUPPORTABLE",
        "NOT_INTERNALLY_IDENTIFIABLE",
        "NOT_SUPPORTED_BY_ARCHIVED_TIERS_ALONE",
    ]
    if actual_statuses != expected_statuses:
        raise RuntimeError("Readiness ordering changed; revise Figure 6 before rendering.")

    positions = [
        (84, 265, 548, 500),
        (568, 265, 1032, 500),
        (1052, 265, 1516, 500),
        (84, 540, 548, 775),
        (568, 540, 1032, 775),
        (1052, 540, 1516, 775),
    ]
    for index, ((title, status, detail, color), bounds) in enumerate(zip(cards, positions), start=1):
        glass_panel(draw, bounds, color, fill=PANEL_DEEP)
        left, top, right, bottom = bounds
        draw.ellipse((left + 28, top + 31, left + 62, top + 65), fill=color)
        draw.text((left + 45, top + 48), str(index), fill=NAVY, font=font(16, "sans-bold"), anchor="mm")
        draw.text((left + 82, top + 37), title, fill=TEXT, font=font(21, "sans-bold"))
        draw.rounded_rectangle((left + 28, top + 91, right - 28, top + 139), radius=24, fill=PANEL_LIGHT, outline=color, width=2)
        status_font = fitted_font(draw, status, right - left - 86, 18, "sans-bold", 14)
        draw.text(((left + right) // 2, top + 115), status, fill=color, font=status_font, anchor="mm")
        wrapped = wrap_text(draw, detail, font(18, "sans"), right - left - 60)
        draw.multiline_text(((left + right) // 2, bottom - 56), wrapped, fill=TEXT_SOFT, font=font(18, "sans"), anchor="mm", align="center", spacing=4)

    glass_panel(draw, (245, 815, 1355, 875), AMBER, fill=PANEL_LIGHT)
    draw.text((800, 845), "READINESS IS A PROPERTY OF A TASK, NOT A TERABYTE COUNT", fill=TEXT, font=font(24, "serif-bold"), anchor="mm")
    chart_footer(draw, "Six verified task states across four independent blocker families. No global ready or unusable verdict.")
    save_chart(image, "Artemis-II-Chart-6-Task-Readiness.png")


def render_opportunity_concentration(stage11t: dict[str, Any]) -> None:
    image, draw = chart_canvas()
    chart_header(
        draw,
        "05",
        "Thirty-six windows do not carry thirty-six equal votes",
        "The apparent number of opportunities contracts as actions become products, then bytes.",
    )

    metrics = stage11t["metrics"]
    rows = [
        ("RAW WINDOW MEMBERSHIPS", metrics["raw_concentration_equivalent_windows"]),
        ("FRACTIONAL OVERLAPS", metrics["fractional_concentration_equivalent_windows"]),
        ("COLLAPSED SAME-NAME OVERLAPS", metrics["collapsed_fractional_concentration_equivalent_windows"]),
    ]
    measures = [
        ("ACTIONS", "actions", TEAL),
        ("PRODUCTS", "products", AMBER),
        ("BYTES", "archive_size_bytes", CORAL),
    ]
    left = 405
    right = 1460
    scale = (right - left) / 20.0
    y0 = 300
    for row_index, (row_label, values) in enumerate(rows):
        panel_top = y0 + row_index * 175
        glass_panel(draw, (84, panel_top - 38, 1516, panel_top + 116), fill=PANEL_DEEP)
        draw.text((112, panel_top - 13), row_label, fill=TEXT_SOFT, font=font(18, "sans-semibold"))
        for measure_index, (label, key, color) in enumerate(measures):
            y = panel_top + 32 + measure_index * 28
            value = float(values[key])
            draw.text((360, y), label, fill=MUTED, font=font(16, "sans-bold"), anchor="rm")
            draw.rounded_rectangle((left, y - 8, right, y + 10), radius=9, fill=TRACK)
            bar_right = left + value * scale
            draw.rounded_rectangle((left, y - 8, bar_right, y + 10), radius=9, fill=color)
            draw.text((bar_right - 12, y + 1), f"{value:.3f}", fill=NAVY, font=font(15, "sans-bold"), anchor="rm")

    glass_panel(draw, (84, 820, 1516, 882), AMBER, fill=PANEL_LIGHT)
    draw.text((116, 850), "Nconcentration = 1 / sum(pᵢ²)", fill=TEXT, font=font(23, "mono"), anchor="lm")
    debt = metrics["replication_debt"]
    draw.text(
        (1480, 850),
        f"DESCRIPTIVE DEBT  +{debt['exact_windows_k2']} TO REACH 2 PER EXACT NAME  /  +{debt['exact_windows_k3']} TO REACH 3",
        fill=AMBER_LIGHT,
        font=font(18, "sans-bold"),
        anchor="rm",
    )
    chart_footer(draw, "Concentration-equivalent window units, not effective sample size or independent scientific events.")
    save_chart(image, "Artemis-II-Chart-7-Opportunity-Concentration.png")


def render_attention_conditioned_detection(stage11s: dict[str, Any]) -> None:
    image, draw = chart_canvas()
    chart_header(
        draw,
        "07",
        "The human detector changed after the first flash",
        "Attention, glare control, display brightness, adaptation, workflow, and prompting changed in sequence.",
    )

    timeline = {row["id"]: row for row in stage11s["timeline"]}
    ordered_ids = [
        "first_pre_explicit_search_report",
        "explicit_search_intent",
        "display_dimming",
        "dedicated_watch_start",
        "shared_report",
        "timeline_return",
        "ground_prompt_end",
        "prompt_proximate_candidate",
        "last_clear_report",
    ]
    labels = {
        "first_pre_explicit_search_report": "FIRST REPORT",
        "explicit_search_intent": "SEARCH INTENT",
        "display_dimming": "DISPLAY DIMMED",
        "dedicated_watch_start": "DEDICATED WATCH",
        "shared_report": "SHARED REPORT",
        "timeline_return": "TIMELINE RETURN",
        "ground_prompt_end": "GROUND QUERY",
        "prompt_proximate_candidate": "REPORT",
        "last_clear_report": "LAST CLEAR REPORT",
    }
    colors = [AMBER, TEAL, BLUE, TEAL, AMBER, VIOLET, CORAL, AMBER, AMBER]
    times = [datetime.fromisoformat(timeline[item]["utc"].replace("Z", "+00:00")) for item in ordered_ids]
    start = times[0]
    total = (times[-1] - start).total_seconds()
    x_left, x_right, line_y = 120, 1480, 520
    draw.line((x_left, line_y, x_right, line_y), fill=GRID, width=6)

    for index, (item, stamp, color) in enumerate(zip(ordered_ids, times, colors)):
        x = x_left + int(((stamp - start).total_seconds() / total) * (x_right - x_left))
        above = index % 2 == 0
        lower_stems = {
            "explicit_search_intent": 635,
            "dedicated_watch_start": 710,
            "timeline_return": 655,
            "prompt_proximate_candidate": 710,
        }
        stem_end = 335 if above else lower_stems[item]
        draw.line((x, line_y, x, stem_end), fill=color, width=3)
        draw.ellipse((x - 10, line_y - 10, x + 10, line_y + 10), fill=color, outline=TEXT, width=2)
        time_text = stamp.strftime("%H:%M:%S")
        if above:
            draw.text((x, stem_end - 42), labels[item], fill=color, font=font(16, "sans-bold"), anchor="ms")
            draw.text((x, stem_end - 16), time_text, fill=TEXT_SOFT, font=font(15, "mono"), anchor="ms")
        else:
            draw.text((x, stem_end + 14), labels[item], fill=color, font=font(16, "sans-bold"), anchor="ma")
            draw.text((x, stem_end + 40), time_text, fill=TEXT_SOFT, font=font(15, "mono"), anchor="ma")

    deltas = stage11s["deltas_seconds"]
    cards = [
        ("138.865 s", "first report to explicit search", TEAL),
        ("500.143 s", "dedicated watch to timeline return", VIOLET),
        ("12.462 s", "ground query to next report", CORAL),
    ]
    if round(float(deltas["first_report_to_search_intent_seconds"]), 3) != 138.865:
        raise RuntimeError("Attention timeline changed; revise Figure 8.")
    for index, (value, note, color) in enumerate(cards):
        left = 180 + index * 430
        glass_panel(draw, (left, 800, left + 390, 884), color, fill=PANEL_LIGHT)
        draw.text((left + 24, 826), value, fill=color, font=font(25, "serif-bold"))
        draw.text((left + 24, 858), note, fill=TEXT_SOFT, font=font(16, "sans"))

    chart_footer(draw, "A nonstationary observation process. No prompt causation, event mapping, or physical clustering is inferred.")
    save_chart(image, "Artemis-II-Chart-8-Attention-Conditioned-Detection.png")


def main() -> None:
    stage11e = load_json("stage11e-result.json")
    stage11g = load_json("stage11g-result.json")
    stage11l = load_json("stage11l-result.json")
    stage10x = load_json("stage10x-result.json")
    stage11s = load_json("stage11s-result.json")
    stage11t = load_json("stage11t-result.json")
    stage11u = load_json("stage11u-selection-weighting-cascade.json")
    for result in (stage11e, stage11g, stage11l, stage10x, stage11s, stage11t, stage11u):
        if not result.get("pass"):
            raise RuntimeError(f"Refusing to render from failed result: {result['testbed_id']}")

    render_cover()
    render_observation_collapse(stage11e["context"])
    render_selection_weighting_cascade(stage11u)
    render_weight_shift(stage11e["measures"])
    render_rank_reversal(
        stage11g["product_reversal_examples"][0],
        stage11g["metrics"]["action_product_reversed_pairs"],
        stage11g["metrics"]["action_product_strictly_comparable_pairs"],
    )
    render_split_receipt(stage11l)
    render_archive_analysis_layers()
    render_task_readiness(stage10x)
    render_opportunity_concentration(stage11t)
    render_attention_conditioned_detection(stage11s)


if __name__ == "__main__":
    main()
