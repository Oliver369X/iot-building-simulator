from typing import Dict, Any, List, Optional
from datetime import datetime, time
import random
import math

class TrafficPattern:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.base_patterns = {
            "workday": {
                "morning_peak": {"start": time(8), "end": time(10), "factor": 1.5},
                "lunch_peak": {"start": time(12), "end": time(14), "factor": 1.2},
                "evening_peak": {"start": time(16), "end": time(18), "factor": 1.3},
                "night_low": {"start": time(22), "end": time(5), "factor": 0.3}
            },
            "weekend": {
                "day_low": {"start": time(8), "end": time(20), "factor": 0.5},
                "night_low": {"start": time(20), "end": time(8), "factor": 0.2}
            }
        }
        
    def get_time_factor(self, current_time: datetime) -> float:
        """Calcula el factor de actividad basado en la hora del día"""
        is_weekend = current_time.weekday() >= 5
        current_hour = current_time.time()
        
        # Selecciona el patrón base según día de la semana
        pattern = self.base_patterns["weekend" if is_weekend else "workday"]
        
        # Factor base
        base_factor = 1.0
        
        # Ajusta según período del día
        for period in pattern.values():
            if (period["start"] <= current_hour <= period["end"] or
                (period["start"] > period["end"] and  # Para períodos que cruzan medianoche
                 (current_hour >= period["start"] or current_hour <= period["end"]))):
                base_factor = period["factor"]
                break
                
        # Añade variación aleatoria
        variation = random.uniform(-0.1, 0.1)
        
        return max(0.1, base_factor + variation)

class DeviceTrafficGenerator:
    def __init__(self, device_type: str, config: Optional[Dict[str, Any]] = None):
        self.device_type = device_type
        self.config = config or {}
        self.pattern = TrafficPattern(config)
        
    def generate_activity_probability(self, current_time: datetime) -> float:
        """Genera probabilidad de actividad para un dispositivo"""
        base_probability = self.config.get("base_probability", 0.5)
        time_factor = self.pattern.get_time_factor(current_time)
        
        # Ajusta según tipo de dispositivo
        if self.device_type == "motion_sensor":
            # Mayor actividad durante horas de trabajo
            if 8 <= current_time.hour <= 18:
                base_probability *= 1.5
        elif self.device_type == "hvac_controller":
            # Mayor actividad en horas pico de temperatura
            if 12 <= current_time.hour <= 15:
                base_probability *= 1.3
                
        return min(1.0, base_probability * time_factor)

class BuildingTrafficSimulator:
    def __init__(self, building_config: Dict[str, Any]):
        self.config = building_config
        self.occupancy_pattern = TrafficPattern(building_config.get("occupancy_pattern"))
        self.device_generators: Dict[str, DeviceTrafficGenerator] = {}
        
    def initialize_device_generators(self, device_types: List[str]) -> None:
        """Inicializa generadores para cada tipo de dispositivo"""
        for device_type in device_types:
            config = self.config.get("device_patterns", {}).get(device_type, {})
            self.device_generators[device_type] = DeviceTrafficGenerator(device_type, config)
            
    def get_current_occupancy(self, current_time: datetime) -> int:
        """Calcula la ocupación actual del edificio"""
        max_occupancy = self.config.get("max_occupancy", 100)
        time_factor = self.occupancy_pattern.get_time_factor(current_time)
        
        base_occupancy = max_occupancy * time_factor
        variation = random.uniform(-5, 5)  # Variación de ±5 personas
        
        return max(0, min(max_occupancy, int(base_occupancy + variation)))
        
    def should_generate_event(self, device_type: str, current_time: datetime) -> bool:
        """Determina si se debe generar un evento para un tipo de dispositivo"""
        if device_type not in self.device_generators:
            return False
            
        generator = self.device_generators[device_type]
        probability = generator.generate_activity_probability(current_time)
        
        return random.random() < probability
        
    def generate_traffic_data(self, current_time: datetime) -> Dict[str, Any]:
        """Genera datos de tráfico para el edificio"""
        occupancy = self.get_current_occupancy(current_time)
        
        return {
            "timestamp": current_time.isoformat(),
            "occupancy": occupancy,
            "activity_level": self.occupancy_pattern.get_time_factor(current_time),
            "device_activities": {
                device_type: self.should_generate_event(device_type, current_time)
                for device_type in self.device_generators
            }
        }
