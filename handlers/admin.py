import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import config
from database import repository as db
from handlers.states import MemeGen
from utils.keyboards import confirm_kb

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids


# ── guard filter ───────────────────────────────────────────────────────────

class AdminFilter:
    def __call__(self, message: Message) -> bool:
        return is_admin(message.from_user.id)


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    stats = await db.get_stats()
    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"📅 DAU (24ч): <b>{stats['dau']}</b>\n"
        f"🖼 Мемов сегодня: <b>{stats['generated_today']}</b>\n"
        f"💰 Выручка: <b>{stats['revenue'] / 100:.0f} ₽</b>"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("give"))
async def cmd_give(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    # /give @username 100
    if len(parts) < 3:
        await message.answer("Использование: /give @username 100")
        return
    username = parts[1].lstrip("@")
    try:
        amount = int(parts[2])
    except ValueError:
        await message.answer("Сумма должна быть числом.")
        return

    user = await db.find_user_by_username(username)
    if not user:
        await message.answer(f"Пользователь @{username} не найден.")
        return

    await db.add_credits(user["user_id"], amount)
    await db.log_event(message.from_user.id, "admin_give", {"target": user["user_id"], "amount": amount})
    await message.answer(f"✅ Начислено {amount} генераций пользователю @{username}.")


@router.message(Command("ban"))
async def cmd_ban(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /ban @username")
        return
    username = parts[1].lstrip("@")
    user = await db.find_user_by_username(username)
    if not user:
        await message.answer(f"Пользователь @{username} не найден.")
        return
    await db.ban_user(user["user_id"], True)
    await message.answer(f"🚫 @{username} заблокирован.")


@router.message(Command("unban"))
async def cmd_unban(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /unban @username")
        return
    username = parts[1].lstrip("@")
    user = await db.find_user_by_username(username)
    if not user:
        await message.answer(f"Пользователь @{username} не найден.")
        return
    await db.ban_user(user["user_id"], False)
    await message.answer(f"✅ @{username} разблокирован.")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(MemeGen.waiting_broadcast)
    await message.answer(
        "📢 Введи текст рассылки (HTML поддерживается).\n"
        "После ввода я покажу предпросмотр и попрошу подтвердить."
    )


@router.message(MemeGen.waiting_broadcast)
async def handle_broadcast_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    text = message.text or message.caption or ""
    await state.update_data(broadcast_text=text)
    await message.answer(
        f"<b>Предпросмотр:</b>\n\n{text}\n\n"
        "Подтвердить рассылку?",
        parse_mode="HTML",
        reply_markup=confirm_kb("broadcast"),
    )


@router.callback_query(F.data == "confirm:broadcast")
async def handle_broadcast_confirm(call: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_admin(call.from_user.id):
        await call.answer("Нет прав.", show_alert=True)
        return

    fsm_data = await state.get_data()
    text = fsm_data.get("broadcast_text", "")
    await state.clear()

    import aiosqlite
    sent_count = 0
    fail_count = 0

    async with aiosqlite.connect(config.db_path) as db_conn:
        db_conn.row_factory = aiosqlite.Row
        rows = await (await db_conn.execute(
            "SELECT user_id FROM users WHERE is_banned=0"
        )).fetchall()

    await call.message.edit_text("📢 Рассылка запущена…")

    for row in rows:
        try:
            await bot.send_message(row["user_id"], text, parse_mode="HTML")
            sent_count += 1
        except Exception:
            fail_count += 1

    await db.log_event(call.from_user.id, "broadcast", {"sent": sent_count, "fail": fail_count})
    await call.message.answer(
        f"✅ Рассылка завершена.\nОтправлено: {sent_count}\nОшибок: {fail_count}"
    )
    await call.answer()
