from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.prompt_builder import STYLES


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 Выбрать стиль", callback_data="show_styles"),
         InlineKeyboardButton(text="⚡ Пакеты/Подписка", callback_data="show_plans")],
        [InlineKeyboardButton(text="🧰 Мои мемы", callback_data="my_memes"),
         InlineKeyboardButton(text="⭐ Избранное", callback_data="favorites")],
        [InlineKeyboardButton(text="🔗 Реферальная ссылка", callback_data="referral"),
         InlineKeyboardButton(text="🆘 Помощь", callback_data="help")],
    ])


def styles_kb(query: str) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for key, info in STYLES.items():
        row.append(InlineKeyboardButton(text=info["label"], callback_data=f"style:{key}:{query[:50]}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def meme_actions_kb(meme_id: int, is_favorite: bool = False) -> InlineKeyboardMarkup:
    fav_text = "💛 В избранном" if is_favorite else "✅ В избранное"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Ещё 1", callback_data=f"regen:1:{meme_id}"),
         InlineKeyboardButton(text="🔁 Ещё 3", callback_data=f"regen:3:{meme_id}")],
        [InlineKeyboardButton(text="✏️ Изменить идею", callback_data=f"edit_idea:{meme_id}"),
         InlineKeyboardButton(text="🧩 Серия из 5", callback_data=f"series:{meme_id}")],
        [InlineKeyboardButton(text=fav_text, callback_data=f"fav:{meme_id}"),
         InlineKeyboardButton(text="📤 Поделиться", callback_data=f"share:{meme_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete:{meme_id}")],
    ])


def plans_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔹 Starter — 300 ген/мес · 299 ₽", callback_data="buy:starter")],
        [InlineKeyboardButton(text="🔷 Pro — 1500 ген/мес · 799 ₽", callback_data="buy:pro")],
        [InlineKeyboardButton(text="💎 Ultra — Fair-use · 1499 ₽/мес", callback_data="buy:ultra")],
        [InlineKeyboardButton(text="📦 50 генераций · 500 ₽", callback_data="buy:pack50")],
        [InlineKeyboardButton(text="📦 200 генераций · 1000 ₽", callback_data="buy:pack200")],
        [InlineKeyboardButton(text="❌ Назад", callback_data="cancel")],
    ])


def my_memes_nav_kb(offset: int, total: int, page_size: int = 5) -> InlineKeyboardMarkup:
    buttons = []
    nav = []
    if offset > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"memes_page:{offset - page_size}"))
    if offset + page_size < total:
        nav.append(InlineKeyboardButton(text="➡️ Далее", callback_data=f"memes_page:{offset + page_size}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_kb(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data=f"confirm:{action}"),
         InlineKeyboardButton(text="❌ Нет", callback_data="cancel")],
    ])
