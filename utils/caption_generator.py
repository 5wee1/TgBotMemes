import logging
import random
from openai import AsyncOpenAI
from config import config

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=config.openai_api_key)
    return _client


STYLE_HINTS = {
    "classic":   "классический интернет-мем, универсальный юмор",
    "shitpost":  "абсурдный шитпост, случайный бред, несерьёзно",
    "sarcasm":   "саркастично, иронично, с подтекстом",
    "smart":     "умный юмор, тонкая ирония, философски",
    "marketing": "маркетинговый мем, бизнес-юмор, узнаваемая ситуация",
    "random":    "любой стиль юмора",
}


async def generate_caption(query: str, style: str) -> str:
    """Short funny Russian meme caption."""
    hint = STYLE_HINTS.get(style, "")
    system = (
        "Ты генератор подписей для мемов. "
        "Отвечай ТОЛЬКО текстом подписи — без кавычек, без объяснений, без эмодзи. "
        "Подпись короткая: 1-2 строки, максимум 80 символов. "
        "Язык: русский. Стиль: смешно, метко, по теме."
    )
    user = f"Тема мема: «{query}». Стиль: {hint}. Придумай подпись."

    try:
        resp = await _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=60,
            temperature=0.9,
        )
        caption = resp.choices[0].message.content.strip().strip('"').strip("«»")
        return caption or query
    except Exception as e:
        logger.warning("Caption generation failed: %s", e)
        return query


_SCENE_FLAVORS = [
    "real people caught mid-reaction in an everyday situation",
    "an office worker in an absurd predicament",
    "a teenager in a chaotic home scene",
    "a surreal dreamlike scenario with floating objects",
    "a cinematic close-up of a dramatic facial expression",
    "a cursed low-quality photo vibe, flash-lit, 2000s phone camera",
    "a renaissance oil painting parody of a modern situation",
    "a retro 80s commercial still, saturated colors",
    "a gritty documentary-style street photo",
    "a cozy domestic scene gone wrong",
    "a sci-fi retro-futuristic setting with a mundane problem",
    "a professional stock-photo gone weirdly wrong",
    "a fantasy medieval scene but with modern complaints",
    "two characters having an intense silent confrontation",
    "an inanimate object anthropomorphized in a dramatic way",
    "a child-like crayon drawing style but highly detailed",
    "a horror-movie atmosphere applied to something trivial",
]

_STYLE_FLAVORS = [
    "hyperrealistic photograph, shallow depth of field",
    "oil painting, dramatic lighting",
    "3D Pixar-style render, cinematic",
    "vintage film photography, grainy",
    "comic book illustration, bold colors",
    "moody cinematic still, film noir lighting",
    "vaporwave aesthetic, neon gradients",
    "watercolor illustration, soft edges",
    "low-poly 3D render",
    "hyper-detailed digital painting",
    "Soviet-era poster style",
    "blurry phone-camera snapshot aesthetic",
]


async def generate_image_prompt(query: str, style: str) -> str:
    """Generate a varied, creative English image prompt."""
    hint = STYLE_HINTS.get(style, "")
    scene = random.choice(_SCENE_FLAVORS)
    visual_style = random.choice(_STYLE_FLAVORS)

    system = (
        "You write creative image prompts for an AI image generator that makes meme visuals. "
        "Be BOLD, UNEXPECTED and VARIED. Never default to cute animals or animals in suits — "
        "prefer humans, objects, surreal scenarios, pop-culture nods, absurd juxtapositions. "
        "Each prompt must feel different from typical AI slop. Surprise the viewer. "
        "Describe ONE vivid scene: subject, expression/action, setting, lighting, composition, mood. "
        "STRICT: no 'meme', 'text', 'caption', 'font', 'write', 'word', 'letter', 'sign'. "
        "Scene must contain ZERO readable text, signs, letters or symbols. "
        "Write in English. Max 70 words. No lists, single paragraph."
    )
    user = (
        f"Topic (Russian): «{query}». Humor style: {hint}. "
        f"Base the scene on this direction: {scene}. Visual style: {visual_style}. "
        f"But feel free to twist it into something more surprising. Describe the scene."
    )

    try:
        resp = await _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=140,
            temperature=1.1,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("Image prompt generation failed: %s", e)
        return f"Funny unexpected scene about {query}, {scene}, {visual_style}, no text"
