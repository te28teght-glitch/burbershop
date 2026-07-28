from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import config
from .models import Base

class Database:
    def __init__(self):
        self.engine = create_async_engine(
            config.DATABASE_URL,
            echo=True,
            future=True
        )
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    def get_session(self):
        """Возвращает контекстный менеджер для сессии"""
        return self.async_session()

db = Database()