# handlers/registration.py - обробник реєстрації 
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.db import Database
from keyboards.reply import get_main_keyboard, get_registration_keyboard
from utils.cache import Cache


class RegistrationStates(StatesGroup):
    waiting_for_confirm = State()


async def start_cmd(message: Message, db: Database, state: FSMContext):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if user:
        await message.answer(
            f"З поверненням, {user['first_name']}!",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            f"Привіт, {message.from_user.first_name}! Для використання бота потрібно зареєструватися.",
            reply_markup=get_registration_keyboard()
        )
        await state.set_state(RegistrationStates.waiting_for_confirm)


async def register_user(message: Message, db: Database, state: FSMContext):
    if message.text == "✅ Зареєструватися":
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        db.add_user(user_id, username, first_name, last_name)
        
        await message.answer(
            "Реєстрація успішна! Тепер ви можете користуватися ботом.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
    else:
        await message.answer(
            "Щоб продовжити, натисніть кнопку 'Зареєструватися'.",
            reply_markup=get_registration_keyboard()
        )


def register_registration_handlers(router: Router):
    router.message.register(start_cmd, Command(commands=["start"]))
    router.message.register(register_user, RegistrationStates.waiting_for_confirm)