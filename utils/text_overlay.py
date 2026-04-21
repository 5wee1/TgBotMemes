"""Overlay meme-style caption on an image using Pillow."""
import textwrap
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Font search order — first match wins
_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/impact.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_PATHS:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def add_caption(image_bytes: bytes, caption: str, position: str = "bottom") -> bytes:
    """
    Add bold white text with black outline to image.
    position: 'bottom' | 'top' | 'both' (top half + bottom half split by ' | ')
    """
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    w, h = img.size

    # Auto font size: ~8% of image height, capped
    font_size = max(32, min(int(h * 0.08), 80))
    font = _load_font(font_size)

    draw = ImageDraw.Draw(img)

    caption = caption.upper()
    max_chars = max(10, int(w / (font_size * 0.55)))
    lines = textwrap.wrap(caption, width=max_chars) or [caption]

    line_h = font_size + 8
    total_h = line_h * len(lines)
    margin = int(h * 0.03)

    if position == "bottom":
        y_start = h - total_h - margin
    else:
        y_start = margin

    outline = max(2, font_size // 18)

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (w - text_w) // 2
        y = y_start + i * line_h

        for dx in range(-outline, outline + 1):
            for dy in range(-outline, outline + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))

    out = BytesIO()
    img.save(out, format="PNG", optimize=True)
    return out.getvalue()
