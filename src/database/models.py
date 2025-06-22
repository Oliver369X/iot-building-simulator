from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Index, Table, Text
from sqlalchemy.dialects.postgresql import JSONB # For explicit JSONB, though SA JSON often defaults to it on PG
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone # Added timezone for UTC awareness

class MixinAsDict:
    def to_dict(self):
        """
        Convierte una instancia de modelo SQLAlchemy en un diccionario.
        Maneja objetos datetime y JSONB para una serialización adecuada.
        """
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                # Convertir datetime a formato ISO 8601 con sufijo 'Z' para UTC
                data[column.name] = value.isoformat().replace("+00:00", "Z")
            elif isinstance(value, dict) and column.type.__class__.__name__ == 'JSONB':
                # Asegurar que los datos JSONB se incluyan como un diccionario
                data[column.name] = value
            else:
                data[column.name] = value
        return data

Base = declarative_base()

# Edificios y Estructura
class Building(MixinAsDict, Base):
    __tablename__ = 'buildings'
    
    id = Column(String, primary_key=True) # Assuming UUIDs are stored as strings
    name = Column(Text, nullable=False)
    address = Column(Text)
    geolocation = Column(JSONB) # JSONB for geo data
    is_simulating = Column(Boolean, default=False) # New field for simulation control
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Floor(MixinAsDict, Base):
    __tablename__ = 'floors'
    
    id = Column(String, primary_key=True) # Assuming UUIDs are stored as strings
    building_id = Column(String, ForeignKey('buildings.id', ondelete='CASCADE'))
    floor_number = Column(Integer, nullable=False)
    plan_url = Column(Text, nullable=True)
    is_simulating = Column(Boolean, default=False) # New field for simulation control
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Room(MixinAsDict, Base):
    __tablename__ = 'rooms'
    
    id = Column(String, primary_key=True) # Assuming UUIDs are stored as strings
    floor_id = Column(String, ForeignKey('floors.id', ondelete='CASCADE'))
    name = Column(Text, nullable=False) # Changed from room_number
    is_simulating = Column(Boolean, default=False) # New field for simulation control
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

# Dispositivos y Configuración
class DeviceType(MixinAsDict, Base):
    __tablename__ = 'device_types'
    
    id = Column(String, primary_key=True) # Assuming UUIDs are stored as strings
    type_name = Column(Text, nullable=False) # Changed from name
    properties = Column(JSONB) # e.g., { "unit": "°C", "actions": ["setState", "setValue"] }
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Device(MixinAsDict, Base):
    __tablename__ = 'devices'
    
    id = Column(String, primary_key=True) # Assuming UUIDs are stored as strings
    name = Column(Text, nullable=False)
    device_type_id = Column(String, ForeignKey('device_types.id'))
    room_id = Column(String, ForeignKey('rooms.id', ondelete='CASCADE'))
    state = Column(JSONB) # e.g., { "power": "OFF", "brightness": 80, "target_temp": 21 }
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class DeviceSchedule(MixinAsDict, Base):
    __tablename__ = 'device_schedules'

    id = Column(String, primary_key=True) # Assuming UUIDs are stored as strings
    device_id = Column(String, ForeignKey('devices.id', ondelete='CASCADE'))
    cron_expression = Column(Text, nullable=False) # e.g., '0 18 * * *'
    action = Column(JSONB, nullable=False) # e.g., { "type": "setState", "payload": { "power": "ON" } }
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Alarm(MixinAsDict, Base):
    __tablename__ = 'alarms' # Renamed from alert_events
    
    id = Column(String, primary_key=True) # Changed from Integer, assuming UUIDs
    device_id = Column(String, ForeignKey('devices.id', ondelete='CASCADE'))
    severity = Column(Text, nullable=False) # e.g., 'CRITICAL', 'HIGH'
    status = Column(Text, nullable=False, default='NEW') # e.g., 'NEW', 'ACK', 'RESOLVED'
    description = Column(Text)
    triggered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)) # Ensure TIMESTAMPZ behavior
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

# Datos y Mediciones (SensorReading kept for now, as Telemetry is for a different DB)
class SensorReading(MixinAsDict, Base):
    __tablename__ = 'sensor_readings'
    __table_args__ = (
        Index('idx_sensor_time', 'device_id', 'timestamp'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey('devices.id', ondelete='CASCADE'))
    timestamp = Column(DateTime(timezone=True), nullable=False, primary_key=True, default=lambda: datetime.now(timezone.utc))
    value = Column(Float)
    unit = Column(String)
    quality = Column(Float)
    extra_data = Column(JSON) # Kept for now, might be useful for specific sensor data

    device = relationship("Device") # Simpler relationship for now

# Actualizar la relación en la clase Device (if SensorReadings are kept)
# Device.readings = relationship("SensorReading", back_populates="device", cascade="all, delete-orphan")
# For now, let's remove the explicit back_populates if we are simplifying or might remove SensorReading later.
# If SensorReading is definitely staying and linked, this relationship should be robust.


# class EnergyConsumption(Base):
#     __tablename__ = 'energy_consumption'
#     __table_args__ = (
#         Index('idx_energy_time', 'device_id', 'timestamp'),
#     )
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     device_id = Column(String, ForeignKey('devices.id'))
#     timestamp = Column(DateTime(timezone=True), nullable=False, primary_key=True, default=lambda: datetime.now(timezone.utc))
#     consumption = Column(Float)
#     peak_demand = Column(Float)
#     extra_data = Column(JSON)

# Agregaciones y Estadísticas (Commented out as per new spec)
# class DailyStats(Base):
#     __tablename__ = 'daily_stats'
#
#     id = Column(Integer, primary_key=True)
#     device_id = Column(String, ForeignKey('devices.id'))
#     date = Column(DateTime(timezone=True), nullable=False)
#     min_value = Column(Float)
#     max_value = Column(Float)
#     avg_value = Column(Float)
#     samples_count = Column(Integer)
#     extra_data = Column(JSON)

# Mantenimiento y Eventos (Commented out as per new spec)
# class MaintenanceLog(Base):
#     __tablename__ = 'maintenance_logs'
#
#     id = Column(Integer, primary_key=True)
#     device_id = Column(String, ForeignKey('devices.id'))
#     timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
#     type = Column(String)  # preventivo, correctivo
#     description = Column(String)
#     technician = Column(String)
#     extra_data = Column(JSON)
