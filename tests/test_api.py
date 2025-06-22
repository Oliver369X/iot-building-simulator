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
    # Use httpx.AsyncClient with ASGITransport for FastAPI app
    from httpx import ASGITransport
    from src.api.main import app # Ensure app is imported

    # Manually manage lifespan for tests if TestClient/AsyncClient isn't fully triggering startup
    # as expected, or if global state isn't ready.
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client

# @pytest.fixture  # This fixture is not aligned with the new BuildingCreate model
# def sample_building_config():
#     return {
#         "id": "test_building",
#         "name": "Test Building",
#         "type": "office",
#         "floors": 2,
#         "rooms_per_floor": 3,
#         "devices_per_room": {
#             "temperature_sensor": 1,
#             "hvac_controller": 1
#         }
#     }

@pytest.fixture
def sample_building_payload():
    """Provides a valid payload for creating a building."""
    return {
        "name": "Test Building Alpha",
        "address": "123 Test St, Testville",
        "geolocation": {"latitude": 34.0522, "longitude": -118.2437}
    }

@pytest.fixture
def sample_building_payload_beta():
    """Provides another valid payload for creating a building."""
    return {
        "name": "Test Building Beta",
        "address": "456 Future Ave, Tech City",
        "geolocation": {"latitude": 40.7128, "longitude": -74.0060}
    }


# @pytest.mark.asyncio  # This test uses the old building creation structure
# async def test_add_building(async_client):
#     response = async_client.post("/buildings", json={
#         "name": "Test Building",
#         "type": "office",
#         "floors": [
#             {
#                 "number": 0,
#                 "rooms": [
#                     {
#                         "number": 0,
#                         "devices": [
#                             {"type": "temperature_sensor", "status": "active"}
#                         ]
#                     }
#                 ]
#             }
#         ]
#     })
#     assert response.status_code == 200 # Old API returned 200, new should be 201

# @pytest.mark.asyncio # This test is for an old, removed endpoint
# async def test_start_simulation(async_client):
#     # Primero crear un edificio
#     building_response = async_client.post("/buildings", json={
#         "name": "Test Building",
#         "type": "office",
#         "floors": [{"number": 0, "rooms": [{"number": 0, "devices": []}]}]
#     })
#     building_id = building_response.json()["building"]["id"]
    
#     # Luego iniciar simulación
#     response = async_client.post("/simulation/start", json={
#         "building_id": building_id,
#         "duration": 3600,
#         "events_per_second": 1.0
#     })
#     assert response.status_code == 200
#     data = response.json()
#     assert "simulation_id" in data

@pytest.mark.asyncio
async def test_create_and_get_building(async_client, sample_building_payload):
    # 1. Create Building
    response_create = await async_client.post("/api/v1/buildings", json=sample_building_payload)
    assert response_create.status_code == 201
    created_data = response_create.json()
    
    assert "id" in created_data
    assert created_data["name"] == sample_building_payload["name"]
    assert created_data["address"] == sample_building_payload["address"]
    assert created_data["geolocation"]["latitude"] == sample_building_payload["geolocation"]["latitude"]
    assert "created_at" in created_data
    assert "updated_at" in created_data
    
    building_id = created_data["id"]

    # 2. Get Building by ID
    response_get = await async_client.get(f"/api/v1/buildings/{building_id}")
    assert response_get.status_code == 200
    retrieved_data = response_get.json()

    assert retrieved_data["id"] == building_id
    assert retrieved_data["name"] == sample_building_payload["name"]
    assert retrieved_data["address"] == sample_building_payload["address"]
    # Compare geolocation carefully due to potential float precision issues if they were transformed
    assert retrieved_data["geolocation"]["latitude"] == sample_building_payload["geolocation"]["latitude"]
    assert retrieved_data["geolocation"]["longitude"] == sample_building_payload["geolocation"]["longitude"]
    assert "created_at" in retrieved_data
    assert "updated_at" in retrieved_data
    assert retrieved_data["created_at"] == created_data["created_at"] # Timestamps should match

@pytest.mark.asyncio
async def test_list_buildings(async_client, sample_building_payload, sample_building_payload_beta):
    # Create a couple of buildings to ensure the list is not empty
    await async_client.post("/api/v1/buildings", json=sample_building_payload)
    await async_client.post("/api/v1/buildings", json=sample_building_payload_beta)

    response = await async_client.get("/api/v1/buildings")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2 # Assuming a clean test DB or that these are the only ones

    for building_data in data:
        assert "id" in building_data
        assert "name" in building_data
        assert "address" in building_data
        assert "geolocation" in building_data
        assert "created_at" in building_data
        assert "updated_at" in building_data
        if building_data["name"] == sample_building_payload["name"]:
            assert building_data["address"] == sample_building_payload["address"]
        elif building_data["name"] == sample_building_payload_beta["name"]:
            assert building_data["address"] == sample_building_payload_beta["address"]


@pytest.mark.asyncio
async def test_create_building_invalid_payload(async_client):
    # Test with missing 'name'
    invalid_payload_missing_name = {
        "address": "123 Invalid St",
        "geolocation": {"latitude": 0.0, "longitude": 0.0}
    }
    response = await async_client.post("/api/v1/buildings", json=invalid_payload_missing_name)
    assert response.status_code == 422  # Unprocessable Entity for Pydantic validation error

    # Test with wrong data type for geolocation (e.g., string instead of dict)
    invalid_payload_wrong_type = {
        "name": "Wrong Type Building",
        "address": "456 Error Ave",
        "geolocation": "not-a-dictionary"
    }
    response = await async_client.post("/api/v1/buildings", json=invalid_payload_wrong_type)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_nonexistent_building(async_client):
    non_existent_id = "00000000-0000-0000-0000-000000000000" # A valid UUID format but unlikely to exist
    response = await async_client.get(f"/api/v1/buildings/{non_existent_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_building(async_client, sample_building_payload):
    # 1. Create a building first
    response_create = await async_client.post("/api/v1/buildings", json=sample_building_payload)
    assert response_create.status_code == 201
    created_building_data = response_create.json()
    building_id = created_building_data["id"]

    # 2. Update the building
    update_payload = {
        "name": "Updated Test Building Alpha",
        "address": "123 Updated St, Testville",
        "geolocation": {"latitude": 35.0000, "longitude": -119.0000}
    }
    response_update = await async_client.put(f"/api/v1/buildings/{building_id}", json=update_payload)
    assert response_update.status_code == 200
    updated_building_data = response_update.json()

    assert updated_building_data["id"] == building_id
    assert updated_building_data["name"] == update_payload["name"]
    assert updated_building_data["address"] == update_payload["address"]
    assert updated_building_data["geolocation"]["latitude"] == update_payload["geolocation"]["latitude"]
    assert updated_building_data["geolocation"]["longitude"] == update_payload["geolocation"]["longitude"]
    assert updated_building_data["created_at"] == created_building_data["created_at"] # created_at should not change
    assert updated_building_data["updated_at"] != created_building_data["updated_at"] # updated_at should change

    # 3. Get the building again to verify persistence of update
    response_get = await async_client.get(f"/api/v1/buildings/{building_id}")
    assert response_get.status_code == 200
    retrieved_building_data = response_get.json()
    assert retrieved_building_data["name"] == update_payload["name"]
    assert retrieved_building_data["address"] == update_payload["address"]

@pytest.mark.asyncio
async def test_update_building_partial(async_client, sample_building_payload):
    # 1. Create a building
    response_create = await async_client.post("/api/v1/buildings", json=sample_building_payload)
    created_building_data = response_create.json()
    building_id = created_building_data["id"]

    # 2. Update only the name
    partial_update_payload = {"name": "Partially Updated Name"}
    response_update = await async_client.put(f"/api/v1/buildings/{building_id}", json=partial_update_payload)
    assert response_update.status_code == 200
    updated_building_data = response_update.json()

    assert updated_building_data["name"] == partial_update_payload["name"]
    assert updated_building_data["address"] == sample_building_payload["address"] # Address should remain unchanged
    assert updated_building_data["geolocation"]["latitude"] == sample_building_payload["geolocation"]["latitude"] # Geolocation should remain

@pytest.mark.asyncio
async def test_update_nonexistent_building(async_client):
    non_existent_id = "11111111-1111-1111-1111-111111111111"
    update_payload = {"name": "Ghost Building"}
    response_update = await async_client.put(f"/api/v1/buildings/{non_existent_id}", json=update_payload)
    assert response_update.status_code == 404

@pytest.mark.asyncio
async def test_delete_building(async_client, sample_building_payload):
    # 1. Create a building
    response_create = await async_client.post("/api/v1/buildings", json=sample_building_payload)
    assert response_create.status_code == 201
    building_id = response_create.json()["id"]

    # 2. Delete the building
    response_delete = await async_client.delete(f"/api/v1/buildings/{building_id}")
    assert response_delete.status_code == 204

    # 3. Try to get the deleted building
    response_get = await async_client.get(f"/api/v1/buildings/{building_id}")
    assert response_get.status_code == 404

@pytest.mark.asyncio
async def test_delete_nonexistent_building(async_client):
    non_existent_id = "22222222-2222-2222-2222-222222222222"
    response_delete = await async_client.delete(f"/api/v1/buildings/{non_existent_id}")
    assert response_delete.status_code == 404


# @pytest.mark.asyncio # This test used old building creation and endpoints
# async def test_simulation_with_multiple_buildings(async_client):
#     buildings = [
#         { # Old structure
#             "name": "Office A",
#             "type": "office",
#             "floors": [ { "number": 0, "rooms": [ { "number": 0, "devices": [ {"type": "temperature_sensor", "status": "active"}, {"type": "hvac_controller", "status": "active"} ] } ] } ]
#         },
#         { # Old structure
#             "name": "Residential B",
#             "type": "residential",
#             "floors": [ { "number": 0, "rooms": [ { "number": 0, "devices": [ {"type": "temperature_sensor", "status": "active"}, {"type": "smart_plug", "status": "active"} ] } ] } ]
#         }
#     ]
#     for building in buildings:
#         response = async_client.post("/buildings", json=building) # Old endpoint
#         assert response.status_code == 200

# @pytest.mark.asyncio # This test used old building creation and endpoints
# async def test_invalid_configuration(async_client):
#     invalid_config = { # Old structure
#         "name": "Invalid Building",
#         "type": "office",
#         "floors": [ { "number": -1, "rooms": [ { "number": 0, "devices": [ {"type": "invalid_type", "status": "active"} ] } ] } ]
#     }
#     response = async_client.post("/buildings", json=invalid_config) # Old endpoint
#     assert response.status_code == 422

# @pytest.mark.asyncio # This test is a duplicate of test_create_and_get_building and uses old client/structure
# async def test_create_building(sample_building): # sample_building fixture is old
#     response = client.post("/buildings", json=sample_building) # Old endpoint, synchronous client
#     assert response.status_code == 200
#     data = response.json()
#     assert "building" in data
#     assert data["building"]["name"] == sample_building["name"]
#     return data["building"]["id"]

# @pytest.mark.asyncio # This test is a duplicate of test_list_buildings and uses old client/structure
# async def test_get_buildings():
#     response = client.get("/buildings") # Old endpoint, synchronous client
#     assert response.status_code == 200
#     data = response.json()
#     assert "buildings" in data
#     assert isinstance(data["buildings"], list)

# @pytest.mark.asyncio # This test is for old, removed endpoints
# async def test_simulation_flow(sample_building): # sample_building fixture is old
#     # 1. Crear edificio
#     building_response = client.post("/buildings", json=sample_building) # Old endpoint
#     building_id = building_response.json()["building"]["id"]
    
#     # 2. Iniciar simulación
#     sim_response = client.post("/simulation/start", json={ # Old endpoint
#         "building_id": building_id,
#         "duration": 3600,
#         "events_per_second": 1.0
#     })
#     assert sim_response.status_code == 200
#     simulation_id = sim_response.json()["simulation_id"]
    
#     # 3. Esperar un momento para que la simulación inicie
#     await asyncio.sleep(1)
    
#     # 4. Verificar estado
#     status_response = client.get(f"/simulation/{simulation_id}/status") # Old endpoint
#     assert status_response.status_code == 200
#     assert status_response.json()["status"] == "running"

# @pytest.mark.asyncio # This test is for old, removed endpoints and old structure
# async def test_device_operations(sample_building): # sample_building fixture is old
#     # 1. Crear edificio con dispositivos
#     building_response = client.post("/buildings", json=sample_building) # Old endpoint
#     building = building_response.json()["building"]
    
#     # 2. Obtener primer dispositivo
#     device_id = building["floors"][0]["rooms"][0]["devices"][0]["id"] # Relies on old structure
    
#     # 3. Actualizar estado del dispositivo
#     response = client.patch(f"/devices/{device_id}/status", json={ # Old endpoint
#         "status": "inactive"
#     })
#     assert response.status_code == 200
    
#     # 4. Verificar lecturas del dispositivo
#     readings_response = client.get(f"/devices/{device_id}/readings") # Old endpoint
#     assert readings_response.status_code == 200