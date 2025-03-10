from typing import Dict, Any, Optional
from ..core.device import Device
import random
from datetime import datetime

class Sensor(Device):
    """Clase base para sensores genéricos"""
    def __init__(
        self,
        location: Dict[str, str],
        sensor_type: str,
        unit: str,
        range_min: float,
        range_max: float,
        precision: int = 2,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(f"sensor_{sensor_type}", location, config)
        self.unit = unit
        self.range_min = range_min
        self.range_max = range_max
        self.precision = precision
        self.last_value = None
        
    def generate_data(self) -> Dict[str, Any]:
        """Genera una lectura del sensor"""
        value = round(random.uniform(self.range_min, self.range_max), self.precision)
        self.last_value = value
        self.last_update = datetime.now()
        
        return {
            "value": value,
            "unit": self.unit,
            "timestamp": self.last_update.isoformat()
        }
    
    def update_state(self, new_state: Dict[str, Any]) -> None:
        """Actualiza el estado del sensor"""
        if "range_min" in new_state:
            self.range_min = new_state["range_min"]
        if "range_max" in new_state:
            self.range_max = new_state["range_max"]
        if "precision" in new_state:
            self.precision = new_state["precision"]
