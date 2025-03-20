from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import Database


class EventStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_date = State()
    waiting_for_description = State()
    waiting_for_new_title = State()
    waiting_for_new_date = State()
    waiting_for_new_description = State()

# Функція створення клавіатури з подіями
def get_events_keyboard(events):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📆 {event['event_date']} — {event['title']}", callback_data=f"event_{event['id']}")]
        for event in events
    ])
    return keyboard


async def list_events(message: Message, db: Database):
    user_id = message.from_user.id
    events = db.get_events(user_id)

    if not events:
        await message.answer("📅 У вас немає запланованих подій.")
        return

    await message.answer("📅 <b>Ваші події:</b>", reply_markup=get_events_keyboard(events), parse_mode="HTML")


async def event_details(callback: CallbackQuery, db: Database):
    event_id = int(callback.data.split("_")[1])
    event = db.execute("SELECT * FROM events WHERE id = ?", (event_id,), fetchone=True)

    if not event:
        await callback.answer("⚠ Подія не знайдена.")
        return

    text = (
        f"📅 <b>Подія</b>\n"
        f"🆔 ID: <code>{event['id']}</code>\n"
        f"📌 Назва: <b>{event['title']}</b>\n"
        f"🕒 Дата: <b>{event['event_date']}</b>\n"
        f"📝 Опис: {event['description'] or '—'}"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_event_edit_keyboard(event_id))


def get_event_edit_keyboard(event_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏ Редагувати", callback_data=f"edit_event_{event_id}")],
        [InlineKeyboardButton(text="❌ Видалити", callback_data=f"delete_event_{event_id}")]
    ])


def get_cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Скасувати редагування", callback_data="cancel_edit")]
    ])


async def add_event_start(message: Message, state: FSMContext):
    await message.answer("✍ Введіть назву події:")
    await state.set_state(EventStates.waiting_for_title)

async def add_event_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📆 Введіть дату події (у форматі: <code>YYYY-MM-DD HH:MM</code>):", parse_mode="HTML")
    await state.set_state(EventStates.waiting_for_date)

async def add_event_date(message: Message, state: FSMContext):
    await state.update_data(event_date=message.text)
    await message.answer("📝 Введіть опис події (або напишіть `-`, якщо не потрібно):")
    await state.set_state(EventStates.waiting_for_description)

async def add_event_description(message: Message, db: Database, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    title = data.get("title")
    event_date = data.get("event_date")
    description = message.text if message.text != "-" else ""

    db.execute("INSERT INTO events (user_id, title, event_date, description) VALUES (?, ?, ?, ?)", 
               (user_id, title, event_date, description), commit=True)
    
    await message.answer(f"✅ <b>Подію додано!</b>\n📌 {title}\n🕒 {event_date}", parse_mode="HTML")
    await state.clear()


async def edit_event(callback: CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[2])
    await state.update_data(event_id=event_id)
    await callback.message.edit_text("✏ Введіть нову назву події:", reply_markup=get_cancel_keyboard())
    await state.set_state(EventStates.waiting_for_new_title)

async def edit_event_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📆 Введіть нову дату події (у форматі: <code>YYYY-MM-DD HH:MM</code>):", parse_mode="HTML", reply_markup=get_cancel_keyboard())
    await state.set_state(EventStates.waiting_for_new_date)

async def edit_event_date(message: Message, state: FSMContext):
    await state.update_data(event_date=message.text)
    await message.answer("📝 Введіть новий опис події (або напишіть `-`, якщо не потрібно):", reply_markup=get_cancel_keyboard())
    await state.set_state(EventStates.waiting_for_new_description)

async def edit_event_description(message: Message, db: Database, state: FSMContext):
    data = await state.get_data()
    event_id = data.get("event_id")
    title = data.get("title")
    event_date = data.get("event_date")
    description = message.text if message.text != "-" else ""

    db.execute("UPDATE events SET title = ?, event_date = ?, description = ? WHERE id = ?", 
               (title, event_date, description, event_id), commit=True)
    
    await message.answer("✅ <b>Подію оновлено!</b>", parse_mode="HTML")
    await state.clear()


async def delete_event(callback: CallbackQuery, db: Database):
    event_id = int(callback.data.split("_")[2])
    db.delete_event(event_id)
    await callback.message.edit_text("❌ <b>Подію видалено.</b>", parse_mode="HTML")


async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ <b>Редагування скасовано.</b>", parse_mode="HTML")

def register_event_handlers(router: Router):
    router.message.register(list_events, F.text == "📅 Мої події")
    router.message.register(add_event_start, F.text == "➕ Додати подію")
    router.message.register(add_event_title, EventStates.waiting_for_title)
    router.message.register(add_event_date, EventStates.waiting_for_date)
    router.message.register(add_event_description, EventStates.waiting_for_description)
    
    router.callback_query.register(event_details, F.data.startswith("event_"))
    router.callback_query.register(edit_event, F.data.startswith("edit_event_"))
    router.callback_query.register(delete_event, F.data.startswith("delete_event_"))
    router.callback_query.register(cancel_edit, F.data == "cancel_edit")

    router.message.register(edit_event_title, EventStates.waiting_for_new_title)
    router.message.register(edit_event_date, EventStates.waiting_for_new_date)
    router.message.register(edit_event_description, EventStates.waiting_for_new_description)
