"""Generates placeholder logos (Image/Logo.png and Image/inverseLogo.png).
Replace them with your own artwork any time - just keep the file names."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "Image"
OUT.mkdir(exist_ok=True)


def font(size):
    for name in ("DejaVuSerif.ttf", "DejaVuSerif-Bold.ttf", "Georgia.ttf", "times.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_logo(color, path):
    w, h = 900, 240
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # simple balance-scale icon
    cx, top = 120, 45
    d.line([(cx, top), (cx, 190)], fill=color, width=8)
    d.line([(cx - 70, top + 15), (cx + 70, top + 15)], fill=color, width=8)
    d.line([(cx - 45, 200), (cx + 45, 200)], fill=color, width=8)
    for sx in (cx - 70, cx + 70):
        d.line([(sx, top + 15), (sx - 30, 115)], fill=color, width=4)
        d.line([(sx, top + 15), (sx + 30, 115)], fill=color, width=4)
        d.arc([sx - 32, 85, sx + 32, 145], 0, 180, fill=color, width=6)
        d.line([(sx - 32, 115), (sx + 32, 115)], fill=color, width=6)
    d.text((240, 60), "LegalEase", font=font(110), fill=color)
    img.save(path)


draw_logo((25, 25, 25, 255), OUT / "Logo.png")
draw_logo((245, 245, 245, 255), OUT / "inverseLogo.png")
print("Logos written to", OUT)
