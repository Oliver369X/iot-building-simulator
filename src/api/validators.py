from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
import uuid

class DeviceCreate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(..., pattern="^(temperature_sensor|pressure_sensor|valve_controller|damper_controller|frequency_controller|power_meter)$")
    status: str = Field(..., pattern="^(active|inactive)$")
    model: Optional[str] = None
    update_interval: int = Field(default=10, ge=1)  # Intervalo de actualización en segundos

class Room(BaseModel):
    number: int = Field(..., ge=0)
    devices: List[DeviceCreate]

class Floor(BaseModel):
    number: int = Field(..., ge=0)
    rooms: List[Room]

class BuildingCreate(BaseModel):
    name: str
    type: str = Field(..., pattern="^(office|residential|commercial)$")
    floors: List[Floor]

class DeviceStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|inactive)$")
    reading: Optional[float] = None
    timestamp: Optional[datetime] = None

class SimulationStart(BaseModel):
    building_id: str
    duration: Optional[int] = Field(default=3600, ge=1)
    events_per_second: Optional[float] = Field(default=1.0, gt=0) 