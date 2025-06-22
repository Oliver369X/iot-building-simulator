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
    """Fixture to create a building and return its ID."""
    payload = {
        "name": "Test Building for Floors",
        "address": "789 Floor Test Ave",
        "geolocation": {"latitude": 30.0, "longitude": -100.0}
    }
    response = await async_client.post(f"{API_PREFIX}/buildings", json=payload)
    assert response.status_code == 201
    return response.json() # Returns the full building dict

@pytest.fixture
async def sample_floor_payload(created_building: dict):
    """Provides a valid payload for creating a floor."""
    # created_building ya es un diccionario gracias al fixture en conftest.py
    return {
        "floor_number": 1,
        "plan_url": "http://example.com/floor1_plan.png"
    }

@pytest.mark.asyncio
async def test_create_and_get_floor(async_client: AsyncClient, created_building, sample_floor_payload):
    building_id = created_building["id"]

    # 1. Create Floor
    response_create = await async_client.post(
        f"{API_PREFIX}/buildings/{building_id}/floors",
        json=sample_floor_payload
    )
    assert response_create.status_code == 201
    created_data = response_create.json()

    assert "id" in created_data
    assert created_data["floor_number"] == sample_floor_payload["floor_number"]
    assert created_data["plan_url"] == sample_floor_payload["plan_url"]
    assert created_data["building_id"] == building_id
    assert "created_at" in created_data
    assert "updated_at" in created_data
    
    floor_id = created_data["id"]

    # 2. Get Floor by ID
    response_get = await async_client.get(f"{API_PREFIX}/floors/{floor_id}")
    assert response_get.status_code == 200
    retrieved_data = response_get.json()

    assert retrieved_data["id"] == floor_id
    assert retrieved_data["floor_number"] == sample_floor_payload["floor_number"]
    assert retrieved_data["plan_url"] == sample_floor_payload["plan_url"]
    assert retrieved_data["building_id"] == building_id
    assert retrieved_data["created_at"] == created_data["created_at"]

@pytest.mark.asyncio
async def test_list_floors_for_building(async_client: AsyncClient, created_building, sample_floor_payload):
    building_id = created_building["id"]

    # Create a floor to ensure the list is not empty
    await async_client.post(f"{API_PREFIX}/buildings/{building_id}/floors", json=sample_floor_payload)
    
    another_floor_payload = {"floor_number": 2, "plan_url": "http://example.com/floor2_plan.png"}
    await async_client.post(f"{API_PREFIX}/buildings/{building_id}/floors", json=another_floor_payload)

    response = await async_client.get(f"{API_PREFIX}/buildings/{building_id}/floors")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

    for floor_data in data:
        assert "id" in floor_data
        assert "floor_number" in floor_data
        assert floor_data["building_id"] == building_id # Corregido: acceder a la clave del diccionario
        if floor_data["floor_number"] == sample_floor_payload["floor_number"]:
            assert floor_data["plan_url"] == sample_floor_payload["plan_url"]
        elif floor_data["floor_number"] == another_floor_payload["floor_number"]:
            assert floor_data["plan_url"] == another_floor_payload["plan_url"]

@pytest.mark.asyncio
async def test_create_floor_invalid_payload(async_client: AsyncClient, created_building):
    building_id = created_building["id"]
    # Missing 'floor_number'
    invalid_payload = {"plan_url": "http://example.com/invalid.png"}
    response = await async_client.post(f"{API_PREFIX}/buildings/{building_id}/floors", json=invalid_payload)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_floor_for_nonexistent_building(async_client: AsyncClient, sample_floor_payload):
    non_existent_building_id = "00000000-0000-0000-0000-000000000000"
    response = await async_client.post(
        f"{API_PREFIX}/buildings/{non_existent_building_id}/floors",
        json=sample_floor_payload
    )
    assert response.status_code == 404 # Building not found

@pytest.mark.asyncio
async def test_get_nonexistent_floor(async_client: AsyncClient):
    non_existent_id = "11111111-1111-1111-1111-111111111111"
    response = await async_client.get(f"{API_PREFIX}/floors/{non_existent_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_floor(async_client: AsyncClient, created_building, sample_floor_payload):
    building_id = created_building["id"]
    
    # 1. Create a floor
    response_create = await async_client.post(
        f"{API_PREFIX}/buildings/{building_id}/floors",
        json=sample_floor_payload
    )
    assert response_create.status_code == 201
    created_floor_data = response_create.json()
    floor_id = created_floor_data["id"]

    # 2. Update the floor
    update_payload = {
        "floor_number": 101,
        "plan_url": "http://example.com/updated_floor_plan.jpg"
    }
    response_update = await async_client.put(f"{API_PREFIX}/floors/{floor_id}", json=update_payload)
    assert response_update.status_code == 200
    updated_floor_data = response_update.json()

    assert updated_floor_data["id"] == floor_id
    assert updated_floor_data["floor_number"] == update_payload["floor_number"]
    assert updated_floor_data["plan_url"] == update_payload["plan_url"]
    assert updated_floor_data["building_id"] == building_id
    assert updated_floor_data["created_at"] == created_floor_data["created_at"]
    assert updated_floor_data["updated_at"] != created_floor_data["updated_at"]

    # 3. Get the floor again to verify persistence
    response_get = await async_client.get(f"{API_PREFIX}/floors/{floor_id}")
    assert response_get.status_code == 200
    retrieved_floor_data = response_get.json()
    assert retrieved_floor_data["floor_number"] == update_payload["floor_number"]
    assert retrieved_floor_data["plan_url"] == update_payload["plan_url"]

@pytest.mark.asyncio
async def test_update_floor_partial(async_client: AsyncClient, created_building, sample_floor_payload):
    building_id = created_building["id"]
    response_create = await async_client.post(
        f"{API_PREFIX}/buildings/{building_id}/floors", json=sample_floor_payload
    )
    created_floor_data = response_create.json()
    floor_id = created_floor_data["id"]

    partial_update_payload = {"floor_number": 77}
    response_update = await async_client.put(f"{API_PREFIX}/floors/{floor_id}", json=partial_update_payload)
    assert response_update.status_code == 200
    updated_data = response_update.json()

    assert updated_data["floor_number"] == partial_update_payload["floor_number"]
    assert updated_data["plan_url"] == sample_floor_payload["plan_url"] # Should remain unchanged

@pytest.mark.asyncio
async def test_update_nonexistent_floor(async_client: AsyncClient):
    non_existent_id = "22222222-2222-2222-2222-222222222222"
    update_payload = {"floor_number": 99}
    response_update = await async_client.put(f"{API_PREFIX}/floors/{non_existent_id}", json=update_payload)
    assert response_update.status_code == 404

@pytest.mark.asyncio
async def test_delete_floor(async_client: AsyncClient, created_building, sample_floor_payload):
    building_id = created_building["id"]
    
    # 1. Create a floor
    response_create = await async_client.post(
        f"{API_PREFIX}/buildings/{building_id}/floors",
        json=sample_floor_payload
    )
    assert response_create.status_code == 201
    floor_id = response_create.json()["id"]

    # 2. Delete the floor
    response_delete = await async_client.delete(f"{API_PREFIX}/floors/{floor_id}")
    assert response_delete.status_code == 204

    # 3. Try to get the deleted floor
    response_get = await async_client.get(f"{API_PREFIX}/floors/{floor_id}")
    assert response_get.status_code == 404

    # 4. Check if it's gone from the building's list of floors
    response_list = await async_client.get(f"{API_PREFIX}/buildings/{building_id}/floors")
    assert response_list.status_code == 200
    floors_in_building = response_list.json()
    assert not any(f["id"] == floor_id for f in floors_in_building)


@pytest.mark.asyncio
async def test_delete_nonexistent_floor(async_client: AsyncClient):
    non_existent_id = "33333333-3333-3333-3333-333333333333"
    response_delete = await async_client.delete(f"{API_PREFIX}/floors/{non_existent_id}")
    assert response_delete.status_code == 404
