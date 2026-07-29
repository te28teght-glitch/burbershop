from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float, BigInteger, Time
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, time

Base = declarative_base()

class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Master(Base):
    __tablename__ = "masters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    telegram_id = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Рабочее время
    work_start = Column(Time, default=time(10, 0))
    work_end = Column(Time, default=time(20, 0))
    slot_duration = Column(Integer, default=30)
    
    services = relationship("Service", secondary="master_services", back_populates="masters")

class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    masters = relationship("Master", secondary="master_services", back_populates="services")

class MasterService(Base):
    __tablename__ = "master_services"
    
    master_id = Column(Integer, ForeignKey("masters.id", ondelete="CASCADE"), primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), primary_key=True)

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(100), nullable=False)
    client_phone = Column(String(20), nullable=False)
    client_telegram_id = Column(String(50), nullable=False)
    
    master_id = Column(Integer, ForeignKey("masters.id", ondelete="CASCADE"))
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"))
    
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_confirmed = Column(Boolean, default=False)
    is_canceled = Column(Boolean, default=False)
    canceled_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    
    master = relationship("Master")
    service = relationship("Service")