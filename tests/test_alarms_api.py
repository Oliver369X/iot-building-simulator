import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app, simulation_engine # Ensure app and engine are imported
from src.api import validators as api_validators
from src.database import models as db_models
from datetime import datetime, timedelta, timezone
import uuid
from unittest.mock import patch, MagicMock # For mocking engine alarm creation

API_PREFIX = "/api/v1"

@pytest.fixture
async def async_client():
    """Async client for API tests."""
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client

# Fixtures to create hierarchy (can be simplified if not all are strictly needed for alarm tests)
@pytest.fixture
async def created_building(async_client: AsyncClient):
    payload = {"name": "Test Building for Alarms"}
    response = await async_client.post(f"{API_PREFIX}/buildings", json=payload)
    return response.json()

@pytest.fixture
async def created_floor(async_client: AsyncClient, created_building):
    payload = {"floor_number": 1}
    response = await async_client.post(f"{API_PREFIX}/buildings/{created_building['id']}/floors", json=payload)
    return response.json()

@pytest.fixture
async def created_room(async_client: AsyncClient, created_floor):
    payload = {"name": "Alarm Control Room"}
    response = await async_client.post(f"{API_PREFIX}/floors/{created_floor['id']}/rooms", json=payload)
    return response.json()

@pytest.fixture
async def created_device_type(async_client: AsyncClient):
    payload = {"id": str(uuid.uuid4()), "type_name": "Alarmable Sensor"}
    response = await async_client.post(f"{API_PREFIX}/device-types", json=payload)
    return response.json()

@pytest.fixture
async def created_device_for_alarm(async_client: AsyncClient, created_room, created_device_type):
    payload = {"name": "Critical Sensor", "device_type_id": created_device_type["id"]}
    response = await async_client.post(f"{API_PREFIX}/rooms/{created_room['id']}/devices", json=payload)
    return response.json()

@pytest.fixture
async def created_alarm_direct(created_device: dict): # Use created_device from conftest
    """
    Crea una alarma directamente en la base de datos a través del motor de simulación
    para pruebas de reconocimiento.
    """
    if not simulation_engine:
        pytest.skip("Simulation engine not available for direct alarm creation")

    alarm_data = api_validators.AlarmCreate(
        device_id=created_device["id"], # Usar el ID del dispositivo creado
        severity="CRITICAL",
        description="Test critical alarm for ACK"
    )
    # Usar el método del motor de simulación para crear la alarma en la DB real
    # Asumiendo que simulation_engine tiene un método para crear alarmas directamente
    # Si no existe, se necesitaría un método `create_alarm` en el motor.
    # Por ahora, vamos a crearla directamente en la sesión de DB para el test.
    db = simulation_engine._get_db() # Acceder a la sesión de DB del motor
    try:
        alarm_id = str(uuid.uuid4())
        db_alarm = db_models.Alarm(
            id=alarm_id,
            device_id=alarm_data.device_id,
            severity=alarm_data.severity,
            status="NEW",
            description=alarm_data.description,
            triggered_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(db_alarm)
        db.commit()
        db.refresh(db_alarm)
        yield db_alarm.to_dict() # Devolver como dict
    except Exception as e:
        db.rollback()
        pytest.fail(f"Failed to create alarm directly in DB: {e}")
    finally:
        db.close()


@pytest.mark.asyncio
async def test_list_alarms_empty(async_client: AsyncClient):
    # Asumiendo un estado limpio o filtros que no producen resultados
    response = await async_client.get(f"{API_PREFIX}/alarms?severity=NON_EXISTENT_SEVERITY")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

@pytest.mark.asyncio
async def test_acknowledge_alarm(async_client: AsyncClient, created_alarm_direct: dict): # Esperar un dict
    alarm_id_to_ack = created_alarm_direct["id"] # Acceder como dict
    
    response_ack = await async_client.post(f"{API_PREFIX}/alarms/{alarm_id_to_ack}/ack")
    
    assert response_ack.status_code == 200
    ack_data = response_ack.json()

    assert ack_data["id"] == alarm_id_to_ack
    assert ack_data["status"] == "ACK"
    assert ack_data["severity"] == created_alarm_direct["severity"]
    # Verificar que updated_at ha cambiado (Pydantic convierte datetime a string)
    assert ack_data["updated_at"] != created_alarm_direct["triggered_at"]


@pytest.mark.asyncio
async def test_acknowledge_nonexistent_alarm(async_client: AsyncClient):
    non_existent_alarm_id = "00000000-0000-0000-0000-000000000000"
    
    response = await async_client.post(f"{API_PREFIX}/alarms/{non_existent_alarm_id}/ack")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_acknowledge_already_acknowledged_alarm(async_client: AsyncClient, created_alarm_direct: dict): # Esperar un dict
    alarm_id_to_ack = created_alarm_direct["id"] # Acceder como dict
    
    # Primero, reconocerla para que esté en estado ACK
    response_first_ack = await async_client.post(f"{API_PREFIX}/alarms/{alarm_id_to_ack}/ack")
    assert response_first_ack.status_code == 200
    
    # Intentar reconocerla de nuevo
    response_second_ack = await async_client.post(f"{API_PREFIX}/alarms/{alarm_id_to_ack}/ack")
    # El endpoint debería devolver 400 si el motor lanza SimulationError
    assert response_second_ack.status_code == 400
    assert "already acknowledged" in response_second_ack.json()["detail"]


@pytest.mark.asyncio
async def test_list_alarms_with_filters(async_client: AsyncClient, created_device: dict): # Usar created_device
    if not simulation_engine:
        pytest.skip("Simulation engine not available for alarm creation/listing")

    # Crear algunas alarmas directamente en la DB para probar los filtros
    db = simulation_engine._get_db()
    try:
        alarm1_data = {
            "id": str(uuid.uuid4()), "device_id": created_device["id"], "severity": "HIGH", "status": "NEW",
            "description": "High temp", "triggered_at": datetime.now(timezone.utc) - timedelta(days=1),
            "updated_at": datetime.now(timezone.utc) - timedelta(days=1)
        }
        alarm2_data = {
            "id": str(uuid.uuid4()), "device_id": created_device["id"], "severity": "CRITICAL", "status": "ACK",
            "description": "System failure", "triggered_at": datetime.now(timezone.utc) - timedelta(hours=5),
            "updated_at": datetime.now(timezone.utc) - timedelta(hours=4) # Acknowledged later
        }
        # Crear una alarma para un dispositivo en otro edificio (mocked)
        # Esto requeriría crear un edificio, piso, habitación y dispositivo separados.
        # Por simplicidad, para este test, nos centraremos en las alarmas del created_device.

        db.add_all([db_models.Alarm(**alarm1_data), db_models.Alarm(**alarm2_data)])
        db.commit()

        # Test 1: Filter by severity and status
        response = await async_client.get(f"{API_PREFIX}/alarms?severity=HIGH&status=NEW")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["severity"] == "HIGH"
        assert data[0]["status"] == "NEW"
        assert data[0]["id"] == alarm1_data["id"]

        # Test 2: Filter by status
        response_ack = await async_client.get(f"{API_PREFIX}/alarms?status=ACK")
        assert response_ack.status_code == 200
        data_ack = response_ack.json()
        assert len(data_ack) == 1
        assert data_ack[0]["status"] == "ACK"
        assert data_ack[0]["id"] == alarm2_data["id"]
        
        # Test 3: Filter by date range
        start_date_filter = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        end_date_filter = datetime.now(timezone.utc).isoformat()
        response_date_range = await async_client.get(f"{API_PREFIX}/alarms?start_date={start_date_filter}&end_date={end_date_filter}")
        assert response_date_range.status_code == 200
        data_date_range = response_date_range.json()
        assert len(data_date_range) == 2 # Both alarms should be within this range

    except Exception as e:
        db.rollback()
        pytest.fail(f"Error during test_list_alarms_with_filters: {e}")
    finally:
        db.close()
