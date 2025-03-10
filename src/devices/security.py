from typing import Dict, Any, Optional
from ..devices.base import Device
import random
from datetime import datetime

class MotionSensor(Device):
    def __init__(self, device_id: str, room_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__("motion_sensor", device_id, room_id, config)
        self.sensitivity = self.config.get("sensitivity", 0.5)
        self.motion_detected = False
        self.last_detection = None
        
    def generate_data(self) -> Dict[str, Any]:
        self.motion_detected = random.random() < self.sensitivity
        return {
            "motion_detected": self.motion_detected,
            "sensitivity": self.sensitivity
        }
    
    def update_state(self, new_state: Dict[str, Any]) -> None:
        if "sensitivity" in new_state:
            self.sensitivity = max(0.0, min(1.0, new_state["sensitivity"]))

class SecurityCamera(Device):
    def __init__(self, device_id: str, room_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__("security_camera", device_id, room_id, config)
        self.status = "recording"
        self.resolution = self.config.get("resolution", "1080p")
        self.recording_mode = self.config.get("recording_mode", "motion")
        self.storage_usage = 0.0
        
    def generate_data(self) -> Dict[str, Any]:
        if self.status == "recording":
            # Simula uso de almacenamiento
            if self.resolution == "1080p":
                storage_increment = random.uniform(0.1, 0.2)  # GB por intervalo
            else:  # 720p
                storage_increment = random.uniform(0.05, 0.1)
            
            self.storage_usage += storage_increment
        
        self.last_update = datetime.now()
        
        return {
            "status": self.status,
            "resolution": self.resolution,
            "recording_mode": self.recording_mode,
            "storage_usage": round(self.storage_usage, 2),
            "timestamp": self.last_update.isoformat()
        }
    
    def update_state(self, new_state: Dict[str, Any]) -> None:
        if "status" in new_state:
            self.status = new_state["status"]
        if "resolution" in new_state:
            self.resolution = new_state["resolution"]
        if "recording_mode" in new_state:
            self.recording_mode = new_state["recording_mode"]

class AccessControl(Device):
    def __init__(self, device_id: str, room_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__("access_control", device_id, room_id, config)
        self.status = "locked"
        self.last_access = None
        self.authorized_cards = self.config.get("authorized_cards", [])
        self.access_log = []
        
    def generate_data(self) -> Dict[str, Any]:
        # Simula intentos de acceso aleatorios
        if random.random() < 0.1:  # 10% de probabilidad de intento de acceso
            card_id = random.choice(self.authorized_cards) if random.random() < 0.8 else "unauthorized"
            access_time = datetime.now()
            access_granted = card_id in self.authorized_cards
            
            if access_granted:
                self.status = "unlocked"
                self.last_access = access_time
                
            self.access_log.append({
                "card_id": card_id,
                "timestamp": access_time.isoformat(),
                "granted": access_granted
            })
            
            # Vuelve a bloquear después de 5 segundos
            if self.status == "unlocked":
                self.status = "locked"
        
        self.last_update = datetime.now()
        
        return {
            "status": self.status,
            "last_access": self.last_access.isoformat() if self.last_access else None,
            "recent_access": self.access_log[-5:],  # Últimos 5 accesos
            "timestamp": self.last_update.isoformat()
        }
    
    def update_state(self, new_state: Dict[str, Any]) -> None:
        if "authorized_cards" in new_state:
            self.authorized_cards = new_state["authorized_cards"]
        if "status" in new_state:
            self.status = new_state["status"]
