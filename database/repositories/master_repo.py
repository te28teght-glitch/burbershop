from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.models import Master
from .base import BaseRepository


class MasterRepository(BaseRepository[Master]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Master)
    
    async def get_with_services(self, master_id: int) -> Master | None:
        query = (
            select(Master)
            .where(Master.id == master_id)
            .options(selectinload(Master.services))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_masters(self) -> list[Master]:
        query = select(Master).where(Master.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_work_days(self, master_id: int) -> list[int]:
        """Получить дни работы мастера"""
        master = await self.get_by_id(master_id)
        if master:
            return master.work_days or []
        return []