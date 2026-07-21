from pathlib import Path
from PIL import Image, ImageFilter

ROOT = Path(r"D:\Github\two-wheeler-hazard-detection")
IMG = ROOT / "assets" / "img"
CANVAS_W, CANVAS_H = 1800, 1400
BG = (255, 255, 255)

JOBS = [
    ("hardware_photo_1.png", "about_pipeline.png"),
    ("scooter_photo.png", "about_scooter.png"),
]


def fit_on_canvas(src: Path, dst: Path) -> None:
    im = Image.open(src).convert("RGB")
    sw, sh = im.size
    scale = min(CANVAS_W / sw, CANVAS_H / sh)
    nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
    resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
    if scale > 1.0:
        resized = resized.filter(ImageFilter.UnsharpMask(radius=1.4, percent=140, threshold=2))
    else:
        resized = resized.filter(ImageFilter.UnsharpMask(radius=0.8, percent=80, threshold=3))
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), BG)
    x = (CANVAS_W - nw) // 2
    y = (CANVAS_H - nh) // 2
    canvas.paste(resized, (x, y))
    canvas.save(dst, "PNG", optimize=True)
    print(f"saved {dst} ({canvas.size[0]}x{canvas.size[1]}) scale={scale:.4f}")


for src_name, dst_name in JOBS:
    fit_on_canvas(IMG / src_name, IMG / dst_name)

print("--- verification ---")
for name in ("about_pipeline.png", "about_scooter.png"):
    p = IMG / name
    with Image.open(p) as im:
        ok = im.size == (CANVAS_W, CANVAS_H)
        print(f"{p}: {im.size[0]}x{im.size[1]} {'OK' if ok else 'FAIL'}")
        if not ok:
            raise SystemExit(1)
