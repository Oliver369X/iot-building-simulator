""" import pytest
from httpx import AsyncClient
from src.api.main import app
from src.database.connection import SessionLocal
from src.database.models import Building, Floor, Room, Device, DeviceType
import asyncio
import json

# Fixture para el cliente asíncrono de FastAPI
@pytest.fixture
async def async_client():
    from httpx import ASGITransport
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client

# Fixture para una sesión de base de datos limpia
@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fixture para crear un edificio, piso, habitación y dispositivo de prueba
@pytest.fixture
async def setup_building_hierarchy(async_client, db_session):
    # Crear tipo de dispositivo
    device_type_payload = {"type_name": "temperature_sensor", "properties": {"unit": "celsius"}}
    resp_dt = await async_client.post("/api/v1/device-types", json=device_type_payload)
    assert resp_dt.status_code == 201
    device_type_id = resp_dt.json()["id"]

    # Crear edificio
    building_payload = {"name": "Test Building Sim", "address": "123 Sim St", "geolocation": {"latitude": 1.0, "longitude": 1.0}}
    resp_b = await async_client.post("/api/v1/buildings", json=building_payload)
    assert resp_b.status_code == 201
    building_id = resp_b.json()["id"]

    # Crear piso
    floor_payload = {"floor_number": 1, "plan_url": "http://example.com/plan1.png"}
    resp_f = await async_client.post(f"/api/v1/buildings/{building_id}/floors", json=floor_payload)
    assert resp_f.status_code == 201
    floor_id = resp_f.json()["id"]

    # Crear habitación
    room_payload = {"name": "Test Room Sim"}
    resp_r = await async_client.post(f"/api/v1/floors/{floor_id}/rooms", json=room_payload)
    assert resp_r.status_code == 201
    room_id = resp_r.json()["id"]

    # Crear dispositivo
    device_payload = {"name": "Test Temp Sensor", "device_type_id": device_type_id, "is_active": True}
    resp_d = await async_client.post(f"/api/v1/rooms/{room_id}/devices", json=device_payload)
    assert resp_d.status_code == 201
    device_id = resp_d.json()["id"]

    yield {
        "building_id": building_id,
        "floor_id": floor_id,
        "room_id": room_id,
        "device_id": device_id,
        "device_type_id": device_type_id
    }

    # Limpieza: Eliminar edificio (esto debería cascadear y eliminar todo lo demás)
    await async_client.delete(f"/api/v1/buildings/{building_id}")
    # Eliminar tipo de dispositivo
    await async_client.delete(f"/api/v1/device-types/{device_type_id}")


@pytest.mark.asyncio
async def test_building_simulation_control(async_client, setup_building_hierarchy, db_session):
    building_id = setup_building_hierarchy["building_id"]
    device_id = setup_building_hierarchy["device_id"]

    # 1. Verificar estado inicial de simulación (debería ser False)
    building_db = db_session.query(Building).filter(Building.id == building_id).first()
    assert building_db.is_simulating is False

    # 2. Activar simulación para el edificio
    response = await async_client.post(f"/api/v1/buildings/{building_id}/simulate?status=true")
    assert response.status_code == 200
    updated_building = response.json()
    assert updated_building["id"] == building_id
    assert updated_building["is_simulating"] is True

    # Verificar en la base de datos
    building_db = db_session.query(Building).filter(Building.id == building_id).first()
    assert building_db.is_simulating is True

    # 3. Desactivar simulación para el edificio
    response = await async_client.post(f"/api/v1/buildings/{building_id}/simulate?status=false")
    assert response.status_code == 200
    updated_building = response.json()
    assert updated_building["id"] == building_id
    assert updated_building["is_simulating"] is False

    # Verificar en la base de datos
    building_db = db_session.query(Building).filter(Building.id == building_id).first()
    assert building_db.is_simulating is False

@pytest.mark.asyncio
async def test_floor_simulation_control(async_client, setup_building_hierarchy, db_session):
    building_id = setup_building_hierarchy["building_id"]
    floor_id = setup_building_hierarchy["floor_id"]
    device_id = setup_building_hierarchy["device_id"]

    # 1. Verificar estado inicial de simulación (debería ser False)
    floor_db = db_session.query(Floor).filter(Floor.id == floor_id).first()
    assert floor_db.is_simulating is False

    # 2. Activar simulación para el piso
    response = await async_client.post(f"/api/v1/floors/{floor_id}/simulate?status=true")
    assert response.status_code == 200
    updated_floor = response.json()
    assert updated_floor["id"] == floor_id
    assert updated_floor["is_simulating"] is True

    # Verificar en la base de datos
    floor_db = db_session.query(Floor).filter(Floor.id == floor_id).first()
    assert floor_db.is_simulating is True

    # 3. Desactivar simulación para el piso
    response = await async_client.post(f"/api/v1/floors/{floor_id}/simulate?status=false")
    assert response.status_code == 200
    updated_floor = response.json()
    assert updated_floor["id"] == floor_id
    assert updated_floor["is_simulating"] is False

    # Verificar en la base de datos
    floor_db = db_session.query(Floor).filter(Floor.id == floor_id).first()
    assert floor_db.is_simulating is False

@pytest.mark.asyncio
async def test_room_simulation_control(async_client, setup_building_hierarchy, db_session):
    building_id = setup_building_hierarchy["building_id"]
    floor_id = setup_building_hierarchy["floor_id"]
    room_id = setup_building_hierarchy["room_id"]
    device_id = setup_building_hierarchy["device_id"]

    # 1. Verificar estado inicial de simulación (debería ser False)
    room_db = db_session.query(Room).filter(Room.id == room_id).first()
    assert room_db.is_simulating is False

    # 2. Activar simulación para la habitación
    response = await async_client.post(f"/api/v1/rooms/{room_id}/simulate?status=true")
    assert response.status_code == 200
    updated_room = response.json()
    assert updated_room["id"] == room_id
    assert updated_room["is_simulating"] is True

    # Verificar en la base de datos
    room_db = db_session.query(Room).filter(Room.id == room_id).first()
    assert room_db.is_simulating is True

    # 3. Desactivar simulación para la habitación
    response = await async_client.post(f"/api/v1/rooms/{room_id}/simulate?status=false")
    assert response.status_code == 200
    updated_room = response.json()
    assert updated_room["id"] == room_id
    assert updated_room["is_simulating"] is False

    # Verificar en la base de datos
    room_db = db_session.query(Room).filter(Room.id == room_id).first()
    assert room_db.is_simulating is False

@pytest.mark.asyncio
async def test_telemetry_websocket(async_client, setup_building_hierarchy, db_session):
    building_id = setup_building_hierarchy["building_id"]
    device_id = setup_building_hierarchy["device_id"]

    # 1. Conectarse al WebSocket usando TestClient
    from fastapi.testclient import TestClient
    test_client = TestClient(app)
    
    with test_client.websocket_connect("/ws/telemetry") as websocket:
        # 2. Activar simulación para el edificio
        response_sim = await async_client.post(f"/api/v1/buildings/{building_id}/simulate?status=true")
        assert response_sim.status_code == 200
        assert response_sim.json()["is_simulating"] is True

        # 3. Esperar y verificar mensajes de telemetría
        received_telemetry = []
        try:
            # Esperar hasta 5 segundos para recibir al menos 2 mensajes
            for _ in range(5): # Check multiple times
                message = await asyncio.wait_for(websocket.receive_json(), timeout=2)
                received_telemetry.append(message)
                if len(received_telemetry) >= 2:
                    break
        except asyncio.TimeoutError:
            pytest.fail("No telemetry messages received via WebSocket within timeout.")
        
        assert len(received_telemetry) >= 1, "Should receive at least one telemetry message"
        
        # Verificar el formato del mensaje
        first_message = received_telemetry[0]
        assert "device_id" in first_message
        assert "key" in first_message
        assert "value" in first_message
        assert "timestamp" in first_message
        assert first_message["device_id"] == device_id # Ensure it's from our device

        # 4. Desactivar simulación para el edificio
        response_sim_stop = await async_client.post(f"/api/v1/buildings/{building_id}/simulate?status=false")
        assert response_sim_stop.status_code == 200
        assert response_sim_stop.json()["is_simulating"] is False

        # 5. Verificar que no se reciben más mensajes después de desactivar
        try:
            await asyncio.wait_for(websocket.receive_json(), timeout=2)
            pytest.fail("Received telemetry message after simulation was stopped.")
        except asyncio.TimeoutError:
            # Expected behavior: no more messages
            pass
 """