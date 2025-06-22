import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app # Ensure app is imported for lifespan and routing

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
        "name": "Test Building for Rooms",
        "address": "456 Room Test Blvd",
        "geolocation": {"latitude": 31.0, "longitude": -101.0}
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
        "plan_url": "http://example.com/bldg_rooms/floor1_plan.png"
    }
    response = await async_client.post(f"{API_PREFIX}/buildings/{building_id}/floors", json=payload)
    assert response.status_code == 201
    return response.json()

@pytest.fixture
async def sample_room_payload(created_floor: dict):
    """Provides a valid payload for creating a room."""
    # created_floor ya es un diccionario gracias al fixture en conftest.py
    return {
        "name": "Living Room"
    }

@pytest.mark.asyncio
async def test_create_and_get_room(async_client: AsyncClient, created_floor, sample_room_payload):
    floor_id = created_floor["id"]

    # 1. Create Room
    response_create = await async_client.post(
        f"{API_PREFIX}/floors/{floor_id}/rooms",
        json=sample_room_payload
    )
    assert response_create.status_code == 201
    created_data = response_create.json()

    assert "id" in created_data
    assert created_data["name"] == sample_room_payload["name"]
    assert created_data["floor_id"] == floor_id
    assert "created_at" in created_data
    assert "updated_at" in created_data
    
    room_id = created_data["id"]

    # 2. Get Room by ID
    response_get = await async_client.get(f"{API_PREFIX}/rooms/{room_id}")
    assert response_get.status_code == 200
    retrieved_data = response_get.json()

    assert retrieved_data["id"] == room_id
    assert retrieved_data["name"] == sample_room_payload["name"]
    assert retrieved_data["floor_id"] == floor_id
    assert retrieved_data["created_at"] == created_data["created_at"]

@pytest.mark.asyncio
async def test_list_rooms_for_floor(async_client: AsyncClient, created_floor, sample_room_payload):
    floor_id = created_floor["id"]

    # Create a room to ensure the list is not empty
    await async_client.post(f"{API_PREFIX}/floors/{floor_id}/rooms", json=sample_room_payload)
    
    another_room_payload = {"name": "Kitchen"}
    await async_client.post(f"{API_PREFIX}/floors/{floor_id}/rooms", json=another_room_payload)

    response = await async_client.get(f"{API_PREFIX}/floors/{floor_id}/rooms")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

    for room_data in data:
        assert "id" in room_data
        assert "name" in room_data
        assert room_data["floor_id"] == floor_id
        if room_data["name"] == sample_room_payload["name"]:
            pass # Already checked general fields
        elif room_data["name"] == another_room_payload["name"]:
            pass

@pytest.mark.asyncio
async def test_create_room_invalid_payload(async_client: AsyncClient, created_floor):
    floor_id = created_floor["id"]
    # Missing 'name'
    invalid_payload = {} 
    response = await async_client.post(f"{API_PREFIX}/floors/{floor_id}/rooms", json=invalid_payload)
    assert response.status_code == 422 # Unprocessable Entity

@pytest.mark.asyncio
async def test_create_room_for_nonexistent_floor(async_client: AsyncClient, sample_room_payload):
    non_existent_floor_id = "00000000-0000-0000-0000-000000000000"
    response = await async_client.post(
        f"{API_PREFIX}/floors/{non_existent_floor_id}/rooms",
        json=sample_room_payload
    )
    assert response.status_code == 404 # Floor not found

@pytest.mark.asyncio
async def test_get_nonexistent_room(async_client: AsyncClient):
    non_existent_id = "11111111-1111-1111-1111-111111111111"
    response = await async_client.get(f"{API_PREFIX}/rooms/{non_existent_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_room(async_client: AsyncClient, created_floor, sample_room_payload):
    floor_id = created_floor["id"]
    
    # 1. Create a room
    response_create = await async_client.post(
        f"{API_PREFIX}/floors/{floor_id}/rooms",
        json=sample_room_payload
    )
    assert response_create.status_code == 201
    created_room_data = response_create.json()
    room_id = created_room_data["id"]

    # 2. Update the room
    update_payload = {
        "name": "Master Bedroom"
    }
    response_update = await async_client.put(f"{API_PREFIX}/rooms/{room_id}", json=update_payload)
    assert response_update.status_code == 200
    updated_room_data = response_update.json()

    assert updated_room_data["id"] == room_id
    assert updated_room_data["name"] == update_payload["name"]
    assert updated_room_data["floor_id"] == floor_id
    assert updated_room_data["created_at"] == created_room_data["created_at"]
    assert updated_room_data["updated_at"] != created_room_data["updated_at"]

    # 3. Get the room again to verify persistence
    response_get = await async_client.get(f"{API_PREFIX}/rooms/{room_id}")
    assert response_get.status_code == 200
    retrieved_room_data = response_get.json()
    assert retrieved_room_data["name"] == update_payload["name"]

@pytest.mark.asyncio
async def test_update_room_partial_not_supported_by_model(async_client: AsyncClient, created_floor, sample_room_payload):
    # Note: RoomUpdate model only has 'name'. If other fields were optional, this test would be different.
    floor_id = created_floor["id"]
    response_create = await async_client.post(
        f"{API_PREFIX}/floors/{floor_id}/rooms", json=sample_room_payload
    )
    created_room_data = response_create.json()
    room_id = created_room_data["id"]

    # Attempting to update with an empty payload (or non-name field)
    # Pydantic models for update usually have all fields optional.
    # If RoomUpdate had e.g. `description: Optional[str] = None`, this test would make more sense.
    # For now, updating with just a new name is the primary case.
    # If we send payload `{"description": "new desc"}`, and `description` is not in `RoomUpdate`,
    # FastAPI/Pydantic might ignore it or error depending on config.
    # Let's test updating only the name, which is the only field in RoomUpdate.
    partial_update_payload = {"name": "Study Room"}
    response_update = await async_client.put(f"{API_PREFIX}/rooms/{room_id}", json=partial_update_payload)
    assert response_update.status_code == 200
    updated_data = response_update.json()
    assert updated_data["name"] == partial_update_payload["name"]


@pytest.mark.asyncio
async def test_update_nonexistent_room(async_client: AsyncClient):
    non_existent_id = "22222222-2222-2222-2222-222222222222"
    update_payload = {"name": "Ghost Room"}
    response_update = await async_client.put(f"{API_PREFIX}/rooms/{non_existent_id}", json=update_payload)
    assert response_update.status_code == 404

@pytest.mark.asyncio
async def test_delete_room(async_client: AsyncClient, created_floor, sample_room_payload):
    floor_id = created_floor["id"]
    
    # 1. Create a room
    response_create = await async_client.post(
        f"{API_PREFIX}/floors/{floor_id}/rooms",
        json=sample_room_payload
    )
    assert response_create.status_code == 201
    room_id = response_create.json()["id"]

    # 2. Delete the room
    response_delete = await async_client.delete(f"{API_PREFIX}/rooms/{room_id}")
    assert response_delete.status_code == 204

    # 3. Try to get the deleted room
    response_get = await async_client.get(f"{API_PREFIX}/rooms/{room_id}")
    assert response_get.status_code == 404

    # 4. Check if it's gone from the floor's list of rooms
    response_list = await async_client.get(f"{API_PREFIX}/floors/{floor_id}/rooms")
    assert response_list.status_code == 200
    rooms_in_floor = response_list.json()
    assert not any(r["id"] == room_id for r in rooms_in_floor)

@pytest.mark.asyncio
async def test_delete_nonexistent_room(async_client: AsyncClient):
    non_existent_id = "33333333-3333-3333-3333-333333333333"
    response_delete = await async_client.delete(f"{API_PREFIX}/rooms/{non_existent_id}")
    assert response_delete.status_code == 404
