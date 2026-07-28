from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List

from database.models import Master, Service


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню (инлайн) - без кнопки админки"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✂️ Записаться", callback_data="booking_start")
    builder.button(text="📋 Мои записи", callback_data="my_bookings")
    builder.button(text="📞 Контакты", callback_data="contacts")
    # Кнопка админки УДАЛЕНА
    builder.adjust(1)
    return builder.as_markup()


def get_masters_keyboard(masters: List[Master]) -> InlineKeyboardMarkup:
    """Клавиатура с выбором мастера"""
    builder = InlineKeyboardBuilder()
    for master in masters:
        builder.button(
            text=f"👤 {master.name}",
            callback_data=f"master_{master.id}"
        )
    builder.button(text="⬅️ Назад", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()


def get_services_keyboard(services: List[Service], master_id: int) -> InlineKeyboardMarkup:
    """Клавиатура с выбором услуги"""
    builder = InlineKeyboardBuilder()
    for service in services:
        builder.button(
            text=f"✂️ {service.name} — {service.price} ₽ ({service.duration_minutes} мин)",
            callback_data=f"service_{master_id}_{service.id}"
        )
    builder.button(text="⬅️ Назад к мастерам", callback_data="back_to_masters")
    builder.adjust(1)
    return builder.as_markup()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Админ-панель (только для админов)"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Записи на сегодня", callback_data="admin_today")
    builder.button(text="📅 Записи на завтра", callback_data="admin_tomorrow")
    builder.button(text="📊 Все записи", callback_data="admin_all")
    builder.button(text="⬅️ Назад", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()