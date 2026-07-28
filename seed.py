import asyncio
from database.db import db
from database.models import Master, Service, MasterService

async def seed():
    await db.create_tables()
    
    async with db.get_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Master))
        existing = result.scalars().first()
        
        if existing:
            print("⚠️ Данные уже есть в БД. Пропускаем.")
            return
        
        # Добавляем мастеров
        masters = [
            Master(name="Алексей", is_active=True),
            Master(name="Дмитрий", is_active=True),
            Master(name="Сергей", is_active=True),
        ]
        session.add_all(masters)
        await session.flush()
        
        # Добавляем услуги
        services = [
            Service(name="Мужская стрижка", description="Классическая стрижка", price=1500, duration_minutes=40),
            Service(name="Стрижка бороды", description="Моделирование бороды", price=800, duration_minutes=30),
            Service(name="Комплекс (стрижка+борода)", description="Полный образ", price=2000, duration_minutes=60),
            Service(name="Детская стрижка", description="Стрижка для детей до 12 лет", price=1000, duration_minutes=30),
        ]
        session.add_all(services)
        await session.flush()
        
        # Привязываем услуги к мастерам
        master_services = [
            MasterService(master_id=1, service_id=1),
            MasterService(master_id=1, service_id=2),
            MasterService(master_id=1, service_id=3),
            MasterService(master_id=2, service_id=1),
            MasterService(master_id=2, service_id=3),
            MasterService(master_id=3, service_id=1),
            MasterService(master_id=3, service_id=2),
            MasterService(master_id=3, service_id=4),
        ]
        session.add_all(master_services)
        
        await session.commit()
        print("✅ База данных заполнена тестовыми данными!")

if __name__ == "__main__":
    asyncio.run(seed())