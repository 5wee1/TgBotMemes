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


async def generate_caption(query: str, style: str, context: str = "") -> str:
    """Generate a sharp, funny Russian meme caption with 3-option selection."""
    hint = STYLE_HINTS.get(style, "любой стиль юмора")
    context_block = f"\n\nКонтекст из интернета:\n{context}" if context else ""

    system = """Ты — автор самых смешных мемов рунета. Твои подписи расходятся по чатам.

ПРАВИЛА ХОРОШЕЙ ПОДПИСИ:
— Конкретность убивает банальность. "Сдал проект в 4 утра и вспомнил что не то задание" > "когда всё идёт не так"
— Неожиданный поворот в конце. Начни в одну сторону, закончи в другую.
— Антикульминация. Огромная проблема → смешное мелкое решение (или наоборот).
— Внутренний монолог. Говори от лица персонажа на картинке.
— Боль узнавания. Читатель должен сказать "блять, это же я".
— Абсурдная логика. Цепочка рассуждений которая звучит разумно но приводит в никуда.
— ЗАПРЕЩЕНО: "когда понимаешь что...", "я когда...", любые шаблонные зачины.

Напиши 3 варианта подписи разными техниками, выбери лучший.

Отвечай ТОЛЬКО валидным JSON:
{
  "captions": ["вариант 1", "вариант 2", "вариант 3"],
  "best": 0,
  "reason": "почему этот вариант лучший"
}"""

    user = f"Тема мема: «{query}»\nСтиль: {hint}{context_block}\n\nМакс 90 символов, без кавычек, без эмодзи."

    try:
        resp = await _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=300,
            temperature=1.0,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content)
        captions = data.get("captions", [])
        best_idx = int(data.get("best", 0))
        caption = captions[best_idx] if captions else query
        return caption.strip().strip('"').strip("«»") or query
    except Exception as e:
        logger.warning("Caption generation failed: %s", e)
        return query


async def generate_image_prompt(query: str, style: str, context: str = "") -> str:
    """Generate a varied, creative English image prompt."""
    hint = STYLE_HINTS.get(style, "")
    scene = random.choice(_SCENE_FLAVORS)
    visual_style = random.choice(_STYLE_FLAVORS)
    context_block = f" Context for inspiration: {context[:300]}" if context else ""

    system = (
        "You write creative image prompts for an AI image generator that makes meme visuals. "
        "Be BOLD, UNEXPECTED and VARIED. Never default to cute animals or animals in suits — "
        "prefer humans, objects, surreal scenarios, pop-culture nods, absurd juxtapositions. "
        "Use any web context provided to make the scene more topical and relatable. "
        "Each prompt must feel different from typical AI slop. Surprise the viewer. "
        "Describe ONE vivid scene: subject, expression/action, setting, lighting, composition, mood. "
        "STRICT: no 'meme', 'text', 'caption', 'font', 'write', 'word', 'letter', 'sign'. "
        "Scene must contain ZERO readable text, signs, letters or symbols. "
        "Write in English. Max 70 words. No lists, single paragraph."
    )
    user = (
        f"Topic (Russian): «{query}». Humor style: {hint}.{context_block} "
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
