from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from datetime import datetime, timedelta

from config import config
from database.db import db
from database.repositories.booking_repo import BookingRepository
from keyboards.inline import get_admin_keyboard, get_main_menu_keyboard

router = Router()

# Простая функция проверки админа
def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Команда /admin — открывает админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return
    
    await message.answer(
        "🛠 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard()
    )


@router.callback_query(lambda c: c.data == "admin_today")
async def admin_today(callback: CallbackQuery):
    """Записи на сегодня"""
    await callback.answer()
    
    if not is_admin(callback.from_user.id):
        await callback.message.edit_text(
            "⛔ У вас нет доступа к админ-панели.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    async with db.get_session() as session:
        repo = BookingRepository(session)
        bookings = await repo.get_by_date_range(today_start, today_end)
        
        if not bookings:
            await callback.message.edit_text(
                "📋 <b>Записи на сегодня:</b>\n\n"
                "Сегодня записей нет 🎉",
                reply_markup=get_admin_keyboard()
            )
            return
        
        text = "📋 <b>Записи на сегодня:</b>\n\n"
        for i, booking in enumerate(bookings, 1):
            text += (
                f"{i}. {booking.client_name} — {booking.service.name} "
                f"({booking.start_time.strftime('%H:%M')})\n"
                f"   Мастер: {booking.master.name}\n"
                f"   📱 {booking.client_phone}\n"
                f"   ID: #{booking.id}\n\n"
            )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_keyboard()
        )


@router.callback_query(lambda c: c.data == "admin_tomorrow")
async def admin_tomorrow(callback: CallbackQuery):
    """Записи на завтра"""
    await callback.answer()
    
    if not is_admin(callback.from_user.id):
        await callback.message.edit_text(
            "⛔ У вас нет доступа к админ-панели.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    tomorrow_start = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end = tomorrow_start + timedelta(days=1)
    
    async with db.get_session() as session:
        repo = BookingRepository(session)
        bookings = await repo.get_by_date_range(tomorrow_start, tomorrow_end)
        
        if not bookings:
            await callback.message.edit_text(
                "📋 <b>Записи на завтра:</b>\n\n"
                "Завтра записей нет 🎉",
                reply_markup=get_admin_keyboard()
            )
            return
        
        text = "📋 <b>Записи на завтра:</b>\n\n"
        for i, booking in enumerate(bookings, 1):
            text += (
                f"{i}. {booking.client_name} — {booking.service.name} "
                f"({booking.start_time.strftime('%H:%M')})\n"
                f"   Мастер: {booking.master.name}\n"
                f"   📱 {booking.client_phone}\n"
                f"   ID: #{booking.id}\n\n"
            )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_keyboard()
        )


@router.callback_query(lambda c: c.data == "admin_all")
async def admin_all(callback: CallbackQuery):
    """Все активные записи"""
    await callback.answer()
    
    if not is_admin(callback.from_user.id):
        await callback.message.edit_text(
            "⛔ У вас нет доступа к админ-панели.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    async with db.get_session() as session:
        repo = BookingRepository(session)
        bookings = await repo.get_active_bookings()
        
        if not bookings:
            await callback.message.edit_text(
                "📋 <b>Все записи:</b>\n\n"
                "Активных записей нет",
                reply_markup=get_admin_keyboard()
            )
            return
        
        text = "📋 <b>Все активные записи:</b>\n\n"
        for i, booking in enumerate(bookings[:20], 1):
            text += (
                f"{i}. {booking.client_name} — {booking.service.name}\n"
                f"   📅 {booking.start_time.strftime('%d.%m %H:%M')}\n"
                f"   Мастер: {booking.master.name}\n"
                f"   ID: #{booking.id}\n\n"
            )
        
        if len(bookings) > 20:
            text += f"\n... и еще {len(bookings) - 20} записей"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_keyboard()
        )


@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_admin(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.answer()
    await callback.message.edit_text(
        "📋 <b>Главное меню</b>",
        reply_markup=get_main_menu_keyboard()
    )