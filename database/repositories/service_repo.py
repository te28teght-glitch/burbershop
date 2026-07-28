from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.models import Service, Master
from .base import BaseRepository


class ServiceRepository(BaseRepository[Service]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Service)
    
    async def get_by_master(self, master_id: int) -> list[Service]:
        query = (
            select(Service)
            .join(Service.masters)
            .where(Master.id == master_id)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_with_masters(self, service_id: int) -> Service | None:
        query = (
            select(Service)
            .where(Service.id == service_id)
            .options(selectinload(Service.masters))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()