from aiogram import Dispatcher, Router

from .registration import register_registration_handlers
from .common import register_common_handlers
from .user import register_user_handlers
from .events import register_event_handlers  # Додаємо події
from .reminders import register_reminder_handlers  # Додаємо нагадування

def setup_handlers(dp: Dispatcher):
    # Створюємо основний роутер
    main_router = Router()
    
    # Реєструємо обробники на роутері
    register_registration_handlers(main_router)
    register_common_handlers(main_router)
    register_user_handlers(main_router)
    register_event_handlers(main_router)  # Реєструємо події
    register_reminder_handlers(main_router)  # Реєструємо нагадування
    
    # Додаємо роутер до диспетчера
    dp.include_router(main_router)
