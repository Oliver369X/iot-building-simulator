from typing import Dict, Any, Optional
from .base import Device
import random
from datetime import datetime
import math

class TemperatureSensor(Device):
    def __init__(self, device_id: str, room_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            device_id=device_id,
            device_type="temperature_sensor",
            room_id=room_id,
            config=config or {}
        )
        self.current_temp = 21.0  # Temperatura inicial
        self.target_temp = self.config.get("target_temp", 22.0)
        self.last_update = datetime.now()
        self.inertia = 0.8  # Factor de inercia térmica (0-1)
        
    def generate_data(self) -> Dict[str, Any]:
        now = datetime.now()
        hour = now.hour
        
        # Ajustar temperatura objetivo según la hora del día
        if 8 <= hour <= 18:  # Horario laboral
            self.target_temp = 22.0
        else:  # Fuera de horario
            self.target_temp = 20.0
            
        # Simular influencia externa (clima)
        external_temp = 20.0 + 5.0 * math.sin(2 * math.pi * (hour - 6) / 24)  # Ciclo diario
        
        # Calcular cambio de temperatura con inercia
        temp_diff = (self.target_temp - self.current_temp) * (1 - self.inertia)
        external_influence = (external_temp - self.current_temp) * 0.1
        
        # Añadir pequeña variación aleatoria
        noise = random.uniform(-0.1, 0.1)
        
        # Actualizar temperatura actual
        self.current_temp += temp_diff + external_influence + noise
        
        # Asegurar que está en rango razonable
        self.current_temp = max(18.0, min(28.0, self.current_temp))
        
        return {
            "temperature": round(self.current_temp, 2),
            "target": round(self.target_temp, 2),
            "unit": "celsius",
            "timestamp": now.isoformat()
        }

class HVACController(Device):
    def __init__(self, device_id: str, room_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            device_id=device_id,
            device_type="hvac_controller",
            room_id=room_id,
            config=config or {}
        )
        self.mode = "auto"
        self.target_temp = 21.0
        
    def generate_data(self) -> Dict[str, Any]:
        return {
            "status": random.choice(["heating", "cooling", "idle"]),
            "target_temp": self.target_temp,
            "power_consumption": random.uniform(100, 1000)
        }
    
    def update_state(self, new_state: Dict[str, Any]) -> None:
        if "mode" in new_state:
            self.mode = new_state["mode"]
        if "target_temperature" in new_state:
            self.target_temp = new_state["target_temperature"]

class HumiditySensor(Device):
    def __init__(
        self,
        location: Dict[str, str],
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__("humidity_sensor", location, config)
        self.current_humidity = 50.0  # % inicial
        self.variation = 2.0  # variación máxima por lectura
        
    def generate_data(self) -> Dict[str, Any]:
        # Simula cambios en la humedad
        variation = random.uniform(-self.variation, self.variation)
        self.current_humidity = max(0, min(100, self.current_humidity + variation))
        self.current_humidity = round(self.current_humidity, 1)
        self.last_update = datetime.now()
        
        return {
            "humidity": self.current_humidity,
            "unit": "percentage",
            "timestamp": self.last_update.isoformat()
        }
    
    def update_state(self, new_state: Dict[str, Any]) -> None:
        if "base_humidity" in new_state:
            self.current_humidity = new_state["base_humidity"]
