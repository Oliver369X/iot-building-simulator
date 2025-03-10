from src.simulator.engine import SimulationEngine
from datetime import timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_buildings():
    # Inicializar el motor de simulación
    engine = SimulationEngine()
    
    # Configuración para un edificio de oficinas
    office_building = {
        "building_id": "office_building_01",
        "name": "Torre Corporativa A",
        "type": "office",
        "floors": 10,
        "rooms_per_floor": 8,
        "devices_per_room": {
            "temperature_sensor": 1,
            "hvac_controller": 1,
            "motion_sensor": 1,
            "smart_plug": 4
        }
    }
    
    # Configuración para un edificio residencial
    residential_building = {
        "building_id": "residential_building_01",
        "name": "Residencial Las Palmas",
        "type": "residential",
        "floors": 15,
        "rooms_per_floor": 4,
        "devices_per_room": {
            "temperature_sensor": 1,
            "smart_plug": 6,
            "security_camera": 1,
            "motion_sensor": 2
        }
    }
    
    try:
        # Crear edificios
        office_id = engine.add_building(office_building)
        logger.info(f"Edificio de oficinas creado con ID: {office_id}")
        
        residential_id = engine.add_building(residential_building)
        logger.info(f"Edificio residencial creado con ID: {residential_id}")
        
        # Iniciar simulación por 1 hora
        engine.start(duration=timedelta(hours=1))
        
    except Exception as e:
        logger.error(f"Error creando edificios: {str(e)}")

if __name__ == "__main__":
    create_sample_buildings() 