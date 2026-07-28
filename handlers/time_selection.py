from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from datetime import datetime, timedelta

from database.db import db
from database.repositories.booking_repo import BookingRepository
from database.repositories.service_repo import ServiceRepository
from keyboards.inline import get_time_slots_keyboard

router = Router()


@router.callback_query(lambda c: c.data.startswith("time_"))
async def process_time_selection(callback: CallbackQuery, state: FSMContext):
    """Выбор времени"""
    await callback.answer()
    
    # Парсим callback_data: time_YYYY-MM-DD_HH:MM
    data_parts = callback.data.split("_")
    date_str = data_parts[1]
    time_str = data_parts[2]
    
    # Формируем datetime
    start_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    
    # Получаем данные из состояния
    state_data = await state.get_data()
    master_id = state_data.get('master_id')
    service_id = state_data.get('service_id')
    
    if not master_id or not service_id:
        await callback.message.edit_text(
            "⚠️ Ошибка, попробуйте начать запись заново.",
            reply_markup=None
        )
        return
    
    # Получаем длительность услуги
    async with db.get_session() as session:
        service_repo = ServiceRepository(session)
        service = await service_repo.get_by_id(service_id)
        
        if not service:
            await callback.message.edit_text(
                "⚠️ Услуга не найдена.",
                reply_markup=None
            )
            return
        
        duration_minutes = service.duration_minutes
        
        # Проверяем, свободно ли время
        booking_repo = BookingRepository(session)
        is_available = await booking_repo.is_time_available(
            master_id=master_id,
            start_time=start_time,
            duration_minutes=duration_minutes
        )
        
        if not is_available:
            # Время занято - показываем другие слоты
            await callback.message.edit_text(
                "⏰ <b>Это время уже занято!</b>\n\n"
                "Пожалуйста, выберите другое время:",
                reply_markup=await get_available_slots_keyboard(
                    master_id=master_id,
                    date=start_time,
                    duration_minutes=duration_minutes
                )
            )
            return
        
        # Время свободно - сохраняем и переходим к имени
        await state.update_data(start_time=start_time.isoformat())
        
        await callback.message.edit_text(
            f"✅ <b>Время свободно!</b>\n\n"
            f"📅 {start_time.strftime('%d.%m.%Y %H:%M')}\n\n"
            "👤 <b>Введите ваше имя:</b>",
            reply_markup=None
        )
        from handlers.booking import BookingStates
        await state.set_state(BookingStates.waiting_for_name)


async def get_available_slots_keyboard(master_id: int, date: datetime, duration_minutes: int):
    """Получить клавиатуру с доступными слотами"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    async with db.get_session() as session:
        booking_repo = BookingRepository(session)
        
        # Получаем занятые слоты
        booked_slots = await booking_repo.get_booked_slots(
            master_id=master_id,
            date=date,
            service_duration=duration_minutes
        )
        
        # Генерируем все возможные слоты (с 10:00 до 20:00 с шагом 30 минут)
        builder = InlineKeyboardBuilder()
        start_hour = 10
        end_hour = 20
        
        current_time = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end_time = date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        
        has_slots = False
        
        while current_time < end_time:
            # Проверяем, свободен ли слот
            is_available = await booking_repo.is_time_available(
                master_id=master_id,
                start_time=current_time,
                duration_minutes=duration_minutes
            )
            
            if is_available:
                has_slots = True
                time_str = current_time.strftime("%H:%M")
                callback_data = f"time_{current_time.strftime('%Y-%m-%d')}_{time_str}"
                builder.button(
                    text=f"🟢 {time_str}",
                    callback_data=callback_data
                )
            else:
                time_str = current_time.strftime("%H:%M")
                # Занятые слоты показываем серыми (но не кликабельными)
                pass
            
            current_time += timedelta(minutes=30)
        
        builder.button(text="⬅️ Назад к дате", callback_data="back_to_date")
        builder.adjust(3)  # по 3 кнопки в ряд
        
        if not has_slots:
            # Если слотов нет - отдельное сообщение
            return None
        
        return builder.as_markup()