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
async def created_building(async_client: AsyncClient):
    """Fixture to create a building and return its data."""
    payload = {
        "name": "Test Building for Devices",
        "address": "111 Device Test Rd",
        "geolocation": {"latitude": 32.0, "longitude": -102.0}
    }
    response = await async_client.post(f"{API_PREFIX}/buildings", json=payload)
    assert response.status_code == 201
    return response.json()

@pytest.fixture
async def created_floor(async_client: AsyncClient, created_building):
    """Fixture to create a floor and return its data."""
    building_id = created_building["id"]
    payload = {
        "floor_number": 1,
        "plan_url": "http://example.com/bldg_devices/floor1_plan.png"
    }
    response = await async_client.post(f"{API_PREFIX}/buildings/{building_id}/floors", json=payload)
    assert response.status_code == 201
    return response.json()

@pytest.fixture
async def created_room(async_client: AsyncClient, created_floor):
    """Fixture to create a room and return its data."""
    floor_id = created_floor["id"]
    payload = {"name": "Device Lab"}
    response = await async_client.post(f"{API_PREFIX}/floors/{floor_id}/rooms", json=payload)
    assert response.status_code == 201
    return response.json()

@pytest.fixture
async def created_device_type(async_client: AsyncClient):
    """Fixture to create a device type and return its data."""
    device_type_id = str(uuid.uuid4())
    payload = {
        "id": device_type_id, # Providing ID for predictability in tests
        "type_name": "Smart Thermostat",
        "properties": {"unit": "°C", "actions": ["setState", "getValue"]}
    }
    response = await async_client.post(f"{API_PREFIX}/device-types", json=payload)
    assert response.status_code == 201
    return response.json()

@pytest.fixture
async def sample_device_payload(created_room: dict, created_device_type: dict):
    """Provides a valid payload for creating a device."""
    # created_room y created_device_type ya son diccionarios gracias a los fixtures en conftest.py
    return {
        "name": "Main Thermostat",
        "device_type_id": created_device_type["id"],
        # room_id is implicitly used via the endpoint path
        "state": {"power": "OFF", "target_temp": 22},
        "is_active": True
    }

@pytest.mark.asyncio
async def test_create_and_get_device(async_client: AsyncClient, created_room, created_device_type, sample_device_payload):
    room_id = created_room["id"]

    # 1. Create Device
    response_create = await async_client.post(
        f"{API_PREFIX}/rooms/{room_id}/devices",
        json=sample_device_payload
    )
    assert response_create.status_code == 201
    created_data = response_create.json()

    assert "id" in created_data
    assert created_data["name"] == sample_device_payload["name"]
    assert created_data["device_type_id"] == sample_device_payload["device_type_id"]
    assert created_data["room_id"] == room_id
    assert created_data["state"]["power"] == "OFF"
    assert created_data["is_active"] is True
    assert "created_at" in created_data
    assert "updated_at" in created_data
    
    device_id = created_data["id"]

    # 2. Get Device by ID
    response_get = await async_client.get(f"{API_PREFIX}/devices/{device_id}")
    assert response_get.status_code == 200
    retrieved_data = response_get.json()

    assert retrieved_data["id"] == device_id
    assert retrieved_data["name"] == sample_device_payload["name"]
    assert retrieved_data["room_id"] == room_id
    assert retrieved_data["created_at"] == created_data["created_at"]

@pytest.mark.asyncio
async def test_list_devices_for_room(async_client: AsyncClient, created_room, created_device_type, sample_device_payload):
    room_id = created_room["id"]

    await async_client.post(f"{API_PREFIX}/rooms/{room_id}/devices", json=sample_device_payload)
    
    another_device_payload = {
        "name": "Secondary Sensor",
        "device_type_id": created_device_type["id"],
        "state": {"power": "ON", "value": 42},
        "is_active": False
    }
    await async_client.post(f"{API_PREFIX}/rooms/{room_id}/devices", json=another_device_payload)

    response = await async_client.get(f"{API_PREFIX}/rooms/{room_id}/devices")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

    for device_data in data:
        assert "id" in device_data
        assert "name" in device_data
        assert device_data["room_id"] == room_id
        assert device_data["device_type_id"] == created_device_type["id"]

@pytest.mark.asyncio
async def test_create_device_invalid_payload(async_client: AsyncClient, created_room, created_device_type):
    room_id = created_room["id"]
    # Missing 'name'
    invalid_payload = {"device_type_id": created_device_type["id"]}
    response = await async_client.post(f"{API_PREFIX}/rooms/{room_id}/devices", json=invalid_payload)
    assert response.status_code == 422

    # Missing 'device_type_id'
    invalid_payload_no_type = {"name": "Nameless Device"}
    response_no_type = await async_client.post(f"{API_PREFIX}/rooms/{room_id}/devices", json=invalid_payload_no_type)
    assert response_no_type.status_code == 422


@pytest.mark.asyncio
async def test_create_device_for_nonexistent_room(async_client: AsyncClient, sample_device_payload):
    non_existent_room_id = "00000000-0000-0000-0000-000000000000"
    response = await async_client.post(
        f"{API_PREFIX}/rooms/{non_existent_room_id}/devices",
        json=sample_device_payload
    )
    assert response.status_code == 404 # Room not found

@pytest.mark.asyncio
async def test_create_device_with_nonexistent_type(async_client: AsyncClient, created_room):
    room_id = created_room["id"]
    non_existent_type_id = "11111111-1111-1111-1111-111111111111"
    payload = {
        "name": "Device With Bad Type",
        "device_type_id": non_existent_type_id,
    }
    response = await async_client.post(f"{API_PREFIX}/rooms/{room_id}/devices", json=payload)
    assert response.status_code == 404 # DeviceType not found

@pytest.mark.asyncio
async def test_get_nonexistent_device(async_client: AsyncClient):
    non_existent_id = "22222222-2222-2222-2222-222222222222"
    response = await async_client.get(f"{API_PREFIX}/devices/{non_existent_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_device(async_client: AsyncClient, created_room, created_device_type, sample_device_payload):
    room_id = created_room["id"]
    
    response_create = await async_client.post(
        f"{API_PREFIX}/rooms/{room_id}/devices", json=sample_device_payload
    )
    assert response_create.status_code == 201
    created_device_data = response_create.json()
    device_id = created_device_data["id"]

    update_payload = {
        "name": "Upgraded Thermostat",
        "state": {"power": "ON", "target_temp": 25, "fan_speed": "HIGH"},
        "is_active": False
    }
    response_update = await async_client.put(f"{API_PREFIX}/devices/{device_id}", json=update_payload)
    assert response_update.status_code == 200
    updated_device_data = response_update.json()

    assert updated_device_data["id"] == device_id
    assert updated_device_data["name"] == update_payload["name"]
    assert updated_device_data["state"]["power"] == "ON"
    assert updated_device_data["state"]["target_temp"] == 25
    assert updated_device_data["state"]["fan_speed"] == "HIGH"
    assert updated_device_data["is_active"] is False
    assert updated_device_data["room_id"] == room_id # room_id not changed here
    assert updated_device_data["device_type_id"] == created_device_type["id"] # device_type_id not changed
    assert updated_device_data["created_at"] == created_device_data["created_at"]
    assert updated_device_data["updated_at"] != created_device_data["updated_at"]

    response_get = await async_client.get(f"{API_PREFIX}/devices/{device_id}")
    assert response_get.status_code == 200
    retrieved_data = response_get.json()
    assert retrieved_data["name"] == update_payload["name"]
    assert retrieved_data["is_active"] is False

@pytest.mark.asyncio
async def test_update_device_partial(async_client: AsyncClient, created_room, sample_device_payload):
    room_id = created_room["id"]
    response_create = await async_client.post(
        f"{API_PREFIX}/rooms/{room_id}/devices", json=sample_device_payload
    )
    created_data = response_create.json()
    device_id = created_data["id"]

    partial_update_payload = {"name": "Thermostat Renamed"}
    response_update = await async_client.put(f"{API_PREFIX}/devices/{device_id}", json=partial_update_payload)
    assert response_update.status_code == 200
    updated_data = response_update.json()

    assert updated_data["name"] == partial_update_payload["name"]
    assert updated_data["state"] == sample_device_payload["state"] # State should remain unchanged
    assert updated_data["is_active"] == sample_device_payload["is_active"] # is_active should remain

@pytest.mark.asyncio
async def test_update_nonexistent_device(async_client: AsyncClient):
    non_existent_id = "33333333-3333-3333-3333-333333333333"
    update_payload = {"name": "Phantom Device"}
    response_update = await async_client.put(f"{API_PREFIX}/devices/{non_existent_id}", json=update_payload)
    assert response_update.status_code == 404

@pytest.mark.asyncio
async def test_delete_device(async_client: AsyncClient, created_room, sample_device_payload):
    room_id = created_room["id"]
    
    response_create = await async_client.post(
        f"{API_PREFIX}/rooms/{room_id}/devices", json=sample_device_payload
    )
    assert response_create.status_code == 201
    device_id = response_create.json()["id"]

    response_delete = await async_client.delete(f"{API_PREFIX}/devices/{device_id}")
    assert response_delete.status_code == 204

    response_get = await async_client.get(f"{API_PREFIX}/devices/{device_id}")
    assert response_get.status_code == 404

    response_list = await async_client.get(f"{API_PREFIX}/rooms/{room_id}/devices")
    assert response_list.status_code == 200
    devices_in_room = response_list.json()
    assert not any(d["id"] == device_id for d in devices_in_room)

@pytest.mark.asyncio
async def test_delete_nonexistent_device(async_client: AsyncClient):
    non_existent_id = "44444444-4444-4444-4444-444444444444"
    response_delete = await async_client.delete(f"{API_PREFIX}/devices/{non_existent_id}")
    assert response_delete.status_code == 404

@pytest.mark.asyncio
async def test_device_action(async_client: AsyncClient, created_room, sample_device_payload):
    room_id = created_room["id"]
    response_create = await async_client.post(
        f"{API_PREFIX}/rooms/{room_id}/devices", json=sample_device_payload
    )
    assert response_create.status_code == 201
    device_id = response_create.json()["id"]
    initial_state = response_create.json()["state"]
    assert initial_state["power"] == "OFF"

    action_payload = {
        "type": "setState",
        "payload": {"power": "ON", "target_temp": 25}
    }
    response_action = await async_client.post(f"{API_PREFIX}/devices/{device_id}/actions", json=action_payload)
    assert response_action.status_code == 200
    action_result_data = response_action.json()

    assert action_result_data["id"] == device_id
    assert action_result_data["state"]["power"] == "ON"
    assert action_result_data["state"]["target_temp"] == 25

    # Verify state change by getting the device again
    response_get = await async_client.get(f"{API_PREFIX}/devices/{device_id}")
    assert response_get.status_code == 200
    updated_device_data = response_get.json()
    assert updated_device_data["state"]["power"] == "ON"
    assert updated_device_data["state"]["target_temp"] == 25

@pytest.mark.asyncio
async def test_device_action_nonexistent_device(async_client: AsyncClient):
    non_existent_id = "55555555-5555-5555-5555-555555555555"
    action_payload = {"type": "setState", "payload": {"power": "ON"}}
    response_action = await async_client.post(f"{API_PREFIX}/devices/{non_existent_id}/actions", json=action_payload)
    assert response_action.status_code == 404

@pytest.mark.asyncio
async def test_device_action_invalid_action_type(async_client: AsyncClient, created_room, sample_device_payload):
    room_id = created_room["id"]
    response_create = await async_client.post(
        f"{API_PREFIX}/rooms/{room_id}/devices", json=sample_device_payload
    )
    device_id = response_create.json()["id"]

    action_payload = {
        "type": "nonExistentActionType", # This type might not be handled by the engine
        "payload": {"value": 100}
    }
    # The expected status code depends on how the engine handles unknown action types.
    # It might be 400 (Bad Request) if the action type is validated and rejected.
    # Or it might be 200 if the engine simply doesn't change state for unknown types but doesn't error.
    # Assuming 400 for now as a common practice for invalid requests.
    response_action = await async_client.post(f"{API_PREFIX}/devices/{device_id}/actions", json=action_payload)
    assert response_action.status_code == 400 # Or another appropriate error code based on engine logic
