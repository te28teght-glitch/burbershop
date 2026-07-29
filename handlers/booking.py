from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime, timedelta

from database.db import db
from database.repositories.master_repo import MasterRepository
from database.repositories.service_repo import ServiceRepository
from database.repositories.booking_repo import BookingRepository
from database.models import Booking
from keyboards.inline import (
    get_main_menu_keyboard,
    get_masters_keyboard,
    get_services_keyboard,
    get_time_slots_keyboard
)

router = Router()

class BookingStates(StatesGroup):
    waiting_for_master = State()
    waiting_for_service = State()
    waiting_for_datetime = State()
    waiting_for_time = State()
    waiting_for_name = State()
    waiting_for_phone = State()


@router.message(Command("booking"))
async def cmd_booking(message: types.Message):
    async with db.get_session() as session:
        repo = MasterRepository(session)
        masters = await repo.get_active_masters()
        
        if not masters:
            await message.answer("😔 К сожалению, сейчас нет доступных мастеров.")
            return
        
        await message.answer(
            "👤 <b>Выберите мастера:</b>",
            reply_markup=get_masters_keyboard(masters)
        )


@router.callback_query(lambda c: c.data == "booking_start")
async def process_booking_start(callback: CallbackQuery):
    await callback.answer()
    async with db.get_session() as session:
        repo = MasterRepository(session)
        masters = await repo.get_active_masters()
        
        if not masters:
            await callback.message.edit_text(
                "😔 К сожалению, сейчас нет доступных мастеров.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        await callback.message.edit_text(
            "👤 <b>Выберите мастера:</b>",
            reply_markup=get_masters_keyboard(masters)
        )


@router.callback_query(lambda c: c.data.startswith("master_") and not c.data.startswith("master_edit_") and c.data.split("_")[1].isdigit())
async def process_master_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    master_id = int(callback.data.split("_")[1])
    await state.update_data(master_id=master_id)
    
    async with db.get_session() as session:
        repo = ServiceRepository(session)
        services = await repo.get_by_master(master_id)
        
        if not services:
            await callback.message.edit_text(
                "😔 У этого мастера пока нет услуг.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        master_repo = MasterRepository(session)
        master = await master_repo.get_by_id(master_id)
        master_name = master.name if master else "Мастер"
        
        await callback.message.edit_text(
            f"✂️ <b>Услуги мастера {master_name}:</b>\n\n"
            "Выберите услугу:",
            reply_markup=get_services_keyboard(services, master_id)
        )


@router.callback_query(lambda c: c.data.startswith("service_") and not c.data.startswith("service_edit_") and not c.data.startswith("service_add_") and not c.data.startswith("service_delete_"))
async def process_service_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split("_")
    if len(parts) != 3:
        await callback.answer("⏳ Пожалуйста, подождите...")
        return
    
    try:
        master_id = int(parts[1])
        service_id = int(parts[2])
    except ValueError:
        await callback.answer("⏳ Пожалуйста, подождите...")
        return
    
    await state.update_data(service_id=service_id, master_id=master_id)
    
    # Получаем клавиатуру с рабочими днями мастера
    keyboard = await get_date_keyboard(master_id)
    
    await callback.message.edit_text(
        "📅 <b>Выберите дату:</b>\n\n"
        "Выберите день для записи:",
        reply_markup=keyboard
    )
    
    await state.set_state(BookingStates.waiting_for_datetime)


@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        "📋 <b>Главное меню</b>",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(lambda c: c.data == "back_to_masters")
async def back_to_masters(callback: CallbackQuery):
    await callback.answer()
    async with db.get_session() as session:
        repo = MasterRepository(session)
        masters = await repo.get_active_masters()
        
        await callback.message.edit_text(
            "👤 <b>Выберите мастера:</b>",
            reply_markup=get_masters_keyboard(masters)
        )


@router.callback_query(lambda c: c.data == "back_to_services")
async def back_to_services(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    master_id = data.get('master_id')
    
    if not master_id:
        await callback.message.edit_text(
            "⚠️ Ошибка, попробуйте начать запись заново.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    async with db.get_session() as session:
        repo = ServiceRepository(session)
        services = await repo.get_by_master(master_id)
        
        master_repo = MasterRepository(session)
        master = await master_repo.get_by_id(master_id)
        master_name = master.name if master else "Мастер"
        
        await callback.message.edit_text(
            f"✂️ <b>Услуги мастера {master_name}:</b>\n\n"
            "Выберите услугу:",
            reply_markup=get_services_keyboard(services, master_id)
        )


@router.callback_query(lambda c: c.data == "back_to_date")
async def back_to_date(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    master_id = data.get('master_id')
    
    keyboard = await get_date_keyboard(master_id)
    
    await callback.message.edit_text(
        "📅 <b>Выберите дату:</b>\n\n"
        "Выберите день для записи:",
        reply_markup=keyboard
    )
    await state.set_state(BookingStates.waiting_for_datetime)


@router.callback_query(lambda c: c.data == "my_bookings")
async def process_my_bookings(callback: CallbackQuery):
    await callback.answer()
    telegram_id = str(callback.from_user.id)
    
    async with db.get_session() as session:
        repo = BookingRepository(session)
        bookings = await repo.get_by_client(telegram_id)
        
        if not bookings:
            await callback.message.edit_text(
                "📋 <b>Ваши записи</b>\n\n"
                "У вас пока нет активных записей.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        text = "📋 <b>Ваши записи:</b>\n\n"
        for i, booking in enumerate(bookings, 1):
            status = "✅ Подтверждена" if booking.is_confirmed else "⏳ Ожидает"
            text += (
                f"{i}. {booking.service.name} — {booking.master.name}\n"
                f"   📅 {booking.start_time.strftime('%d.%m.%Y %H:%M')}\n"
                f"   Статус: {status}\n"
                f"   ID: #{booking.id}\n\n"
            )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_main_menu_keyboard()
        )


@router.callback_query(lambda c: c.data == "contacts")
async def process_contacts(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "📞 <b>Наши контакты:</b>\n\n"
        "📍 Адрес: ул. Петровская, д. 15\n"
        "📱 Телефон: +7 (999) 123-45-67\n"
        "🕐 Режим работы: 10:00 - 22:00\n\n"
        "💬 Также вы можете связаться с нами в Telegram:\n"
        "@barbershop_petrovsky",
        reply_markup=get_main_menu_keyboard()
    )


async def get_date_keyboard(master_id: int = None):
    """Клавиатура для выбора даты (только рабочие дни мастера)"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    today = datetime.now()
    
    # Если есть master_id, получаем дни работы
    work_days = None
    if master_id:
        async with db.get_session() as session:
            repo = MasterRepository(session)
            master = await repo.get_by_id(master_id)
            if master:
                work_days = master.work_days
    
    days_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    buttons_added = 0
    
    # Показываем следующие 14 дней
    for i in range(14):
        date = today + timedelta(days=i)
        day_of_week = date.weekday()
        day_name = days_names[day_of_week]
        
        # Если мастер не выбран или день рабочий - показываем
        if work_days is None or day_of_week in work_days:
            builder.button(
                text=f"📅 {day_name} {date.strftime('%d.%m')}",
                callback_data=f"date_{date.strftime('%Y-%m-%d')}"
            )
            buttons_added += 1
    
    # Если нет доступных дней, показываем сообщение
    if buttons_added == 0:
        builder.button(
            text="😔 Нет доступных дней",
            callback_data="no_days"
        )
    
    builder.button(text="⬅️ Назад к услугам", callback_data="back_to_services")
    builder.adjust(2)
    return builder.as_markup()


@router.callback_query(lambda c: c.data.startswith("date_"))
async def process_date_selection(callback: CallbackQuery, state: FSMContext):
    """Выбор даты -> показываем свободное время"""
    await callback.answer()
    date_str = callback.data.split("_")[1]
    selected_date = datetime.strptime(date_str, "%Y-%m-%d")
    
    data = await state.get_data()
    master_id = data.get('master_id')
    service_id = data.get('service_id')
    
    if not master_id or not service_id:
        await callback.message.edit_text(
            "⚠️ Ошибка, попробуйте начать запись заново.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    async with db.get_session() as session:
        master_repo = MasterRepository(session)
        master = await master_repo.get_by_id(master_id)
        
        if not master:
            await callback.message.edit_text(
                "⚠️ Мастер не найден.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Проверяем, работает ли мастер в этот день
        day_of_week = selected_date.weekday()
        work_days = master.work_days or []
        
        if day_of_week not in work_days:
            days_names = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
            work_days_str = ", ".join([days_names[d] for d in work_days]) if work_days else "не работает"
            
            keyboard = await get_date_keyboard(master_id)
            await callback.message.edit_text(
                f"😔 Мастер <b>{master.name}</b> не работает в {days_names[day_of_week]}.\n\n"
                f"📅 Дни работы: <b>{work_days_str}</b>\n\n"
                "Пожалуйста, выберите другой день:",
                reply_markup=keyboard
            )
            return
        
        service_repo = ServiceRepository(session)
        service = await service_repo.get_by_id(service_id)
        
        if not service:
            await callback.message.edit_text(
                "⚠️ Услуга не найдена.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        duration_minutes = service.duration_minutes
        
        booking_repo = BookingRepository(session)
        available_slots = await booking_repo.get_available_slots(
            master_id=master_id,
            date=selected_date,
            duration_minutes=duration_minutes
        )
        
        if not available_slots:
            keyboard = await get_date_keyboard(master_id)
            await callback.message.edit_text(
                f"😔 На {selected_date.strftime('%d.%m.%Y')} нет свободных слотов.\n\n"
                "Пожалуйста, выберите другую дату:",
                reply_markup=keyboard
            )
            return
        
        await state.update_data(selected_date=date_str)
        keyboard = get_time_slots_keyboard(available_slots)
        
        await callback.message.edit_text(
            f"⏰ <b>Выберите время на {selected_date.strftime('%d.%m.%Y')}:</b>\n\n"
            f"🟢 Свободно | 🔴 Занято\n\n"
            f"Длительность услуги: {duration_minutes} минут",
            reply_markup=keyboard
        )
        await state.set_state(BookingStates.waiting_for_time)


@router.callback_query(lambda c: c.data.startswith("time_"))
async def process_time_selection(callback: CallbackQuery, state: FSMContext):
    """Выбор времени"""
    await callback.answer()
    
    parts = callback.data.split("_")
    if len(parts) != 3:
        await callback.answer("⏳ Пожалуйста, подождите...")
        return
    
    date_str = parts[1]
    time_str = parts[2]
    start_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    
    state_data = await state.get_data()
    master_id = state_data.get('master_id')
    service_id = state_data.get('service_id')
    
    if not master_id or not service_id:
        await callback.message.edit_text(
            "⚠️ Ошибка, попробуйте начать запись заново.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    async with db.get_session() as session:
        service_repo = ServiceRepository(session)
        service = await service_repo.get_by_id(service_id)
        
        if not service:
            await callback.message.edit_text(
                "⚠️ Услуга не найдена.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        duration_minutes = service.duration_minutes
        
        booking_repo = BookingRepository(session)
        is_available = await booking_repo.is_time_available(
            master_id=master_id,
            start_time=start_time,
            duration_minutes=duration_minutes
        )
        
        if not is_available:
            available_slots = await booking_repo.get_available_slots(
                master_id=master_id,
                date=start_time,
                duration_minutes=duration_minutes
            )
            
            if not available_slots:
                keyboard = await get_date_keyboard(master_id)
                await callback.message.edit_text(
                    "⏰ <b>Это время уже занято!</b>\n\n"
                    "Свободных слотов на эту дату больше нет.\n"
                    "Пожалуйста, выберите другую дату:",
                    reply_markup=keyboard
                )
                return
            
            keyboard = get_time_slots_keyboard(available_slots)
            await callback.message.edit_text(
                "⏰ <b>Это время уже занято!</b>\n\n"
                "Пожалуйста, выберите другое время:",
                reply_markup=keyboard
            )
            return
        
        await state.update_data(start_time=start_time.isoformat())
        
        await callback.message.edit_text(
            f"✅ <b>Время свободно!</b>\n\n"
            f"📅 {start_time.strftime('%d.%m.%Y %H:%M')}\n\n"
            "👤 <b>Введите ваше имя:</b>",
            reply_markup=None
        )
        await state.set_state(BookingStates.waiting_for_name)


@router.message(BookingStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(client_name=message.text.strip())
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "📱 <b>Введите ваш номер телефона:</b>\n\n"
        "Нажмите кнопку ниже, чтобы отправить автоматически,\n"
        "или введите номер вручную (например: +79991234567)",
        reply_markup=keyboard
    )
    await state.set_state(BookingStates.waiting_for_phone)


@router.message(BookingStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text.strip()
    
    await message.answer(
        "⏳ Создаем запись...",
        reply_markup=ReplyKeyboardRemove()
    )
    
    data = await state.get_data()
    master_id = data.get('master_id')
    service_id = data.get('service_id')
    start_time_str = data.get('start_time')
    client_name = data.get('client_name')
    
    if not start_time_str:
        await message.answer(
            "⚠️ Ошибка времени, попробуйте записаться заново.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    start_time = datetime.fromisoformat(start_time_str)
    
    async with db.get_session() as session:
        service_repo = ServiceRepository(session)
        service = await service_repo.get_by_id(service_id)
        
        if not service:
            await message.answer(
                "⚠️ Услуга не найдена.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        end_time = start_time + timedelta(minutes=service.duration_minutes)
        
        booking_repo = BookingRepository(session)
        is_available = await booking_repo.is_time_available(
            master_id=master_id,
            start_time=start_time,
            duration_minutes=service.duration_minutes
        )
        
        if not is_available:
            await message.answer(
                "⏰ К сожалению, это время уже занято.\n\n"
                "Пожалуйста, начните запись заново.",
                reply_markup=get_main_menu_keyboard()
            )
            await state.clear()
            return
        
        booking = Booking(
            client_name=client_name,
            client_phone=phone,
            client_telegram_id=str(message.from_user.id),
            master_id=master_id,
            service_id=service_id,
            start_time=start_time,
            end_time=end_time,
            is_confirmed=False
        )
        session.add(booking)
        await session.commit()
        await session.refresh(booking)
        booking_id = booking.id
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>Запись создана!</b>\n\n"
        f"👤 Имя: {client_name}\n"
        f"📱 Телефон: {phone}\n"
        f"🕐 Время: {start_time.strftime('%d.%m.%Y %H:%M')}\n"
        f"⏱ Длительность: {service.duration_minutes} мин\n\n"
        f"Номер записи: <b>#{booking_id}</b>\n\n"
        f"Администратор свяжется с вами для подтверждения.",
        reply_markup=get_main_menu_keyboard()
    )