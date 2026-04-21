import hashlib
import random
from typing import Optional

STYLES: dict[str, dict] = {
    "classic":    {"label": "😂 Классика",       "desc": "classic internet meme scene, expressive characters, bold visual humor"},
    "shitpost":   {"label": "🤡 Шитпост",        "desc": "absurdist surreal shitpost meme, chaotic weird imagery, low effort aesthetic"},
    "sarcasm":    {"label": "😈 Сарказм",         "desc": "sarcastic dark humor scene, ironic expression, deadpan reaction face"},
    "smart":      {"label": "🧠 Умный/Ироничный", "desc": "intellectual ironic scene, sophisticated visual metaphor, witty imagery"},
    "marketing":  {"label": "💼 Маркетинг",       "desc": "viral marketing meme scene, relatable situation, clean professional look"},
    "random":     {"label": "🎲 Случайный",       "desc": None},
}

_QUALITY_MAP = {
    "free":    "standard",
    "starter": "standard",
    "pro":     "hd",
    "ultra":   "hd",
}


def build_prompt(query: str, style_key: str, variant_seed: Optional[int] = None, plan: str = "free") -> tuple[str, int, str]:
    """Returns (prompt, seed, quality). Prompt has NO text — caption is overlaid via Pillow."""
    if style_key == "random":
        real_style = random.choice([k for k in STYLES if k != "random"])
    else:
        real_style = style_key

    style_desc = STYLES[real_style]["desc"]
    seed = variant_seed if variant_seed is not None else random.randint(1, 999999)
    quality = _QUALITY_MAP.get(plan, "standard")

    prompt = (
        f"Funny meme image, no text, no words, no letters anywhere. "
        f"Style: {style_desc}. "
        f"Theme: {query}. "
        f"Expressive faces, high contrast, clean composition, meme aesthetic. "
        f"Safe for work, no explicit content."
    )
    return prompt, seed, quality


def prompt_hash(prompt: str) -> str:
    return hashlib.md5(prompt.encode()).hexdigest()[:16]


def get_style_label(style_key: str) -> str:
    return STYLES.get(style_key, {}).get("label", style_key)
