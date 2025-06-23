from fastapi import APIRouter, WebSocket, HTTPException, Depends, Request
from typing import List, Dict, Any
from datetime import datetime
import asyncio
import json
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from src.simulator.engine import SimulationEngine
# from src.database.db_manager import DatabaseManager # Eliminado
from src.templates.building_templates import BuildingTemplateManager
from src.database.connection import SessionLocal, get_db
from src.database.models import Building, Floor, Room, Device, DeviceType, SensorReading

# Importar la instancia global del motor de simulación desde main.py
# from src.api.main import simulation_engine as global_simulation_engine
from src.api import validators as api_validators # Necesario para BuildingCreate

router = APIRouter()
# db_manager = DatabaseManager() # Eliminado
template_manager = BuildingTemplateManager()

# Nueva función de dependencia para obtener el engine desde app.state
def get_simulation_engine(request: Request) -> SimulationEngine:
    engine = request.app.state.simulation_engine
    if not engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")
    return engine

@router.post("/simulations/start_global")
async def start_global_simulation(request: Request, simulation_engine: SimulationEngine = Depends(get_simulation_engine)):
    """
    Inicia la simulación para todos los edificios, pisos y habitaciones existentes
    en la base de datos, marcándolos como 'is_simulating=True'.
    """
    try:
        with SessionLocal() as db:
            # Marcar todos los edificios como simulando
            buildings = db.query(Building).all()
            for building in buildings:
                building.is_simulating = True
                db.add(building)
            
            # Marcar todos los pisos como simulando
            floors = db.query(Floor).all()
            for floor in floors:
                floor.is_simulating = True
                db.add(floor)

            # Marcar todas las habitaciones como simulando
            rooms = db.query(Room).all()
            for room in rooms:
                room.is_simulating = True
                db.add(room)
            
            db.commit()
            
            # Asegurar que el bucle principal del motor de simulación esté corriendo
            await simulation_engine.start_engine_main_loop()
            
            return {"message": "Simulación global iniciada para todos los edificios, pisos y habitaciones."}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al iniciar simulación global: {str(e)}")

@router.post("/simulations/stop_global")
async def stop_global_simulation(request: Request, simulation_engine: SimulationEngine = Depends(get_simulation_engine)):
    """
    Detiene la simulación para todos los edificios, pisos y habitaciones existentes
    en la base de datos, marcándolos como 'is_simulating=False'.
    """
    try:
        with SessionLocal() as db:
            # Marcar todos los edificios como no simulando
            buildings = db.query(Building).all()
            for building in buildings:
                building.is_simulating = False
                db.add(building)
            
            # Marcar todos los pisos como no simulando
            floors = db.query(Floor).all()
            for floor in floors:
                floor.is_simulating = False
                db.add(floor)

            # Marcar todas las habitaciones como no simulando
            rooms = db.query(Room).all()
            for room in rooms:
                room.is_simulating = False
                db.add(room)
            
            db.commit()
            
            # Detener el bucle principal del motor de simulación
            await simulation_engine.stop_engine_main_loop()
            
            return {"message": "Simulación global detenida para todos los edificios, pisos y habitaciones."}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al detener simulación global: {str(e)}")

@router.post("/simulations/start_new_building_simulation")
async def start_new_building_simulation(config: Dict[str, Any], request: Request, simulation_engine: SimulationEngine = Depends(get_simulation_engine)):
    """Inicia una nueva simulación creando un edificio desde una plantilla."""
    try:
        # Crear edificio desde plantilla
        building_data_dict = template_manager.create_building_from_template(
            template_name=config["template"],
            building_name=config["name"],
            location=config["location"]
        )
        
        # Convertir el diccionario a un modelo Pydantic para usar con create_building
        building_create_model = api_validators.BuildingCreate(
            name=building_data_dict["name"],
            address=building_data_dict.get("address"),
            geolocation=building_data_dict.get("geolocation")
        )
        
        # Guardar en base de datos usando el motor de simulación
        # El método create_building del motor ya maneja la persistencia
        created_building_db_model = simulation_engine.create_building(building_create_model)
        
        # Marcar el nuevo edificio como simulando
        with SessionLocal() as db:
            db_building = db.query(Building).filter(Building.id == created_building_db_model.id).first()
            if db_building:
                db_building.is_simulating = True
                db.add(db_building)
                db.commit()
                db.refresh(db_building)

        # Asegurar que el bucle principal del motor de simulación esté corriendo
        await simulation_engine.start_engine_main_loop()
        
        return {"simulation_id": created_building_db_model.id, "building_id": created_building_db_model.id, "message": "Simulación de nuevo edificio iniciada."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/simulations/{simulation_id}/status")
async def get_simulation_status(simulation_id: str):
    """Obtiene el estado de una simulación (ahora basado en el estado del edificio/entidad)"""
    with SessionLocal() as db:
        building = db.query(Building).filter(Building.id == simulation_id).first()
        if building:
            return {"simulation_id": simulation_id, "is_simulating": building.is_simulating, "entity_type": "building"}
        
        floor = db.query(Floor).filter(Floor.id == simulation_id).first()
        if floor:
            return {"simulation_id": simulation_id, "is_simulating": floor.is_simulating, "entity_type": "floor"}

        room = db.query(Room).filter(Room.id == simulation_id).first()
        if room:
            return {"simulation_id": simulation_id, "is_simulating": room.is_simulating, "entity_type": "room"}

        raise HTTPException(status_code=404, detail="Simulation/Entity not found or not directly controllable via this ID")

@router.get("/buildings/{building_id}/data")
async def get_building_data(
    building_id: str,
    request: Request,
    start_time: datetime = None,
    end_time: datetime = None,
    simulation_engine: SimulationEngine = Depends(get_simulation_engine)
):
    """Obtiene datos históricos de un edificio"""
    # Ahora se usa simulation_engine para obtener datos, asumiendo que tiene un método adecuado
    # o que se puede acceder a la DB a través de él.
    # Si get_device_data no está en SimulationEngine, se necesitará una refactorización.
    # Por ahora, asumo que el motor puede manejar esto o que se puede usar get_db() directamente.
    # Si db_manager.get_device_data era una función de DatabaseManager,
    # y DatabaseManager fue eliminado, esta línea causará un error.
    # Necesitamos una alternativa.
    # Revisando engine.py, no hay un get_device_data directo.
    # La lógica de obtener datos históricos debería ir a DatabaseManager o ser implementada en Engine.
    # Por ahora, para evitar el error, usaré una sesión de DB directa para consultar SensorReading
    # o AggregatedReading, que es lo que el motor hace para KPIs.
    
    # Opción 1: Si get_device_data es una función del motor (no lo es actualmente)
    # data = simulation_engine.get_device_data(
    #     building_id=building_id,
    #     start_time=start_time,
    #     end_time=end_time
    # )

    # Opción 2: Acceder directamente a la DB para datos de telemetría
    with SessionLocal() as db:
        # Esto es una simplificación. Idealmente, se consultaría AggregatedReading
        # o SensorReading con joins a Building, Floor, Room, Device.
        # Para el propósito de este endpoint, se puede obtener la telemetría de los dispositivos
        # del edificio y luego filtrarla.
        
        # Obtener todos los dispositivos del edificio
        devices_in_building = db.query(Device)\
            .join(Room, Device.room_id == Room.id)\
            .join(Floor, Room.floor_id == Floor.id)\
            .filter(Floor.building_id == building_id).all()
        
        device_ids = [d.id for d in devices_in_building]
        
        # Consultar SensorReading para estos dispositivos
        query = db.query(Device, Building, Floor, Room, DeviceType, SensorReading)\
            .join(Room, Device.room_id == Room.id)\
            .join(Floor, Room.floor_id == Floor.id)\
            .join(Building, Floor.building_id == Building.id)\
            .join(DeviceType, Device.device_type_id == DeviceType.id)\
            .join(SensorReading, Device.id == SensorReading.device_id)\
            .filter(Building.id == building_id)
        
        if start_time:
            query = query.filter(SensorReading.timestamp >= start_time)
        if end_time:
            query = query.filter(SensorReading.timestamp < end_time)
            
        results = query.order_by(SensorReading.timestamp).all()
        
        # Formatear los resultados
        formatted_data = []
        for device, building, floor, room, device_type, reading in results:
            formatted_data.append({
                "device_id": device.id,
                "device_name": device.name,
                "device_type": device_type.type_name,
                "room_id": room.id,
                "room_name": room.name,
                "floor_id": floor.id,
                "floor_number": floor.floor_number,
                "building_id": building.id,
                "building_name": building.name,
                "timestamp": reading.timestamp.isoformat().replace("+00:00", "Z"),
                "key": reading.extra_data.get("key") if reading.extra_data else None, # Asumiendo que 'key' está en extra_data
                "value": reading.value,
                "unit": reading.unit
            })
        return formatted_data

@router.websocket("/ws/simulation/{simulation_id}")
async def websocket_endpoint(websocket: WebSocket, simulation_id: str, request: Request, simulation_engine: SimulationEngine = Depends(get_simulation_engine)):
    """Endpoint WebSocket para datos en tiempo real"""
    await websocket.accept()
    # Acceder a la cola de telemetría desde la instancia global del motor de simulación
    # No crear una nueva cola aquí, usar la que ya está en el motor.
    if not simulation_engine._telemetry_queue:
        raise HTTPException(status_code=503, detail="Telemetry queue not initialized in simulation engine.")

    try:
        while True:
            data = await simulation_engine._telemetry_queue.get()
            if data:
                await websocket.send_json(data)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # No limpiar la cola aquí, ya que es global y otros clientes podrían usarla.
        # La gestión de la cola debe ser más sofisticada si hay múltiples clientes.
        # Por ahora, simplemente cerrar el websocket.
        await websocket.close()

@router.get("/buildings/{building_id}/live_data")
async def get_live_building_data(
    building_id: str,
    limit_per_device: int = 1,  # Por defecto, solo la última lectura por dispositivo
    db: Session = Depends(get_db)
):
    """
    Devuelve la última lectura de cada dispositivo activo en un edificio.
    """
    try:
        # Obtener los IDs de los dispositivos activos del edificio
        device_ids = [
            d.id for d in db.query(Device)
            .join(Room, Device.room_id == Room.id)
            .join(Floor, Room.floor_id == Floor.id)
            .filter(Floor.building_id == building_id)
            .filter(Device.is_active == True)
            .all()
        ]
        if not device_ids:
            return []

        # Subconsulta: última lectura por dispositivo
        subq = (
            db.query(
                SensorReading.device_id,
                func.max(SensorReading.timestamp).label("max_timestamp")
            )
            .filter(SensorReading.device_id.in_(device_ids))
            .group_by(SensorReading.device_id)
            .subquery()
        )

        latest_readings = (
            db.query(SensorReading)
            .join(
                subq,
                (SensorReading.device_id == subq.c.device_id) &
                (SensorReading.timestamp == subq.c.max_timestamp)
            )
            .all()
        )

        # Formatear la respuesta
        return [
            {
                "device_id": r.device_id,
                "timestamp": r.timestamp.isoformat().replace("+00:00", "Z"),
                "key": r.extra_data.get("key") if r.extra_data else None,
                "value": r.value,
                "unit": r.unit
            }
            for r in latest_readings
        ]
    except Exception as e:
        print(f"Error en get_live_building_data: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener datos en vivo.")
