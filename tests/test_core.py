import pytest
from datetime import datetime
from src.core.building import Building
from src.core.floor import Floor
from src.core.room import Room
from src.core.device import Device

class TestBuilding:
    def test_building_creation(self):
        building = Building(
            "test_building",
            "Test Building",
            {"city": "Test City"}
        )
        assert building.building_id == "test_building"
        assert len(building.floors) == 0
        
    def test_floor_management(self):
        building = Building("test_building", "Test Building", {})
        floor = Floor("floor_1", building.building_id, 1)
        
        building.add_floor(floor)
        assert "floor_1" in building.floors
        
        building.remove_floor("floor_1")
        assert "floor_1" not in building.floors
        
    def test_device_aggregation(self):
        building = Building("test_building", "Test Building", {})
        floor = Floor("floor_1", building.building_id, 1)
        room = Room("room_1", floor.floor_id, "office", 25)
        
        # Añade dispositivos a la habitación
        room.add_device("temperature_sensor", {"update_interval": 300})
        room.add_device("motion_sensor", {"sensitivity": 0.8})
        
        floor.add_room(room)
        building.add_floor(floor)
        
        # Verifica que podemos obtener todos los dispositivos
        all_devices = building.get_all_devices()
        assert len(all_devices) == 2
        assert all(isinstance(d, dict) for d in all_devices)  # Verifica que son diccionarios
        
        # Verifica que podemos filtrar por tipo
        temp_sensors = building.get_devices_by_type("temperature_sensor")
        assert len(temp_sensors) == 1

class TestRoom:
    def test_room_creation(self):
        room = Room("room_1", "floor_1", "office", 25)
        assert room.room_id == "room_1"
        assert room.area == 25
        assert len(room.devices) == 0
        
    def test_device_management(self):
        room = Room("room_1", "floor_1", "office", 25)
        
        # Añade dispositivos
        room.add_device("temperature_sensor", {"range_min": 18, "range_max": 25})
        assert len(room.devices) == 1
        
        # Verifica filtrado de dispositivos
        temp_sensors = room.get_devices("temperature_sensor")
        assert len(temp_sensors) == 1
        
        # Elimina dispositivo
        device_id = temp_sensors[0].device_id
        room.remove_device(device_id)
        assert len(room.devices) == 0 