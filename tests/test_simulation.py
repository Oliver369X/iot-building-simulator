import asyncio
import pytest
from src.api.simulation import SimulationManager
from src.api.validators import BuildingCreate

async def test_simulation_flow():
    # 1. Crear un edificio de prueba
    building_data = {
        "name": "Test Building",
        "type": "office",
        "floors": [
            {
                "number": 0,
                "rooms": [
                    {
                        "number": 0,
                        "devices": [
                            {"type": "temperature_sensor", "status": "active"},
                            {"type": "motion_sensor", "status": "active"}
                        ]
                    }
                ]
            }
        ]
    }
    
    building = BuildingCreate(**building_data)
    created_building = SimulationManager.create_building(building)
    
    # 2. Iniciar simulación
    simulation_id = SimulationManager.start_simulation(
        created_building["id"],
        duration=10,
        events_per_second=1.0
    )
    
    # 3. Esperar y verificar datos
    await asyncio.sleep(5)  # Esperar 5 segundos
    
    # Verificar que hay datos generados
    building = SimulationManager._buildings[created_building["id"]]
    device = building["floors"][0]["rooms"][0]["devices"][0]
    
    assert "last_reading" in device
    assert device["status"] == "active"
    
    print(f"Device readings: {device['last_reading']}") 