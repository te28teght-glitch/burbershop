from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from datetime import datetime, timedelta

from config import config
from database.db import db
from database.repositories.booking_repo import BookingRepository
from keyboards.inline import get_admin_keyboard, get_main_menu_keyboard

router = Router()

def admin_only(func):
    async def wrapper(message_or_callback, *args, **kwargs):
        user_id = None
        if isinstance(message_or_callback, types.Message):
            user_id = message_or_callback.from_user.id
        elif isinstance(message_or_callback, types.CallbackQuery):
            user_id = message_or_callback.from_user.id
            await message_or_callback.answer()
        
        if user_id not in config.ADMIN_IDS:
            if isinstance(message_or_callback, types.Message):
                await message_or_callback.answer("⛔ У вас нет доступа к админ-панели.")
            elif isinstance(message_or_callback, types.CallbackQuery):
                await message_or_callback.message.edit_text(
                    "⛔ У вас нет доступа к админ-панели.",
                    reply_markup=get_main_menu_keyboard()
                )
            return
        return await func(message_or_callback, *args, **kwargs)
    return wrapper


@router.message(Command("admin"))
@admin_only
async def cmd_admin(message: types.Message):
    await message.answer(
        "🛠 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard()
    )


@router.callback_query(lambda c: c.data == "admin_panel")
@admin_only
async def process_admin_panel(callback: CallbackQuery):
    await callback.message.edit_text(
        "🛠 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard()
    )


@router.callback_query(lambda c: c.data == "admin_today")
@admin_only
async def admin_today(callback: CallbackQuery):
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
@admin_only
async def admin_tomorrow(callback: CallbackQuery):
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
@admin_only
async def admin_all(callback: CallbackQuery):
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
    await callback.answer()
    await callback.message.edit_text(
        "📋 <b>Главное меню</b>",
        reply_markup=get_main_menu_keyboard()
    )