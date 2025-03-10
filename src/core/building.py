from typing import Dict, List, Any, Optional
from .floor import Floor
from datetime import datetime
from uuid import uuid4

class Building:
    def __init__(
        self,
        building_id: str,
        name: str,
        location: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ):
        self.building_id = building_id
        self.name = name
        self.location = location
        self.config = config or {}
        self.floors: Dict[str, Floor] = {}
        self.creation_date = datetime.now()
        self.last_update = self.creation_date
        
    def add_floor(self, floor: Floor) -> None:
        """Añade un piso al edificio"""
        if floor.building_id != self.building_id:
            raise ValueError("El piso pertenece a otro edificio")
        self.floors[floor.floor_id] = floor
        self.last_update = datetime.now()
        
    def remove_floor(self, floor_id: str) -> None:
        """Elimina un piso del edificio"""
        if floor_id in self.floors:
            del self.floors[floor_id]
            self.last_update = datetime.now()
            
    def get_floor(self, floor_id: str) -> Optional[Floor]:
        """Obtiene un piso específico"""
        return self.floors.get(floor_id)
    
    def get_all_devices(self) -> List[Dict[str, Any]]:
        """Obtiene todos los dispositivos en el edificio"""
        devices = []
        for floor in self.floors.values():
            for room in floor.get_all_rooms():
                devices.extend(room.get_devices())
        return [device.to_dict() for device in devices]
    
    def get_devices_by_type(self, device_type: str) -> List[Dict[str, Any]]:
        """Obtiene todos los dispositivos de un tipo específico"""
        devices = []
        for floor in self.floors.values():
            devices.extend(floor.get_devices_by_type(device_type))
        return devices
    
    def get_building_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del edificio"""
        total_floors = len(self.floors)
        total_rooms = sum(len(floor.rooms) for floor in self.floors.values())
        total_devices = len(self.get_all_devices())
        
        return {
            "total_floors": total_floors,
            "total_rooms": total_rooms,
            "total_devices": total_devices,
            "last_update": self.last_update.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el edificio a diccionario para serialización"""
        return {
            "building_id": self.building_id,
            "name": self.name,
            "location": self.location,
            "config": self.config,
            "floors": {floor_id: floor.to_dict() for floor_id, floor in self.floors.items()},
            "stats": self.get_building_stats(),
            "creation_date": self.creation_date.isoformat(),
            "last_update": self.last_update.isoformat()
        }
