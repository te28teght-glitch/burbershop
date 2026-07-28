from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta

from config import config
from database.db import db
from database.repositories.booking_repo import BookingRepository
from database.repositories.master_repo import MasterRepository
from database.repositories.service_repo import ServiceRepository
from database.repositories.admin_repo import AdminRepository
from keyboards.inline import get_admin_main_keyboard, get_main_menu_keyboard, get_admin_services_keyboard

router = Router()

# Состояния для FSM админки
class AdminStates(StatesGroup):
    # Управление админами
    adding_admin = State()
    removing_admin = State()
    
    # Управление мастерами
    adding_master = State()
    editing_master_name = State()
    editing_master_status = State()
    
    # Управление услугами
    adding_service = State()
    adding_service_name = State()
    adding_service_price = State()
    adding_service_duration = State()
    editing_service_name = State()
    editing_service_price = State()
    editing_service_duration = State()
    
    # Управление записями
    confirming_booking = State()
    canceling_booking = State()

# Функция проверки админа
async def is_admin(user_id: int) -> bool:
    async with db.get_session() as session:
        repo = AdminRepository(session)
        return await repo.is_admin(user_id)


@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Команда /admin — открывает админ-панель"""
    if not await is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return
    
    await message.answer(
        "🛠 <b>Админ-панель</b>\n\n"
        "Выберите раздел:",
        reply_markup=get_admin_main_keyboard()
    )


@router.callback_query(lambda c: c.data == "admin_main")
async def admin_main(callback: CallbackQuery):
    """Главное меню админки"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.edit_text(
            "⛔ У вас нет доступа к админ-панели.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "🛠 <b>Админ-панель</b>\n\n"
        "Выберите раздел:",
        reply_markup=get_admin_main_keyboard()
    )


# ========== УПРАВЛЕНИЕ АДМИНАМИ ==========

@router.callback_query(lambda c: c.data == "admin_manage")
async def admin_manage(callback: CallbackQuery):
    """Управление админами"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    async with db.get_session() as session:
        repo = AdminRepository(session)
        admins = await repo.get_active_admins()
        
        text = "👑 <b>Управление администраторами</b>\n\n"
        if admins:
            text += "Список админов:\n"
            for i, admin in enumerate(admins, 1):
                username = f"@{admin.username}" if admin.username else "без username"
                text += f"{i}. {admin.full_name or 'Неизвестно'} ({username})\n"
                text += f"   ID: <code>{admin.telegram_id}</code>\n\n"
        else:
            text += "Админов пока нет.\n"
        
        text += "\nДля добавления админа используйте кнопку ниже."
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin_add_start")],
            [InlineKeyboardButton(text="❌ Удалить админа", callback_data="admin_remove_start")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_main")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "admin_add_start")
async def admin_add_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления админа"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    await callback.message.edit_text(
        "➕ <b>Добавление администратора</b>\n\n"
        "Отправьте Telegram ID пользователя, которого хотите сделать админом.\n"
        "Пользователь может узнать свой ID у бота @userinfobot.\n\n"
        "Пример: <code>123456789</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_manage")]
        ])
    )
    await state.set_state(AdminStates.adding_admin)


@router.message(AdminStates.adding_admin)
async def admin_add_process(message: types.Message, state: FSMContext):
    """Добавление админа"""
    try:
        telegram_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Введите число (Telegram ID).",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_manage")]
            ])
        )
        return
    
    async with db.get_session() as session:
        repo = AdminRepository(session)
        
        existing = await repo.get_by_telegram_id(telegram_id)
        if existing and existing.is_active:
            await message.answer(
                "⚠️ Этот пользователь уже является администратором.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_manage")]
                ])
            )
            await state.clear()
            return
        
        admin = await repo.add_admin(telegram_id)
        
        await message.answer(
            f"✅ Администратор добавлен!\n\n"
            f"ID: <code>{admin.telegram_id}</code>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_manage")]
            ])
        )
        await state.clear()


@router.callback_query(lambda c: c.data == "admin_remove_start")
async def admin_remove_start(callback: CallbackQuery, state: FSMContext):
    """Начало удаления админа"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    async with db.get_session() as session:
        repo = AdminRepository(session)
        admins = await repo.get_active_admins()
        
        if len(admins) <= 1:
            await callback.message.edit_text(
                "⚠️ Нельзя удалить последнего администратора!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_manage")]
                ])
            )
            return
        
        builder = InlineKeyboardBuilder()
        for admin in admins:
            if admin.telegram_id == callback.from_user.id:
                continue
            text = f"❌ {admin.full_name or admin.telegram_id}"
            builder.button(text=text, callback_data=f"admin_remove_{admin.telegram_id}")
        builder.button(text="⬅️ Отмена", callback_data="admin_manage")
        builder.adjust(1)
        
        await callback.message.edit_text(
            "❌ <b>Удаление администратора</b>\n\n"
            "Выберите админа для удаления:",
            reply_markup=builder.as_markup()
        )


@router.callback_query(lambda c: c.data.startswith("admin_remove_"))
async def admin_remove_process(callback: CallbackQuery):
    """Удаление админа"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    telegram_id = int(callback.data.split("_")[2])
    
    async with db.get_session() as session:
        repo = AdminRepository(session)
        admins = await repo.get_active_admins()
        
        if len(admins) <= 1:
            await callback.message.edit_text(
                "⚠️ Нельзя удалить последнего администратора!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_manage")]
                ])
            )
            return
        
        await repo.remove_admin(telegram_id)
        
        await callback.message.edit_text(
            f"✅ Администратор с ID <code>{telegram_id}</code> удалён.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_manage")]
            ])
        )


# ========== УПРАВЛЕНИЕ ЗАПИСЯМИ ==========

@router.callback_query(lambda c: c.data == "admin_bookings")
async def admin_bookings(callback: CallbackQuery):
    """Управление записями"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Записи на сегодня", callback_data="admin_today")],
        [InlineKeyboardButton(text="📅 Записи на завтра", callback_data="admin_tomorrow")],
        [InlineKeyboardButton(text="📊 Все записи", callback_data="admin_all")],
        [InlineKeyboardButton(text="✅ Подтвердить запись", callback_data="admin_confirm_booking_start")],
        [InlineKeyboardButton(text="❌ Отменить запись", callback_data="admin_cancel_booking_start")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_main")]
    ])
    
    await callback.message.edit_text(
        "📋 <b>Управление записями</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data == "admin_today")
async def admin_today(callback: CallbackQuery):
    """Записи на сегодня"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
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
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_bookings")]
                ])
            )
            return
        
        text = "📋 <b>Записи на сегодня:</b>\n\n"
        for i, booking in enumerate(bookings, 1):
            status = "✅" if booking.is_confirmed else "⏳"
            text += (
                f"{i}. {booking.client_name} — {booking.service.name}\n"
                f"   ⏰ {booking.start_time.strftime('%H:%M')}\n"
                f"   👤 Мастер: {booking.master.name}\n"
                f"   📱 {booking.client_phone}\n"
                f"   {status} Статус: {'Подтверждена' if booking.is_confirmed else 'Ожидает'}\n"
                f"   ID: #{booking.id}\n\n"
            )
        
        builder = InlineKeyboardBuilder()
        for booking in bookings[:5]:
            builder.button(
                text=f"✏️ Запись #{booking.id}",
                callback_data=f"admin_booking_detail_{booking.id}"
            )
        builder.button(text="⬅️ Назад", callback_data="admin_bookings")
        builder.adjust(1)
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(lambda c: c.data == "admin_tomorrow")
async def admin_tomorrow(callback: CallbackQuery):
    """Записи на завтра"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
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
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_bookings")]
                ])
            )
            return
        
        text = "📋 <b>Записи на завтра:</b>\n\n"
        for i, booking in enumerate(bookings, 1):
            status = "✅" if booking.is_confirmed else "⏳"
            text += (
                f"{i}. {booking.client_name} — {booking.service.name}\n"
                f"   ⏰ {booking.start_time.strftime('%H:%M')}\n"
                f"   👤 Мастер: {booking.master.name}\n"
                f"   📱 {booking.client_phone}\n"
                f"   {status} Статус: {'Подтверждена' if booking.is_confirmed else 'Ожидает'}\n"
                f"   ID: #{booking.id}\n\n"
            )
        
        builder = InlineKeyboardBuilder()
        for booking in bookings[:5]:
            builder.button(
                text=f"✏️ Запись #{booking.id}",
                callback_data=f"admin_booking_detail_{booking.id}"
            )
        builder.button(text="⬅️ Назад", callback_data="admin_bookings")
        builder.adjust(1)
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(lambda c: c.data == "admin_all")
async def admin_all(callback: CallbackQuery):
    """Все активные записи"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    async with db.get_session() as session:
        repo = BookingRepository(session)
        bookings = await repo.get_active_bookings()
        
        if not bookings:
            await callback.message.edit_text(
                "📋 <b>Все записи:</b>\n\n"
                "Активных записей нет",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_bookings")]
                ])
            )
            return
        
        text = "📋 <b>Все активные записи (последние 20):</b>\n\n"
        for i, booking in enumerate(bookings[:20], 1):
            status = "✅" if booking.is_confirmed else "⏳"
            text += (
                f"{i}. {booking.client_name} — {booking.service.name}\n"
                f"   📅 {booking.start_time.strftime('%d.%m %H:%M')}\n"
                f"   👤 {booking.master.name}\n"
                f"   {status} {booking.is_confirmed and 'Подтверждена' or 'Ожидает'}\n"
                f"   ID: #{booking.id}\n\n"
            )
        
        if len(bookings) > 20:
            text += f"\n... и еще {len(bookings) - 20} записей"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_bookings")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(lambda c: c.data.startswith("admin_booking_detail_"))
async def admin_booking_detail(callback: CallbackQuery):
    """Детали записи"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    parts = callback.data.split("_")
    if len(parts) != 4:
        await callback.answer("⏳ Пожалуйста, подождите...")
        return
    
    try:
        booking_id = int(parts[3])
    except ValueError:
        await callback.answer("⏳ Пожалуйста, подождите...")
        return
    
    async with db.get_session() as session:
        repo = BookingRepository(session)
        booking = await repo.get_by_id(booking_id)
        
        if not booking:
            await callback.message.edit_text(
                "❌ Запись не найдена.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_bookings")]
                ])
            )
            return
        
        status = "✅ Подтверждена" if booking.is_confirmed else "⏳ Ожидает подтверждения"
        
        text = (
            f"📋 <b>Детали записи #{booking.id}</b>\n\n"
            f"👤 Клиент: {booking.client_name}\n"
            f"📱 Телефон: {booking.client_phone}\n"
            f"🆔 Telegram ID: <code>{booking.client_telegram_id}</code>\n\n"
            f"✂️ Услуга: {booking.service.name}\n"
            f"💰 Стоимость: {booking.service.price} ₽\n"
            f"⏱ Длительность: {booking.service.duration_minutes} мин\n\n"
            f"👤 Мастер: {booking.master.name}\n"
            f"📅 Дата: {booking.start_time.strftime('%d.%m.%Y')}\n"
            f"⏰ Время: {booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}\n\n"
            f"📊 Статус: {status}\n"
            f"📅 Создана: {booking.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Подтвердить" if not booking.is_confirmed else "❌ Отменить подтверждение",
                callback_data=f"admin_confirm_{booking.id}"
            )],
            [InlineKeyboardButton(
                text="❌ Отменить запись",
                callback_data=f"admin_cancel_{booking.id}"
            )],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_bookings")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(lambda c: c.data.startswith("admin_confirm_") and c.data != "admin_confirm_booking_start")
async def admin_confirm_booking(callback: CallbackQuery):
    """Подтверждение записи"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    if callback.data == "admin_confirm_booking_start":
        return
    
    parts = callback.data.split("_")
    if len(parts) != 3:
        await callback.answer("⏳ Пожалуйста, подождите...")
        return
    
    try:
        booking_id = int(parts[2])
    except ValueError:
        await callback.answer("⏳ Пожалуйста, подождите...")
        return
    
    async with db.get_session() as session:
        repo = BookingRepository(session)
        booking = await repo.get_by_id(booking_id)
        
        if not booking:
            await callback.message.edit_text("❌ Запись не найдена.")
            return
        
        booking.is_confirmed = not booking.is_confirmed
        booking.confirmed_at = datetime.now() if booking.is_confirmed else None
        await session.commit()
        
        status = "подтверждена" if booking.is_confirmed else "отменена"
        await callback.message.edit_text(
            f"✅ Статус записи #{booking.id} изменён на '{status}'.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_bookings")]
            ])
        )


@router.callback_query(lambda c: c.data.startswith("admin_cancel_") and c.data != "admin_cancel_booking_start")
async def admin_cancel_booking(callback: CallbackQuery):
    """Отмена записи админом"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    if callback.data == "admin_cancel_booking_start":
        return
    
    parts = callback.data.split("_")
    if len(parts) != 3:
        await callback.answer("⏳ Пожалуйста, подождите...")
        return
    
    try:
        booking_id = int(parts[2])
    except ValueError:
        await callback.answer("⏳ Пожалуйста, подождите...")
        return
    
    async with db.get_session() as session:
        repo = BookingRepository(session)
        booking = await repo.get_by_id(booking_id)
        
        if not booking:
            await callback.message.edit_text("❌ Запись не найдена.")
            return
        
        booking.is_canceled = True
        booking.canceled_at = datetime.now()
        await session.commit()
        
        await callback.message.edit_text(
            f"❌ Запись #{booking_id} отменена.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_bookings")]
            ])
        )


@router.callback_query(lambda c: c.data == "admin_confirm_booking_start")
async def admin_confirm_booking_start(callback: CallbackQuery, state: FSMContext):
    """Начало подтверждения записи по ID"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    await callback.message.edit_text(
        "✅ <b>Подтверждение записи</b>\n\n"
        "Введите ID записи, которую нужно подтвердить:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_bookings")]
        ])
    )
    await state.set_state(AdminStates.confirming_booking)


@router.message(AdminStates.confirming_booking)
async def admin_confirm_booking_process(message: types.Message, state: FSMContext):
    """Подтверждение записи по ID"""
    try:
        booking_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Введите число.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_bookings")]
            ])
        )
        return
    
    async with db.get_session() as session:
        repo = BookingRepository(session)
        booking = await repo.get_by_id(booking_id)
        
        if not booking:
            await message.answer(
                f"❌ Запись #{booking_id} не найдена.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_bookings")]
                ])
            )
            await state.clear()
            return
        
        booking.is_confirmed = True
        booking.confirmed_at = datetime.now()
        await session.commit()
        
        await message.answer(
            f"✅ Запись #{booking_id} подтверждена!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_bookings")]
            ])
        )
        await state.clear()


@router.callback_query(lambda c: c.data == "admin_cancel_booking_start")
async def admin_cancel_booking_start(callback: CallbackQuery, state: FSMContext):
    """Начало отмены записи по ID"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    await callback.message.edit_text(
        "❌ <b>Отмена записи</b>\n\n"
        "Введите ID записи, которую нужно отменить:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_bookings")]
        ])
    )
    await state.set_state(AdminStates.canceling_booking)


@router.message(AdminStates.canceling_booking)
async def admin_cancel_booking_process(message: types.Message, state: FSMContext):
    """Отмена записи по ID"""
    try:
        booking_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Введите число.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_bookings")]
            ])
        )
        return
    
    async with db.get_session() as session:
        repo = BookingRepository(session)
        booking = await repo.get_by_id(booking_id)
        
        if not booking:
            await message.answer(
                f"❌ Запись #{booking_id} не найдена.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_bookings")]
                ])
            )
            await state.clear()
            return
        
        booking.is_canceled = True
        booking.canceled_at = datetime.now()
        await session.commit()
        
        await message.answer(
            f"❌ Запись #{booking_id} отменена!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_bookings")]
            ])
        )
        await state.clear()


# ========== УПРАВЛЕНИЕ МАСТЕРАМИ ==========

@router.callback_query(lambda c: c.data == "admin_masters")
async def admin_masters(callback: CallbackQuery):
    """Управление мастерами"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    async with db.get_session() as session:
        repo = MasterRepository(session)
        masters = await repo.get_all()
        
        text = "💈 <b>Управление мастерами</b>\n\n"
        if masters:
            for master in masters:
                status = "🟢 Активен" if master.is_active else "🔴 Неактивен"
                text += f"👤 {master.name} — {status}\n"
                text += f"   ID: #{master.id}\n\n"
        else:
            text += "Мастеров пока нет.\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить мастера", callback_data="master_add_start")],
            [InlineKeyboardButton(text="✏️ Редактировать мастера", callback_data="master_edit_start")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_main")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "master_add_start")
async def master_add_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления мастера"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    await callback.message.edit_text(
        "➕ <b>Добавление мастера</b>\n\n"
        "Введите имя нового мастера:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_masters")]
        ])
    )
    await state.set_state(AdminStates.adding_master)


@router.message(AdminStates.adding_master)
async def master_add_process(message: types.Message, state: FSMContext):
    """Добавление мастера"""
    name = message.text.strip()
    
    async with db.get_session() as session:
        from database.models import Master
        master = Master(name=name, is_active=True)
        session.add(master)
        await session.commit()
        await session.refresh(master)
    
    await message.answer(
        f"✅ Мастер '{name}' добавлен!\n"
        f"ID: #{master.id}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_masters")]
        ])
    )
    await state.clear()


# ========== РЕДАКТИРОВАНИЕ МАСТЕРОВ ==========

@router.callback_query(lambda c: c.data == "master_edit_start")
async def master_edit_start(callback: CallbackQuery):
    """Начало редактирования мастера - выбор мастера"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    async with db.get_session() as session:
        repo = MasterRepository(session)
        masters = await repo.get_all()
        
        if not masters:
            await callback.message.edit_text(
                "⚠️ Нет мастеров для редактирования.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_masters")]
                ])
            )
            return
        
        builder = InlineKeyboardBuilder()
        for master in masters:
            status = "🟢" if master.is_active else "🔴"
            builder.button(
                text=f"{status} {master.name}",
                callback_data=f"master_edit_{master.id}"
            )
        builder.button(text="⬅️ Назад", callback_data="admin_masters")
        builder.adjust(1)
        
        await callback.message.edit_text(
            "✏️ <b>Редактирование мастера</b>\n\n"
            "Выберите мастера для редактирования:",
            reply_markup=builder.as_markup()
        )


@router.callback_query(lambda c: c.data.startswith("master_edit_") and c.data != "master_edit_start")
async def master_edit_detail(callback: CallbackQuery, state: FSMContext):
    """Детали мастера для редактирования"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    master_id = int(callback.data.split("_")[2])
    
    async with db.get_session() as session:
        repo = MasterRepository(session)
        master = await repo.get_by_id(master_id)
        
        if not master:
            await callback.message.edit_text(
                "❌ Мастер не найден.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_masters")]
                ])
            )
            return
        
        await state.update_data(editing_master_id=master_id)
        
        status = "🟢 Активен" if master.is_active else "🔴 Неактивен"
        text = (
            f"✏️ <b>Редактирование мастера</b>\n\n"
            f"Имя: <b>{master.name}</b>\n"
            f"Статус: {status}\n\n"
            f"Что хотите сделать?"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить имя", callback_data="master_edit_name")],
            [InlineKeyboardButton(
                text="🔄 Сделать неактивным" if master.is_active else "🔄 Активировать",
                callback_data="master_edit_status"
            )],
            [InlineKeyboardButton(text="❌ Удалить мастера", callback_data="master_delete")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_masters")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "master_edit_name")
async def master_edit_name_start(callback: CallbackQuery, state: FSMContext):
    """Изменение имени мастера"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    await callback.message.edit_text(
        "✏️ <b>Изменить имя мастера</b>\n\n"
        "Введите новое имя:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_masters")]
        ])
    )
    await state.set_state(AdminStates.editing_master_name)


@router.message(AdminStates.editing_master_name)
async def master_edit_name_process(message: types.Message, state: FSMContext):
    """Сохранение нового имени мастера"""
    new_name = message.text.strip()
    data = await state.get_data()
    master_id = data.get('editing_master_id')
    
    async with db.get_session() as session:
        repo = MasterRepository(session)
        master = await repo.get_by_id(master_id)
        
        if master:
            master.name = new_name
            await session.commit()
            
            await message.answer(
                f"✅ Имя мастера изменено на: <b>{new_name}</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад к мастерам", callback_data="admin_masters")]
                ])
            )
        else:
            await message.answer(
                "❌ Мастер не найден.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_masters")]
                ])
            )
        
        await state.clear()


@router.callback_query(lambda c: c.data == "master_edit_status")
async def master_edit_status(callback: CallbackQuery, state: FSMContext):
    """Изменение статуса мастера"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    data = await state.get_data()
    master_id = data.get('editing_master_id')
    
    async with db.get_session() as session:
        repo = MasterRepository(session)
        master = await repo.get_by_id(master_id)
        
        if master:
            master.is_active = not master.is_active
            await session.commit()
            status = "активирован" if master.is_active else "деактивирован"
            
            await callback.message.edit_text(
                f"✅ Мастер {status}!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад к мастерам", callback_data="admin_masters")]
                ])
            )
        else:
            await callback.message.edit_text(
                "❌ Мастер не найден.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_masters")]
                ])
            )


@router.callback_query(lambda c: c.data == "master_delete")
async def master_delete_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления мастера"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    data = await state.get_data()
    master_id = data.get('editing_master_id')
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"master_delete_confirm_{master_id}")],
        [InlineKeyboardButton(text="❌ Нет, отмена", callback_data="admin_masters")]
    ])
    
    await callback.message.edit_text(
        "⚠️ <b>Вы уверены, что хотите удалить этого мастера?</b>\n\n"
        "Все записи к этому мастеру также будут удалены.",
        reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data.startswith("master_delete_confirm_"))
async def master_delete_process(callback: CallbackQuery):
    """Удаление мастера"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    master_id = int(callback.data.split("_")[3])
    
    async with db.get_session() as session:
        repo = MasterRepository(session)
        master = await repo.get_by_id(master_id)
        
        if master:
            await session.delete(master)
            await session.commit()
            
            await callback.message.edit_text(
                f"✅ Мастер удалён!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад к мастерам", callback_data="admin_masters")]
                ])
            )
        else:
            await callback.message.edit_text(
                "❌ Мастер не найден.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_masters")]
                ])
            )


# ========== УПРАВЛЕНИЕ УСЛУГАМИ ==========

@router.callback_query(lambda c: c.data == "admin_services")
async def admin_services(callback: CallbackQuery):
    """Управление услугами"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    async with db.get_session() as session:
        repo = ServiceRepository(session)
        services = await repo.get_all()
        
        text = "✂️ <b>Управление услугами</b>\n\n"
        if services:
            for service in services:
                text += (
                    f"✂️ {service.name}\n"
                    f"   💰 {service.price} ₽ | ⏱ {service.duration_minutes} мин\n"
                    f"   ID: #{service.id}\n\n"
                )
        else:
            text += "Услуг пока нет.\n"
        
        await callback.message.edit_text(text, reply_markup=get_admin_services_keyboard())


@router.callback_query(lambda c: c.data == "service_add_start")
async def service_add_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления услуги"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    await callback.message.edit_text(
        "➕ <b>Добавление услуги</b>\n\n"
        "Введите название услуги:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_services")]
        ])
    )
    await state.set_state(AdminStates.adding_service_name)


@router.message(AdminStates.adding_service_name)
async def service_add_name_process(message: types.Message, state: FSMContext):
    """Добавление услуги - шаг 1: название"""
    await state.update_data(service_name=message.text.strip())
    
    await message.answer(
        "💰 Введите стоимость услуги (в рублях):\n"
        "Пример: <code>1500</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_services")]
        ])
    )
    await state.set_state(AdminStates.adding_service_price)


@router.message(AdminStates.adding_service_price)
async def service_add_price_process(message: types.Message, state: FSMContext):
    """Добавление услуги - шаг 2: цена"""
    try:
        price = float(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Введите число (например, 1500):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_services")]
            ])
        )
        return
    
    await state.update_data(service_price=price)
    
    await message.answer(
        "⏱ Введите длительность услуги в минутах:\n"
        "Пример: <code>30</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_services")]
        ])
    )
    await state.set_state(AdminStates.adding_service_duration)


@router.message(AdminStates.adding_service_duration)
async def service_add_duration_process(message: types.Message, state: FSMContext):
    """Добавление услуги - шаг 3: длительность"""
    try:
        duration = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Введите число (например, 30):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_services")]
            ])
        )
        return
    
    data = await state.get_data()
    name = data.get('service_name')
    price = data.get('service_price')
    
    async with db.get_session() as session:
        from database.models import Service
        service = Service(
            name=name,
            price=price,
            duration_minutes=duration,
            is_active=True
        )
        session.add(service)
        await session.commit()
        await session.refresh(service)
    
    await message.answer(
        f"✅ Услуга добавлена!\n\n"
        f"✂️ {name}\n"
        f"💰 {price} ₽\n"
        f"⏱ {duration} мин",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")]
        ])
    )
    await state.clear()


# ========== РЕДАКТИРОВАНИЕ УСЛУГ ==========

@router.callback_query(lambda c: c.data == "service_edit_start")
async def service_edit_start(callback: CallbackQuery):
    """Начало редактирования услуги - выбор услуги"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    async with db.get_session() as session:
        repo = ServiceRepository(session)
        services = await repo.get_all()
        
        if not services:
            await callback.message.edit_text(
                "⚠️ Нет услуг для редактирования.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")]
                ])
            )
            return
        
        builder = InlineKeyboardBuilder()
        for service in services:
            builder.button(
                text=f"✏️ {service.name} — {service.price} ₽",
                callback_data=f"service_edit_{service.id}"
            )
        builder.button(text="⬅️ Назад", callback_data="admin_services")
        builder.adjust(1)
        
        await callback.message.edit_text(
            "✏️ <b>Редактирование услуги</b>\n\n"
            "Выберите услугу для редактирования:",
            reply_markup=builder.as_markup()
        )


@router.callback_query(lambda c: c.data.startswith("service_edit_") and c.data != "service_edit_start")
async def service_edit_detail(callback: CallbackQuery, state: FSMContext):
    """Детали услуги для редактирования"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    parts = callback.data.split("_")
    if len(parts) != 3:
        await callback.answer("⏳ Пожалуйста, подождите...")
        return
    
    try:
        service_id = int(parts[2])
    except ValueError:
        await callback.answer("⏳ Пожалуйста, подождите...")
        return
    
    async with db.get_session() as session:
        repo = ServiceRepository(session)
        service = await repo.get_by_id(service_id)
        
        if not service:
            await callback.message.edit_text(
                "❌ Услуга не найдена.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")]
                ])
            )
            return
        
        await state.update_data(editing_service_id=service_id)
        
        text = (
            f"✏️ <b>Редактирование услуги</b>\n\n"
            f"Название: <b>{service.name}</b>\n"
            f"Цена: <b>{service.price} ₽</b>\n"
            f"Длительность: <b>{service.duration_minutes} мин</b>\n\n"
            f"Что хотите изменить?"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить название", callback_data="service_edit_name_action")],
            [InlineKeyboardButton(text="💰 Изменить цену", callback_data="service_edit_price_action")],
            [InlineKeyboardButton(text="⏱ Изменить длительность", callback_data="service_edit_duration_action")],
            [InlineKeyboardButton(text="❌ Удалить услугу", callback_data="service_delete_action")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "service_edit_name_action")
async def service_edit_name_start(callback: CallbackQuery, state: FSMContext):
    """Изменение названия услуги"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    data = await state.get_data()
    service_id = data.get('editing_service_id')
    
    if not service_id:
        await callback.message.edit_text(
            "❌ Ошибка: не найдена услуга для редактирования.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")]
            ])
        )
        return
    
    await callback.message.edit_text(
        "✏️ <b>Изменить название</b>\n\n"
        "Введите новое название услуги:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_services")]
        ])
    )
    await state.set_state(AdminStates.editing_service_name)


@router.message(AdminStates.editing_service_name)
async def service_edit_name_process(message: types.Message, state: FSMContext):
    """Сохранение нового названия"""
    new_name = message.text.strip()
    data = await state.get_data()
    service_id = data.get('editing_service_id')
    
    if not service_id:
        await message.answer(
            "❌ Ошибка: не найдена услуга для редактирования.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")]
            ])
        )
        await state.clear()
        return
    
    async with db.get_session() as session:
        repo = ServiceRepository(session)
        service = await repo.get_by_id(service_id)
        
        if service:
            service.name = new_name
            await session.commit()
            
            await message.answer(
                f"✅ Название услуги изменено на: <b>{new_name}</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад к услугам", callback_data="admin_services")]
                ])
            )
        else:
            await message.answer(
                "❌ Услуга не найдена.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")]
                ])
            )
        
        await state.clear()


@router.callback_query(lambda c: c.data == "service_edit_price_action")
async def service_edit_price_start(callback: CallbackQuery, state: FSMContext):
    """Изменение цены услуги"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    data = await state.get_data()
    service_id = data.get('editing_service_id')
    
    if not service_id:
        await callback.message.edit_text(
            "❌ Ошибка: не найдена услуга для редактирования.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")]
            ])
        )
        return
    
    await callback.message.edit_text(
        "💰 <b>Изменить цену</b>\n\n"
        "Введите новую цену (в рублях):\n"
        "Пример: <code>1500</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_services")]
        ])
    )
    await state.set_state(AdminStates.editing_service_price)


@router.message(AdminStates.editing_service_price)
async def service_edit_price_process(message: types.Message, state: FSMContext):
    """Сохранение новой цены"""
    try:
        new_price = float(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Введите число.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_services")]
            ])
        )
        return
    
    data = await state.get_data()
    service_id = data.get('editing_service_id')
    
    if not service_id:
        await message.answer(
            "❌ Ошибка: не найдена услуга для редактирования.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")]
            ])
        )
        await state.clear()
        return
    
    async with db.get_session() as session:
        repo = ServiceRepository(session)
        service = await repo.get_by_id(service_id)
        
        if service:
            service.price = new_price
            await session.commit()
            
            await message.answer(
                f"✅ Цена изменена на: <b>{new_price} ₽</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад к услугам", callback_data="admin_services")]
                ])
            )
        else:
            await message.answer(
                "❌ Услуга не найдена.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")]
                ])
            )
        
        await state.clear()


@router.callback_query(lambda c: c.data == "service_edit_duration_action")
async def service_edit_duration_start(callback: CallbackQuery, state: FSMContext):
    """Изменение длительности услуги"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    data = await state.get_data()
    service_id = data.get('editing_service_id')
    
    if not service_id:
        await callback.message.edit_text(
            "❌ Ошибка: не найдена услуга для редактирования.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")]
            ])
        )
        return
    
    await callback.message.edit_text(
        "⏱ <b>Изменить длительность</b>\n\n"
        "Введите новую длительность (в минутах):\n"
        "Пример: <code>40</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_services")]
        ])
    )
    await state.set_state(AdminStates.editing_service_duration)


@router.message(AdminStates.editing_service_duration)
async def service_edit_duration_process(message: types.Message, state: FSMContext):
    """Сохранение новой длительности"""
    try:
        new_duration = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Введите число.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_services")]
            ])
        )
        return
    
    data = await state.get_data()
    service_id = data.get('editing_service_id')
    
    if not service_id:
        await message.answer(
            "❌ Ошибка: не найдена услуга для редактирования.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")]
            ])
        )
        await state.clear()
        return
    
    async with db.get_session() as session:
        repo = ServiceRepository(session)
        service = await repo.get_by_id(service_id)
        
        if service:
            service.duration_minutes = new_duration
            await session.commit()
            
            await message.answer(
                f"✅ Длительность изменена на: <b>{new_duration} мин</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад к услугам", callback_data="admin_services")]
                ])
            )
        else:
            await message.answer(
                "❌ Услуга не найдена.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")]
                ])
            )
        
        await state.clear()


@router.callback_query(lambda c: c.data == "service_delete_action")
async def service_delete_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления услуги"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    data = await state.get_data()
    service_id = data.get('editing_service_id')
    
    if not service_id:
        await callback.message.edit_text(
            "❌ Ошибка: не найдена услуга для удаления.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")]
            ])
        )
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"service_delete_confirm_{service_id}")],
        [InlineKeyboardButton(text="❌ Нет, отмена", callback_data="admin_services")]
    ])
    
    await callback.message.edit_text(
        "⚠️ <b>Вы уверены, что хотите удалить эту услугу?</b>\n\n"
        "Это действие нельзя отменить.",
        reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data.startswith("service_delete_confirm_"))
async def service_delete_process(callback: CallbackQuery):
    """Удаление услуги"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    parts = callback.data.split("_")
    if len(parts) != 4:
        await callback.answer("⏳ Пожалуйста, подождите...")
        return
    
    try:
        service_id = int(parts[3])
    except ValueError:
        await callback.answer("⏳ Пожалуйста, подождите...")
        return
    
    async with db.get_session() as session:
        repo = ServiceRepository(session)
        service = await repo.get_by_id(service_id)
        
        if service:
            await session.delete(service)
            await session.commit()
            
            await callback.message.edit_text(
                f"✅ Услуга удалена!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад к услугам", callback_data="admin_services")]
                ])
            )
        else:
            await callback.message.edit_text(
                "❌ Услуга не найдена.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_services")]
                ])
            )


# ========== СТАТИСТИКА ==========

@router.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Статистика"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        return
    
    async with db.get_session() as session:
        booking_repo = BookingRepository(session)
        total_bookings = len(await booking_repo.get_all())
        
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        today_bookings = await booking_repo.get_by_date_range(today_start, today_end)
        
        active_bookings = await booking_repo.get_active_bookings()
        
        master_repo = MasterRepository(session)
        masters = await master_repo.get_all()
        
        service_repo = ServiceRepository(session)
        services = await service_repo.get_all()
        
        total_revenue = 0
        for booking in active_bookings:
            if booking.is_confirmed:
                total_revenue += booking.service.price
        
        text = (
            "📊 <b>Статистика</b>\n\n"
            f"📋 Всего записей: {total_bookings}\n"
            f"📅 Сегодня: {len(today_bookings)}\n"
            f"📊 Активных: {len(active_bookings)}\n"
            f"💰 Выручка: {total_revenue} ₽\n\n"
            f"💈 Мастеров: {len(masters)}\n"
            f"✂️ Услуг: {len(services)}"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_main")]
            ])
        )


@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.answer()
    await callback.message.edit_text(
        "📋 <b>Главное меню</b>",
        reply_markup=get_main_menu_keyboard()
    )