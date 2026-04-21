from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import repository as db

router = Router()


@router.message(Command("referral"))
@router.callback_query(F.data == "referral")
async def show_referral(event, bot: Bot):
    if isinstance(event, Message):
        user_id = event.from_user.id
        answer = event.answer
    else:
        user_id = event.from_user.id
        answer = event.message.answer
        await event.answer()

    user = await db.get_user(user_id)
    if not user:
        return

    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user['ref_code']}"

    text = (
        "🔗 <b>Реферальная программа</b>\n\n"
        f"Твоя ссылка:\n<code>{ref_link}</code>\n\n"
        "За каждого друга, который сделает хотя бы 1 мем — ты получаешь <b>+10 генераций</b>!\n\n"
        "Поделись ссылкой и зарабатывай мемы 🎉"
    )
    await answer(text, parse_mode="HTML")
