from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from database.models import MasterService
from .base import BaseRepository


class MasterServiceRepository(BaseRepository[MasterService]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, MasterService)
    
    async def get_service_ids_by_master(self, master_id: int) -> list[int]:
        """Получить ID всех услуг, привязанных к мастеру"""
        query = select(MasterService.service_id).where(MasterService.master_id == master_id)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_master_ids_by_service(self, service_id: int) -> list[int]:
        """Получить ID всех мастеров, которые оказывают услугу"""
        query = select(MasterService.master_id).where(MasterService.service_id == service_id)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def add_service_to_master(self, master_id: int, service_id: int) -> bool:
        """Привязать услугу к мастеру"""
        # Проверяем, не существует ли уже такая связь
        query = select(MasterService).where(
            and_(
                MasterService.master_id == master_id,
                MasterService.service_id == service_id
            )
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            return False
        
        master_service = MasterService(master_id=master_id, service_id=service_id)
        self.session.add(master_service)
        await self.session.commit()
        return True
    
    async def remove_service_from_master(self, master_id: int, service_id: int) -> bool:
        """Отвязать услугу от мастера"""
        query = delete(MasterService).where(
            and_(
                MasterService.master_id == master_id,
                MasterService.service_id == service_id
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def sync_master_services(self, master_id: int, service_ids: list[int]) -> bool:
        """Синхронизировать услуги мастера (заменить все на новый список)"""
        # Удаляем все старые связи
        query = delete(MasterService).where(MasterService.master_id == master_id)
        await self.session.execute(query)
        
        # Добавляем новые
        for service_id in service_ids:
            master_service = MasterService(master_id=master_id, service_id=service_id)
            self.session.add(master_service)
        
        await self.session.commit()
        return True