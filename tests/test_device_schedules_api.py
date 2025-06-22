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
    payload = {"name": "Test Building for Schedules"}
    response = await async_client.post(f"{API_PREFIX}/buildings", json=payload)
    return response.json()

@pytest.fixture
async def created_floor(async_client: AsyncClient, created_building):
    payload = {"floor_number": 1}
    response = await async_client.post(f"{API_PREFIX}/buildings/{created_building['id']}/floors", json=payload)
    return response.json()

@pytest.fixture
async def created_room(async_client: AsyncClient, created_floor):
    payload = {"name": "Scheduled Room"}
    response = await async_client.post(f"{API_PREFIX}/floors/{created_floor['id']}/rooms", json=payload)
    return response.json()

@pytest.fixture
async def created_device_type(async_client: AsyncClient):
    payload = {"id": str(uuid.uuid4()), "type_name": "Schedulable Light"}
    response = await async_client.post(f"{API_PREFIX}/device-types", json=payload)
    return response.json()

@pytest.fixture
async def created_device(async_client: AsyncClient, created_room, created_device_type):
    """Fixture to create a device and return its data."""
    payload = {
        "name": "Lounge Light",
        "device_type_id": created_device_type["id"],
        "state": {"power": "OFF"}
    }
    response = await async_client.post(f"{API_PREFIX}/rooms/{created_room['id']}/devices", json=payload)
    assert response.status_code == 201
    return response.json()

@pytest.fixture
async def sample_schedule_payload(created_device: dict):
    """Provides a valid payload for creating a device schedule."""
    # created_device ya es un diccionario gracias al fixture en conftest.py
    return {
        "cron_expression": "0 18 * * *", # At 6 PM every day
        "action": {"type": "setState", "payload": {"power": "ON", "brightness": 75}},
        "is_enabled": True
    }

@pytest.mark.asyncio
async def test_create_and_get_schedule(async_client: AsyncClient, created_device, sample_schedule_payload):
    device_id = created_device["id"]

    # 1. Create Schedule
    response_create = await async_client.post(
        f"{API_PREFIX}/devices/{device_id}/schedules",
        json=sample_schedule_payload
    )
    assert response_create.status_code == 201
    created_data = response_create.json()

    assert "id" in created_data
    assert created_data["cron_expression"] == sample_schedule_payload["cron_expression"]
    assert created_data["action"] == sample_schedule_payload["action"]
    assert created_data["is_enabled"] == sample_schedule_payload["is_enabled"]
    assert created_data["device_id"] == device_id
    assert "created_at" in created_data
    assert "updated_at" in created_data
    
    schedule_id = created_data["id"]

    # 2. Get Schedule by ID (using the generic /schedules/{id} endpoint)
    response_get = await async_client.get(f"{API_PREFIX}/schedules/{schedule_id}")
    assert response_get.status_code == 200
    retrieved_data = response_get.json()

    assert retrieved_data["id"] == schedule_id
    assert retrieved_data["cron_expression"] == sample_schedule_payload["cron_expression"]
    assert retrieved_data["action"] == sample_schedule_payload["action"]
    assert retrieved_data["device_id"] == device_id
    assert retrieved_data["created_at"] == created_data["created_at"]

@pytest.mark.asyncio
async def test_list_schedules_for_device(async_client: AsyncClient, created_device, sample_schedule_payload):
    device_id = created_device["id"]

    await async_client.post(f"{API_PREFIX}/devices/{device_id}/schedules", json=sample_schedule_payload)
    
    another_schedule_payload = {
        "cron_expression": "0 6 * * *", # At 6 AM
        "action": {"type": "setState", "payload": {"power": "OFF"}},
        "is_enabled": True
    }
    await async_client.post(f"{API_PREFIX}/devices/{device_id}/schedules", json=another_schedule_payload)

    response = await async_client.get(f"{API_PREFIX}/devices/{device_id}/schedules")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

    for schedule_data in data:
        assert "id" in schedule_data
        assert "cron_expression" in schedule_data
        assert schedule_data["device_id"] == device_id

@pytest.mark.asyncio
async def test_create_schedule_invalid_payload(async_client: AsyncClient, created_device):
    device_id = created_device["id"]
    # Missing 'cron_expression'
    invalid_payload = {"action": {"type": "setState", "payload": {"power": "ON"}}}
    response = await async_client.post(f"{API_PREFIX}/devices/{device_id}/schedules", json=invalid_payload)
    assert response.status_code == 422

    # Missing 'action'
    invalid_payload_no_action = {"cron_expression": "* * * * *"}
    response_no_action = await async_client.post(f"{API_PREFIX}/devices/{device_id}/schedules", json=invalid_payload_no_action)
    assert response_no_action.status_code == 422

@pytest.mark.asyncio
async def test_create_schedule_for_nonexistent_device(async_client: AsyncClient, sample_schedule_payload):
    non_existent_device_id = "00000000-0000-0000-0000-000000000000"
    response = await async_client.post(
        f"{API_PREFIX}/devices/{non_existent_device_id}/schedules",
        json=sample_schedule_payload
    )
    assert response.status_code == 404 # Device not found

@pytest.mark.asyncio
async def test_get_nonexistent_schedule(async_client: AsyncClient):
    non_existent_id = "11111111-1111-1111-1111-111111111111"
    response = await async_client.get(f"{API_PREFIX}/schedules/{non_existent_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_schedule(async_client: AsyncClient, created_device, sample_schedule_payload):
    device_id = created_device["id"]
    
    response_create = await async_client.post(
        f"{API_PREFIX}/devices/{device_id}/schedules", json=sample_schedule_payload
    )
    assert response_create.status_code == 201
    created_schedule_data = response_create.json()
    schedule_id = created_schedule_data["id"]

    update_payload = {
        "cron_expression": "30 7 * * 1-5", # 7:30 AM on weekdays
        "action": {"type": "setState", "payload": {"power": "ON", "brightness": 100}},
        "is_enabled": False
    }
    response_update = await async_client.put(f"{API_PREFIX}/schedules/{schedule_id}", json=update_payload)
    assert response_update.status_code == 200
    updated_schedule_data = response_update.json()

    assert updated_schedule_data["id"] == schedule_id
    assert updated_schedule_data["cron_expression"] == update_payload["cron_expression"]
    assert updated_schedule_data["action"] == update_payload["action"]
    assert updated_schedule_data["is_enabled"] is False
    assert updated_schedule_data["device_id"] == device_id
    assert updated_schedule_data["created_at"] == created_schedule_data["created_at"]
    assert updated_schedule_data["updated_at"] != created_schedule_data["updated_at"]

    response_get = await async_client.get(f"{API_PREFIX}/schedules/{schedule_id}")
    assert response_get.status_code == 200
    retrieved_data = response_get.json()
    assert retrieved_data["cron_expression"] == update_payload["cron_expression"]
    assert retrieved_data["is_enabled"] is False

@pytest.mark.asyncio
async def test_update_schedule_partial(async_client: AsyncClient, created_device, sample_schedule_payload):
    device_id = created_device["id"]
    response_create = await async_client.post(
        f"{API_PREFIX}/devices/{device_id}/schedules", json=sample_schedule_payload
    )
    created_data = response_create.json()
    schedule_id = created_data["id"]

    partial_update_payload = {"is_enabled": False}
    response_update = await async_client.put(f"{API_PREFIX}/schedules/{schedule_id}", json=partial_update_payload)
    assert response_update.status_code == 200
    updated_data = response_update.json()

    assert updated_data["is_enabled"] is False
    assert updated_data["cron_expression"] == sample_schedule_payload["cron_expression"] # Should remain
    assert updated_data["action"] == sample_schedule_payload["action"] # Should also remain

@pytest.mark.asyncio
async def test_update_nonexistent_schedule(async_client: AsyncClient):
    non_existent_id = "22222222-2222-2222-2222-222222222222"
    update_payload = {"is_enabled": True}
    response_update = await async_client.put(f"{API_PREFIX}/schedules/{non_existent_id}", json=update_payload)
    assert response_update.status_code == 404

@pytest.mark.asyncio
async def test_delete_schedule(async_client: AsyncClient, created_device, sample_schedule_payload):
    device_id = created_device["id"]
    
    response_create = await async_client.post(
        f"{API_PREFIX}/devices/{device_id}/schedules", json=sample_schedule_payload
    )
    assert response_create.status_code == 201
    schedule_id = response_create.json()["id"]

    response_delete = await async_client.delete(f"{API_PREFIX}/schedules/{schedule_id}")
    assert response_delete.status_code == 204

    response_get = await async_client.get(f"{API_PREFIX}/schedules/{schedule_id}")
    assert response_get.status_code == 404

    response_list = await async_client.get(f"{API_PREFIX}/devices/{device_id}/schedules")
    assert response_list.status_code == 200
    schedules_for_device = response_list.json()
    assert not any(s["id"] == schedule_id for s in schedules_for_device)

@pytest.mark.asyncio
async def test_delete_nonexistent_schedule(async_client: AsyncClient):
    non_existent_id = "33333333-3333-3333-3333-333333333333"
    response_delete = await async_client.delete(f"{API_PREFIX}/schedules/{non_existent_id}")
    assert response_delete.status_code == 404
