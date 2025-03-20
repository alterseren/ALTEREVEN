# handlers/common.py - загальні обробники 
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from database.db import Database
from utils.cache import Cache


async def help_cmd(message: Message):
    help_text = """
    Доступні команди:
    /start - Почати роботу з ботом
    /help - Отримати довідку
    /profile - Переглянути свій профіль
    """
    await message.answer(help_text)


async def profile_cmd(message: Message, db: Database, cache: Cache):
    user_id = message.from_user.id
    
    cache_key = f"user_profile:{user_id}"
    user_data = cache.get(cache_key)
    
    if not user_data:
        user_data = db.get_user(user_id)
        if user_data:
            cache.set(cache_key, user_data, ttl=600)
    
    if user_data:
        profile_text = f"""
        👤 Ваш профіль:
        ID: {user_data['user_id']}
        Ім'я: {user_data['first_name']}
        {f"Прізвище: {user_data['last_name']}" if user_data['last_name'] else ""}
        {f"Username: @{user_data['username']}" if user_data['username'] else ""}
        Дата реєстрації: {user_data['registered_at']}
        """
        await message.answer(profile_text)
    else:
        await message.answer("Ви не зареєстровані. Використайте команду /start для реєстрації.")


def register_common_handlers(router: Router):
    router.message.register(help_cmd, Command(commands=["help"]))
    router.message.register(profile_cmd, Command(commands=["profile"]))