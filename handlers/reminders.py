from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import Database

class ReminderStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_time = State()
    waiting_for_new_text = State()
    waiting_for_new_time = State()

def get_reminders_keyboard(reminders):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🕒 {r['remind_at']} — {r['text']}", callback_data=f"reminder_{r['id']}")]
        for r in reminders
    ])
    return keyboard

async def list_reminders(message: Message, db: Database):
    user_id = message.from_user.id
    reminders = db.get_reminders(user_id)

    if not reminders:
        await message.answer("⏰ У вас немає активних нагадувань.")
        return

    await message.answer("⏰ <b>Ваші нагадування:</b>", reply_markup=get_reminders_keyboard(reminders), parse_mode="HTML")

async def reminder_details(callback: CallbackQuery, db: Database):
    reminder_id = int(callback.data.split("_")[1])
    reminder = db.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,), fetchone=True)

    if not reminder:
        await callback.answer("⚠ Нагадування не знайдено.")
        return

    text = (
        f"⏰ <b>Нагадування</b>\n"
        f"🆔 ID: <code>{reminder['id']}</code>\n"
        f"📌 Текст: <b>{reminder['text']}</b>\n"
        f"🕒 Час: <b>{reminder['remind_at']}</b>"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_reminder_edit_keyboard(reminder_id))

def get_reminder_edit_keyboard(reminder_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏ Редагувати", callback_data=f"edit_reminder_{reminder_id}")],
        [InlineKeyboardButton(text="❌ Видалити", callback_data=f"delete_reminder_{reminder_id}")]
    ])

def get_cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Скасувати редагування", callback_data="cancel_edit")]
    ])

async def add_reminder_start(message: Message, state: FSMContext):
    await message.answer("✍ Введіть текст нагадування:")
    await state.set_state(ReminderStates.waiting_for_text)

async def add_reminder_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer("⏰ Введіть час нагадування (у форматі: <code>YYYY-MM-DD HH:MM</code>):", parse_mode="HTML")
    await state.set_state(ReminderStates.waiting_for_time)

async def add_reminder_time(message: Message, db: Database, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    text = data.get("text")
    remind_at = message.text

    db.execute("INSERT INTO reminders (user_id, text, remind_at) VALUES (?, ?, ?)", (user_id, text, remind_at), commit=True)
    await message.answer(f"✅ <b>Нагадування додано!</b>\n📌 {text}\n🕒 {remind_at}", parse_mode="HTML")
    await state.clear()

async def edit_reminder(callback: CallbackQuery, state: FSMContext):
    reminder_id = int(callback.data.split("_")[2])
    await state.update_data(reminder_id=reminder_id)
    await callback.message.edit_text("✏ Введіть новий текст нагадування:", reply_markup=get_cancel_keyboard())
    await state.set_state(ReminderStates.waiting_for_new_text)

async def edit_reminder_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer("⏰ Введіть новий час нагадування (у форматі: <code>YYYY-MM-DD HH:MM</code>):", parse_mode="HTML", reply_markup=get_cancel_keyboard())
    await state.set_state(ReminderStates.waiting_for_new_time)

async def edit_reminder_time(message: Message, db: Database, state: FSMContext):
    data = await state.get_data()
    reminder_id = data.get("reminder_id")
    text = data.get("text")
    remind_at = message.text

    db.execute("UPDATE reminders SET text = ?, remind_at = ? WHERE id = ?", 
               (text, remind_at, reminder_id), commit=True)
    
    await message.answer("✅ <b>Нагадування оновлено!</b>", parse_mode="HTML")
    await state.clear()

async def delete_reminder(callback: CallbackQuery, db: Database):
    reminder_id = int(callback.data.split("_")[2])
    db.delete_reminder(reminder_id)
    await callback.message.edit_text("❌ <b>Нагадування видалено.</b>", parse_mode="HTML")

async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ <b>Редагування скасовано.</b>", parse_mode="HTML")

def register_reminder_handlers(router: Router):
    router.message.register(list_reminders, F.text == "⏰ Мої нагадування")
    router.message.register(add_reminder_start, F.text == "➕ Додати нагадування")
    router.message.register(add_reminder_text, ReminderStates.waiting_for_text)
    router.message.register(add_reminder_time, ReminderStates.waiting_for_time)
    
    router.callback_query.register(reminder_details, F.data.startswith("reminder_"))
    router.callback_query.register(edit_reminder, F.data.startswith("edit_reminder_"))
    router.callback_query.register(delete_reminder, F.data.startswith("delete_reminder_"))
    router.callback_query.register(cancel_edit, F.data == "cancel_edit")

    router.message.register(edit_reminder_text, ReminderStates.waiting_for_new_text)
    router.message.register(edit_reminder_time, ReminderStates.waiting_for_new_time)
