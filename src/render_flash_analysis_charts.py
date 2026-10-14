from __future__ import annotations

if __name__ == "__main__":
    raise SystemExit(
        "STOP: this historical renderer includes withdrawn timeline and distance-advantage graphics. "
        "It is disabled before imports or writes. See TIMING-SOURCE-QUALIFICATION.md and "
        "paper-review/range-geometry/RANGE-RECONCILIATION.md."
    )

from datetime import datetime, timezone

from PIL import Image, ImageDraw

from render_public_analysis_charts import (
    AMBER,
    AMBER_LIGHT,
    BLUE,
    CHART_H,
    CHART_W,
    CORAL,
    GREEN,
    GRID,
    MUTED,
    NAVY,
    PANEL,
    PANEL_DEEP,
    PANEL_LIGHT,
    ROOT,
    TEAL,
    TEXT,
    TEXT_SOFT,
    VIOLET,
    chart_canvas,
    chart_footer,
    chart_header,
    draw_arrow,
    fitted_font,
    font,
    glass_panel,
    glow_disc,
    load_json,
    save_chart,
    wrap_text,
)


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def render_flash_timeline(result: dict) -> None:
    raise RuntimeError("Withdrawn: background-photo timing does not bound all accepted events.")
    image, draw = chart_canvas()
    chart_header(
        draw,
        "F1",
        "Five marked events. One later high-rate window.",
        "The public record separates real-time voice anchors, a curated ledger, and camera coverage.",
    )

    start = parse_utc("2026-04-07T00:39:00Z")
    stop = parse_utc("2026-04-07T01:23:00Z")
    x0, x1 = 130, 1480

    def x_at(value: str) -> int:
        moment = parse_utc(value)
        return round(x0 + (x1 - x0) * (moment - start).total_seconds() / (stop - start).total_seconds())

    y = 520
    glass_panel(draw, (84, 245, 1516, 825), BLUE, fill=PANEL_DEEP)
    draw.text((122, 298), "VOICE RECORD", fill=TEXT_SOFT, font=font(17, "sans-bold"))
    draw.line((x0, y, x1, y), fill=GRID, width=5)
    for tick in (
        "2026-04-07T00:40:00Z",
        "2026-04-07T00:50:00Z",
        "2026-04-07T01:00:00Z",
        "2026-04-07T01:10:00Z",
        "2026-04-07T01:20:00Z",
    ):
        x = x_at(tick)
        draw.line((x, y - 16, x, y + 18), fill=MUTED, width=2)
        draw.text((x, y + 34), parse_utc(tick).strftime("%H:%M"), fill=TEXT_SOFT, font=font(16, "mono"), anchor="ma")

    anchors = [
        ("2026-04-07T00:41:00.680Z", "FIRST CLEAR", BLUE, 395),
        ("2026-04-07T00:51:15.947Z", "SHARED", TEAL, 675),
        ("2026-04-07T00:52:52.411Z", "LESS SURE", AMBER, 390),
        ("2026-04-07T00:59:18.291Z", "CLEAR", BLUE, 675),
        ("2026-04-07T01:03:04.906Z", "CLEAR", BLUE, 390),
    ]
    for timestamp, label, color, label_y in anchors:
        x = x_at(timestamp)
        draw.line((x, y - 6, x, label_y + (38 if label_y < y else -15)), fill=color, width=3)
        if label == "LESS SURE":
            draw.ellipse((x - 12, y - 12, x + 12, y + 12), fill=PANEL_DEEP, outline=color, width=4)
        else:
            draw.ellipse((x - 11, y - 11, x + 11, y + 11), fill=color)
        draw.text((x, label_y), label, fill=color, font=font(16, "sans-bold"), anchor="mm")
        draw.text((x, label_y + 26), parse_utc(timestamp).strftime("%H:%M:%S"), fill=TEXT_SOFT, font=font(15, "mono"), anchor="mm")

    ledger_x = x_at(result["camera_window"]["annotation_ledger_utc"])
    draw.line((ledger_x, 610, ledger_x, 756), fill=VIOLET, width=4)
    draw.rounded_rectangle((ledger_x - 92, 610, ledger_x + 92, 688), radius=18, fill=PANEL_LIGHT, outline=VIOLET, width=3)
    draw.text((ledger_x, 638), "5-EVENT LEDGER", fill=VIOLET, font=font(16, "sans-bold"), anchor="mm")
    draw.text((ledger_x, 666), "01:04:00", fill=TEXT, font=font(20, "mono"), anchor="mm")

    camera_start = result["camera_window"]["camera_start_utc"]
    camera_stop = result["camera_window"]["camera_stop_utc"]
    camera_x0, camera_x1 = x_at(camera_start), x_at(camera_stop)
    draw.rounded_rectangle((camera_x0, 700, camera_x1, 748), radius=22, fill=CORAL)
    draw.text(((camera_x0 + camera_x1) // 2, 724), "30 FPS", fill=NAVY, font=font(16, "sans-bold"), anchor="mm")
    draw.text(((camera_x0 + camera_x1) // 2, 774), "01:19:13–01:21:23".replace("–", " to "), fill=TEXT_SOFT, font=font(15, "mono"), anchor="mm")
    draw_arrow(draw, (ledger_x + 96, 651), (camera_x0 - 16, 651), AMBER, 4)
    draw.text(((ledger_x + camera_x0) // 2, 623), "15 MIN 13 SEC", fill=AMBER_LIGHT, font=font(18, "sans-bold"), anchor="mm")

    draw.rounded_rectangle((115, 790, 1485, 820), radius=15, fill=PANEL)
    draw.text((800, 805), "VOICE ANCHORS ARE NOT ASSIGNED ONE-TO-ONE TO THE FIVE ANNOTATED EVENTS", fill=TEXT, font=font(17, "sans-bold"), anchor="mm")
    chart_footer(draw, "Sources: crew transcripts, official five-event annotation, and PDS camera label. The 30 fps null is a later interval.")
    save_chart(image, "Artemis-II-Flash-Chart-1-Timeline.png")


def render_witness_matrix(result: dict) -> None:
    image, draw = chart_canvas()
    chart_header(
        draw,
        "F2",
        "Five events, eight witness marks",
        "Cross-witness structure strengthens the ledger without turning it into a calibrated survey.",
    )
    glass_panel(draw, (130, 235, 1470, 835), TEAL, fill=PANEL_DEEP)
    observers = [
        ("REID WISEMAN", BLUE),
        ("JEREMY HANSEN", CORAL),
        ("VICTOR GLOVER", GREEN),
    ]
    xs = [660, 930, 1200]
    for (name, color), x in zip(observers, xs):
        draw.text((x, 292), name, fill=color, font=font(17, "sans-bold"), anchor="mm")
        draw.line((x, 325, x, 735), fill=GRID, width=2)

    name_map = {"Reid Wiseman": BLUE, "Jeremy Hansen": CORAL, "Victor Glover": GREEN}
    observer_index = {"Reid Wiseman": 0, "Jeremy Hansen": 1, "Victor Glover": 2}
    ys = [380, 465, 550, 635, 720]
    for event, y in zip(result["annotation_events"], ys):
        draw.text((210, y), f"EVENT {event['event_id']}", fill=TEXT, font=font(25, "serif-bold"), anchor="lm")
        draw.text((390, y), f"{len(event['observers'])} witness" + ("es" if len(event["observers"]) > 1 else ""), fill=TEXT_SOFT, font=font(18, "sans"), anchor="lm")
        draw.line((540, y, 1325, y), fill="#1E3B58", width=2)
        for observer in event["observers"]:
            x = xs[observer_index[observer]]
            color = name_map[observer]
            glow_disc(image, (x, y), 28, tuple(int(color[i:i+2], 16) for i in (1, 3, 5)), 70)
            draw = ImageDraw.Draw(image)
            draw.ellipse((x - 15, y - 15, x + 15, y + 15), fill=color, outline=TEXT, width=2)
        state = "THREE-WITNESS" if len(event["observers"]) == 3 else ("SHARED" if len(event["observers"]) == 2 else "SINGLE")
        state_color = TEAL if len(event["observers"]) >= 2 else MUTED
        draw.text((1390, y), state, fill=state_color, font=font(15, "sans-bold"), anchor="rm")

    draw.rounded_rectangle((280, 775, 1320, 820), radius=22, fill=PANEL_LIGHT)
    draw.text((800, 797), "5 EVENTS  •  8 MARKS  •  3 OBSERVERS  •  2 MULTI-WITNESS EVENTS", fill=TEXT, font=font(19, "sans-bold"), anchor="mm")
    chart_footer(draw, "Source: NASA crew annotation and observer-color key. Exact event times remain unresolved.")
    save_chart(image, "Artemis-II-Flash-Chart-2-Witness-Matrix.png")


def render_count_to_flux(result: dict) -> None:
    image, draw = chart_canvas()
    chart_header(
        draw,
        "F3",
        "Five flashes set a floor, not a calibrated flux",
        "NASA's lower-bound claim is defensible. Survey comparison still needs a measurement function.",
    )
    glass_panel(draw, (90, 250, 500, 810), VIOLET, fill=PANEL_DEEP)
    draw.text((295, 310), "PUBLIC EVENT LEDGER", fill=VIOLET, font=font(18, "sans-bold"), anchor="mm")
    draw.text((295, 445), "5", fill=TEXT, font=font(150, "serif-bold"), anchor="mm")
    draw.text((295, 535), "CONFIRMED EVENTS", fill=TEXT, font=font(20, "sans-bold"), anchor="mm")
    draw.text((295, 590), "cross-witnessed", fill=TEXT_SOFT, font=font(19, "sans"), anchor="mm")
    draw.text((295, 625), "rough locations", fill=TEXT_SOFT, font=font(19, "sans"), anchor="mm")
    draw.text((295, 660), "no calibrated brightness", fill=TEXT_SOFT, font=font(19, "sans"), anchor="mm")
    draw.rounded_rectangle((145, 720, 445, 775), radius=27, fill=PANEL_LIGHT, outline=VIOLET, width=2)
    draw.text((295, 747), "ACCEPTED COUNT", fill=VIOLET, font=font(17, "sans-bold"), anchor="mm")

    floor = result["geometry"]["all_lunar_one_hour_detected_count_floor_km2_hour"]
    draw.text((800, 308), "CONSERVATIVE COUNT FLOOR", fill=AMBER_LIGHT, font=font(18, "sans-bold"), anchor="mm")
    draw.text((800, 382), "5 ÷ (4πR² × 1 h)", fill=TEXT, font=font(38, "mono"), anchor="mm")
    draw.text((800, 465), f"{floor / 1e-7:.2f} × 10⁻⁷", fill=AMBER, font=font(49, "mono"), anchor="mm")
    draw.text((800, 520), "per km² per hour", fill=TEXT_SOFT, font=font(21, "sans"), anchor="mm")
    draw.rounded_rectangle((585, 570, 1015, 670), radius=20, fill=PANEL_LIGHT, outline=AMBER, width=2)
    draw.text((800, 595), "ASSUMPTIONS", fill=AMBER_LIGHT, font=font(16, "sans-bold"), anchor="mm")
    draw.text((800, 627), "5 accepted impacts  •  ≤1 hour", fill=TEXT, font=font(17, "sans"), anchor="mm")
    draw.text((800, 653), "entire lunar surface as denominator", fill=TEXT_SOFT, font=font(16, "sans"), anchor="mm")
    draw.rounded_rectangle((575, 710, 1025, 780), radius=20, fill=PANEL_LIGHT, outline=CORAL, width=3)
    draw.text((800, 735), "NO LIMITING MAGNITUDE", fill=CORAL, font=font(17, "sans-bold"), anchor="mm")
    draw.text((800, 761), "NO COMPLETENESS  •  NOT SURVEY-COMPARABLE", fill=TEXT, font=font(15, "sans-bold"), anchor="mm")

    glass_panel(draw, (1100, 250, 1510, 810), TEAL, fill=PANEL_DEEP)
    draw.text((1305, 310), "WHAT A SURVEY ADDS", fill=TEAL, font=font(18, "sans-bold"), anchor="mm")
    requirements = [
        ("LIVE TIME", "when observers or sensors were active"),
        ("MONITORED AREA", "where a flash could have been seen"),
        ("COMPLETENESS", "recovery by brightness, place, and background"),
        ("CALIBRATION", "counts or magnitudes tied to a response"),
        ("CONFIRMATION", "independent channels and rejection rules"),
    ]
    y = 370
    for title, detail in requirements:
        draw.ellipse((1140, y - 7, 1156, y + 9), fill=TEAL)
        draw.text((1180, y), title, fill=TEXT, font=font(18, "sans-bold"), anchor="lm")
        wrapped = wrap_text(draw, detail, font(15, "sans"), 275)
        draw.multiline_text((1180, y + 24), wrapped, fill=TEXT_SOFT, font=font(15, "sans"), spacing=2)
        y += 72
    draw.rounded_rectangle((1140, 735, 1470, 785), radius=25, fill=PANEL_LIGHT, outline=TEAL, width=2)
    draw.text((1305, 760), "CALIBRATED FLUX", fill=TEAL, font=font(17, "sans-bold"), anchor="mm")
    chart_footer(draw, "The count floor uses the Moon's full surface and a one-hour ceiling. Survey flux needs brightness-dependent exposure.")
    save_chart(image, "Artemis-II-Flash-Chart-3-Count-To-Flux.png")


def render_distance_advantage(result: dict) -> None:
    raise RuntimeError("Withdrawn: the historical distance input is not a verified observing advantage.")
    image, draw = chart_canvas()
    chart_header(
        draw,
        "F4",
        "Orion had a 27-fold geometric light advantage",
        "Closer range can make intrinsically faint point sources much easier to see without implying a higher impact rate.",
    )
    geometry = result["geometry"]
    glass_panel(draw, (110, 245, 1490, 820), AMBER, fill=PANEL_DEEP)
    draw.text((260, 315), "ORION", fill=BLUE, font=font(19, "sans-bold"), anchor="mm")
    draw.text((260, 360), "46,000 mi", fill=TEXT, font=font(34, "serif-bold"), anchor="mm")
    draw.text((260, 397), "from the Moon", fill=TEXT_SOFT, font=font(17, "sans"), anchor="mm")
    draw.text((1340, 315), "EARTH", fill=TEAL, font=font(19, "sans-bold"), anchor="mm")
    draw.text((1340, 360), "238,855 mi", fill=TEXT, font=font(34, "serif-bold"), anchor="mm")
    draw.text((1340, 397), "average range", fill=TEXT_SOFT, font=font(17, "sans"), anchor="mm")

    moon_x, moon_y = 800, 430
    glow_disc(image, (moon_x, moon_y), 70, (255, 184, 77), 90)
    draw = ImageDraw.Draw(image)
    draw.ellipse((moon_x - 55, moon_y - 55, moon_x + 55, moon_y + 55), fill="#D6D8D5")
    draw.ellipse((moon_x - 75, moon_y - 58, moon_x + 30, moon_y + 58), fill=NAVY)
    draw.ellipse((moon_x + 18, moon_y - 8, moon_x + 34, moon_y + 8), fill=AMBER)
    draw.line((315, moon_y, moon_x - 85, moon_y), fill=BLUE, width=7)
    draw.line((moon_x + 85, moon_y, 1285, moon_y), fill=TEAL, width=7)
    draw.ellipse((240, moon_y - 20, 280, moon_y + 20), fill=BLUE)
    draw.ellipse((1320, moon_y - 20, 1360, moon_y + 20), fill=TEAL)

    draw.text((800, 570), "POINT-SOURCE GEOMETRY", fill=AMBER_LIGHT, font=font(18, "sans-bold"), anchor="mm")
    equation = f"(238,855 ÷ 46,000)² = {geometry['inverse_square_received_flux_advantage']:.1f}×"
    draw.text((800, 635), equation, fill=TEXT, font=font(43, "mono"), anchor="mm")
    draw.text((800, 700), f"5 log₁₀(238,855 ÷ 46,000) = {geometry['magnitude_advantage']:.2f} mag", fill=TEXT, font=font(29, "serif-bold"), anchor="mm")
    draw.rounded_rectangle((340, 752, 1260, 800), radius=24, fill=PANEL_LIGHT, outline=CORAL, width=2)
    draw.text((800, 776), "VISIBILITY EXPLANATION  •  NOT FLASH PHOTOMETRY OR AN IMPACT-SIZE MEASUREMENT", fill=CORAL, font=font(16, "sans-bold"), anchor="mm")
    chart_footer(draw, "Sources: NASA's 46,000-mile Artemis II range and 238,855-mile average Earth-Moon distance.")
    save_chart(image, "Artemis-II-Flash-Chart-4-Distance-Advantage.png")


def render_overlap_context(result: dict) -> None:
    image, draw = chart_canvas()
    chart_header(
        draw,
        "F5",
        "The Moon occupied a ten-pixel footprint",
        "A 60 fps clip spans the crew report, but scale and calibration limit what its silence can mean.",
    )
    glass_panel(draw, (84, 245, 846, 675), BLUE, fill=PANEL_DEEP)
    frame = Image.open(ROOT / "evidence/stage11p/report-frame.png").convert("RGB")
    shown = frame.resize((720, 405), Image.Resampling.LANCZOS)
    image.paste(shown, (105, 258))
    draw = ImageDraw.Draw(image)
    moon_x = 105 + round(373 * 720 / 1280)
    moon_y = 258 + round(124 * 405 / 720)
    draw.ellipse((moon_x - 18, moon_y - 18, moon_x + 18, moon_y + 18), outline=AMBER, width=3)
    draw.line((moon_x + 20, moon_y + 10, moon_x + 150, moon_y + 80), fill=AMBER, width=3)
    draw.text((moon_x + 160, moon_y + 82), "MOON", fill=AMBER_LIGHT, font=font(16, "sans-bold"), anchor="lm")
    draw.text((465, 642), "REPORT-TIME FRAME  •  1280 × 720", fill=TEXT_SOFT, font=font(15, "sans-bold"), anchor="mm")

    glass_panel(draw, (882, 245, 1516, 675), AMBER, fill=PANEL_DEEP)
    footprint = result["lunar_footprint"]
    crop = frame.crop((358, 109, 389, 140)).resize((310, 310), Image.Resampling.NEAREST)
    image.paste(crop, (930, 285))
    draw = ImageDraw.Draw(image)
    draw.rectangle((930, 285, 1240, 595), outline=GRID, width=2)
    draw.text((1370, 320), "THRESHOLD", fill=TEXT_SOFT, font=font(15, "sans-bold"), anchor="mm")
    draw.text((1370, 356), "> 10 gray", fill=TEXT, font=font(20, "mono"), anchor="mm")
    draw.text((1370, 425), "FOOTPRINT", fill=TEXT_SOFT, font=font(15, "sans-bold"), anchor="mm")
    draw.text((1370, 464), f"{footprint['apparent_width_pixels']} × {footprint['apparent_height_pixels']} px", fill=AMBER_LIGHT, font=font(27, "serif-bold"), anchor="mm")
    draw.text((1370, 535), "ILLUSTRATIVE", fill=TEXT_SOFT, font=font(15, "sans-bold"), anchor="mm")
    draw.text((1370, 568), f"~{footprint['illustrative_km_per_apparent_pixel']:.0f} km / px", fill=TEXT, font=font(18, "mono"), anchor="mm")
    draw.text((1198, 642), "IMAGE FOOTPRINT  •  NOT OPTICAL RESOLUTION", fill=CORAL, font=font(15, "sans-bold"), anchor="mm")

    glass_panel(draw, (84, 705, 1516, 875), TEAL, fill=PANEL_DEEP)
    series = result["pulse_screen"]["robust_z_series"]
    x0, x1, y0, y1 = 135, 1465, 745, 835
    draw.line((x0, (y0 + y1) // 2, x1, (y0 + y1) // 2), fill=GRID, width=2)
    points = []
    for index, value in enumerate(series):
        x = x0 + (x1 - x0) * index / (len(series) - 1)
        clipped = max(-2.5, min(2.5, value))
        y = y1 - (clipped + 2.5) * (y1 - y0) / 5.0
        points.append((x, y))
    draw.line(points, fill=TEAL, width=3)
    event_x = x0 + (x1 - x0) * 5.947 / 15.015
    draw.line((event_x, y0 - 5, event_x, y1 + 5), fill=AMBER, width=4)
    draw.text((event_x, 725), "CREW REPORT", fill=AMBER_LIGHT, font=font(14, "sans-bold"), anchor="mm")
    draw.text((x0, 850), "00:51:10", fill=TEXT_SOFT, font=font(14, "mono"), anchor="lm")
    draw.text((x1, 850), "00:51:25", fill=TEXT_SOFT, font=font(14, "mono"), anchor="rm")
    draw.rounded_rectangle((1000, 818, 1475, 862), radius=20, fill=PANEL_LIGHT, outline=CORAL, width=2)
    draw.text((1237, 840), "NO SCREENED PULSE  •  NOT AN EXCLUSION", fill=CORAL, font=font(15, "sans-bold"), anchor="mm")
    chart_footer(draw, "Exact 15-second overlap; transcoded screening pixels. A dedicated narrow-field calibrated sensor is still required.")
    save_chart(image, "Artemis-II-Flash-Chart-5-Overlap-Limit.png")


def render_injection_recovery(result: dict) -> None:
    image, draw = chart_canvas()
    chart_header(
        draw,
        "F6",
        "The null failed its own sensitivity test",
        "A frozen 1,458-trial injection grid recovered only 5.6% at the maximum requested pulse.",
    )

    baseline = result["baseline"]
    curve = result["recovery_curve"]
    glass_panel(draw, (84, 245, 650, 820), AMBER, fill=PANEL_DEEP)
    draw.text((128, 302), "WHAT THE SCREEN REQUIRED", fill=AMBER_LIGHT, font=font(18, "sans-bold"))
    draw.text((128, 346), "Added clip-native digital counts at the median frame", fill=TEXT_SOFT, font=font(16, "sans"))
    thresholds = [
        ("20% RELATIVE RISE", baseline["analytic_added_dn_for_relative_threshold_at_median"], TEAL),
        ("ROBUST Z = 6", baseline["analytic_added_dn_for_robust_z_at_median"], AMBER),
    ]
    maximum = max(value for _, value, _ in thresholds)
    y = 430
    for label, value, color in thresholds:
        draw.text((128, y), label, fill=color, font=font(16, "sans-bold"))
        draw.rounded_rectangle((128, y + 36, 592, y + 76), radius=20, fill=PANEL_LIGHT)
        width = round(464 * value / maximum)
        draw.rounded_rectangle((128, y + 36, 128 + width, y + 76), radius=20, fill=color)
        draw.text((580, y + 18), f"+{value:,.0f} DN", fill=TEXT, font=font(20, "mono"), anchor="ra")
        y += 145
    draw.rounded_rectangle((128, 710, 592, 782), radius=20, fill=PANEL_LIGHT, outline=CORAL, width=2)
    draw.text((360, 734), "FRAME VARIABILITY CONTROLLED", fill=CORAL, font=font(16, "sans-bold"), anchor="mm")
    draw.text((360, 759), "about 8× the relative-rise threshold", fill=TEXT, font=font(16, "sans"), anchor="mm")

    glass_panel(draw, (690, 245, 1516, 820), BLUE, fill=PANEL_DEEP)
    draw.text((734, 302), "FROZEN INJECTION RECOVERY", fill=BLUE, font=font(18, "sans-bold"))
    draw.text((734, 346), "162 trials at each requested pulse level", fill=TEXT_SOFT, font=font(16, "sans"))
    draw.text((734, 382), "MAX REALIZED ADDITION: +4,046 DN AFTER CLIPPING", fill=AMBER_LIGHT, font=font(14, "sans-bold"))
    plot_x0, plot_x1 = 760, 1435
    plot_y0, plot_y1 = 420, 685
    for percent in (0, 25, 50, 75, 100):
        y = plot_y1 - (plot_y1 - plot_y0) * percent / 100
        draw.line((plot_x0, y, plot_x1, y), fill=GRID, width=2)
        draw.text((plot_x0 - 18, y), f"{percent}%", fill=TEXT_SOFT, font=font(14, "mono"), anchor="rm")
    amplitudes = [row["requested_integrated_dn_per_frame"] for row in curve]
    points = []
    for row in curve:
        x = plot_x0 + (plot_x1 - plot_x0) * row["requested_integrated_dn_per_frame"] / max(amplitudes)
        y = plot_y1 - (plot_y1 - plot_y0) * row["recovery_fraction"]
        points.append((x, y))
    draw.line(points, fill=TEAL, width=5)
    for (x, y), row in zip(points, curve):
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=TEAL, outline=TEXT, width=2)
        if row["recovery_fraction"] > 0:
            draw.text((x, y - 28), f"{row['recovery_fraction'] * 100:.1f}%", fill=AMBER_LIGHT, font=font(18, "sans-bold"), anchor="mm")
    for amplitude in (0, 4000, 8000, 12000, 16000):
        x = plot_x0 + (plot_x1 - plot_x0) * amplitude / max(amplitudes)
        draw.text((x, plot_y1 + 24), f"{amplitude // 1000}k", fill=TEXT_SOFT, font=font(14, "mono"), anchor="mm")
    draw.text(((plot_x0 + plot_x1) // 2, plot_y1 + 55), "REQUESTED INTEGRATED DN PER FRAME", fill=TEXT_SOFT, font=font(14, "sans-bold"), anchor="mm")
    draw.rounded_rectangle((770, 754, 1435, 800), radius=22, fill=PANEL_LIGHT, outline=CORAL, width=2)
    draw.text((1102, 777), "50% RECOVERY NOT REACHED", fill=CORAL, font=font(18, "sans-bold"), anchor="mm")

    chart_footer(draw, "Transcoded clip-native units only. The curve is not a brightness limit, sensor calibration, or event exclusion.")
    save_chart(image, "Artemis-II-Flash-Chart-6-Injection-Recovery.png")


def main() -> None:
    raise RuntimeError("Historical six-figure renderer disabled; do not restore withdrawn graphics.")
    result = load_json("stage11n-result.json")
    if not result.get("pass"):
        raise RuntimeError("Refusing to render from a failed Stage 11N receipt.")
    render_flash_timeline(result)
    render_witness_matrix(result)
    render_count_to_flux(result)
    render_distance_advantage(result)
    overlap_result = load_json("stage11p-overlap-pixel-screen.json")
    if not overlap_result.get("pass"):
        raise RuntimeError("Refusing to render from a failed Stage 11P screen.")
    render_overlap_context(overlap_result)
    injection_result = load_json("stage11q-injection-recovery.json")
    if not injection_result.get("pass"):
        raise RuntimeError("Refusing to render from a failed Stage 11Q injection receipt.")
    render_injection_recovery(injection_result)


if __name__ == "__main__":
    main()
