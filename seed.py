import asyncio
from database.db import db
from database.models import Master, Service, MasterService, Admin

async def seed():
    await db.create_tables()
    
    async with db.get_session() as session:
        from sqlalchemy import select
        
        # Проверяем мастеров
        result = await session.execute(select(Master))
        existing_masters = result.scalars().first()
        
        if not existing_masters:
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
            
            print("✅ Мастера и услуги добавлены!")
        
        # Проверяем админов
        result = await session.execute(select(Admin))
        existing_admin = result.scalars().first()
        
        if not existing_admin:
            # Добавляем первого админа (ЗАМЕНИ НА СВОЙ TELEGRAM ID)
            admin = Admin(
                telegram_id=1178663467,  # ← ЗАМЕНИ НА СВОЙ ID
                username="admin",
                full_name="Главный администратор",
                is_active=True
            )
            session.add(admin)
            print("✅ Администратор добавлен!")
        
        await session.commit()
        print("✅ База данных заполнена!")

if __name__ == "__main__":
    asyncio.run(seed())