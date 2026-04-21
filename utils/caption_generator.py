import logging
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
    """Generate a short funny Russian meme caption via GPT-4o-mini."""
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
