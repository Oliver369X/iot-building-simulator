from typing import List, Dict, Any, Optional
from fastapi import WebSocket
import asyncio
import uuid
import random
from datetime import datetime
import logging
from .validators import BuildingCreate, DeviceStatusUpdate
import json
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimulationManager:
    _buildings: Dict[str, Any] = {}
    _simulations: Dict[str, Any] = {}
    _clients: Dict[str, List[WebSocket]] = {}
    _websocket_connections: Dict[str, WebSocket] = {}
    _last_values: Dict[str, float] = {}

    @classmethod
    def get_buildings(cls) -> List[Dict[str, Any]]:
        logger.info(f"Getting buildings. Current buildings: {len(cls._buildings)}")
        buildings = []
        for building_id, building in cls._buildings.items():
            buildings.append({
                "id": building_id,
                "name": building["name"],
                "type": building["type"],
                "floors": building["floors"],
                "devices_count": sum(
                    len(room["devices"]) 
                    for floor in building["floors"] 
                    for room in floor["rooms"]
                )
            })
        return buildings

    @classmethod
    def create_building(cls, building: BuildingCreate) -> Dict[str, Any]:
        try:
            building_id = str(uuid.uuid4())
            building_data = building.dict()
            
            # Asegurar que cada piso tiene rooms y devices
            for floor in building_data["floors"]:
                if "rooms" not in floor:
                    floor["rooms"] = []
                for room in floor["rooms"]:
                    if "devices" not in room:
                        room["devices"] = []
                    # Asegurar que cada dispositivo tiene un ID y estado
                    for device in room["devices"]:
                        if "id" not in device:
                            device["id"] = str(uuid.uuid4())
                        if "status" not in device:
                            device["status"] = "inactive"
                        device["last_reading"] = {}
                        device["readings"] = []

            building_data["id"] = building_id
            cls._buildings[building_id] = building_data
            logger.info(f"Created building {building_id}: {building.name}")
            return building_data
        except Exception as e:
            logger.error(f"Error creating building: {str(e)}")
            raise Exception(f"Error creating building: {str(e)}")

    @classmethod
    async def start_simulation(cls, building_id: str) -> Dict[str, Any]:
        """Inicia una simulación para un edificio específico"""
        if building_id not in cls._buildings:
            raise ValueError("Building not found")

        try:
            building = cls._buildings[building_id]
            
            # Verificar la estructura del edificio
            if "floors" not in building:
                raise ValueError("Building structure is invalid: missing floors")
            
            for floor in building["floors"]:
                if "rooms" not in floor:
                    raise ValueError("Building structure is invalid: floor missing rooms")
                for room in floor["rooms"]:
                    if "devices" not in room:
                        raise ValueError("Building structure is invalid: room missing devices")

            simulation_id = str(uuid.uuid4())
            cls._simulations[simulation_id] = {
                "building_id": building_id,
                "status": "running",
                "start_time": datetime.now(),
                "active_devices": cls._get_active_devices(building_id),
                "events_per_second": 1.0
            }

            # Iniciar el proceso de simulación en segundo plano
            asyncio.create_task(cls._run_simulation(simulation_id))

            return {
                "simulation_id": simulation_id,
                "status": "running",
                "building_id": building_id
            }
        except Exception as e:
            logger.error(f"Error starting simulation for building {building_id}: {str(e)}")
            raise Exception(f"Error starting simulation: {str(e)}")

    @classmethod
    async def connect_client(cls, simulation_id: str, websocket: WebSocket) -> None:
        try:
            if simulation_id not in cls._simulations:
                raise ValueError(f"Simulation {simulation_id} not found")
            
            simulation = cls._simulations[simulation_id]
            logger.info(f"Client connected to simulation {simulation_id}")
            
            while True:
                # Obtener datos actualizados de la simulación
                devices_status = cls.get_devices_status(simulation_id)
                active_devices = len([d for d in devices_status if d["status"] == "active"])
                
                data = {
                    "simulation_id": simulation_id,
                    "status": simulation["status"],
                    "active_devices": active_devices,
                    "events_per_second": simulation["events_per_second"],
                    "devices": devices_status
                }
                
                # Enviar datos al cliente
                try:
                    await websocket.send_json(data)
                    await asyncio.sleep(1)  # Actualizar cada segundo
                except Exception as e:
                    logger.error(f"Error sending data to client: {e}")
                    break
                
        except ValueError as e:
            logger.error(f"Simulation error: {e}")
            await websocket.send_json({"error": str(e)})
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket connection: {e}")
            await websocket.send_json({"error": "Internal server error"})
        finally:
            # Limpiar la conexión
            if simulation_id in cls._websocket_connections:
                cls._websocket_connections.pop(simulation_id)
            logger.info(f"Client disconnected from simulation {simulation_id}")

    @classmethod
    async def _generate_device_data(cls, device_type: str) -> Dict[str, Any]:
        """Genera datos simulados según el tipo de dispositivo"""
        import random
        from datetime import datetime
        import math

        now = datetime.now()
        hour = now.hour
        base_data = {
            "timestamp": now.isoformat()
        }

        if device_type == "temperature_sensor":
            # Temperatura base según hora del día (más alta durante horas laborales)
            base_temp = 21.0
            if 8 <= hour <= 18:
                base_temp = 22.0
            
            # Añadir variación según hora del día
            time_variation = math.sin(2 * math.pi * (hour - 6) / 24) * 1.5
            
            # Pequeña variación aleatoria
            random_variation = random.uniform(-0.2, 0.2)
            
            temperature = base_temp + time_variation + random_variation
            temperature = round(max(18.0, min(28.0, temperature)), 2)
            
            base_data["temperature"] = temperature
            base_data["unit"] = "celsius"

        elif device_type == "pressure_sensor":
            base_data["pressure"] = round(random.uniform(980.0, 1020.0), 2)
        elif device_type == "valve_controller":
            base_data["position"] = round(random.uniform(0.0, 100.0), 2)
        elif device_type == "damper_controller":
            base_data["position"] = round(random.uniform(0.0, 100.0), 2)
        elif device_type == "frequency_controller":
            base_data["frequency"] = round(random.uniform(0.0, 60.0), 2)
        elif device_type == "power_meter":
            base_data["current_power"] = round(random.uniform(0.0, 5000.0), 2)
        else:
            base_data["value"] = 0
            print(f"Tipo de dispositivo desconocido: {device_type}")

        return base_data

    @classmethod
    async def _run_simulation(cls, simulation_id: str):
        """Ejecuta la simulación generando datos para todos los dispositivos"""
        try:
            simulation = cls._simulations[simulation_id]
            building_id = simulation["building_id"]
            building = cls._buildings[building_id]

            while simulation["status"] == "running":
                # Generar datos para cada dispositivo
                for floor in building["floors"]:
                    for room in floor["rooms"]:
                        for device in room["devices"]:
                            if device["status"] == "active":
                                data = await cls._generate_device_data(device["type"])
                                device["last_reading"] = data
                                await cls._notify_clients(simulation_id, {
                                    "device_id": device["id"],
                                    "type": device["type"],
                                    "data": data,
                                    "timestamp": datetime.now().isoformat()
                                })

                await asyncio.sleep(1)  # Esperar 1 segundo entre actualizaciones

        except Exception as e:
            logger.error(f"Error en simulación {simulation_id}: {str(e)}")
            simulation["status"] = "error"
            simulation["error"] = str(e)

    @classmethod
    def _get_active_devices(cls, building_id: str) -> List[Dict[str, Any]]:
        """Obtiene los dispositivos activos de un edificio"""
        if building_id not in cls._buildings:
            raise ValueError("Building not found")
            
        building = cls._buildings[building_id]
        active_devices = []
        
        for floor in building["floors"]:
            for room in floor["rooms"]:
                for device in room["devices"]:
                    if device.get("status") == "active":
                        active_devices.append(device)
        
        return active_devices

    @classmethod
    def get_simulation_status(cls, simulation_id: str) -> str:
        if simulation_id not in cls._simulations:
            raise ValueError("Simulation not found")
        return cls._simulations[simulation_id]["status"]

    @classmethod
    def update_device_status(cls, device_id: str, status_update: DeviceStatusUpdate) -> None:
        # Buscar el dispositivo en todos los edificios
        for building in cls._buildings.values():
            for floor in building["floors"]:
                for room in floor["rooms"]:
                    for device in room["devices"]:
                        if device.get("id") == device_id:
                            device["status"] = status_update.status
                            return
        raise ValueError("Device not found")

    @classmethod
    def get_device_readings(cls, device_id: str) -> Dict[str, Any]:
        # Buscar el dispositivo en todos los edificios
        for building in cls._buildings.values():
            for floor in building["floors"]:
                for room in floor["rooms"]:
                    for device in room["devices"]:
                        if device.get("id") == device_id:
                            return device.get("last_reading", {})
        raise ValueError("Device not found")

    @classmethod
    def get_devices_status(cls, simulation_id: str) -> List[Dict[str, Any]]:
        simulation = cls._simulations[simulation_id]
        building = cls._buildings[simulation["building_id"]]
        
        devices_status = []
        for floor in building["floors"]:
            for room in floor["rooms"]:
                for device in room["devices"]:
                    devices_status.append({
                        "device_id": device["id"],
                        "type": device["type"],
                        "status": device.get("status", "inactive"),
                        "last_reading": device.get("last_reading", {})
                    })
        
        return devices_status 

    @classmethod
    def stop_simulation(cls, simulation_id: str) -> None:
        if simulation_id not in cls._simulations:
            raise ValueError("Simulation not found")
        
        simulation = cls._simulations[simulation_id]
        simulation["status"] = "stopped"
        
        # Limpiar conexiones WebSocket
        if simulation_id in cls._websocket_connections:
            cls._websocket_connections.pop(simulation_id)
        
        logger.info(f"Simulation {simulation_id} stopped") 

    @classmethod
    def get_building(cls, building_id: str) -> Dict[str, Any]:
        """
        Obtiene un edificio específico por su ID.
        
        Args:
            building_id: ID del edificio a obtener
            
        Returns:
            Dict con la información del edificio
            
        Raises:
            ValueError: Si el edificio no existe
        """
        logger.info(f"Getting building {building_id}")
        
        if building_id not in cls._buildings:
            logger.error(f"Building {building_id} not found")
            raise ValueError("Building not found")
        
        building = cls._buildings[building_id]
        return {
            "id": building_id,
            "name": building["name"],
            "type": building["type"],
            "floors": building["floors"],
            "devices_count": sum(
                len(room["devices"]) 
                for floor in building["floors"] 
                for room in floor["rooms"]
            )
        }

    @classmethod
    def delete_building(cls, building_id: str) -> None:
        """
        Elimina un edificio y detiene sus simulaciones asociadas.
        """
        logger.info(f"Attempting to delete building {building_id}")
        
        # Primero verificar que el edificio existe
        if building_id not in cls._buildings:
            logger.error(f"Building {building_id} not found")
            raise ValueError("Building not found")
        
        try:
            # Obtener todas las simulaciones activas para este edificio
            active_simulations = [
                (sim_id, sim) for sim_id, sim in cls._simulations.items()
                if sim["building_id"] == building_id and sim["status"] == "running"
            ]
            
            # Detener simulaciones activas
            for sim_id, _ in active_simulations:
                try:
                    logger.info(f"Stopping simulation {sim_id} for building {building_id}")
                    cls.stop_simulation(sim_id)
                except Exception as e:
                    logger.error(f"Error stopping simulation {sim_id}: {e}")
                    # Continuar con otras simulaciones incluso si una falla
            
            # Eliminar el edificio
            building = cls._buildings.pop(building_id)
            logger.info(f"Building {building_id} ({building['name']}) deleted successfully")
            
            # Limpiar todas las simulaciones asociadas (no solo las activas)
            cls._simulations = {
                sim_id: sim for sim_id, sim in cls._simulations.items()
                if sim["building_id"] != building_id
            }
            
            # Limpiar conexiones WebSocket asociadas
            for sim_id, _ in active_simulations:
                if sim_id in cls._websocket_connections:
                    cls._websocket_connections.pop(sim_id)
                if sim_id in cls._clients:
                    cls._clients.pop(sim_id)
            
            return
            
        except Exception as e:
            logger.error(f"Error while deleting building {building_id}: {e}")
            # Intentar restaurar el edificio si algo falla
            if building_id not in cls._buildings and 'building' in locals():
                cls._buildings[building_id] = building
            raise 

    @classmethod
    def get_building_devices(cls, building_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene los datos históricos de todos los dispositivos de un edificio.
        """
        if building_id not in cls._buildings:
            raise ValueError("Building not found")

        building = cls._buildings[building_id]
        devices = []

        try:
            for floor in building["floors"]:
                for room in floor["rooms"]:
                    for device in room["devices"]:
                        device_data = {
                            "id": device.get("id", str(uuid.uuid4())),  # Generar ID si no existe
                            "type": device["type"],
                            "name": f"{device['type'].replace('_', ' ').title()} - Room {room.get('number', 'Unknown')}",
                            "status": device.get("status", "inactive"),
                            "readings": device.get("readings", []),
                            "last_reading": device.get("last_reading", {})
                        }
                        devices.append(device_data)
        except Exception as e:
            logger.error(f"Error getting devices for building {building_id}: {str(e)}")
            raise Exception(f"Error processing building structure: {str(e)}")

        return devices

    @classmethod
    def get_building_history(
        cls,
        building_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        device_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de lecturas de los dispositivos de un edificio.
        """
        if building_id not in cls._buildings:
            raise ValueError("Building not found")

        building = cls._buildings[building_id]
        history = []

        # Convertir strings de tiempo a datetime si se proporcionan
        start = datetime.fromisoformat(start_time) if start_time else None
        end = datetime.fromisoformat(end_time) if end_time else None

        for floor in building["floors"]:
            for room in floor["rooms"]:
                for device in room["devices"]:
                    # Filtrar por tipo de dispositivo si se especifica
                    if device_types and device["type"] not in device_types:
                        continue

                    readings = device.get("readings", [])
                    
                    # Filtrar por rango de tiempo si se especifica
                    if start:
                        readings = [r for r in readings if datetime.fromisoformat(r["timestamp"]) >= start]
                    if end:
                        readings = [r for r in readings if datetime.fromisoformat(r["timestamp"]) <= end]

                    if readings:
                        history.append({
                            "device_id": device["id"],
                            "type": device["type"],
                            "room": room["number"],
                            "floor": floor["number"],
                            "readings": readings
                        })

        return history 

    @classmethod
    async def _notify_clients(cls, simulation_id: str, message: Dict[str, Any]) -> None:
        """Notifica a los clientes conectados"""
        if simulation_id in cls._clients:
            for websocket in cls._clients[simulation_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"Error enviando datos al cliente: {e}")
                    cls._clients[simulation_id].remove(websocket) 