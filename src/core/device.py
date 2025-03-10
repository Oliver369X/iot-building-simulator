from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

class Device(ABC):
    def __init__(
        self,
        device_type: str,
        location: Dict[str, str],
        config: Optional[Dict[str, Any]] = None
    ):
        self.device_id = str(uuid.uuid4())
        self.device_type = device_type
        self.location = location  # {building_id, floor_id, room_id}
        self.config = config or {}
        self.status = "active"
        self.last_update = datetime.now()
        
    @abstractmethod
    def generate_data(self) -> Dict[str, Any]:
        """Genera datos del dispositivo según su tipo"""
        pass
    
    @abstractmethod
    def update_state(self, new_state: Dict[str, Any]) -> None:
        """Actualiza el estado del dispositivo"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el dispositivo a diccionario para serialización"""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "location": self.location,
            "config": self.config,
            "status": self.status,
            "last_update": self.last_update.isoformat()
        }
