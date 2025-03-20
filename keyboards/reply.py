from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профіль")],
            [KeyboardButton(text="📅 Мої події"), KeyboardButton(text="⏰ Мої нагадування")],
            [KeyboardButton(text="➕ Додати подію"), KeyboardButton(text="➕ Додати нагадування")],
            [KeyboardButton(text="ℹ️ Інформація"), KeyboardButton(text="📞 Контакти")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_registration_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Зареєструватися")]
        ],
        resize_keyboard=True
    )
    return keyboard
