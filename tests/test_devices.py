import pytest
from datetime import datetime
from src.devices.climate import TemperatureSensor, HVACController
from src.devices.security import MotionSensor, SecurityCamera
from src.devices.energy import PowerMeter, SmartPlug

@pytest.fixture
def sample_location():
    return {
        "building_id": "test_building",
        "floor_id": "floor_1",
        "room_id": "room_101"
    }

@pytest.fixture
def sample_device_config():
    return {
        "update_interval": 300,
        "sensitivity": 0.8
    }

class TestTemperatureSensor:
    def test_initialization(self, sample_device_config):
        sensor = TemperatureSensor(
            device_id="test_sensor",
            room_id="room_101",
            config=sample_device_config
        )
        assert sensor.device_type == "temperature_sensor"
        assert sensor.config == sample_device_config

    def test_generate_data(self, sample_device_config):
        sensor = TemperatureSensor(
            device_id="test_sensor",
            room_id="room_101",
            config=sample_device_config
        )
        data = sensor.generate_data()
        assert "temperature" in data
        assert "unit" in data
        assert data["unit"] == "celsius"

class TestHVACController:
    def test_initialization(self, sample_device_config):
        hvac = HVACController(
            device_id="test_hvac",
            room_id="room_101",
            config=sample_device_config
        )
        assert hvac.device_type == "hvac_controller"
        assert hvac.mode == "auto"
        
    def test_generate_data_when_off(self, sample_device_config):
        hvac = HVACController(
            device_id="test_hvac",
            room_id="room_101",
            config={"status": "off", **sample_device_config}
        )
        data = hvac.generate_data()
        assert "status" in data
        assert "power_consumption" in data
        
    def test_generate_data_when_on(self, sample_device_config):
        hvac = HVACController(
            device_id="test_hvac",
            room_id="room_101",
            config={"status": "on", **sample_device_config}
        )
        data = hvac.generate_data()
        assert "status" in data
        assert "power_consumption" in data
        assert data["power_consumption"] > 0

class TestMotionSensor:
    def test_initialization(self, sample_device_config):
        sensor = MotionSensor(
            device_id="test_motion",
            room_id="room_101",
            config={"sensitivity": 0.5}
        )
        assert sensor.sensitivity == 0.5
        assert not sensor.motion_detected

    def test_generate_data(self, sample_device_config):
        sensor = MotionSensor(
            device_id="test_motion",
            room_id="room_101",
            config={"sensitivity": 1.0}
        )
        data = sensor.generate_data()
        assert "motion_detected" in data
        assert isinstance(data["motion_detected"], bool)

class TestSmartPlug:
    def test_initialization(self, sample_device_config):
        config = {"device_connected": "computer"}
        plug = SmartPlug(
            device_id="test_plug",
            room_id="room_101",
            config=config
        )
        assert plug.status == "active"
        assert plug.device_connected == "computer"
        
    def test_power_consumption(self, sample_device_config):
        config = {"device_connected": "computer"}
        plug = SmartPlug(
            device_id="test_plug",
            room_id="room_101",
            config=config
        )
        data = plug.generate_data()
        assert "current_power" in data
        assert "device_connected" in data
        assert data["device_connected"] == "computer" 