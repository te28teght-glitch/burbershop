import asyncio
from datetime import time
from database.db import db
from database.models import Master, Service, MasterService, Admin

async def seed():
    await db.create_tables()
    
    async with db.get_session() as session:
        from sqlalchemy import select
        
        result = await session.execute(select(Master))
        existing_masters = result.scalars().first()
        
        if not existing_masters:
            masters = [
                Master(
                    name="Алексей", 
                    is_active=True,
                    work_start=time(10, 0),
                    work_end=time(21, 0),
                    slot_duration=30,
                    work_days=[0, 1, 2, 3, 4, 5]  # ПН-СБ
                ),
                Master(
                    name="Дмитрий", 
                    is_active=True,
                    work_start=time(9, 0),
                    work_end=time(20, 0),
                    slot_duration=30,
                    work_days=[0, 1, 2, 3, 4]  # ПН-ПТ
                ),
                Master(
                    name="Сергей", 
                    is_active=True,
                    work_start=time(11, 0),
                    work_end=time(22, 0),
                    slot_duration=30,
                    work_days=[1, 2, 3, 4, 5, 6]  # ВТ-ВС
                ),
            ]
            session.add_all(masters)
            await session.flush()
            
            services = [
                Service(name="Мужская стрижка", description="Классическая стрижка", price=1500, duration_minutes=40),
                Service(name="Стрижка бороды", description="Моделирование бороды", price=800, duration_minutes=30),
                Service(name="Комплекс (стрижка+борода)", description="Полный образ", price=2000, duration_minutes=60),
                Service(name="Детская стрижка", description="Стрижка для детей до 12 лет", price=1000, duration_minutes=30),
            ]
            session.add_all(services)
            await session.flush()
            
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
        
        result = await session.execute(select(Admin))
        existing_admin = result.scalars().first()
        
        if not existing_admin:
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