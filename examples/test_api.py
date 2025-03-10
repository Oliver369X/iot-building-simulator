import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def test_api():
    # 1. Crear un edificio
    building_config = {
        "building_id": "test_building_01",
        "name": "Edificio de Prueba",
        "type": "office",
        "floors": 5,
        "rooms_per_floor": 4,
        "devices_per_room": {
            "temperature_sensor": 1,
            "hvac_controller": 1
        }
    }
    
    response = requests.post(f"{BASE_URL}/buildings", json=building_config)
    print("Edificio creado:", response.json())
    
    # 2. Iniciar simulación
    sim_config = {
        "duration_hours": 1,
        "time_scale": 2.0
    }
    
    response = requests.post(f"{BASE_URL}/simulation/start", json=sim_config)
    simulation_id = response.json()["simulation_id"]
    print("Simulación iniciada:", simulation_id)
    
    # 3. Monitorear estado
    for _ in range(5):
        response = requests.get(f"{BASE_URL}/simulation/{simulation_id}/status")
        print("Estado:", response.json())
        time.sleep(10)
    
    # 4. Obtener datos
    response = requests.get(f"{BASE_URL}/buildings/test_building_01/stats")
    print("Estadísticas:", response.json())

if __name__ == "__main__":
    test_api() 