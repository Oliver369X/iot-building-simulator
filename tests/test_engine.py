import pytest
from datetime import datetime, timedelta
from src.simulator.engine import SimulationEngine
from src.core.building import Building
import tempfile
import json
import os
import asyncio

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

class TestSimulationEngine:
    @pytest.fixture
    def engine(self, temp_data_dir):
        return SimulationEngine(data_dir=temp_data_dir)

    def test_add_building(self, engine):
        building_config = {
            "name": "Test Building",
            "type": "office",
            "floors": 3,
            "rooms_per_floor": 4,
            "devices_per_room": {
                "temperature_sensor": 1,
                "hvac_controller": 1
            }
        }
        building_id = engine.add_building(building_config)
        assert building_id in engine.buildings

    @pytest.mark.asyncio
    async def test_simulation_run(self, engine):
        # Primero añadimos un edificio
        building_config = {
            "name": "Test Building",
            "type": "office",
            "floors": 3,
            "rooms_per_floor": 4,
            "devices_per_room": {
                "temperature_sensor": 1
            }
        }
        engine.add_building(building_config)
        
        # Iniciamos la simulación
        simulation_id = await engine.start(timedelta(minutes=5))
        assert simulation_id in engine.running_simulations

    @pytest.mark.asyncio
    async def test_status_reporting(self, engine):
        # Primero iniciamos una simulación
        simulation_id = await engine.start(timedelta(minutes=5))
        
        # Verificamos el estado
        status = await engine.get_simulation_status(simulation_id)
        assert status["status"] in ["running", "completed"]
        assert "buildings" in status 