from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import json
import uuid
from pathlib import Path
import asyncio
import random
from sqlalchemy.exc import IntegrityError

from ..core.building import Building
from .scheduler import Scheduler
from .traffic import BuildingTrafficSimulator
from ..database.connection import get_db
from ..database.models import Building, Floor, Room, Device, DeviceType, SensorReading

class SimulationError(Exception):
    """Error base para excepciones de simulación"""
    pass

class DeviceError(SimulationError):
    """Error relacionado con dispositivos"""
    pass

class SimulationNotFoundError(SimulationError):
    """Error cuando no se encuentra una simulación"""
    pass

class SimulationEngine:
    def __init__(
        self,
        config_path: Optional[str] = None,
        time_scale: float = 1.0,
        data_dir: str = "./data",
        db=None
    ):
        self.simulation_id = str(uuid.uuid4())
        self.buildings: Dict[str, Building] = {}
        self.scheduler = Scheduler(time_scale)
        self.traffic_simulators: Dict[str, BuildingTrafficSimulator] = {}
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Estado de la simulación
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.status = "initialized"
        
        self.running_simulations = {}
        
        self.db = db
        
        if config_path:
            self.load_config(config_path)
            
    def load_config(self, config_path: str) -> None:
        """Carga la configuración de la simulación"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            self.config = config
            self.logger.info(f"Configuración cargada desde {config_path}")
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {str(e)}")
            raise
            
    def get_building(self, building_id: str):
        """Obtiene un edificio por su ID"""
        return self.buildings.get(building_id)

    async def add_building(self, config: Dict[str, Any]) -> str:
        building_id = str(uuid.uuid4())
        self.buildings[building_id] = {
            "id": building_id,
            "config": config,
            "created_at": datetime.now()
        }
        return building_id

    def setup_simulation_events(self) -> None:
        """Configura los eventos recurrentes de la simulación"""
        # Evento para actualización de dispositivos (cada 5 minutos)
        self.scheduler.add_recurring_event(
            "device_update",
            self.update_devices,
            timedelta(minutes=5)
        )
        
        # Evento para generación de tráfico (cada 15 minutos)
        self.scheduler.add_recurring_event(
            "traffic_generation",
            self.generate_traffic,
            timedelta(minutes=15)
        )
        
        # Evento para guardado de datos (cada hora)
        self.scheduler.add_recurring_event(
            "data_save",
            self.save_simulation_data,
            timedelta(hours=1)
        )
        
    def update_devices(self, data: Dict[str, Any]) -> None:
        """Actualiza el estado de todos los dispositivos"""
        current_time = self.scheduler.current_time
        
        for building in self.buildings.values():
            traffic_sim = self.traffic_simulators[building.building_id]
            traffic_data = traffic_sim.generate_traffic_data(current_time)
            
            for device in building.get_all_devices():
                if traffic_sim.should_generate_event(device["device_type"], current_time):
                    try:
                        device_data = device.generate_data()
                        self.store_device_data(building.building_id, device["device_id"], device_data)
                    except Exception as e:
                        self.logger.error(f"Error actualizando dispositivo {device['device_id']}: {str(e)}")
                        
    def generate_traffic(self, data: Dict[str, Any]) -> None:
        """Genera datos de tráfico para todos los edificios"""
        current_time = self.scheduler.current_time
        
        for building_id, simulator in self.traffic_simulators.items():
            traffic_data = simulator.generate_traffic_data(current_time)
            self.store_traffic_data(building_id, traffic_data)
            
    def store_device_data(self, building_id: str, device_id: str, data: Dict[str, Any]) -> None:
        """Almacena los datos generados por un dispositivo"""
        # Guardar lectura en la base de datos
        reading = SensorReading(
            device_id=device_id,
            data=data
        )
        self.db.add(reading)
        self.db.commit()
            
    def store_traffic_data(self, building_id: str, data: Dict[str, Any]) -> None:
        """Almacena los datos de tráfico"""
        timestamp = datetime.now().strftime("%Y%m%d_%H")
        data_file = self.data_dir / f"traffic_data_{building_id}_{timestamp}.jsonl"
        
        try:
            with open(data_file, 'a') as f:
                json.dump({
                    "building_id": building_id,
                    "timestamp": self.scheduler.current_time.isoformat(),
                    "data": data
                }, f)
                f.write('\n')
        except Exception as e:
            self.logger.error(f"Error almacenando datos de tráfico: {str(e)}")
            
    def save_simulation_data(self, data: Dict[str, Any]) -> None:
        """Guarda el estado actual de la simulación"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        state_file = self.data_dir / f"simulation_state_{self.simulation_id}_{timestamp}.json"
        
        state = {
            "simulation_id": self.simulation_id,
            "current_time": self.scheduler.current_time.isoformat(),
            "status": self.status,
            "buildings": {bid: building.to_dict() for bid, building in self.buildings.items()},
            "events_count": self.scheduler.get_event_count()
        }
        
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error guardando estado de simulación: {str(e)}")
            
    def get_all_devices(self) -> List[Dict[str, Any]]:
        """Obtiene todos los dispositivos de todos los edificios"""
        devices = []
        for building in self.buildings.values():
            for floor in building['floors']:
                for room in floor['rooms']:
                    for device in room['devices']:
                        devices.append({
                            'id': device['id'],
                            'type': device['type'],
                            'room_id': room['id'],
                            'floor_id': floor['id'],
                            'building_id': building['id'],
                            'status': device.get('status', 'active')
                        })
        return devices

    async def start(self, duration: timedelta) -> str:
        simulation_id = str(uuid.uuid4())
        self.running_simulations[simulation_id] = {
            "id": simulation_id,
            "start_time": datetime.now(),
            "duration": duration,
            "status": "running"
        }
        # Iniciar simulación en background
        asyncio.create_task(self._run_simulation(simulation_id))
        return simulation_id

    async def get_status(self, simulation_id: str) -> str:
        if simulation_id not in self.running_simulations:
            raise ValueError("Simulation not found")
        return self.running_simulations[simulation_id]["status"]

    async def _run_simulation(self, simulation_id: str):
        simulation = self.running_simulations[simulation_id]
        try:
            while (
                simulation["status"] == "running" and
                datetime.now() - simulation["start_time"] < simulation["duration"]
            ):
                await asyncio.sleep(1)
            simulation["status"] = "completed"
        except Exception as e:
            simulation["status"] = "error"
            raise e

    async def stop_simulation(self, simulation_id: str):
        """Detiene una simulación en curso"""
        if simulation_id in self.running_simulations:
            self.running_simulations[simulation_id]["status"] = "stopped"
            logger.info(f"Simulación {simulation_id} detenida")
