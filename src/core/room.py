from typing import Dict, List, Any, Optional
from .device import Device
from uuid import uuid4

class Room:
    def __init__(
        self,
        room_id: str,
        floor_id: str,
        room_type: str,
        area: float,
        config: Optional[Dict[str, Any]] = None
    ):
        self.room_id = room_id
        self.floor_id = floor_id
        self.room_type = room_type
        self.area = area
        self.config = config or {}
        self.devices: List[Device] = []
        
    def add_device(self, device_type: str, config: Dict[str, Any]):
        from src.devices.base import Device
        device = Device(
            device_id=str(uuid4()),
            device_type=device_type,
            room_id=self.room_id,
            config=config
        )
        self.devices.append(device)
        return device
        
    def remove_device(self, device_id: str) -> None:
        """Elimina un dispositivo de la habitación"""
        self.devices = [d for d in self.devices if d.device_id != device_id]
        
    def get_devices(self, device_type: str = None) -> List[Device]:
        """Obtiene dispositivos, opcionalmente filtrados por tipo"""
        if device_type:
            return [d for d in self.devices if d.device_type == device_type]
        return self.devices
        
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la habitación a diccionario para serialización"""
        return {
            "room_id": self.room_id,
            "floor_id": self.floor_id,
            "room_type": self.room_type,
            "area": self.area,
            "config": self.config,
            "devices": [d.to_dict() for d in self.devices]
        }
