import hashlib
import random
from typing import Optional

STYLES: dict[str, dict] = {
    "classic":    {"label": "😂 Классика",      "desc": "classic internet meme, bold Impact font, top and bottom caption"},
    "shitpost":   {"label": "🤡 Шитпост",       "desc": "absurdist shitpost meme, chaotic, surreal, weird humor"},
    "sarcasm":    {"label": "😈 Сарказм",        "desc": "sarcastic meme, dark humor, ironic expression"},
    "smart":      {"label": "🧠 Умный/Ироничный","desc": "intellectual ironic meme, witty, sophisticated humor"},
    "marketing":  {"label": "💼 Маркетинг",      "desc": "viral marketing meme, relatable, branded, professional look"},
    "random":     {"label": "🎲 Случайный",      "desc": None},
}

_QUALITY_MAP = {
    "free":    "standard",
    "starter": "standard",
    "pro":     "hd",
    "ultra":   "hd",
}


def build_prompt(query: str, style_key: str, variant_seed: Optional[int] = None, plan: str = "free") -> tuple[str, int, str]:
    """Returns (prompt, seed, quality)."""
    if style_key == "random":
        real_style = random.choice([k for k in STYLES if k != "random"])
    else:
        real_style = style_key

    style_desc = STYLES[real_style]["desc"]
    seed = variant_seed if variant_seed is not None else random.randint(1, 999999)
    quality = _QUALITY_MAP.get(plan, "standard")

    prompt = (
        f"Create a funny meme image. Style: {style_desc}. "
        f'Caption in Russian: "{query}". '
        "Make the caption large, bold, highly readable. "
        "High contrast background, clean typography, no watermarks. "
        "meme format, funny, clear message. "
        "safe for work, no gore, no explicit content."
    )
    return prompt, seed, quality


def prompt_hash(prompt: str) -> str:
    return hashlib.md5(prompt.encode()).hexdigest()[:16]


def get_style_label(style_key: str) -> str:
    return STYLES.get(style_key, {}).get("label", style_key)
