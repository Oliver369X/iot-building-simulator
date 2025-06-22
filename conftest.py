import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.database.models import Base, Building, Floor, Room, DeviceType, Device, Alarm
from src.database.connection import engine, SessionLocal
from src.database.init_db import init_db as initialize_database_schema
from src.api.main import app, simulation_engine, startup_event, shutdown_event, get_db
from src.simulator.engine import SimulationEngine # Import SimulationEngine
from httpx import AsyncClient
import uuid
from datetime import datetime, timezone

# Añadir el directorio src al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "src")) # Adjust path to include 'src'

@pytest.fixture(scope="session", autouse=True)
def initialize_db_for_tests():
    """
    Fixture para inicializar la base de datos una vez por sesión de prueba.
    Esto asegura que las tablas se creen con el esquema más reciente.
    """
    print("\nInitializing database for tests...")
    initialize_database_schema()
    print("Database initialized.")
    yield
    # Opcional: limpiar la base de datos después de todas las pruebas si es necesario
    # initialize_database_schema() # Esto limpiaría la base de datos al final

@pytest.fixture(scope="function")
def db_session():
    """
    Fixture que proporciona una sesión de base de datos transaccional para cada prueba.
    La sesión se revierte al final de cada prueba para asegurar el aislamiento.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback() # Revertir la transacción para limpiar los cambios de la prueba
    connection.close()

@pytest.fixture(scope="session")
def anyio_backend():
    """
    Fixture necesario para pytest-asyncio y httpx.AsyncClient.
    Define el backend de AnyIO a usar.
    """
    return "asyncio"

@pytest.fixture(scope="function")
def test_engine(db_session: Session):
    """
    Fixture que proporciona una instancia de SimulationEngine configurada para usar
    la sesión de base de datos de prueba.
    """
    # Crear una SessionLocal temporal que use la conexión de prueba
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_session.bind)
    engine_instance = SimulationEngine(db_session_local=TestSessionLocal)
    # No iniciar el bucle continuo del motor en el contexto de las pruebas
    yield engine_instance

@pytest.fixture(scope="function")
async def async_client(db_session: Session, test_engine: SimulationEngine): # Inyectar db_session y test_engine
    """
    Fixture que proporciona un cliente HTTP asíncrono para las pruebas de la API.
    Sobrescribe las dependencias de la base de datos y del motor de simulación.
    """
    # Sobrescribir la dependencia get_db para usar la sesión de prueba
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Sobrescribir la instancia global de simulation_engine en main.py
    # Esto es un hack, pero necesario para que los endpoints usen la instancia de prueba del motor.
    original_simulation_engine = app.extra.get("simulation_engine_instance") # Guardar la original si existe
    app.extra["simulation_engine_instance"] = test_engine # Usar un atributo extra para almacenar la instancia

    # Ejecutar el evento de inicio de la aplicación, pasando is_testing=True
    # Esto inicializará el motor global, pero no iniciará su bucle continuo.
    # Luego, lo sobrescribiremos con nuestra instancia de test_engine.
    await startup_event(is_testing=True) 
    
    # Asegurarse de que la instancia global de simulation_engine en main.py sea la de test_engine
    # Esto es crucial porque los endpoints de main.py acceden a `simulation_engine` globalmente.
    import src.api.main
    src.api.main.simulation_engine = test_engine

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Limpiar la sobrescritura de la dependencia
    app.dependency_overrides.clear()
    
    # Restaurar la instancia original del motor si existía
    if original_simulation_engine:
        src.api.main.simulation_engine = original_simulation_engine
    else:
        src.api.main.simulation_engine = None # O el valor por defecto

    # Ejecutar el evento de apagado de la aplicación
    await shutdown_event()

# --- Fixtures para la creación de entidades de prueba ---

@pytest.fixture(scope="function")
async def created_building(async_client: AsyncClient):
    """Crea un edificio de prueba a través de la API y lo devuelve."""
    payload = {
        "name": "Test Building",
        "address": "123 Test St",
        "geolocation": {"latitude": 40.0, "longitude": -75.0}
    }
    response = await async_client.post(f"{API_PREFIX}/buildings", json=payload)
    assert response.status_code == 201
    return response.json()

@pytest.fixture(scope="function")
async def created_floor(async_client: AsyncClient, created_building: dict):
    """Crea un piso de prueba a través de la API y lo devuelve."""
    building_id = created_building["id"]
    payload = {
        "floor_number": 1,
        "plan_url": "http://example.com/plan.png"
    }
    response = await async_client.post(f"{API_PREFIX}/buildings/{building_id}/floors", json=payload)
    assert response.status_code == 201
    return response.json()
    
@pytest.fixture(scope="function")
async def created_room(async_client: AsyncClient, created_floor: dict):
    """Crea una habitación de prueba a través de la API y la devuelve."""
    floor_id = created_floor["id"]
    payload = {
        "name": "Test Room"
    }
    response = await async_client.post(f"{API_PREFIX}/floors/{floor_id}/rooms", json=payload)
    assert response.status_code == 201
    return response.json()

@pytest.fixture(scope="function")
async def created_device_type(async_client: AsyncClient):
    """Crea un tipo de dispositivo de prueba a través de la API y lo devuelve."""
    payload = {
        "id": str(uuid.uuid4()), # Proporcionar ID para predictibilidad
        "type_name": "Test Device Type",
        "properties": {"unit": "test", "actions": ["test_action"]}
    }
    response = await async_client.post(f"{API_PREFIX}/device-types", json=payload)
    assert response.status_code == 201
    return response.json()

@pytest.fixture(scope="function")
async def created_device(async_client: AsyncClient, created_room: dict, created_device_type: dict):
    """Crea un dispositivo de prueba a través de la API y lo devuelve."""
    room_id = created_room["id"]
    payload = {
        "name": "Test Device",
        "device_type_id": created_device_type["id"],
        "state": {"power": "OFF"},
        "is_active": True
    }
    response = await async_client.post(f"{API_PREFIX}/rooms/{room_id}/devices", json=payload)
    assert response.status_code == 201
    return response.json()

@pytest.fixture(scope="function")
async def created_alarm_direct(async_client: AsyncClient, created_device: dict):
    """Crea una alarma directamente en la base de datos a través del motor de simulación
    para pruebas de reconocimiento. (Asume que el motor tiene un método para esto o se mockea)
    Para este fixture, crearemos la alarma a través de la API si hay un endpoint,
    o simularemos su existencia para el test de ACK.
    Dado que no hay un endpoint POST /alarms, simularemos la creación directa en el motor.
    """
    if not simulation_engine:
        pytest.skip("Simulation engine not available for direct alarm creation")

    alarm_id = str(uuid.uuid4())
    alarm_data = {
        "id": alarm_id,
        "device_id": created_device["id"],
        "severity": "HIGH",
        "status": "NEW",
        "description": "Test Alarm",
        "triggered_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }
    
    # Simular la creación de la alarma en el motor para que get_alarms la encuentre
    # Esto es un hack, idealmente el motor tendría un método create_alarm_for_test
    # o el test de alarms usaría el endpoint de creación de alarmas si existiera.
    # Para que el test de ACK funcione, la alarma debe existir en la DB.
    # Usaremos la sesión de DB del motor para insertarla directamente.
    db = simulation_engine._get_db()
    try:
        db_alarm_instance = Alarm(
            id=alarm_id,
            device_id=created_device["id"],
            severity="HIGH",
            status="NEW",
            description="Test Alarm",
            triggered_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(db_alarm_instance)
        db.commit()
        db.refresh(db_alarm_instance)
        yield db_alarm_instance.to_dict()
    except Exception as e:
        db.rollback()
        pytest.fail(f"Failed to create alarm directly in DB for fixture: {e}")
    finally:
        db.close()
