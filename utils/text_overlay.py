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


def _text_width(draw, text, font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _wrap_by_pixel(draw, text, font, max_width) -> list[str]:
    """Wrap text so each line fits within max_width pixels."""
    words = text.split()
    if not words:
        return [text]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = current + " " + word
        if _text_width(draw, candidate, font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def add_caption(image_bytes: bytes, caption: str, position: str = "bottom") -> bytes:
    """Add bold white text with black outline to image."""
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    w, h = img.size

    pad_x = int(w * 0.08)
    max_text_w = w - pad_x * 2

    draw = ImageDraw.Draw(img)
    caption = caption.upper()

    # Auto-shrink font until longest line fits the available width
    font_size = max(24, min(int(h * 0.06), 58))
    while font_size >= 18:
        font = _load_font(font_size)
        lines = _wrap_by_pixel(draw, caption, font, max_text_w)
        longest = max((_text_width(draw, l, font) for l in lines), default=0)
        if longest <= max_text_w:
            break
        font_size -= 2
    else:
        font = _load_font(font_size)
        lines = _wrap_by_pixel(draw, caption, font, max_text_w)

    line_h = font_size + 10
    total_h = line_h * len(lines)
    margin_y = int(h * 0.04)

    y_start = h - total_h - margin_y if position == "bottom" else margin_y
    outline = max(2, font_size // 20)

    for i, line in enumerate(lines):
        text_w = _text_width(draw, line, font)
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
