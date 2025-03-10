from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Index, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Edificios y Estructura
class Building(Base):
    __tablename__ = 'buildings'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    status = Column(String, default='active')
    extra_data = Column(JSON)  # Cambiado de metadata a extra_data
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Floor(Base):
    __tablename__ = 'floors'
    
    id = Column(String, primary_key=True)
    building_id = Column(String, ForeignKey('buildings.id', ondelete='CASCADE'))
    floor_number = Column(Integer, nullable=False)
    type = Column(String)  # tipo de piso (oficinas, residencial, etc.)
    area = Column(Float)
    extra_data = Column(JSON)  # Cambiado de metadata a extra_data

class Room(Base):
    __tablename__ = 'rooms'
    
    id = Column(String, primary_key=True)
    floor_id = Column(String, ForeignKey('floors.id', ondelete='CASCADE'))
    room_number = Column(String, nullable=False)
    type = Column(String)  # oficina, sala de reuniones, etc.
    area = Column(Float)
    extra_data = Column(JSON)  # Cambiado de metadata a extra_data

# Dispositivos y Configuración
class DeviceType(Base):
    __tablename__ = 'device_types'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String)  # sensor, actuador, etc.
    measurement_type = Column(String)  # temperatura, humedad, etc.
    properties = Column(JSON)  # Cambiado de metadata a properties

class Device(Base):
    __tablename__ = 'devices'
    
    id = Column(String, primary_key=True)
    room_id = Column(String, ForeignKey('rooms.id', ondelete='CASCADE'))
    device_type_id = Column(String, ForeignKey('device_types.id'))
    status = Column(String, default='active')
    installation_date = Column(DateTime, default=datetime.now)
    last_maintenance = Column(DateTime)
    config = Column(JSON)
    extra_data = Column(JSON)  # Cambiado de metadata a extra_data

# Datos y Mediciones
class SensorReading(Base):
    __tablename__ = 'sensor_readings'
    __table_args__ = (
        Index('idx_sensor_time', 'device_id', 'timestamp'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey('devices.id', ondelete='CASCADE'))
    timestamp = Column(DateTime, nullable=False, primary_key=True)
    value = Column(Float)
    unit = Column(String)
    quality = Column(Float)
    extra_data = Column(JSON)

    device = relationship("Device", back_populates="readings")

# Actualizar la relación en la clase Device
Device.readings = relationship("SensorReading", back_populates="device", cascade="all, delete-orphan")

class EnergyConsumption(Base):
    __tablename__ = 'energy_consumption'
    __table_args__ = (
        Index('idx_energy_time', 'device_id', 'timestamp'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey('devices.id'))
    timestamp = Column(DateTime, nullable=False, primary_key=True)
    consumption = Column(Float)
    peak_demand = Column(Float)
    extra_data = Column(JSON)

# Agregaciones y Estadísticas
class DailyStats(Base):
    __tablename__ = 'daily_stats'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String, ForeignKey('devices.id'))
    date = Column(DateTime, nullable=False)
    min_value = Column(Float)
    max_value = Column(Float)
    avg_value = Column(Float)
    samples_count = Column(Integer)
    extra_data = Column(JSON)  # Cambiado de metadata a extra_data

# Mantenimiento y Eventos
class MaintenanceLog(Base):
    __tablename__ = 'maintenance_logs'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String, ForeignKey('devices.id'))
    timestamp = Column(DateTime, default=datetime.now)
    type = Column(String)  # preventivo, correctivo
    description = Column(String)
    technician = Column(String)
    extra_data = Column(JSON)  # Cambiado de metadata a extra_data

class AlertEvent(Base):
    __tablename__ = 'alert_events'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String, ForeignKey('devices.id'))
    timestamp = Column(DateTime, default=datetime.now)
    type = Column(String)  # error, warning, info
    severity = Column(Integer)
    message = Column(String)
    extra_data = Column(JSON)  # Cambiado de metadata a extra_data 