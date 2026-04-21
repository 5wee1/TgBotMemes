import asyncio
import logging
import random
from io import BytesIO

import httpx
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, CallbackQuery, BufferedInputFile, InputMediaPhoto
)

from database import repository as db
from handlers.states import MemeGen
from providers.image_provider import image_provider, ImageGenerationError
from utils.content_filter import is_blocked
from utils.keyboards import styles_kb, meme_actions_kb, main_menu_kb
from utils.prompt_builder import build_prompt, prompt_hash, STYLES, get_style_label
from utils.text_overlay import add_caption

logger = logging.getLogger(__name__)
router = Router()


# ── helpers ────────────────────────────────────────────────────────────────

async def _download_image(url: str) -> bytes:
    if url.startswith("data:image"):
        import base64
        b64 = url.split(",", 1)[1]
        return base64.b64decode(b64)
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


async def _generate_and_send(
    bot: Bot,
    chat_id: int,
    user_id: int,
    query: str,
    style_key: str,
    plan: str,
    seed: int | None = None,
    status_message: Message | None = None,
) -> int | None:
    """Core generation routine. Returns meme_id or None on failure."""
    prompt, used_seed, quality = build_prompt(query, style_key, seed, plan)
    phash = prompt_hash(prompt)

    allowed, reason = await db.can_generate(user_id)
    if not allowed:
        text = {
            "daily_limit": "⛔ Дневной лимит исчерпан (3 мема). Купи пакет или приходи завтра.",
            "no_credits": "⛔ Генерации закончились. Пополни баланс в /plans.",
            "banned": "🚫 Аккаунт заблокирован.",
        }.get(reason, "⛔ Генерация недоступна.")
        if status_message:
            await status_message.edit_text(text)
        else:
            await bot.send_message(chat_id, text)
        return None

    await db.consume_generation(user_id, reason)
    meme_id = await db.save_meme(user_id, query, style_key, phash)

    try:
        image_url = await image_provider.generate_image(
            prompt=prompt,
            seed=used_seed,
            quality=quality,
        )
        raw_bytes = await _download_image(image_url)
        image_bytes = add_caption(raw_bytes, query)
    except ImageGenerationError as e:
        logger.error("ImageGenerationError user=%s: %s", user_id, e)
        text = "😔 Не удалось создать мем. Попробуй ещё раз или переформулируй запрос."
        if status_message:
            await status_message.edit_text(text)
        else:
            await bot.send_message(chat_id, text)
        return None

    style_label = get_style_label(style_key)
    caption = f"<b>{style_label}</b>  |  <i>{query}</i>"

    if status_message:
        try:
            await status_message.delete()
        except Exception:
            pass

    sent = await bot.send_photo(
        chat_id=chat_id,
        photo=BufferedInputFile(image_bytes, filename="meme.png"),
        caption=caption,
        parse_mode="HTML",
        reply_markup=meme_actions_kb(meme_id),
    )
    file_id = sent.photo[-1].file_id
    await db.update_meme_file_id(meme_id, file_id)
    await db.log_event(user_id, "meme_generated", {"meme_id": meme_id, "style": style_key})
    return meme_id


# ── text input → style picker ──────────────────────────────────────────────

@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_input(message: Message, state: FSMContext):
    query = message.text.strip()
    if not query:
        return

    if is_blocked(query):
        await message.answer("🚫 Не могу сгенерировать это. Сформулируй иначе.")
        return

    await state.set_state(MemeGen.waiting_style)
    await state.update_data(query=query)
    await message.answer(
        f"🎨 Выбери стиль для мема:\n<i>{query}</i>",
        parse_mode="HTML",
        reply_markup=styles_kb(query),
    )


# ── style selected ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("style:"))
async def handle_style_choice(call: CallbackQuery, state: FSMContext, bot: Bot):
    _, style_key, query_short = call.data.split(":", 2)

    fsm_data = await state.get_data()
    query = fsm_data.get("query", query_short)
    await state.clear()

    user = call.from_user
    db_user = await db.get_user(user.id)
    plan = db_user["plan"] if db_user else "free"

    await call.message.edit_text(f"⏳ Генерирую мем…\n<i>{query}</i>", parse_mode="HTML")

    await _generate_and_send(
        bot=bot,
        chat_id=call.message.chat.id,
        user_id=user.id,
        query=query,
        style_key=style_key,
        plan=plan,
        status_message=call.message,
    )
    await call.answer()


# ── regen ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("regen:"))
async def handle_regen(call: CallbackQuery, bot: Bot):
    _, count_str, meme_id_str = call.data.split(":")
    count = int(count_str)
    meme_id = int(meme_id_str)

    user_id = call.from_user.id
    memes = await db.get_user_memes(user_id, limit=50)
    source = next((m for m in memes if m["id"] == meme_id), None)
    if not source:
        await call.answer("Мем не найден.", show_alert=True)
        return

    db_user = await db.get_user(user_id)
    plan = db_user["plan"] if db_user else "free"

    await call.answer(f"Генерирую {count} вариант(а)…")

    for _ in range(count):
        seed = random.randint(1, 999999)
        status = await call.message.answer("⏳ Генерирую…")
        await _generate_and_send(
            bot=bot,
            chat_id=call.message.chat.id,
            user_id=user_id,
            query=source["query"],
            style_key=source["style"],
            plan=plan,
            seed=seed,
            status_message=status,
        )


# ── edit idea ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("edit_idea:"))
async def handle_edit_idea(call: CallbackQuery, state: FSMContext):
    meme_id = int(call.data.split(":")[1])
    await state.set_state(MemeGen.waiting_new_idea)
    await state.update_data(source_meme_id=meme_id)
    await call.message.answer("✏️ Напиши новую формулировку для мема:")
    await call.answer()


@router.message(MemeGen.waiting_new_idea)
async def handle_new_idea(message: Message, state: FSMContext, bot: Bot):
    new_query = message.text.strip()
    if is_blocked(new_query):
        await message.answer("🚫 Не могу сгенерировать это. Сформулируй иначе.")
        await state.clear()
        return

    fsm_data = await state.get_data()
    meme_id = fsm_data.get("source_meme_id")
    await state.clear()

    user_id = message.from_user.id
    db_user = await db.get_user(user_id)
    plan = db_user["plan"] if db_user else "free"

    style_key = "classic"
    if meme_id:
        memes = await db.get_user_memes(user_id, limit=50)
        source = next((m for m in memes if m["id"] == meme_id), None)
        if source:
            style_key = source["style"]

    status = await message.answer("⏳ Генерирую мем с новой идеей…")
    await _generate_and_send(
        bot=bot,
        chat_id=message.chat.id,
        user_id=user_id,
        query=new_query,
        style_key=style_key,
        plan=plan,
        status_message=status,
    )


# ── series ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("series:"))
async def handle_series(call: CallbackQuery, bot: Bot):
    meme_id = int(call.data.split(":")[1])
    user_id = call.from_user.id

    memes = await db.get_user_memes(user_id, limit=50)
    source = next((m for m in memes if m["id"] == meme_id), None)
    if not source:
        await call.answer("Мем не найден.", show_alert=True)
        return

    db_user = await db.get_user(user_id)
    plan = db_user["plan"] if db_user else "free"

    await call.answer("🧩 Генерирую серию из 5 мемов…")
    status = await call.message.answer("🧩 Генерирую серию из 5 мемов, подожди…")

    for i in range(5):
        seed = random.randint(1, 999999)
        await _generate_and_send(
            bot=bot,
            chat_id=call.message.chat.id,
            user_id=user_id,
            query=source["query"],
            style_key=source["style"],
            plan=plan,
            seed=seed,
        )
        if i == 0:
            try:
                await status.delete()
            except Exception:
                pass


# ── favorite ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("fav:"))
async def handle_favorite(call: CallbackQuery):
    meme_id = int(call.data.split(":")[1])
    is_fav = await db.toggle_favorite(meme_id, call.from_user.id)
    text = "💛 Добавлено в избранное!" if is_fav else "🗑 Убрано из избранного."
    await call.answer(text)
    try:
        await call.message.edit_reply_markup(
            reply_markup=meme_actions_kb(meme_id, is_favorite=is_fav)
        )
    except Exception:
        pass


# ── share ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("share:"))
async def handle_share(call: CallbackQuery, bot: Bot):
    meme_id = int(call.data.split(":")[1])
    user_id = call.from_user.id
    memes = await db.get_user_memes(user_id, limit=50)
    source = next((m for m in memes if m["id"] == meme_id), None)
    if not source:
        await call.answer("Мем не найден.", show_alert=True)
        return

    tag_map = {
        "classic": "#классикамем #мем #юмор",
        "shitpost": "#шитпост #мем #рандом",
        "sarcasm": "#сарказм #ирония #мем",
        "smart": "#умныймем #ирония #мысли",
        "marketing": "#маркетинг #бизнес #мем",
        "random": "#мем #юмор #рандом",
    }
    tags = tag_map.get(source["style"], "#мем #юмор")
    share_text = f"😂 {source['query']}\n\n{tags}\n\nСоздано в @{(await bot.get_me()).username}"
    await call.message.answer(f"📤 Текст для репоста:\n\n<code>{share_text}</code>", parse_mode="HTML")
    await call.answer()


# ── delete ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("delete:"))
async def handle_delete(call: CallbackQuery):
    meme_id = int(call.data.split(":")[1])
    await db.delete_meme(meme_id, call.from_user.id)
    try:
        await call.message.delete()
    except Exception:
        await call.message.edit_caption("🗑 Удалено")
    await call.answer("Мем удалён.")


# ── cancel / main menu ─────────────────────────────────────────────────────

@router.callback_query(F.data == "cancel")
async def handle_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Отменено.", reply_markup=None)
    await call.answer()


@router.callback_query(F.data == "main_menu")
async def handle_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "🏠 Главное меню",
        reply_markup=main_menu_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "show_styles")
async def handle_show_styles(call: CallbackQuery, state: FSMContext):
    await call.message.answer(
        "Напиши текст мема, и я покажу варианты стилей.",
        reply_markup=main_menu_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "help")
async def handle_help_cb(call: CallbackQuery):
    from handlers.start import WELCOME_TEXT
    await call.message.answer(WELCOME_TEXT, parse_mode="HTML")
    await call.answer()
