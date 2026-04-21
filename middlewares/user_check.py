from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from database.repository import get_or_create_user


class UserCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            fu = event.from_user
            user = await get_or_create_user(fu.id, fu.username)
            if user.get("is_banned"):
                if isinstance(event, Message):
                    await event.answer("🚫 Ваш аккаунт заблокирован.")
                else:
                    await event.answer("🚫 Заблокирован.", show_alert=True)
                return
        data["db_user"] = user
        return await handler(event, data)
