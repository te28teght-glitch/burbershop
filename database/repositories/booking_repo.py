from typing import List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from database.models import Booking
from .base import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Booking)
    
    async def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Booking]:
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
        booking = await self.get_by_id(booking_id)
        if booking:
            booking.is_canceled = True
            await self.session.commit()
            return True
        return False