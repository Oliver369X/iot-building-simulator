from typing import Dict, Any
from datetime import datetime

class Device:
    def __init__(self, device_type: str, device_id: str, room_id: str, config: Dict[str, Any] = None):
        """
        Args:
            device_type: Tipo de dispositivo
            device_id: ID único del dispositivo
            room_id: ID de la habitación donde está el dispositivo
            config: Configuración opcional del dispositivo
        """
        self.device_type = device_type
        self.device_id = device_id
        self.room_id = room_id
        self.config = config or {}
        self.status = "active"
        self.last_update = datetime.now()

    def generate_data(self) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement generate_data()")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el dispositivo a diccionario para serialización"""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "room_id": self.room_id,
            "config": self.config,
            "status": self.status,
            "last_update": self.last_update.isoformat()
        } 