from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from database.repository import get_or_create_user
from utils.keyboards import main_menu_kb

router = Router()

WELCOME_TEXT = (
    "👋 Привет! Я генерирую мемы по твоему тексту.\n\n"
    "Напиши, например: <code>мем про понедельник</code>\n\n"
    "Я выберу стиль — и через несколько секунд мем готов 🎨"
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    args = message.text.split(maxsplit=1)
    ref_code = args[1].strip() if len(args) > 1 else None

    referred_by = None
    if ref_code and ref_code.startswith("ref_"):
        from database.repository import get_db
        import aiosqlite
        async with aiosqlite.connect(__import__("config").config.db_path) as db:
            db.row_factory = aiosqlite.Row
            row = await (await db.execute(
                "SELECT user_id FROM users WHERE ref_code=?", (ref_code[4:],)
            )).fetchone()
            if row and row["user_id"] != message.from_user.id:
                referred_by = row["user_id"]

    await get_or_create_user(message.from_user.id, message.from_user.username, referred_by)
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb(), parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "🆘 <b>Помощь</b>\n\n"
        "Просто напиши текст — бот создаст мем.\n\n"
        "<b>Команды:</b>\n"
        "/start — главное меню\n"
        "/mymemes — мои мемы\n"
        "/favorites — избранное\n"
        "/plans — пакеты и подписки\n"
        "/referral — моя реферальная ссылка\n"
        "/help — эта справка\n\n"
        "<b>Лимиты (Free):</b> 5 мемов в день\n"
        "Купи пакет или подписку для большего 🚀"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())
