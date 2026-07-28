from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Master(Base):
    __tablename__ = "masters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    telegram_id = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    
    services = relationship("Service", secondary="master_services", back_populates="masters")

class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    
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
    
    master = relationship("Master")
    service = relationship("Service")