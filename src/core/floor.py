from typing import Dict, List, Any, Optional
from .room import Room

class Floor:
    def __init__(
        self,
        floor_id: str,
        building_id: str,
        floor_number: int,
        config: Optional[Dict[str, Any]] = None
    ):
        self.floor_id = floor_id
        self.building_id = building_id
        self.floor_number = floor_number
        self.config = config or {}
        self.rooms: Dict[str, Room] = {}
        
    def add_room(self, room: Room) -> None:
        """Añade una habitación al piso"""
        if room.floor_id != self.floor_id:
            raise ValueError("La habitación pertenece a otro piso")
        self.rooms[room.room_id] = room
        
    def remove_room(self, room_id: str) -> None:
        """Elimina una habitación del piso"""
        if room_id in self.rooms:
            del self.rooms[room_id]
            
    def get_room(self, room_id: str) -> Optional[Room]:
        """Obtiene una habitación específica"""
        return self.rooms.get(room_id)
    
    def get_all_rooms(self) -> List[Room]:
        """Obtiene todas las habitaciones del piso"""
        return list(self.rooms.values())
    
    def get_devices_by_type(self, device_type: str) -> List[Dict[str, Any]]:
        """Obtiene todos los dispositivos de un tipo específico en el piso"""
        devices = []
        for room in self.rooms.values():
            devices.extend(room.get_devices(device_type))
        return [device.to_dict() for device in devices]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el piso a diccionario para serialización"""
        return {
            "floor_id": self.floor_id,
            "building_id": self.building_id,
            "floor_number": self.floor_number,
            "config": self.config,
            "rooms": {room_id: room.to_dict() for room_id, room in self.rooms.items()}
        }
