from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from database import repository as db
from utils.keyboards import my_memes_nav_kb, meme_actions_kb

router = Router()
PAGE_SIZE = 5


async def _send_memes_page(target, user_id: int, offset: int, mode: str):
    """mode: 'all' | 'fav'"""
    if mode == "fav":
        memes = await db.get_favorites(user_id, limit=PAGE_SIZE, offset=offset)
        total_all = await db.get_favorites(user_id, limit=9999)
        total = len(total_all)
        title = "⭐ Избранное"
    else:
        memes = await db.get_user_memes(user_id, limit=PAGE_SIZE, offset=offset)
        total_all = await db.get_user_memes(user_id, limit=9999)
        total = len(total_all)
        title = "🧰 Мои мемы"

    if not memes:
        text = f"{title}\n\nПусто."
        if isinstance(target, Message):
            await target.answer(text)
        else:
            await target.message.edit_text(text, reply_markup=my_memes_nav_kb(offset, total, PAGE_SIZE))
        return

    if isinstance(target, Message):
        await target.answer(f"{title} ({total} шт.):")
    else:
        await target.message.edit_text(
            f"{title} ({total} шт.):",
            reply_markup=my_memes_nav_kb(offset, total, PAGE_SIZE),
        )

    for meme in memes:
        caption = f"<b>{meme['style']}</b>  |  <i>{meme['query']}</i>"
        is_fav = bool(meme["is_favorite"])
        if meme.get("file_id"):
            if isinstance(target, Message):
                await target.answer_photo(
                    photo=meme["file_id"],
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=meme_actions_kb(meme["id"], is_fav),
                )
            else:
                await target.message.answer_photo(
                    photo=meme["file_id"],
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=meme_actions_kb(meme["id"], is_fav),
                )

    kb = my_memes_nav_kb(offset, total, PAGE_SIZE)
    if isinstance(target, Message):
        await target.answer("Навигация:", reply_markup=kb)


@router.message(Command("mymemes"))
@router.callback_query(F.data == "my_memes")
async def show_my_memes(event, state=None):
    if isinstance(event, Message):
        await _send_memes_page(event, event.from_user.id, 0, "all")
    else:
        await _send_memes_page(event, event.from_user.id, 0, "all")
        await event.answer()


@router.message(Command("favorites"))
@router.callback_query(F.data == "favorites")
async def show_favorites(event, state=None):
    if isinstance(event, Message):
        await _send_memes_page(event, event.from_user.id, 0, "fav")
    else:
        await _send_memes_page(event, event.from_user.id, 0, "fav")
        await event.answer()


@router.callback_query(F.data.startswith("memes_page:"))
async def handle_page(call: CallbackQuery):
    offset = int(call.data.split(":")[1])
    await _send_memes_page(call, call.from_user.id, offset, "all")
    await call.answer()
