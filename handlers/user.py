# handlers/user.py - обробники дій користувача 
from aiogram import Router, F
from aiogram.types import Message

from database.db import Database
from utils.cache import Cache
from keyboards.reply import get_main_keyboard


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


async def profile_button(message: Message, db: Database, cache: Cache):
    if message.text == "👤 Профіль":
        await profile_cmd(message, db, cache)


async def info_button(message: Message):
    if message.text == "ℹ️ Інформація":
        await message.answer("Це демонстраційний бот на aiogram з SQLite та кешуванням.")


async def contacts_button(message: Message):
    if message.text == "📞 Контакти":
        await message.answer("Для зв'язку: example@example.com")


def register_user_handlers(router: Router):
    router.message.register(profile_button, F.text == "👤 Профіль")
    router.message.register(info_button, F.text == "ℹ️ Інформація")
    router.message.register(contacts_button, F.text == "📞 Контакти")