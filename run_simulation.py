import yaml
import click
from src.simulator.engine import SimulationEngine
from datetime import timedelta, datetime
import time
import asyncio
from functools import wraps
from src.database.connection import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_devices(devices_config):
    """Genera la lista de dispositivos según la configuración"""
    devices = []
    for device_type, count in devices_config.items():
        for _ in range(count):
            devices.append({
                "type": device_type,
                "config": {}
            })
    return devices

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def async_command(f):
    """Decorador para manejar comandos async con Click"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

@click.command()
@click.option('--config', '-c', default='config.yaml', help='Archivo de configuración')
@click.option('--verbose', '-v', is_flag=True, help='Mostrar más detalles')
@async_command
async def run_simulation(config, verbose):
    """Ejecuta la simulación usando la configuración del archivo YAML"""
    
    with open(config, 'r') as f:
        config_data = yaml.safe_load(f)
    
    engine = SimulationEngine()
    db = next(get_db())
    
    try:
        # Verificar si el edificio ya existe
        existing_building = engine.get_building("building_edificio_principal")
        if not existing_building:
            # Crear edificio solo si no existe
            building_config = {
                "id": "building_edificio_principal",
                "name": "Edificio Principal",
                "type": "office",
                "floors": 5,
                "rooms_per_floor": 4,
                "devices_per_room": {
                    "temperature_sensor": 1,
                    "motion_sensor": 1,
                    "smart_plug": 2,
                    "hvac_controller": 1
                }
            }
            
            await engine.add_building(building_config)
            logger.info("Edificio creado exitosamente")
        else:
            logger.info("Usando edificio existente")

        # Iniciar simulación
        simulation_id = await engine.start_simulation(
            building_id="building_edificio_principal",
            duration_hours=1
        )
        
        logger.info(f"Simulación iniciada con ID: {simulation_id}")
        
        # Mantener la simulación corriendo
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Deteniendo simulación...")
            await engine.stop_simulation(simulation_id)
            
    except Exception as e:
        logger.error(f"Error en la simulación: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    run_simulation() 