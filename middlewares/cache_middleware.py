# cache_middleware.py - middleware для кешування 
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from utils.cache import Cache


class CacheMiddleware(BaseMiddleware):
    def __init__(self, cache: Cache):
        self.cache = cache
        
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        data['cache'] = self.cache
        
        return await handler(event, data)