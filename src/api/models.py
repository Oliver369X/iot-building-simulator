from pydantic import BaseModel
from typing import List

class Device(BaseModel):
    type: str
    status: str = "active"

class Room(BaseModel):
    number: int
    devices: List[Device] = []

class Floor(BaseModel):
    number: int
    rooms: List[Room] = []

class BuildingCreate(BaseModel):
    name: str
    type: str
    floors: List[Floor]  # Esto espera una lista de pisos, no un número
    rooms_per_floor: int  # Habitaciones por piso 

class Building(BaseModel):
    id: str
    name: str
    type: str
    floors: List[Floor]
    devices_count: int = 0  # Añadir esto

    @property
    def calculate_devices_count(self) -> int:
        return sum(
            len(room.devices)
            for floor in self.floors
            for room in floor.rooms
        ) 