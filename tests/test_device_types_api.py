import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app # Ensure app is imported for lifespan and routing
import uuid

API_PREFIX = "/api/v1"

@pytest.fixture
async def async_client():
    """Async client for API tests."""
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client

@pytest.fixture
def sample_device_type_payload():
    """Provides a valid payload for creating a device type."""
    # Generate a unique ID for each test run to avoid conflicts if DB is not reset
    return {
        "id": str(uuid.uuid4()), 
        "type_name": "Smart Light Bulb",
        "properties": {"colors": ["RGB", "White"], "dimmable": True, "actions": ["setState", "getColor"]}
    }

@pytest.fixture
def sample_device_type_payload_beta():
    """Provides another valid payload for creating a device type."""
    return {
        "id": str(uuid.uuid4()),
        "type_name": "Temperature Sensor",
        "properties": {"unit": "Celsius", "range": [-50, 150], "actions": ["getValue"]}
    }

@pytest.mark.asyncio
async def test_create_and_get_device_type(async_client: AsyncClient, sample_device_type_payload):
    # 1. Create Device Type
    response_create = await async_client.post(
        f"{API_PREFIX}/device-types",
        json=sample_device_type_payload
    )
    assert response_create.status_code == 201
    created_data = response_create.json()

    assert created_data["id"] == sample_device_type_payload["id"]
    assert created_data["type_name"] == sample_device_type_payload["type_name"]
    assert created_data["properties"] == sample_device_type_payload["properties"]
    assert "created_at" in created_data
    assert "updated_at" in created_data
    
    device_type_id = created_data["id"]

    # 2. Get Device Type by ID
    response_get = await async_client.get(f"{API_PREFIX}/device-types/{device_type_id}")
    assert response_get.status_code == 200
    retrieved_data = response_get.json()

    assert retrieved_data["id"] == device_type_id
    assert retrieved_data["type_name"] == sample_device_type_payload["type_name"]
    assert retrieved_data["properties"] == sample_device_type_payload["properties"]
    assert retrieved_data["created_at"] == created_data["created_at"]

@pytest.mark.asyncio
async def test_list_device_types(async_client: AsyncClient, sample_device_type_payload, sample_device_type_payload_beta):
    # Create a couple of device types
    await async_client.post(f"{API_PREFIX}/device-types", json=sample_device_type_payload)
    await async_client.post(f"{API_PREFIX}/device-types", json=sample_device_type_payload_beta)

    response = await async_client.get(f"{API_PREFIX}/device-types")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2 # Assuming these are added to whatever exists

    # Check if our created types are in the list
    found_payload1 = any(dt["id"] == sample_device_type_payload["id"] for dt in data)
    found_payload2 = any(dt["id"] == sample_device_type_payload_beta["id"] for dt in data)
    assert found_payload1
    assert found_payload2

    for dt_data in data:
        assert "id" in dt_data
        assert "type_name" in dt_data
        assert "properties" in dt_data

@pytest.mark.asyncio
async def test_create_device_type_invalid_payload(async_client: AsyncClient):
    # Missing 'type_name'
    invalid_payload = {"id": str(uuid.uuid4()), "properties": {}}
    response = await async_client.post(f"{API_PREFIX}/device-types", json=invalid_payload)
    assert response.status_code == 422 # Unprocessable Entity

    # ID not a string (if not auto-generated and type is strict)
    # Pydantic usually handles string conversion for UUIDs if field type is str.
    # If ID is optional and auto-generated, this test might change.
    # For now, assuming ID is provided as string.

@pytest.mark.asyncio
async def test_create_device_type_duplicate_id(async_client: AsyncClient, sample_device_type_payload):
    # Create it once
    await async_client.post(f"{API_PREFIX}/device-types", json=sample_device_type_payload)
    
    # Try to create with the same ID again
    # This depends on DB constraints / engine logic for handling duplicate IDs.
    # Assuming a 400 or 409 (Conflict) if ID must be unique.
    # If the engine overwrites or ignores, this test would fail or need adjustment.
    response_duplicate = await async_client.post(f"{API_PREFIX}/device-types", json=sample_device_type_payload)
    assert response_duplicate.status_code in [400, 409] # Or specific error from engine

@pytest.mark.asyncio
async def test_get_nonexistent_device_type(async_client: AsyncClient):
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    response = await async_client.get(f"{API_PREFIX}/device-types/{non_existent_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_device_type(async_client: AsyncClient, sample_device_type_payload):
    # 1. Create a device type
    response_create = await async_client.post(f"{API_PREFIX}/device-types", json=sample_device_type_payload)
    assert response_create.status_code == 201
    created_data = response_create.json()
    device_type_id = created_data["id"]

    # 2. Update the device type
    update_payload = {
        "type_name": "Advanced Smart Bulb v2",
        "properties": {"colors": ["RGBW"], "dimmable": True, "power_consumption": "5W"}
    }
    response_update = await async_client.put(f"{API_PREFIX}/device-types/{device_type_id}", json=update_payload)
    assert response_update.status_code == 200
    updated_data = response_update.json()

    assert updated_data["id"] == device_type_id
    assert updated_data["type_name"] == update_payload["type_name"]
    assert updated_data["properties"] == update_payload["properties"]
    assert updated_data["created_at"] == created_data["created_at"]
    assert updated_data["updated_at"] != created_data["updated_at"]

    # 3. Get again to verify persistence
    response_get = await async_client.get(f"{API_PREFIX}/device-types/{device_type_id}")
    assert response_get.status_code == 200
    retrieved_data = response_get.json()
    assert retrieved_data["type_name"] == update_payload["type_name"]
    assert retrieved_data["properties"] == update_payload["properties"]

@pytest.mark.asyncio
async def test_update_device_type_partial(async_client: AsyncClient, sample_device_type_payload):
    response_create = await async_client.post(f"{API_PREFIX}/device-types", json=sample_device_type_payload)
    created_data = response_create.json()
    device_type_id = created_data["id"]

    partial_update_payload = {"type_name": "Basic Light Bulb"}
    response_update = await async_client.put(f"{API_PREFIX}/device-types/{device_type_id}", json=partial_update_payload)
    assert response_update.status_code == 200
    updated_data = response_update.json()

    assert updated_data["type_name"] == partial_update_payload["type_name"]
    assert updated_data["properties"] == sample_device_type_payload["properties"] # Properties should remain

@pytest.mark.asyncio
async def test_update_nonexistent_device_type(async_client: AsyncClient):
    non_existent_id = "11111111-1111-1111-1111-111111111111"
    update_payload = {"type_name": "Ghost Type"}
    response_update = await async_client.put(f"{API_PREFIX}/device-types/{non_existent_id}", json=update_payload)
    assert response_update.status_code == 404

@pytest.mark.asyncio
async def test_delete_device_type(async_client: AsyncClient, sample_device_type_payload):
    # 1. Create a device type
    response_create = await async_client.post(f"{API_PREFIX}/device-types", json=sample_device_type_payload)
    assert response_create.status_code == 201
    device_type_id = response_create.json()["id"]

    # 2. Delete the device type
    response_delete = await async_client.delete(f"{API_PREFIX}/device-types/{device_type_id}")
    assert response_delete.status_code == 204

    # 3. Try to get the deleted device type
    response_get = await async_client.get(f"{API_PREFIX}/device-types/{device_type_id}")
    assert response_get.status_code == 404

@pytest.mark.asyncio
async def test_delete_nonexistent_device_type(async_client: AsyncClient):
    non_existent_id = "22222222-2222-2222-2222-222222222222"
    response_delete = await async_client.delete(f"{API_PREFIX}/device-types/{non_existent_id}")
    assert response_delete.status_code == 404

@pytest.mark.asyncio
async def test_delete_device_type_in_use(async_client: AsyncClient, created_room: dict, created_device_type: dict):
    # This test assumes that the engine prevents deletion of a device type if it's in use.
    # 1. Device type is already created by `created_device_type` fixture.
    # 2. Create a device that uses this device type.
    device_payload = {
        "name": "Thermostat Using Type",
        "device_type_id": created_device_type["id"],
        "state": {"power": "ON"}
    }
    # created_room y created_device_type ya son diccionarios gracias a los fixtures en conftest.py
    await async_client.post(f"{API_PREFIX}/rooms/{created_room['id']}/devices", json=device_payload)

    # 3. Attempt to delete the device type
    response_delete = await async_client.delete(f"{API_PREFIX}/device-types/{created_device_type['id']}")
    # Expecting a 409 Conflict or similar error indicating it's in use.
    # The exact code depends on the engine's implementation.
    assert response_delete.status_code == 409 # Or 400, based on API spec for this case
