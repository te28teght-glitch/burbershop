from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from database.models import Booking
from .base import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Booking)
    
    async def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Booking]:
        """Получить записи за период"""
        query = (
            select(Booking)
            .where(
                and_(
                    Booking.start_time >= start_date,
                    Booking.start_time < end_date,
                    Booking.is_canceled == False
                )
            )
            .options(
                selectinload(Booking.master),
                selectinload(Booking.service)
            )
            .order_by(Booking.start_time)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_active_bookings(self) -> List[Booking]:
        """Получить все активные записи"""
        query = (
            select(Booking)
            .where(Booking.is_canceled == False)
            .options(
                selectinload(Booking.master),
                selectinload(Booking.service)
            )
            .order_by(Booking.start_time)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_client(self, telegram_id: str) -> List[Booking]:
        """Получить записи клиента"""
        query = (
            select(Booking)
            .where(
                and_(
                    Booking.client_telegram_id == telegram_id,
                    Booking.is_canceled == False,
                    Booking.start_time >= datetime.now()
                )
            )
            .options(
                selectinload(Booking.master),
                selectinload(Booking.service)
            )
            .order_by(Booking.start_time)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def cancel_booking(self, booking_id: int) -> bool:
        """Отменить запись"""
        booking = await self.get_by_id(booking_id)
        if booking:
            booking.is_canceled = True
            booking.canceled_at = datetime.now()
            await self.session.commit()
            return True
        return False
    
    async def get_booked_slots(
        self, 
        master_id: int, 
        date: datetime, 
        duration_minutes: int
    ) -> List[datetime]:
        """Получить все занятые слоты для мастера на конкретную дату"""
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        query = (
            select(Booking)
            .where(
                and_(
                    Booking.master_id == master_id,
                    Booking.start_time >= day_start,
                    Booking.start_time < day_end,
                    Booking.is_canceled == False
                )
            )
            .order_by(Booking.start_time)
        )
        result = await self.session.execute(query)
        bookings = result.scalars().all()
        
        booked_slots = []
        for booking in bookings:
            current = booking.start_time
            minutes = current.minute
            if minutes % 30 != 0:
                current = current.replace(minute=(minutes // 30) * 30)
            
            while current < booking.end_time:
                booked_slots.append(current)
                current += timedelta(minutes=30)
        
        return booked_slots
    
    async def is_time_available(
        self, 
        master_id: int, 
        start_time: datetime, 
        duration_minutes: int
    ) -> bool:
        """Проверить, свободно ли время"""
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        query = (
            select(Booking)
            .where(
                and_(
                    Booking.master_id == master_id,
                    Booking.is_canceled == False,
                    Booking.start_time < end_time,
                    Booking.end_time > start_time
                )
            )
        )
        result = await self.session.execute(query)
        overlapping = result.scalars().first()
        
        return overlapping is None
    
    async def get_available_slots(
        self,
        master_id: int,
        date: datetime,
        duration_minutes: int
    ) -> List[datetime]:
        """Получить все свободные слоты на дату с учётом рабочего времени мастера"""
        from database.repositories.master_repo import MasterRepository
        master_repo = MasterRepository(self.session)
        master = await master_repo.get_by_id(master_id)
        
        if not master:
            return []
        
        day_start = datetime.combine(date.date(), master.work_start)
        day_end = datetime.combine(date.date(), master.work_end)
        slot_step = master.slot_duration or 30
        
        booked_slots = await self.get_booked_slots(master_id, date, duration_minutes)
        
        available_slots = []
        current = day_start
        
        while current + timedelta(minutes=duration_minutes) <= day_end:
            is_available = True
            
            for booked in booked_slots:
                if booked >= current and booked < current + timedelta(minutes=duration_minutes):
                    is_available = False
                    break
            
            if is_available:
                if await self.is_time_available(master_id, current, duration_minutes):
                    available_slots.append(current)
            
            current += timedelta(minutes=slot_step)
        
        return available_slots