from datetime import datetime, timedelta
import yaml
import logging
from pathlib import Path

from src.simulator.engine import SimulationEngine
from src.core.building import Building
from src.core.floor import Floor
from src.core.room import Room
from utils.data_analyzer import IoTDataAnalyzer

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_building_config(config_path: str) -> dict:
    """Carga la configuración del edificio desde YAML"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def create_devices_from_template(room: Room, template: dict):
    """Crea dispositivos según la plantilla"""
    for device_config in template["devices"]:
        count = device_config.get("count", 1)
        for _ in range(count):
            device_type = device_config["type"]
            config = device_config.get("config", {})
            room.add_device(device_type, config)

def create_building_from_config(config: dict) -> Building:
    """Crea un edificio basado en la configuración"""
    building = Building(
        config["building_id"],
        config["name"],
        config["location"]
    )
    
    # Procesa la configuración de pisos
    floor_configs = config["floors"]
    templates = config["room_templates"]
    
    # Crea pisos típicos
    for floor_num in range(1, config["config"]["floors"] + 1):
        floor = Floor(f"floor_{floor_num}", building.building_id, floor_num)
        
        # Usa configuración de piso típico
        floor_config = floor_configs["typical_floor"]
        
        # Crea habitaciones según la configuración
        for room_type, count in floor_config["rooms"].items():
            template = templates[room_type]
            for room_num in range(1, count + 1):
                room = Room(
                    f"room_{floor_num}_{room_num}",
                    floor.floor_id,
                    room_type,
                    template["area"]
                )
                create_devices_from_template(room, template)
                floor.add_room(room)
                
        building.add_floor(floor)
    
    return building

def main():
    # Carga configuración
    config_path = Path("config/buildings/office_building.yaml")
    building_config = load_building_config(config_path)
    
    # Inicializa el motor de simulación
    engine = SimulationEngine(data_dir="./data")
    
    # Crea y añade edificio
    building = create_building_from_config(building_config)
    engine.add_building(building)
    
    # Ejecuta simulación por 24 horas
    logger.info("Iniciando simulación...")
    engine.start(timedelta(hours=24))
    
    # Analiza resultados
    analyzer = IoTDataAnalyzer("./data")
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    df = analyzer.load_device_data(start_time, end_time)
    
    # Genera análisis
    temp_patterns = analyzer.analyze_temperature_patterns(df)
    energy_patterns = analyzer.analyze_energy_consumption(df)
    
    logger.info("Resultados de temperatura:")
    logger.info(f"Temperatura promedio: {temp_patterns['average_temp']:.1f}°C")
    logger.info(f"Temperatura máxima: {temp_patterns['max_temp']:.1f}°C")
    
    logger.info("\nConsumo de energía:")
    logger.info(f"Consumo total: {energy_patterns['total_consumption']:.2f} kWh")
    logger.info(f"Potencia máxima: {energy_patterns['peak_power']:.2f} kW")
    
    # Genera gráficos
    analyzer.plot_temperature_distribution(df, "temp_distribution.png")
    analyzer.plot_energy_over_time(df, "energy_consumption.png")
    
if __name__ == "__main__":
    main() 