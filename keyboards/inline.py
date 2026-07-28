from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
from datetime import datetime

from database.models import Master, Service


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню (инлайн) - без кнопки админки"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✂️ Записаться", callback_data="booking_start")
    builder.button(text="📋 Мои записи", callback_data="my_bookings")
    builder.button(text="📞 Контакты", callback_data="contacts")
    builder.adjust(1)
    return builder.as_markup()


def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню админ-панели"""
    builder = InlineKeyboardBuilder()
    builder.button(text="👑 Управление админами", callback_data="admin_manage")
    builder.button(text="📋 Управление записями", callback_data="admin_bookings")
    builder.button(text="💈 Управление мастерами", callback_data="admin_masters")
    builder.button(text="✂️ Управление услугами", callback_data="admin_services")
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="⬅️ Назад в меню", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()


def get_admin_services_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления услугами"""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить услугу", callback_data="service_add_start")
    builder.button(text="✏️ Редактировать услугу", callback_data="service_edit_start")
    builder.button(text="⬅️ Назад", callback_data="admin_main")
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


def get_time_slots_keyboard(slots: List[datetime]) -> InlineKeyboardMarkup:
    """Клавиатура с выбором времени"""
    builder = InlineKeyboardBuilder()
    
    for slot in slots:
        time_str = slot.strftime("%H:%M")
        date_str = slot.strftime("%Y-%m-%d")
        builder.button(
            text=f"🟢 {time_str}",
            callback_data=f"time_{date_str}_{time_str}"
        )
    
    builder.button(text="⬅️ Назад к дате", callback_data="back_to_date")
    builder.adjust(3)
    return builder.as_markup()