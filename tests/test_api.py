import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from src.api.main import app
import asyncio

# Cliente síncrono para pruebas simples
client = TestClient(app)

@pytest.fixture
async def async_client():
    """Cliente para pruebas"""
    return TestClient(app)

@pytest.fixture
def sample_building_config():
    return {
        "id": "test_building",
        "name": "Test Building",
        "type": "office",
        "floors": 2,
        "rooms_per_floor": 3,
        "devices_per_room": {
            "temperature_sensor": 1,
            "hvac_controller": 1
        }
    }

@pytest.fixture
def sample_building():
    return {
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

@pytest.mark.asyncio
async def test_add_building(async_client):
    response = async_client.post("/buildings", json={
        "name": "Test Building",
        "type": "office",
        "floors": [
            {
                "number": 0,
                "rooms": [
                    {
                        "number": 0,
                        "devices": [
                            {"type": "temperature_sensor", "status": "active"}
                        ]
                    }
                ]
            }
        ]
    })
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_start_simulation(async_client):
    # Primero crear un edificio
    building_response = async_client.post("/buildings", json={
        "name": "Test Building",
        "type": "office",
        "floors": [{"number": 0, "rooms": [{"number": 0, "devices": []}]}]
    })
    building_id = building_response.json()["building"]["id"]
    
    # Luego iniciar simulación
    response = async_client.post("/simulation/start", json={
        "building_id": building_id,
        "duration": 3600,
        "events_per_second": 1.0
    })
    assert response.status_code == 200
    data = response.json()
    assert "simulation_id" in data

@pytest.mark.asyncio
async def test_simulation_with_multiple_buildings(async_client):
    buildings = [
        {
            "name": "Office A",
            "type": "office",
            "floors": [
                {
                    "number": 0,
                    "rooms": [
                        {
                            "number": 0,
                            "devices": [
                                {"type": "temperature_sensor", "status": "active"},
                                {"type": "hvac_controller", "status": "active"}
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "name": "Residential B",
            "type": "residential",
            "floors": [
                {
                    "number": 0,
                    "rooms": [
                        {
                            "number": 0,
                            "devices": [
                                {"type": "temperature_sensor", "status": "active"},
                                {"type": "smart_plug", "status": "active"}
                            ]
                        }
                    ]
                }
            ]
        }
    ]

    for building in buildings:
        response = async_client.post("/buildings", json=building)
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_invalid_configuration(async_client):
    invalid_config = {
        "name": "Invalid Building",
        "type": "office",
        "floors": [
            {
                "number": -1,
                "rooms": [
                    {
                        "number": 0,
                        "devices": [
                            {"type": "invalid_type", "status": "active"}
                        ]
                    }
                ]
            }
        ]
    }
    response = async_client.post("/buildings", json=invalid_config)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_building(sample_building):
    response = client.post("/buildings", json=sample_building)
    assert response.status_code == 200
    data = response.json()
    assert "building" in data
    assert data["building"]["name"] == sample_building["name"]
    return data["building"]["id"]

@pytest.mark.asyncio
async def test_get_buildings():
    response = client.get("/buildings")
    assert response.status_code == 200
    data = response.json()
    assert "buildings" in data
    assert isinstance(data["buildings"], list)

@pytest.mark.asyncio
async def test_simulation_flow(sample_building):
    # 1. Crear edificio
    building_response = client.post("/buildings", json=sample_building)
    building_id = building_response.json()["building"]["id"]
    
    # 2. Iniciar simulación
    sim_response = client.post("/simulation/start", json={
        "building_id": building_id,
        "duration": 3600,
        "events_per_second": 1.0
    })
    assert sim_response.status_code == 200
    simulation_id = sim_response.json()["simulation_id"]
    
    # 3. Esperar un momento para que la simulación inicie
    await asyncio.sleep(1)
    
    # 4. Verificar estado
    status_response = client.get(f"/simulation/{simulation_id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "running"

@pytest.mark.asyncio
async def test_device_operations(sample_building):
    # 1. Crear edificio con dispositivos
    building_response = client.post("/buildings", json=sample_building)
    building = building_response.json()["building"]
    
    # 2. Obtener primer dispositivo
    device_id = building["floors"][0]["rooms"][0]["devices"][0]["id"]
    
    # 3. Actualizar estado del dispositivo
    response = client.patch(f"/devices/{device_id}/status", json={
        "status": "inactive"
    })
    assert response.status_code == 200
    
    # 4. Verificar lecturas del dispositivo
    readings_response = client.get(f"/devices/{device_id}/readings")
    assert readings_response.status_code == 200 