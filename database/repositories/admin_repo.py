from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from database.models import Admin
from .base import BaseRepository


class AdminRepository(BaseRepository[Admin]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Admin)
    
    async def get_by_telegram_id(self, telegram_id: int) -> Admin | None:
        query = select(Admin).where(Admin.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_admins(self) -> list[Admin]:
        query = select(Admin).where(Admin.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def add_admin(self, telegram_id: int, username: str = None, full_name: str = None) -> Admin:
        admin = Admin(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name
        )
        self.session.add(admin)
        await self.session.commit()
        await self.session.refresh(admin)
        return admin
    
    async def remove_admin(self, telegram_id: int) -> bool:
        admin = await self.get_by_telegram_id(telegram_id)
        if admin:
            admin.is_active = False
            await self.session.commit()
            return True
        return False
    
    async def is_admin(self, telegram_id: int) -> bool:
        admin = await self.get_by_telegram_id(telegram_id)
        return admin is not None and admin.is_active