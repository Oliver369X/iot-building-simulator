from typing import Dict, Any, Optional
from .base import Device
import random
from datetime import datetime

class PowerMeter(Device):
    def __init__(self, device_id: str, room_id: str, config: Optional[Dict[str, Any]] = None):
        Device.__init__(self, "power_meter", device_id, room_id, config)
        self.total_consumption = 0.0  # kWh
        self.current_power = 0.0  # kW
        self.voltage = 220.0  # V
        self.base_load = self.config.get("base_load", 1.0)  # kW
        
    def generate_data(self) -> Dict[str, Any]:
        # Simula consumo de energía con variaciones
        time_factor = 1.0  # Factor según hora del día (podría variar)
        variation = random.uniform(-0.2, 0.2)
        
        self.current_power = max(0, self.base_load * time_factor + variation)
        self.voltage = 220.0 + random.uniform(-5, 5)
        
        # Acumula consumo (asumiendo intervalos de 5 minutos)
        interval_hours = 5/60
        self.total_consumption += self.current_power * interval_hours
        
        self.last_update = datetime.now()
        
        return {
            "current_power": round(self.current_power, 2),
            "voltage": round(self.voltage, 1),
            "total_consumption": round(self.total_consumption, 2),
            "unit": "kWh",
            "timestamp": self.last_update.isoformat()
        }
    
    def update_state(self, new_state: Dict[str, Any]) -> None:
        if "base_load" in new_state:
            self.base_load = new_state["base_load"]

class SmartPlug(Device):
    def __init__(self, device_id: str, room_id: str, config: Optional[Dict[str, Any]] = None):
        Device.__init__(self, "smart_plug", device_id, room_id, config)
        self.device_connected = self.config.get("device_connected", "unknown")
        self.current_power = 0.0

    def generate_data(self) -> Dict[str, Any]:
        if self.status == "active":
            self.current_power = random.uniform(50, 150)
        else:
            self.current_power = 0.0

        return {
            "status": self.status,
            "current_power": self.current_power,
            "device_connected": self.device_connected
        }
    
    def update_state(self, new_state: Dict[str, Any]) -> None:
        if "status" in new_state:
            self.status = new_state["status"]
        if "device_connected" in new_state:
            self.device_connected = new_state["device_connected"]

class SolarPanel(Device):
    def __init__(self, device_id: str, room_id: str, config: Optional[Dict[str, Any]] = None):
        Device.__init__(self, "solar_panel", device_id, room_id, config)
        self.current_power = 0.0  # kW
        self.total_generation = 0.0  # kWh
        self.efficiency = self.config.get("efficiency", 0.15)
        self.panel_area = self.config.get("panel_area", 1.6)  # m²
        self.status = "active"
        
    def generate_data(self) -> Dict[str, Any]:
        # Simula generación solar basada en hora del día
        hour = datetime.now().hour
        base_irradiance = max(0, min(1000, 
            -4.5 * (hour - 12) ** 2 + 1000))  # Máximo al mediodía
        
        # Añade variación por clima
        weather_factor = random.uniform(0.6, 1.0)
        actual_irradiance = base_irradiance * weather_factor
        
        # Calcula generación
        self.current_power = (actual_irradiance * self.panel_area * self.efficiency) / 1000
        
        # Acumula generación (asumiendo intervalos de 5 minutos)
        self.total_generation += self.current_power * (5/60)
        
        self.last_update = datetime.now()
        
        return {
            "current_power": round(self.current_power, 3),
            "total_generation": round(self.total_generation, 2),
            "efficiency": self.efficiency,
            "status": self.status,
            "irradiance": round(actual_irradiance, 1),
            "timestamp": self.last_update.isoformat()
        }
    
    def update_state(self, new_state: Dict[str, Any]) -> None:
        if "efficiency" in new_state:
            self.efficiency = new_state["efficiency"]
        if "status" in new_state:
            self.status = new_state["status"]
