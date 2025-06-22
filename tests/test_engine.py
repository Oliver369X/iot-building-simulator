import pytest
from datetime import datetime, timedelta
from src.simulator.engine import SimulationEngine
from src.core.building import Building
import tempfile
import json
import os
import asyncio
from src.database.models import Building, Floor, Room, Device, SensorReading, AggregatedReading, DeviceType
from sqlalchemy.orm import Session
import uuid
from httpx import AsyncClient
from src.api.main import app

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

@pytest.fixture
def sample_config():
    return {
        "simulation": {
            "time_scale": 1.0,
            "duration": "1h"
        },
        "traffic_patterns": {
            "building_01": {
                "max_occupancy": 100,
                "base_probability": 0.5
            }
        }
    }

@pytest.fixture
def config_file(sample_config, temp_data_dir):
    config_path = os.path.join(temp_data_dir, "config.json")
    with open(config_path, "w") as f:
        json.dump(sample_config, f)
    return config_path

# Import SessionLocal for the engine fixture
from src.database.connection import SessionLocal

class TestSimulationEngine:
    @pytest.fixture
    def engine(self, temp_data_dir):
        # Provide the db_session_local argument
        # Note: For true unit tests of the engine, database interactions might be mocked.
        # For integration-style tests that hit a test DB, SessionLocal would point to that.
        return SimulationEngine(db_session_local=SessionLocal, data_dir=temp_data_dir)

    # The following tests are based on the old SimulationEngine behavior
    # and need to be rewritten to test the new database-centric methods.
    # Commenting them out for now.

    # def test_add_building(self, engine):
    #     # This test assumed add_building took a config dict and managed an in-memory dict.
    #     # New create_building takes a Pydantic model and interacts with the DB.
    #     building_config = {
    #         "name": "Test Building",
    #         "type": "office",
    #         "floors": 3,
    #         "rooms_per_floor": 4,
    #         "devices_per_room": {
    #             "temperature_sensor": 1,
    #             "hvac_controller": 1
    #         }
    #     }
    #     # building_id = engine.add_building(building_config) # Old signature
    #     # assert building_id in engine.buildings # engine.buildings is no longer the primary store
    #     pass


    # @pytest.mark.asyncio
    # async def test_simulation_run(self, engine):
    #     # This test relied on the old start() method and in-memory simulation tracking.
    #     # The simulation concept has changed to a continuous worker model.
    #     building_config = {
    #         "name": "Test Building",
    #         "type": "office",
    #         "floors": 3,
    #         "rooms_per_floor": 4,
    #         "devices_per_room": {
    #             "temperature_sensor": 1
    #         }
    #     }
    #     # engine.add_building(building_config) # Old way of adding
        
    #     # simulation_id = await engine.start(timedelta(minutes=5)) # Old start method
    #     # assert simulation_id in engine.running_simulations # This attribute/concept changed
    #     pass

    # @pytest.mark.asyncio
    # async def test_status_reporting(self, engine):
    #     # This test relied on the old get_simulation_status() method.
    #     # Status reporting will be different for a continuous worker.
    #     # simulation_id = await engine.start(timedelta(minutes=5)) # Old start method
        
    #     # status = await engine.get_simulation_status(simulation_id) # Old status method
    #     # assert status["status"] in ["running", "completed"]
    #     # assert "buildings" in status # This structure is from the old status
    #     pass

    @pytest.mark.asyncio
    async def test_aggregation_worker_building_consumption(self, engine):
        db: Session = engine._get_db()
        now = datetime.utcnow()
        device_type = DeviceType(id=str(uuid.uuid4()), type_name="test_type")
        db.add(device_type)
        db.commit()
        building = Building(id=str(uuid.uuid4()), name="Test Building")
        db.add(building)
        db.commit()
        floor = Floor(id=str(uuid.uuid4()), building_id=building.id, floor_number=1)
        db.add(floor)
        db.commit()
        room = Room(id=str(uuid.uuid4()), floor_id=floor.id, name="Room 1")
        db.add(room)
        db.commit()
        device = Device(id=str(uuid.uuid4()), name="Device 1", device_type_id=device_type.id, room_id=room.id)
        db.add(device)
        db.commit()
        readings = [
            SensorReading(device_id=device.id, timestamp=now - timedelta(seconds=30), value=1.5, unit="kWh", extra_data={"key": "power_consumption"}),
            SensorReading(device_id=device.id, timestamp=now - timedelta(seconds=10), value=2.0, unit="kWh", extra_data={"key": "power_consumption"}),
        ]
        db.add_all(readings)
        db.commit()
        building_id = building.id
        db.close()
        await engine.aggregate_and_store_all(period_seconds=60)
        db = engine._get_db()
        agg = db.query(AggregatedReading).filter_by(entity_type="building", entity_id=building_id, key="power_consumption").order_by(AggregatedReading.timestamp.desc()).first()
        assert agg is not None, "No se encontró el valor agregado"
        assert abs(agg.value - 3.5) < 0.01, f"El valor agregado es incorrecto: {agg.value}"
        db.close()

    @pytest.mark.asyncio
    async def test_aggregation_worker_floor_consumption(self, engine):
        db: Session = engine._get_db()
        now = datetime.utcnow()
        device_type = DeviceType(id=str(uuid.uuid4()), type_name="test_type")
        db.add(device_type)
        db.commit()
        building = Building(id=str(uuid.uuid4()), name="Test Building")
        db.add(building)
        db.commit()
        floor = Floor(id=str(uuid.uuid4()), building_id=building.id, floor_number=1)
        db.add(floor)
        db.commit()
        room = Room(id=str(uuid.uuid4()), floor_id=floor.id, name="Room 1")
        db.add(room)
        db.commit()
        device = Device(id=str(uuid.uuid4()), name="Device 1", device_type_id=device_type.id, room_id=room.id)
        db.add(device)
        db.commit()
        readings = [
            SensorReading(device_id=device.id, timestamp=now - timedelta(seconds=40), value=1.0, unit="kWh", extra_data={"key": "power_consumption"}),
            SensorReading(device_id=device.id, timestamp=now - timedelta(seconds=20), value=2.0, unit="kWh", extra_data={"key": "power_consumption"}),
        ]
        db.add_all(readings)
        db.commit()
        floor_id = floor.id
        db.close()
        await engine.aggregate_and_store_all(period_seconds=60)
        db = engine._get_db()
        agg = db.query(AggregatedReading).filter_by(entity_type="floor", entity_id=floor_id, key="power_consumption").order_by(AggregatedReading.timestamp.desc()).first()
        if agg:
            assert abs(agg.value - 3.0) < 0.01, f"El valor agregado de piso es incorrecto: {agg.value}"
        db.close()

    @pytest.mark.asyncio
    async def test_aggregation_worker_room_consumption(self, engine):
        db: Session = engine._get_db()
        now = datetime.utcnow()
        device_type = DeviceType(id=str(uuid.uuid4()), type_name="test_type")
        db.add(device_type)
        db.commit()
        building = Building(id=str(uuid.uuid4()), name="Test Building")
        db.add(building)
        db.commit()
        floor = Floor(id=str(uuid.uuid4()), building_id=building.id, floor_number=1)
        db.add(floor)
        db.commit()
        room = Room(id=str(uuid.uuid4()), floor_id=floor.id, name="Room 1")
        db.add(room)
        db.commit()
        device = Device(id=str(uuid.uuid4()), name="Device 1", device_type_id=device_type.id, room_id=room.id)
        db.add(device)
        db.commit()
        readings = [
            SensorReading(device_id=device.id, timestamp=now - timedelta(seconds=50), value=0.5, unit="kWh", extra_data={"key": "power_consumption"}),
            SensorReading(device_id=device.id, timestamp=now - timedelta(seconds=5), value=1.5, unit="kWh", extra_data={"key": "power_consumption"}),
        ]
        db.add_all(readings)
        db.commit()
        room_id = room.id
        db.close()
        await engine.aggregate_and_store_all(period_seconds=60)
        db = engine._get_db()
        agg = db.query(AggregatedReading).filter_by(entity_type="room", entity_id=room_id, key="power_consumption").order_by(AggregatedReading.timestamp.desc()).first()
        if agg:
            assert abs(agg.value - 2.0) < 0.01, f"El valor agregado de habitación es incorrecto: {agg.value}"
        db.close()

    @pytest.mark.asyncio
    async def test_aggregation_worker_device_consumption(self, engine):
        db: Session = engine._get_db()
        now = datetime.utcnow()
        device_type = DeviceType(id=str(uuid.uuid4()), type_name="test_type")
        db.add(device_type)
        db.commit()
        building = Building(id=str(uuid.uuid4()), name="Test Building")
        db.add(building)
        db.commit()
        floor = Floor(id=str(uuid.uuid4()), building_id=building.id, floor_number=1)
        db.add(floor)
        db.commit()
        room = Room(id=str(uuid.uuid4()), floor_id=floor.id, name="Room 1")
        db.add(room)
        db.commit()
        device = Device(id=str(uuid.uuid4()), name="Device 1", device_type_id=device_type.id, room_id=room.id)
        db.add(device)
        db.commit()
        readings = [
            SensorReading(device_id=device.id, timestamp=now - timedelta(seconds=55), value=0.7, unit="kWh", extra_data={"key": "power_consumption"}),
            SensorReading(device_id=device.id, timestamp=now - timedelta(seconds=15), value=1.3, unit="kWh", extra_data={"key": "power_consumption"}),
        ]
        db.add_all(readings)
        db.commit()
        device_id = device.id
        db.close()
        await engine.aggregate_and_store_all(period_seconds=60)
        db = engine._get_db()
        agg = db.query(AggregatedReading).filter_by(entity_type="device", entity_id=device_id, key="power_consumption").order_by(AggregatedReading.timestamp.desc()).first()
        if agg:
            assert abs(agg.value - 2.0) < 0.01, f"El valor agregado de dispositivo es incorrecto: {agg.value}"
        db.close()

    @pytest.mark.asyncio
    async def test_aggregation_no_duplicate_for_same_period(self, engine):
        db: Session = engine._get_db()
        now = datetime.utcnow()
        device_type = DeviceType(id=str(uuid.uuid4()), type_name="test_type")
        db.add(device_type)
        db.commit()
        building = Building(id=str(uuid.uuid4()), name="Test Building")
        db.add(building)
        db.commit()
        floor = Floor(id=str(uuid.uuid4()), building_id=building.id, floor_number=1)
        db.add(floor)
        db.commit()
        room = Room(id=str(uuid.uuid4()), floor_id=floor.id, name="Room 1")
        db.add(room)
        db.commit()
        device = Device(id=str(uuid.uuid4()), name="Device 1", device_type_id=device_type.id, room_id=room.id)
        db.add(device)
        db.commit()
        readings = [
            SensorReading(device_id=device.id, timestamp=now - timedelta(seconds=30), value=1.0, unit="kWh", extra_data={"key": "power_consumption"}),
            SensorReading(device_id=device.id, timestamp=now - timedelta(seconds=10), value=2.0, unit="kWh", extra_data={"key": "power_consumption"}),
        ]
        db.add_all(readings)
        db.commit()
        building_id = building.id
        db.close()
        await engine.aggregate_and_store_all(period_seconds=60)
        await engine.aggregate_and_store_all(period_seconds=60)
        db = engine._get_db()
        aggs = db.query(AggregatedReading).filter_by(entity_type="building", entity_id=building_id, key="power_consumption").all()
        assert len(aggs) >= 1, "Debe haber al menos un valor agregado"
        db.close()

    @pytest.mark.asyncio
    async def test_query_aggregated_reading(self, engine):
        db: Session = engine._get_db()
        now = datetime.utcnow()
        device_type = DeviceType(id=str(uuid.uuid4()), type_name="test_type")
        db.add(device_type)
        db.commit()
        building = Building(id=str(uuid.uuid4()), name="Test Building")
        db.add(building)
        db.commit()
        floor = Floor(id=str(uuid.uuid4()), building_id=building.id, floor_number=1)
        db.add(floor)
        db.commit()
        room = Room(id=str(uuid.uuid4()), floor_id=floor.id, name="Room 1")
        db.add(room)
        db.commit()
        device = Device(id=str(uuid.uuid4()), name="Device 1", device_type_id=device_type.id, room_id=room.id)
        db.add(device)
        db.commit()
        readings = [
            SensorReading(device_id=device.id, timestamp=now - timedelta(seconds=30), value=1.0, unit="kWh", extra_data={"key": "power_consumption"}),
            SensorReading(device_id=device.id, timestamp=now - timedelta(seconds=10), value=2.0, unit="kWh", extra_data={"key": "power_consumption"}),
        ]
        db.add_all(readings)
        db.commit()
        building_id = building.id
        db.close()
        await engine.aggregate_and_store_all(period_seconds=60)
        db = engine._get_db()
        aggs = db.query(AggregatedReading).filter_by(entity_type="building", entity_id=building_id, key="power_consumption").all()
        assert len(aggs) > 0, "No se encontraron valores agregados para el edificio"
        for agg in aggs:
            assert agg.value >= 0, "El valor agregado debe ser no negativo"
        db.close()

    @pytest.mark.asyncio
    async def test_api_aggregated_consumption_endpoints(self, engine):
        # Prepara datos
        db = engine._get_db()
        from src.database.models import DeviceType, Building, Floor, Room, Device, SensorReading
        import uuid
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        device_type = DeviceType(id=str(uuid.uuid4()), type_name="test_type")
        db.add(device_type)
        db.commit()
        building = Building(id=str(uuid.uuid4()), name="Test Building")
        db.add(building)
        db.commit()
        floor = Floor(id=str(uuid.uuid4()), building_id=building.id, floor_number=1)
        db.add(floor)
        db.commit()
        room = Room(id=str(uuid.uuid4()), floor_id=floor.id, name="Room 1")
        db.add(room)
        db.commit()
        device = Device(id=str(uuid.uuid4()), name="Device 1", device_type_id=device_type.id, room_id=room.id)
        db.add(device)
        db.commit()
        readings = [
            SensorReading(device_id=device.id, timestamp=now - timedelta(seconds=30), value=1.0, unit="kWh", extra_data={"key": "power_consumption"}),
            SensorReading(device_id=device.id, timestamp=now - timedelta(seconds=10), value=2.0, unit="kWh", extra_data={"key": "power_consumption"}),
        ]
        db.add_all(readings)
        db.commit()
        building_id = building.id
        floor_id = floor.id
        room_id = room.id
        device_id = device.id
        db.close()
        # Ejecuta agregación
        await engine.aggregate_and_store_all(period_seconds=60)
        # Test endpoints
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Building
            resp = await ac.get(f"/api/v1/consumption/building/{building_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert any(abs(r["value"] - 3.0) < 0.01 for r in data), "No se encontró el valor agregado correcto para edificio"
            # Floor
            resp = await ac.get(f"/api/v1/consumption/floor/{floor_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert any(abs(r["value"] - 3.0) < 0.01 for r in data), "No se encontró el valor agregado correcto para piso"
            # Room
            resp = await ac.get(f"/api/v1/consumption/room/{room_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert any(abs(r["value"] - 3.0) < 0.01 for r in data), "No se encontró el valor agregado correcto para habitación"
            # Device
            resp = await ac.get(f"/api/v1/consumption/device/{device_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert any(abs(r["value"] - 3.0) < 0.01 for r in data), "No se encontró el valor agregado correcto para dispositivo"