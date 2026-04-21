import time
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from config import config


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self):
        self._last_request: dict[int, float] = defaultdict(float)
        self._active: dict[int, int] = defaultdict(int)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.monotonic()
        elapsed = now - self._last_request[user_id]

        if elapsed < config.rate_limit_seconds:
            wait = config.rate_limit_seconds - elapsed
            await event.answer(f"⏳ Подожди ещё {wait:.0f} сек перед следующим запросом.")
            return

        if self._active[user_id] >= config.max_concurrent_per_user:
            await event.answer("⏳ У тебя уже идёт генерация. Дождись результата.")
            return

        self._last_request[user_id] = now
        self._active[user_id] += 1
        try:
            return await handler(event, data)
        finally:
            self._active[user_id] -= 1
