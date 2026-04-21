import json
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

_VISUAL_STYLES = [
    "hyperrealistic photo, shallow depth of field, candid shot",
    "oil painting, dramatic chiaroscuro lighting",
    "3D Pixar-style render, cinematic composition",
    "vintage film photography, grain, washed colors",
    "comic book illustration, bold outlines, flat colors",
    "moody film noir, high contrast black and white",
    "vaporwave aesthetic, neon pink and purple gradients",
    "Soviet propaganda poster style, bold geometry",
    "blurry 2000s phone camera snapshot, flash-lit",
    "hyper-detailed digital painting, editorial illustration",
    "Renaissance oil painting applied to a modern scene",
    "retro 80s VHS screenshot look",
]

_SCENE_TYPES = [
    "a real person caught in an awkward mid-reaction moment",
    "an office worker in a surreal predicament",
    "a dramatic cinematic close-up of a single expressive face",
    "an absurd juxtaposition of two unrelated things",
    "a cozy everyday scene that has gone subtly wrong",
    "a professional/formal setting with something deeply out of place",
    "a lone figure confronting something enormous or absurd",
    "a historical or fantasy setting with a very modern problem",
    "an inanimate object treated with extreme gravitas",
    "two people having an intense silent standoff",
    "a chaotic background with one person completely unbothered",
    "a stock-photo-perfect scene but something is deeply off",
]


async def _web_search_context(query: str) -> str:
    """Fetch trending/funny context about the topic via OpenAI web search."""
    try:
        resp = await _get_client().responses.create(
            model="gpt-4o-mini-search-preview",
            tools=[{"type": "web_search_preview"}],
            input=(
                f"Найди 3-5 смешных, актуальных или неожиданных факта/ситуации по теме: «{query}». "
                "Только конкретные инсайты которые можно использовать для мема. Коротко."
            ),
        )
        return resp.output_text.strip()
    except Exception as e:
        logger.warning("Web search failed: %s", e)
        return ""


async def generate_meme_content(query: str, style: str, context: str = "") -> tuple[str, str]:
    """
    Think → pick angle → return (caption, image_prompt).
    Single GPT call with chain-of-thought reasoning in JSON.
    """
    hint = STYLE_HINTS.get(style, "любой стиль юмора")
    visual_style = random.choice(_VISUAL_STYLES)
    scene_type = random.choice(_SCENE_TYPES)
    context_block = f"\n\nАктуальный контекст из интернета:\n{context}" if context else ""

    system = """Ты — лучший создатель вирусных мемов в рунете. Ты не генеришь первое что пришло в голову.
Ты ДУМАЕШЬ прежде чем делать.

Твой процесс:
1. АНАЛИЗ — что здесь реально смешного, нелепого или болезненно узнаваемого?
2. УГЛЫ — придумай 3 разных подхода к этой теме (неожиданные, острые, не банальные)
3. ВЫБОР — выбери САМЫЙ смешной угол и объясни почему он бьёт в цель
4. ПОДПИСЬ — напиши финальную подпись на русском (1-2 строки, макс 80 символов, без кавычек, без эмодзи, всё заглавными не надо — только если для эффекта)
5. КАРТИНКА — опиши визуальную сцену для AI-генератора (английский, макс 70 слов, НОЛЬ текста/букв/надписей на картинке)

Отвечай ТОЛЬКО валидным JSON без markdown-обёртки:
{
  "analysis": "что здесь смешного и почему",
  "angles": ["угол 1", "угол 2", "угол 3"],
  "best_angle": "выбранный угол и почему он лучший",
  "caption": "финальная подпись",
  "image_prompt": "visual scene description in English"
}"""

    user = (
        f"Тема: «{query}»\n"
        f"Стиль юмора: {hint}{context_block}\n\n"
        f"Для картинки используй направление: {scene_type}\n"
        f"Визуальный стиль: {visual_style}\n"
        f"Но если другой стиль подойдёт лучше — бери его. Главное чтобы картинка усиливала шутку."
    )

    try:
        resp = await _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=500,
            temperature=1.0,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content.strip()
        data = json.loads(raw)
        caption = data.get("caption", "").strip().strip('"').strip("«»") or query
        image_prompt = data.get("image_prompt", "").strip()
        logger.debug("Meme reasoning: %s", data.get("best_angle", ""))
        if not image_prompt:
            raise ValueError("empty image_prompt")
        return caption, image_prompt
    except Exception as e:
        logger.warning("generate_meme_content failed: %s", e)
        return query, f"Funny scene about {query}, {scene_type}, {visual_style}, no text no letters"


# Keep these for backward compat (not used internally anymore)
async def generate_caption(query: str, style: str, context: str = "") -> str:
    caption, _ = await generate_meme_content(query, style, context)
    return caption


async def generate_image_prompt(query: str, style: str, context: str = "") -> str:
    _, prompt = await generate_meme_content(query, style, context)
    return prompt
