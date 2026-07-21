"""Regenerate unclear diagram PNGs with larger fonts + upscale low-res assets."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "assets" / "img"

# Colors
INK = (14, 21, 27)
MUTED = (74, 87, 96)
LINE = (218, 221, 215)
PAPER = (255, 255, 255)
TEAL = (31, 107, 98)
TEAL_BRIGHT = (62, 214, 196)
ORANGE = (195, 98, 27)
GREEN = (56, 116, 94)
BLUE = (37, 99, 140)
PURPLE = (92, 64, 140)
DARK = (15, 32, 41)
RED = (196, 60, 58)
AMBER = (210, 150, 40)


def fonts(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def rounded(draw: ImageDraw.ImageDraw, xy, fill, outline=None, radius=18, width=2):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text_w(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if text_w(draw, trial, font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [text]


def draw_wrapped(draw, xy, text, font, fill, max_width, line_gap=6):
    x, y = xy
    line_h = getattr(font, "size", 24) + line_gap
    for line in wrap_text(draw, text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h
    return y


def upscale_sharpen(path: Path, scale: float = 2.2) -> None:
    im = Image.open(path).convert("RGB")
    w, h = im.size
    out = im.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    out = out.filter(ImageFilter.UnsharpMask(radius=1.6, percent=140, threshold=2))
    out = ImageEnhance.Contrast(out).enhance(1.08)
    out = ImageEnhance.Sharpness(out).enhance(1.25)
    out.save(path, "PNG", optimize=True)
    print(f"upscaled {path.name}: {w}x{h} -> {out.size[0]}x{out.size[1]}")


def make_stage3() -> None:
    W, H = 2200, 980
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    title = fonts(42, True)
    body = fonts(26)
    small = fonts(24)
    label = fonts(22, True)

    steps = [
        (TEAL, "1  Field capture", "RGB, radar, and calibration are recorded together."),
        (BLUE, "2  Frame bundle", "Each sample keeps synchronized sensor context."),
        (ORANGE, "3  3D annotation", "One master-frame box is edited in both views."),
        (PURPLE, "4  Review gate", "Radar fit, RGB projection, visibility, and ID are checked."),
        (GREEN, "5  Export", "Reviewed labels feed training and evaluation."),
    ]
    pad = 36
    gap = 18
    box_w = (W - 2 * pad - 4 * gap) // 5
    box_h = 250
    y0 = 48
    for i, (color, heading, desc) in enumerate(steps):
        x = pad + i * (box_w + gap)
        rounded(d, (x, y0, x + box_w, y0 + box_h), PAPER, LINE, 20)
        d.rounded_rectangle((x, y0, x + box_w, y0 + 64), radius=20, fill=color)
        d.rectangle((x, y0 + 40, x + box_w, y0 + 64), fill=color)
        d.text((x + 18, y0 + 16), heading, font=label, fill=PAPER)
        draw_wrapped(d, (x + 18, y0 + 88), desc, body, MUTED, box_w - 36, 8)
        if i < 4:
            ax = x + box_w + 4
            ay = y0 + box_h // 2
            d.polygon([(ax, ay - 8), (ax + 12, ay), (ax, ay + 8)], fill=INK)

    # Bottom panels
    panel_y = y0 + box_h + 48
    left_w = int(W * 0.48) - pad
    right_x = pad + left_w + 24
    right_w = W - right_x - pad
    panel_h = H - panel_y - pad
    rounded(d, (pad, panel_y, pad + left_w, panel_y + panel_h), PAPER, LINE, 20)
    rounded(d, (right_x, panel_y, right_x + right_w, panel_y + panel_h), PAPER, LINE, 20)
    d.text((pad + 28, panel_y + 24), "Observed sequence", font=title, fill=INK)
    d.text((right_x + 28, panel_y + 24), "Internal-label class distribution", font=title, fill=INK)

    cards = [
        (TEAL, "1,496", "RGB images"),
        (BLUE, "277", "labelled frames"),
        (GREEN, "547", "reviewed objects"),
        (PURPLE, "per-frame", "calibration"),
    ]
    cw = (left_w - 56 - 16) // 2
    ch = 120
    for i, (color, num, caption) in enumerate(cards):
        cx = pad + 28 + (i % 2) * (cw + 16)
        cy = panel_y + 100 + (i // 2) * (ch + 16)
        rounded(d, (cx, cy, cx + cw, cy + ch), (248, 249, 247), LINE, 14)
        d.rectangle((cx, cy + 10, cx + 10, cy + ch - 10), fill=color)
        d.text((cx + 28, cy + 24), num, font=fonts(40, True), fill=INK)
        d.text((cx + 28, cy + 74), caption, font=small, fill=MUTED)

    # Bars
    bars = [("Pedestrian", 461, TEAL), ("Cyclist", 83, ORANGE)]
    max_v = 461
    bar_left = right_x + 28
    bar_right = right_x + right_w - 100
    by = panel_y + 130
    for name, val, color in bars:
        d.text((bar_left, by), name, font=fonts(28, True), fill=INK)
        track_y = by + 44
        rounded(d, (bar_left, track_y, bar_right, track_y + 40), (238, 240, 236), None, 10)
        fill_w = int((bar_right - bar_left) * (val / max_v))
        rounded(d, (bar_left, track_y, bar_left + max(fill_w, 48), track_y + 40), color, None, 10)
        d.text((bar_right + 16, track_y + 6), str(val), font=fonts(28, True), fill=INK)
        by += 130

    out = IMG / "stage3_annotation_context.png"
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out.name} {img.size}")


def make_stage4() -> None:
    W, H = 2200, 1100
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    pad = 40
    steps = [
        (BLUE, "1. Observe", "Forward camera image, radar point cloud and object labels from the loaded road sequence."),
        (GREEN, "2. Align", "Calibration places detections in one road-centred coordinate system."),
        (AMBER, "3. Measure", "TTC, distance, required braking, headway, crowding and visibility are computed."),
        (ORANGE, "4. Prioritise", "Each object receives Low, Medium, High or Critical risk using fixed thresholds."),
        (RED, "5. Warn", "Dashboard panels, colour coding, timeline and optional audio support rider action."),
    ]
    gap = 16
    box_w = (W - 2 * pad - 4 * gap) // 5
    box_h = 260
    y0 = 40
    heading_f = fonts(28, True)
    body_f = fonts(24)
    for i, (color, title, desc) in enumerate(steps):
        x = pad + i * (box_w + gap)
        rounded(d, (x, y0, x + box_w, y0 + box_h), PAPER, color, 18, 3)
        d.text((x + 18, y0 + 20), title, font=heading_f, fill=color)
        draw_wrapped(d, (x + 18, y0 + 70), desc, body_f, MUTED, box_w - 36, 7)
        if i < 4:
            ax = x + box_w + 2
            ay = y0 + box_h // 2
            d.polygon([(ax, ay - 9), (ax + 14, ay), (ax, ay + 9)], fill=INK)

    # Risk bar
    by = y0 + box_h + 50
    d.text((pad, by), "Live sequence evidence: 277 frames analysed", font=fonts(36, True), fill=BLUE)
    bar_y = by + 70
    bar_h = 70
    segments = [
        (122, (76, 175, 80), "LOW 122 (44%)", INK),
        (3, (242, 201, 76), "MEDIUM 3 (1%)", INK),
        (62, (230, 126, 34), "HIGH 62 (22%)", PAPER),
        (90, (192, 57, 43), "CRITICAL 90 (32%)", PAPER),
    ]
    total = 277
    x = pad
    usable = W - 2 * pad
    for val, color, label, tcol in segments:
        w = max(int(usable * val / total), 8 if val else 0)
        if w <= 0:
            continue
        d.rectangle((x, bar_y, x + w, bar_y + bar_h), fill=color)
        if w > 120:
            tw = text_w(d, label, fonts(24, True))
            d.text((x + (w - tw) / 2, bar_y + 20), label, font=fonts(24, True), fill=tcol)
        elif val == 3:
            d.text((x - 10, bar_y - 34), "MEDIUM 3 (1%)", font=fonts(20, True), fill=MUTED)
        x += w
    d.rounded_rectangle((pad, bar_y, W - pad, bar_y + bar_h), radius=8, outline=LINE, width=2)

    # Cards
    cards = [
        ("Frames", "277", "sequential loaded moments"),
        ("Critical scenes", "90", "frames needing immediate attention"),
        ("Ego speed", "32 km/h", "used for approach and headway"),
        ("Crowd trigger", "4+ objects", "within 45 m ahead"),
    ]
    cy = bar_y + bar_h + 50
    cw = (W - 2 * pad - 3 * 18) // 4
    ch = H - cy - pad
    for i, (title, value, sub) in enumerate(cards):
        x = pad + i * (cw + 18)
        rounded(d, (x, cy, x + cw, cy + ch), PAPER, BLUE, 18, 2)
        d.text((x + 24, cy + 28), title, font=fonts(26, True), fill=BLUE)
        d.text((x + 24, cy + 80), value, font=fonts(48, True), fill=BLUE)
        draw_wrapped(d, (x + 24, cy + 150), sub, fonts(24), MUTED, cw - 48, 6)

    out = IMG / "stage4_dashboard_loop.png"
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out.name} {img.size}")


def make_stage2() -> None:
    W, H = 2400, 1200
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    pad = 40
    title_f = fonts(40, True)
    sub_f = fonts(26)
    body_f = fonts(25)
    small_f = fonts(22)

    d.text((pad, 28), "Recording Sequence", font=title_f, fill=INK)
    d.text((pad, 84), "FusionApp paired recording clock and temporal export", font=sub_f, fill=MUTED)

    # Left clock panel
    left = (pad, 140, int(W * 0.58), H - pad)
    right = (int(W * 0.58) + 20, 140, W - pad, int(H * 0.52))
    bottom = (pad, int(H * 0.55), W - pad, H - pad)
    rounded(d, left, PAPER, LINE, 20)
    rounded(d, right, PAPER, LINE, 20)
    rounded(d, bottom, PAPER, LINE, 20)

    d.text((left[0] + 28, left[1] + 24), "Shared Monotonic Capture Clock", font=fonts(30, True), fill=INK)

    def timeline(y, label, center_label, center_color):
        d.text((left[0] + 28, y - 36), label, font=fonts(24, True), fill=MUTED)
        x0, x1 = left[0] + 60, left[2] - 60
        d.line((x0, y, x1, y), fill=LINE, width=4)
        for i, lab in enumerate(["Previous", center_label, "Next"]):
            cx = x0 + (x1 - x0) * (0.18 + i * 0.32)
            color = center_color if i == 1 else (200, 205, 210)
            d.ellipse((cx - 22, y - 22, cx + 22, y + 22), fill=color, outline=INK, width=2)
            tw = text_w(d, lab, small_f)
            d.text((cx - tw / 2, y + 34), lab, font=small_f, fill=INK if i == 1 else MUTED)
        return x0 + (x1 - x0) * 0.5

    c1 = timeline(280, "TI AWR2243 Radar", "Radar sample", GREEN)
    c2 = timeline(430, "Intel RealSense D455 RGB", "Saved pair", TEAL)
    d.line((c1, 302, c1, 408), fill=BLUE, width=3)
    d.polygon([(c2 - 10, 408), (c2 + 10, 408), (c2, 422)], fill=BLUE)
    rounded(d, (c2 - 90, 470, c2 + 90, 520), (232, 244, 242), TEAL, 12)
    d.text((c2 - 55, 482), "Saved Pair", font=fonts(24, True), fill=TEAL)

    rounded(d, (left[0] + 28, 560, left[0] + 420, 640), (248, 249, 247), LINE, 12)
    draw_wrapped(d, (left[0] + 44, 576), "Manifest stores pair sequence and clock delta.", body_f, MUTED, 360, 4)
    rounded(d, (left[0] + 460, 560, left[2] - 28, 640), (248, 249, 247), LINE, 12)
    draw_wrapped(d, (left[0] + 476, 576), "Pair request latches RGB target from buffer.", body_f, MUTED, 360, 4)

    # Right steps
    d.text((right[0] + 28, right[1] + 24), "Recording Pair Formation", font=fonts(30, True), fill=INK)
    steps = [
        (GREEN, "1", "Unified capture clock"),
        (BLUE, "2", "Radar reserves pair sequence"),
        (TEAL, "3", "Camera saves closest buffered RGB"),
        (ORANGE, "4", "Manifest writes measured clock delta"),
    ]
    sy = right[1] + 90
    for color, num, text in steps:
        rounded(d, (right[0] + 28, sy, right[2] - 28, sy + 78), PAPER, LINE, 14)
        d.ellipse((right[0] + 48, sy + 18, right[0] + 88, sy + 58), fill=color)
        tw = text_w(d, num, fonts(24, True))
        d.text((right[0] + 68 - tw / 2, sy + 26), num, font=fonts(24, True), fill=PAPER)
        d.text((right[0] + 110, sy + 24), text, font=fonts(26, True), fill=INK)
        sy += 92

    # Bottom temporal export
    d.text((bottom[0] + 28, bottom[1] + 22), "Temporal Export Options", font=fonts(30, True), fill=INK)
    draw_wrapped(
        d,
        (bottom[0] + 28, bottom[1] + 70),
        "RGB comes from the current FusionApp pair (time id 0); older slices add radar context.",
        body_f,
        MUTED,
        W - 2 * pad - 56,
        4,
    )
    boxes = [
        ("1 Scan", [("0", ORANGE)], "RGB and radar from current pair"),
        ("3 Scans", [("-2", BLUE), ("-1", TEAL), ("0", ORANGE)], "Anchor RGB from time id 0 pair"),
        ("5 Scans", [("-4", (160, 165, 170)), ("-3", BLUE), ("-2", TEAL), ("-1", GREEN), ("0", ORANGE)], "Anchor RGB from time id 0 pair"),
    ]
    bw = (W - 2 * pad - 56 - 40) // 3
    by = bottom[1] + 140
    bh = bottom[3] - by - 28
    for i, (title, circles, caption) in enumerate(boxes):
        x = bottom[0] + 28 + i * (bw + 20)
        rounded(d, (x, by, x + bw, by + bh), PAPER, LINE, 16)
        d.text((x + 24, by + 20), title, font=fonts(28, True), fill=INK)
        cx = x + 40
        cy = by + 90
        for lab, color in circles:
            d.ellipse((cx, cy, cx + 54, cy + 54), fill=color, outline=INK, width=2)
            tw = text_w(d, lab, fonts(22, True))
            d.text((cx + 27 - tw / 2, cy + 14), lab, font=fonts(22, True), fill=PAPER)
            cx += 66
        draw_wrapped(d, (x + 24, by + 170), caption, body_f, MUTED, bw - 48, 5)

    out = IMG / "stage2_sync_diagram.png"
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out.name} {img.size}")


def make_pipeline_overview() -> None:
    W, H = 2000, 1500
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    title_f = fonts(44, True)
    sub_f = fonts(26)
    head_f = fonts(28, True)
    body_f = fonts(24)
    d.text((48, 36), "Integrated Camera-Radar Safety Pipeline", font=title_f, fill=INK)
    draw_wrapped(
        d,
        (48, 96),
        "From autonomous field sensing to reviewed multimodal data and interpretable two-wheeler hazard evidence.",
        sub_f,
        MUTED,
        W - 96,
        6,
    )

    cards = [
        (ORANGE, "1. Sensing and Edge Platform", [
            "Intel RealSense D455 RGB camera and TI AWR2243 mmWave radar",
            "NVIDIA Jetson Orin for acquisition, processing, control and streaming",
            "Local SSD, portable battery, hotspot and browser-based supervision",
            "Handlebar three-level indicator for rider-facing risk status",
        ], "Timestamped RGB frames and raw radar recordings"),
        (GREEN, "2. Synchronised Recording and Preparation", [
            "Radar-led saved-pair association in a shared monotonic clock domain",
            "Calibration-aware radar decoding and camera-radar alignment",
            "Seven-field VoD-compatible rows with explicit temporal scan history",
            "Optional velocity compensation and multi-scan accumulation",
        ], "Calibrated, annotation-ready camera-radar samples"),
        (BLUE, "3. 3D Annotation and Quality Control", [
            "One editable Box3D state rendered in radar BEV and RGB views",
            "Manual placement plus RT-DETR/YOLO-assisted proposals",
            "Identity-aware tracking, validation warnings and human correction",
            "Reviewed internal JSON with KITTI/VoD and JSON/CSV exports",
        ], "Auditable 3D object labels and temporal identities"),
        (DARK, "4. Safety Dashboard and Hazard Analysis", [
            "Fused object states with visible camera/radar evidence provenance",
            "TTC, distance, headway, stopping margin and brake-demand metrics",
            "Low, Medium, High and Critical risk prioritisation",
            "Timeline, event log, object table and rider/reviewer warning views",
        ], "Explainable, time-aware hazard evidence and warnings"),
    ]
    pad = 48
    gap = 24
    cw = (W - 2 * pad - gap) // 2
    ch = 430
    y0 = 170
    for i, (color, title, bullets, output) in enumerate(cards):
        x = pad + (i % 2) * (cw + gap)
        y = y0 + (i // 2) * (ch + gap)
        rounded(d, (x, y, x + cw, y + ch), PAPER, color, 20, 3)
        d.rounded_rectangle((x, y, x + cw, y + 58), radius=20, fill=color)
        d.rectangle((x, y + 30, x + cw, y + 58), fill=color)
        d.text((x + 22, y + 14), title, font=head_f, fill=PAPER)
        by = y + 80
        for bullet in bullets:
            d.ellipse((x + 24, by + 10, x + 34, by + 20), fill=color)
            by = draw_wrapped(d, (x + 46, by), bullet, body_f, MUTED, cw - 70, 5) + 8
        # Output strip
        sy = y + ch - 78
        d.rounded_rectangle((x + 18, sy, x + cw - 18, sy + 58), radius=12, fill=color)
        draw_wrapped(d, (x + 34, sy + 14), f"Output  ·  {output}", fonts(22, True), PAPER, cw - 70, 3)

    # Aims
    ay = y0 + 2 * (ch + gap) + 10
    d.text((pad, ay), "Report Aims", font=fonts(32, True), fill=INK)
    aims = [
        (ORANGE, "Aim 1 — End-to-end integration",
         "Document and verify how the scooter hardware, FusionApp recording, calibration, radar preparation and annotation workflow form one reproducible data pipeline."),
        (BLUE, "Aim 2 — Safety-oriented evidence",
         "Demonstrate how calibrated camera-radar observations and reviewed object states can support auditable, temporal hazard assessment for two-wheeled vehicles."),
    ]
    aw = (W - 2 * pad - gap) // 2
    ah = H - ay - 70
    for i, (color, title, text) in enumerate(aims):
        x = pad + i * (aw + gap)
        rounded(d, (x, ay + 50, x + aw, ay + 50 + ah), PAPER, color, 18, 3)
        d.text((x + 22, ay + 70), title, font=fonts(26, True), fill=color)
        draw_wrapped(d, (x + 22, ay + 120), text, body_f, MUTED, aw - 44, 6)

    out = IMG / "hardware_photo.png"
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out.name} {img.size}")


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    make_stage2()
    make_stage3()
    make_stage4()
    make_pipeline_overview()
    # Low native resolution — enlarge and sharpen
    upscale_sharpen(IMG / "hardware_architecture.png", 2.6)
    upscale_sharpen(IMG / "vod_architecture.png", 1.35)
    # Screenshots: mild sharpen only
    for name in ("annotation_interface.png", "dashboard_overview.png"):
        path = IMG / name
        im = Image.open(path).convert("RGB")
        im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=2))
        im = ImageEnhance.Contrast(im).enhance(1.05)
        im.save(path, "PNG", optimize=True)
        print(f"sharpened {name}")


if __name__ == "__main__":
    main()
