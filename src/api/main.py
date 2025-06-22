from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect, Query, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Any
from datetime import datetime
import logging
import asyncio
from sqlalchemy.orm import Session

from . import validators as api_validators
from ..simulator.engine import SimulationEngine, SimulationError
from ..database.connection import SessionLocal, get_db
from ..database import models as db_models
from ..database.models import AggregatedReading

# Importar los routers de las rutas
from .routes import simulation as simulation_router_module
from .routes import templates as templates_router_module # Assuming you have a templates router

logger = logging.getLogger(__name__)

# Instancia global del motor de simulación
simulation_engine: Optional[SimulationEngine] = None

app = FastAPI(title="IoT Building Simulator API", version="1.0.0")

# --- Application Lifecycle ---
@app.on_event("startup")
async def startup_event():
    global simulation_engine
    logger.info("Application startup: Initializing Simulation Engine...")
    simulation_engine = SimulationEngine(db_session_local=SessionLocal)
    
    # Cola para eventos de telemetría en tiempo real
    telemetry_queue: asyncio.Queue = asyncio.Queue()
    simulation_engine.set_telemetry_queue(telemetry_queue) # Pass the queue to the engine
    
    simulation_engine.setup_simulation_events()  # Configure recurring tasks
    
    # Iniciar el worker de agregación en segundo plano
    asyncio.create_task(simulation_engine.start_aggregation_worker(60)) # Start aggregation worker
    
    # Guardar la instancia global en app.state
    app.state.simulation_engine = simulation_engine
    logger.info("Simulation Engine initialized and stored in app.state (NOT started by default). Use the /simulation/start endpoint to start.")

@app.on_event("shutdown")
async def shutdown_event():
    global simulation_engine
    if simulation_engine:
        logger.info("Application shutdown: Stopping Simulation Engine...")
        await simulation_engine.stop_engine_main_loop() # Ensure the main loop is stopped
        logger.info("Simulation Engine stopped.")

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints (Prefix: /api/v1) ---
API_PREFIX = "/api/v1"

# Incluir los routers de las rutas
# Se pasa la instancia global de simulation_engine a los routers
# Esto requiere que los endpoints en simulation.py acepten simulation_engine como dependencia
# o que accedan a la variable global. Para simplificar, haremos que accedan a la global.
# Sin embargo, la inyección de dependencia es una mejor práctica.
# Por ahora, ajustaremos simulation.py para que use la global.

# Importar el router de simulación después de definir simulation_engine
# para que pueda acceder a la instancia global.
# Alternativa: usar Depends(get_simulation_engine) en cada endpoint.
# Para este caso, dado que simulation_engine es global y se inicializa en startup,
# podemos hacer que los routers lo importen directamente.

# Registrar los routers
app.include_router(simulation_router_module.router, prefix=API_PREFIX, tags=["Simulation"])
app.include_router(templates_router_module.router, prefix=API_PREFIX, tags=["Templates"])


# --- Gestión de Infraestructura (Endpoints existentes, se mantienen) ---

# Edificios
@app.post(
    f"{API_PREFIX}/buildings",
    response_model=api_validators.BuildingRead,
    status_code=201,
    tags=["Buildings"],
    summary="Crear un nuevo edificio",
    description="Crea un nuevo edificio en el sistema con el nombre, dirección y geolocalización proporcionados."
)
async def create_building_endpoint(building_data: api_validators.BuildingCreate):
    global simulation_engine # Access global instance
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        created_building_db_model = simulation_engine.create_building(building_data)
        return api_validators.BuildingRead.from_orm(created_building_db_model)
    except SimulationError as e:
        logger.error(f"Error creating building: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating building: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while creating building")

@app.get(
    f"{API_PREFIX}/buildings/{{building_id}}",
    response_model=api_validators.BuildingRead,
    tags=["Buildings"],
    summary="Obtener un edificio específico por ID",
    description="Recupera los detalles de un edificio específico usando su ID único."
)
async def get_building_endpoint(building_id: str):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        building_db_model = simulation_engine.get_building_by_id(building_id)
        if not building_db_model:
            logger.info(f"Building with id {building_id} not found by engine.")
            raise HTTPException(status_code=404, detail=f"Building with id {building_id} not found")
        
        return api_validators.BuildingRead.from_orm(building_db_model)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error getting building {building_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving building")

@app.get(
    f"{API_PREFIX}/buildings",
    response_model=List[api_validators.BuildingRead],
    tags=["Buildings"],
    summary="Listar todos los edificios",
    description="Recupera una lista de todos los edificios en el sistema, con paginación opcional usando skip y limit."
)
async def list_buildings_endpoint(skip: int = 0, limit: int = 100):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        buildings_db = simulation_engine.get_all_buildings(skip=skip, limit=limit)
        return buildings_db
    except Exception as e:
        logger.error(f"Error listing buildings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while listing buildings")

@app.put(
    f"{API_PREFIX}/buildings/{{building_id}}",
    response_model=api_validators.BuildingRead,
    tags=["Buildings"],
    summary="Actualizar un edificio existente",
    description="Actualiza los detalles de un edificio existente identificado por su ID. Solo se actualizarán los campos proporcionados."
)
async def update_building_endpoint(building_id: str, building_data: api_validators.BuildingUpdate):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        updated_building_db_model = simulation_engine.update_building(building_id, building_data)
        if not updated_building_db_model:
            raise HTTPException(status_code=404, detail=f"Building with id {building_id} not found")
        return api_validators.BuildingRead.from_orm(updated_building_db_model)
    except SimulationError as e:
        logger.error(f"Error updating building {building_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error updating building {building_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while updating building")

@app.delete(
    f"{API_PREFIX}/buildings/{{building_id}}",
    status_code=204,
    tags=["Buildings"],
    summary="Eliminar un edificio por ID",
    description="Elimina un edificio y toda su jerarquía (pisos, habitaciones, dispositivos) usando su ID único."
)
async def delete_building_endpoint(building_id: str):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        success = simulation_engine.delete_building(building_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Building with id {building_id} not found")
        return None
    except HTTPException as http_exc:
        raise http_exc
    except SimulationError as e:
        logger.error(f"Error deleting building {building_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting building {building_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while deleting building")

# --- Control de Simulación (Simulation Control) ---

@app.post(
    f"{API_PREFIX}/buildings/{{building_id}}/simulate",
    response_model=api_validators.BuildingRead,
    tags=["Simulation Control"],
    summary="Activar/Desactivar simulación para un edificio",
    description="Establece el estado de simulación para un edificio completo. Esto afectará a todos los dispositivos dentro de ese edificio."
)
async def set_building_simulation_status_endpoint(
    building_id: str, 
    status: bool = Query(..., description="True para activar, False para desactivar la simulación"),
    db: Session = Depends(get_db)
):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        updated_building = simulation_engine.update_building_simulation_status(building_id, status, db)
        if not updated_building:
            raise HTTPException(status_code=404, detail=f"Building with id {building_id} not found")
        return api_validators.BuildingRead.from_orm(updated_building)
    except SimulationError as e:
        logger.error(f"Error updating simulation status for building {building_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error setting simulation status for building {building_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while setting simulation status")

@app.post(
    f"{API_PREFIX}/floors/{{floor_id}}/simulate",
    response_model=api_validators.FloorRead,
    tags=["Simulation Control"],
    summary="Activar/Desactivar simulación para un piso",
    description="Establece el estado de simulación para un piso específico. Esto afectará a todos los dispositivos dentro de ese piso, anulando el estado del edificio si es diferente."
)
async def set_floor_simulation_status_endpoint(
    floor_id: str, 
    status: bool = Query(..., description="True para activar, False para desactivar la simulación"),
    db: Session = Depends(get_db)
):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        updated_floor = simulation_engine.update_floor_simulation_status(floor_id, status, db)
        if not updated_floor:
            raise HTTPException(status_code=404, detail=f"Floor with id {floor_id} not found")
        return api_validators.FloorRead.from_orm(updated_floor)
    except SimulationError as e:
        logger.error(f"Error updating simulation status for floor {floor_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error setting simulation status for floor {floor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while setting simulation status")

@app.post(
    f"{API_PREFIX}/rooms/{{room_id}}/simulate",
    response_model=api_validators.RoomRead,
    tags=["Simulation Control"],
    summary="Activar/Desactivar simulación para una habitación",
    description="Establece el estado de simulación para una habitación específica. Esto afectará a todos los dispositivos dentro de esa habitación, anulando el estado del piso/edificio si es diferente."
)
async def set_room_simulation_status_endpoint(
    room_id: str, 
    status: bool = Query(..., description="True para activar, False para desactivar la simulación"),
    db: Session = Depends(get_db)
):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        updated_room = simulation_engine.update_room_simulation_status(room_id, status, db)
        if not updated_room:
            raise HTTPException(status_code=404, detail=f"Room with id {room_id} not found")
        return api_validators.RoomRead.from_orm(updated_room)
    except SimulationError as e:
        logger.error(f"Error updating simulation status for room {room_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error setting simulation status for room {room_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while setting simulation status")

# --- Pisos (Floors) ---

@app.post(
    f"{API_PREFIX}/buildings/{{building_id}}/floors",
    response_model=api_validators.FloorRead,
    status_code=201,
    tags=["Floors"],
    summary="Crear un nuevo piso para un edificio",
    description="Crea un nuevo piso dentro del edificio especificado."
)
async def create_floor_endpoint(building_id: str, floor_data: api_validators.FloorCreate):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        # Ensure building exists before creating a floor
        building = simulation_engine.get_building_by_id(building_id)
        if not building:
            raise HTTPException(status_code=404, detail=f"Building with id {building_id} not found")
        
        created_floor_db_model = simulation_engine.create_floor(building_id, floor_data)
        return api_validators.FloorRead.from_orm(created_floor_db_model)
    except SimulationError as e:
        logger.error(f"Error creating floor for building {building_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error creating floor: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while creating floor")

@app.get(
    f"{API_PREFIX}/buildings/{{building_id}}/floors",
    response_model=List[api_validators.FloorRead],
    tags=["Floors"],
    summary="Listar pisos para un edificio específico",
    description="Recupera una lista de todos los pisos para un edificio dado."
)
async def list_floors_for_building_endpoint(building_id: str, skip: int = 0, limit: int = 100):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        # Ensure building exists
        building = simulation_engine.get_building_by_id(building_id)
        if not building:
            raise HTTPException(status_code=404, detail=f"Building with id {building_id} not found")

        floors_db = simulation_engine.get_floors_by_building_id(building_id, skip=skip, limit=limit)
        return floors_db
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error listing floors for building {building_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while listing floors")

@app.get(
    f"{API_PREFIX}/floors/{{floor_id}}",
    response_model=api_validators.FloorRead,
    tags=["Floors"],
    summary="Obtener un piso específico por ID",
    description="Recupera los detalles de un piso específico usando su ID único."
)
async def get_floor_endpoint(floor_id: str):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        floor_db_model = simulation_engine.get_floor_by_id(floor_id)
        if not floor_db_model:
            raise HTTPException(status_code=404, detail=f"Floor with id {floor_id} not found")
        return api_validators.FloorRead.from_orm(floor_db_model)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error getting floor {floor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving floor")

@app.put(
    f"{API_PREFIX}/floors/{{floor_id}}",
    response_model=api_validators.FloorRead,
    tags=["Floors"],
    summary="Actualizar un piso existente",
    description="Actualiza los detalles de un piso existente identificado por su ID."
)
async def update_floor_endpoint(floor_id: str, floor_data: api_validators.FloorUpdate):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        updated_floor_db_model = simulation_engine.update_floor(floor_id, floor_data)
        if not updated_floor_db_model:
            raise HTTPException(status_code=404, detail=f"Floor with id {floor_id} not found")
        return api_validators.FloorRead.from_orm(updated_floor_db_model)
    except SimulationError as e:
        logger.error(f"Error updating floor {floor_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error updating floor {floor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while updating floor")

@app.delete(
    f"{API_PREFIX}/floors/{{floor_id}}",
    status_code=204,
    tags=["Floors"],
    summary="Eliminar un piso por ID",
    description="Elimina un piso y sus habitaciones y dispositivos asociados usando su ID único."
)
async def delete_floor_endpoint(floor_id: str):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        success = simulation_engine.delete_floor(floor_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Floor with id {floor_id} not found")
        return None
    except HTTPException as http_exc:
        raise http_exc
    except SimulationError as e:
        logger.error(f"Error deleting floor {floor_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting floor {floor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while deleting floor")

# --- Habitaciones (Rooms) ---

@app.post(
    f"{API_PREFIX}/floors/{{floor_id}}/rooms",
    response_model=api_validators.RoomRead,
    status_code=201,
    tags=["Rooms"],
    summary="Crear una nueva habitación en un piso",
    description="Crea una nueva habitación dentro del piso especificado."
)
async def create_room_endpoint(floor_id: str, room_data: api_validators.RoomCreate):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        # Ensure floor exists
        floor = simulation_engine.get_floor_by_id(floor_id)
        if not floor:
            raise HTTPException(status_code=404, detail=f"Floor with id {floor_id} not found")

        created_room_db_model = simulation_engine.create_room(floor_id, room_data)
        return api_validators.RoomRead.from_orm(created_room_db_model)
    except SimulationError as e:
        logger.error(f"Error creating room for floor {floor_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error creating room: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while creating room")

@app.get(
    f"{API_PREFIX}/floors/{{floor_id}}/rooms",
    response_model=List[api_validators.RoomRead],
    tags=["Rooms"],
    summary="Listar habitaciones para un piso específico",
    description="Recupera una lista de todas las habitaciones para un piso dado."
)
async def list_rooms_for_floor_endpoint(floor_id: str, skip: int = 0, limit: int = 100):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        # Ensure floor exists
        floor = simulation_engine.get_floor_by_id(floor_id)
        if not floor:
            raise HTTPException(status_code=404, detail=f"Floor with id {floor_id} not found")

        rooms_db = simulation_engine.get_rooms_by_floor_id(floor_id, skip=skip, limit=limit)
        return rooms_db
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error listing rooms for floor {floor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while listing rooms")

@app.get(
    f"{API_PREFIX}/rooms/{{room_id}}",
    response_model=api_validators.RoomRead,
    tags=["Rooms"],
    summary="Obtener una habitación específica por ID",
    description="Recupera los detalles de una habitación específica usando su ID único."
)
async def get_room_endpoint(room_id: str):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        room_db_model = simulation_engine.get_room_by_id(room_id)
        if not room_db_model:
            raise HTTPException(status_code=404, detail=f"Room with id {room_id} not found")
        return api_validators.RoomRead.from_orm(room_db_model)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error getting room {room_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving room")

@app.put(
    f"{API_PREFIX}/rooms/{{room_id}}",
    response_model=api_validators.RoomRead,
    tags=["Rooms"],
    summary="Actualizar una habitación existente",
    description="Actualiza los detalles de una habitación existente identificada por su ID."
)
async def update_room_endpoint(room_id: str, room_data: api_validators.RoomUpdate):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        updated_room_db_model = simulation_engine.update_room(room_id, room_data)
        if not updated_room_db_model:
            raise HTTPException(status_code=404, detail=f"Room with id {room_id} not found")
        return api_validators.RoomRead.from_orm(updated_room_db_model)
    except SimulationError as e:
        logger.error(f"Error updating room {room_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error updating room {room_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while updating room")

@app.delete(
    f"{API_PREFIX}/rooms/{{room_id}}",
    status_code=204,
    tags=["Rooms"],
    summary="Eliminar una habitación por ID",
    description="Elimina una habitación y sus dispositivos asociados usando su ID único."
)
async def delete_room_endpoint(room_id: str):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        success = simulation_engine.delete_room(room_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Room with id {room_id} not found")
        return None
    except HTTPException as http_exc:
        raise http_exc
    except SimulationError as e:
        logger.error(f"Error deleting room {room_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting room {room_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while deleting room")

# --- Dispositivos (Devices) ---

@app.post(
    f"{API_PREFIX}/rooms/{{room_id}}/devices",
    response_model=api_validators.DeviceRead,
    status_code=201,
    tags=["Devices"],
    summary="Crear un nuevo dispositivo en una habitación",
    description="Crea un nuevo dispositivo dentro de la habitación especificada."
)
async def create_device_endpoint(room_id: str, device_data: api_validators.DeviceCreate):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        # Ensure room exists
        room = simulation_engine.get_room_by_id(room_id)
        if not room:
            raise HTTPException(status_code=404, detail=f"Room with id {room_id} not found")
        
        # Ensure device type exists
        device_type = simulation_engine.get_device_type_by_id(device_data.device_type_id)
        if not device_type:
            raise HTTPException(status_code=404, detail=f"DeviceType with id {device_data.device_type_id} not found")

        created_device_db_model = simulation_engine.create_device(room_id, device_data)
        return api_validators.DeviceRead.from_orm(created_device_db_model)
    except SimulationError as e:
        logger.error(f"Error creating device for room {room_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error creating device: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while creating device")

@app.get(
    f"{API_PREFIX}/rooms/{{room_id}}/devices",
    response_model=List[api_validators.DeviceRead],
    tags=["Devices"],
    summary="Listar dispositivos para una habitación específica",
    description="Recupera una lista de todos los dispositivos para una habitación dada."
)
async def list_devices_for_room_endpoint(room_id: str, skip: int = 0, limit: int = 100):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        # Ensure room exists
        room = simulation_engine.get_room_by_id(room_id)
        if not room:
            raise HTTPException(status_code=404, detail=f"Room with id {room_id} not found")

        devices_db = simulation_engine.get_devices_by_room_id(room_id, skip=skip, limit=limit)
        return devices_db
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error listing devices for room {room_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while listing devices")

@app.get(
    f"{API_PREFIX}/devices/{{device_id}}",
    response_model=api_validators.DeviceRead,
    tags=["Devices"],
    summary="Obtener un dispositivo específico por ID",
    description="Recupera los detalles de un dispositivo específico usando su ID único."
)
async def get_device_endpoint(device_id: str):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        device_db_model = simulation_engine.get_device_by_id(device_id)
        if not device_db_model:
            raise HTTPException(status_code=404, detail=f"Device with id {device_id} not found")
        return api_validators.DeviceRead.from_orm(device_db_model)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error getting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving device")

@app.put(
    f"{API_PREFIX}/devices/{{device_id}}",
    response_model=api_validators.DeviceRead,
    tags=["Devices"],
    summary="Actualizar un dispositivo existente",
    description="Actualiza los detalles de un dispositivo existente identificado por su ID. Puede usarse para cambiar el nombre, la ubicación (room_id), el estado, etc."
)
async def update_device_endpoint(device_id: str, device_data: api_validators.DeviceUpdate):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        # If room_id is being updated, ensure the new room exists
        if device_data.room_id:
            new_room = simulation_engine.get_room_by_id(device_data.room_id)
            if not new_room:
                raise HTTPException(status_code=404, detail=f"New room with id {device_data.room_id} not found")
        
        # If device_type_id is being updated, ensure the new device type exists
        if device_data.device_type_id:
            new_device_type = simulation_engine.get_device_type_by_id(device_data.device_type_id)
            if not new_device_type:
                raise HTTPException(status_code=404, detail=f"New DeviceType with id {device_data.device_type_id} not found")

        updated_device_db_model = simulation_engine.update_device(device_id, device_data)
        if not updated_device_db_model:
            raise HTTPException(status_code=404, detail=f"Device with id {device_id} not found")
        return api_validators.DeviceRead.from_orm(updated_device_db_model)
    except SimulationError as e:
        logger.error(f"Error updating device {device_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error updating device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while updating device")

@app.delete(
    f"{API_PREFIX}/devices/{{device_id}}",
    status_code=204,
    tags=["Devices"],
    summary="Eliminar un dispositivo por ID",
    description="Elimina un dispositivo usando su ID único."
)
async def delete_device_endpoint(device_id: str):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        success = simulation_engine.delete_device(device_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Device with id {device_id} not found")
        return None
    except HTTPException as http_exc:
        raise http_exc
    except SimulationError as e:
        logger.error(f"Error deleting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while deleting device")

# --- Tipos de Dispositivos (DeviceTypes) ---

@app.post(
    f"{API_PREFIX}/device-types",
    response_model=api_validators.DeviceTypeRead,
    status_code=201,
    tags=["DeviceTypes"],
    summary="Crear un nuevo tipo de dispositivo",
    description="Crea un nuevo tipo de dispositivo que puede ser usado en el sistema."
)
async def create_device_type_endpoint(device_type_data: api_validators.DeviceTypeCreate):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        # Check if a device type with this ID or name already exists to prevent duplicates if needed
        # For now, assuming engine handles this or ID is unique.
        created_device_type_db_model = simulation_engine.create_device_type(device_type_data)
        return api_validators.DeviceTypeRead.from_orm(created_device_type_db_model)
    except SimulationError as e:
        logger.error(f"Error creating device type: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating device type: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while creating device type")

@app.get(
    f"{API_PREFIX}/device-types/{{device_type_id}}",
    response_model=api_validators.DeviceTypeRead,
    tags=["DeviceTypes"],
    summary="Obtener un tipo de dispositivo específico por ID",
    description="Recupera los detalles de un tipo de dispositivo específico usando su ID único."
)
async def get_device_type_endpoint(device_type_id: str):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        device_type_db_model = simulation_engine.get_device_type_by_id(device_type_id)
        if not device_type_db_model:
            raise HTTPException(status_code=404, detail=f"DeviceType with id {device_type_id} not found")
        return api_validators.DeviceTypeRead.from_orm(device_type_db_model)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error getting device type {device_type_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving device type")

@app.get(
    f"{API_PREFIX}/device-types",
    response_model=List[api_validators.DeviceTypeRead],
    tags=["DeviceTypes"],
    summary="Listar todos los tipos de dispositivos",
    description="Recupera una lista de todos los tipos de dispositivos disponibles en el sistema."
)
async def list_device_types_endpoint(skip: int = 0, limit: int = 100):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        device_types_db = simulation_engine.get_all_device_types(skip=skip, limit=limit)
        return device_types_db
    except Exception as e:
        logger.error(f"Error listing device types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while listing device types")

@app.put(
    f"{API_PREFIX}/device-types/{{device_type_id}}",
    response_model=api_validators.DeviceTypeRead,
    tags=["DeviceTypes"],
    summary="Actualizar un tipo de dispositivo existente",
    description="Actualiza los detalles de un tipo de dispositivo existente identificado por su ID."
)
async def update_device_type_endpoint(device_type_id: str, device_type_data: api_validators.DeviceTypeUpdate):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        updated_device_type_db_model = simulation_engine.update_device_type(device_type_id, device_type_data)
        if not updated_device_type_db_model:
            raise HTTPException(status_code=404, detail=f"DeviceType with id {device_type_id} not found")
        return api_validators.DeviceTypeRead.from_orm(updated_device_type_db_model)
    except SimulationError as e:
        logger.error(f"Error updating device type {device_type_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error updating device type {device_type_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while updating device type")

@app.delete(
    f"{API_PREFIX}/device-types/{{device_type_id}}",
    status_code=204,
    tags=["DeviceTypes"],
    summary="Eliminar un tipo de dispositivo por ID",
    description="Elimina un tipo de dispositivo usando su ID único. Nota: Esto podría fallar si hay dispositivos usando este tipo actualmente."
)
async def delete_device_type_endpoint(device_type_id: str):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        # Consider implications: what if devices are using this type?
        # The engine's delete_device_type should handle this (e.g., prevent deletion or cascade).
        success = simulation_engine.delete_device_type(device_type_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"DeviceType with id {device_type_id} not found or deletion constrained")
        return None
    except HTTPException as http_exc:
        raise http_exc
    except SimulationError as e:
        logger.error(f"Error deleting device type {device_type_id}: {e}")
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting device type {device_type_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while deleting device type")

# --- Programación de Dispositivos (DeviceSchedules) ---

@app.post(
    f"{API_PREFIX}/devices/{{device_id}}/schedules",
    response_model=api_validators.DeviceScheduleRead,
    status_code=201,
    tags=["DeviceSchedules"],
    summary="Crear una nueva programación para un dispositivo",
    description="Crea una nueva tarea programada para el dispositivo especificado."
)
async def create_device_schedule_endpoint(device_id: str, schedule_data: api_validators.DeviceScheduleCreate):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        # Ensure device exists
        device = simulation_engine.get_device_by_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device with id {device_id} not found")

        created_schedule_db_model = simulation_engine.create_device_schedule(device_id, schedule_data)
        return api_validators.DeviceScheduleRead.from_orm(created_schedule_db_model)
    except SimulationError as e:
        logger.error(f"Error creating schedule for device {device_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error creating device schedule: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while creating device schedule")

@app.get(
    f"{API_PREFIX}/devices/{{device_id}}/schedules",
    response_model=List[api_validators.DeviceScheduleRead],
    tags=["DeviceSchedules"],
    summary="Listar programaciones para un dispositivo específico",
    description="Recupera una lista de todas las tareas programadas para un dispositivo dado."
)
async def list_schedules_for_device_endpoint(device_id: str, skip: int = 0, limit: int = 100):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        # Ensure device exists
        device = simulation_engine.get_device_by_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device with id {device_id} not found")

        schedules_db = simulation_engine.get_schedules_by_device_id(device_id, skip=skip, limit=limit)
        return schedules_db
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error listing schedules for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while listing device schedules")

@app.get(
    f"{API_PREFIX}/schedules/{{schedule_id}}",
    response_model=api_validators.DeviceScheduleRead,
    tags=["DeviceSchedules"],
    summary="Obtener una programación específica por ID",
    description="Recupera los detalles de una programación específica usando su ID único."
)
async def get_schedule_endpoint(schedule_id: str):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        schedule_db_model = simulation_engine.get_schedule_by_id(schedule_id)
        if not schedule_db_model:
            raise HTTPException(status_code=404, detail=f"Schedule with id {schedule_id} not found")
        return api_validators.DeviceScheduleRead.from_orm(schedule_db_model)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error getting schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving schedule")

@app.put(
    f"{API_PREFIX}/schedules/{{schedule_id}}",
    response_model=api_validators.DeviceScheduleRead,
    tags=["DeviceSchedules"],
    summary="Actualizar una programación existente",
    description="Actualiza los detalles de una programación existente identificada por su ID."
)
async def update_schedule_endpoint(schedule_id: str, schedule_data: api_validators.DeviceScheduleUpdate):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        updated_schedule_db_model = simulation_engine.update_device_schedule(schedule_id, schedule_data)
        if not updated_schedule_db_model:
            raise HTTPException(status_code=404, detail=f"Schedule with id {schedule_id} not found")
        return api_validators.DeviceScheduleRead.from_orm(updated_schedule_db_model)
    except SimulationError as e:
        logger.error(f"Error updating schedule {schedule_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error updating schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while updating schedule")

@app.delete(
    f"{API_PREFIX}/schedules/{{schedule_id}}",
    status_code=204,
    tags=["DeviceSchedules"],
    summary="Eliminar una programación por ID",
    description="Elimina una programación usando su ID único."
)
async def delete_schedule_endpoint(schedule_id: str):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        success = simulation_engine.delete_device_schedule(schedule_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Schedule with id {schedule_id} not found")
        return None
    except HTTPException as http_exc:
        raise http_exc
    except SimulationError as e:
        logger.error(f"Error deleting schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while deleting schedule")

# --- Alarmas (Alarms) ---

@app.get(
    f"{API_PREFIX}/alarms",
    response_model=List[api_validators.AlarmRead],
    tags=["Alarms"],
    summary="Listar alarmas con filtros",
    description="Recupera una lista de alarmas, con filtrado opcional por estado, severidad, ID de edificio y rango de fechas."
)
async def list_alarms_endpoint(
    status: Optional[str] = Query(None, description="Filtrar por estado de alarma (ej., 'NEW', 'ACK', 'RESOLVED')"),
    severity: Optional[str] = Query(None, description="Filtrar por severidad de alarma (ej., 'CRITICAL', 'HIGH')"),
    building_id: Optional[str] = Query(None, description="Filtrar alarmas por ID de edificio"),
    start_date: Optional[datetime] = Query(None, description="Inicio del rango de fechas para 'triggered_at' de la alarma"),
    end_date: Optional[datetime] = Query(None, description="Fin del rango de fechas para 'triggered_at' de la alarma"),
    skip: int = 0,
    limit: int = 100
):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        alarms_db = simulation_engine.get_alarms(
            status=status,
            severity=severity,
            building_id=building_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        return alarms_db
    except Exception as e:
        logger.error(f"Error listing alarms: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while listing alarms")

@app.post(
    f"{API_PREFIX}/alarms/{{alarm_id}}/ack",
    response_model=api_validators.AlarmRead,
    tags=["Alarms"],
    summary="Reconocer una alarma",
    description="Marca una alarma como reconocida (estado='ACK')."
)
async def acknowledge_alarm_endpoint(alarm_id: str):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        acknowledged_alarm_db_model = simulation_engine.acknowledge_alarm(alarm_id)
        if not acknowledged_alarm_db_model:
            raise HTTPException(status_code=404, detail=f"Alarm with id {alarm_id} not found or already acknowledged/resolved")
        return api_validators.AlarmRead.from_orm(acknowledged_alarm_db_model)
    except SimulationError as e:
        logger.error(f"Error acknowledging alarm {alarm_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error acknowledging alarm {alarm_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while acknowledging alarm")

# --- Control y Simulación ---

@app.post(
    f"{API_PREFIX}/devices/{{device_id}}/actions",
    response_model=api_validators.DeviceRead,
    tags=["Device Control"],
    summary="Enviar una acción a un dispositivo",
    description="Envía un comando a un dispositivo para cambiar su estado (ej., encender/apagar, establecer valor). El estado del dispositivo en la base de datos se actualiza inmediatamente."
)
async def device_action_endpoint(device_id: str, action_data: api_validators.DeviceAction):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        # Ensure device exists
        device = simulation_engine.get_device_by_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device with id {device_id} not found")

        updated_device_db_model = simulation_engine.execute_device_action(device_id, action_data)
        if not updated_device_db_model:
            raise HTTPException(status_code=400, detail="Failed to execute action or update device state")
        return api_validators.DeviceRead.from_orm(updated_device_db_model)
    except SimulationError as e:
        logger.error(f"Error executing action for device {device_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error executing action for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while executing device action")

# --- Datos y Visualización ---

@app.get(
    f"{API_PREFIX}/telemetry/device/{{device_id}}",
    response_model=api_validators.TelemetryResponse,
    tags=["Data & Visualization"],
    summary="Obtener datos históricos de telemetría para un dispositivo",
    description="Recupera datos históricos de telemetría para un dispositivo específico, con opciones de filtrado por clave, rango de tiempo y agregación."
)
async def get_device_telemetry_endpoint(
    device_id: str,
    key: Optional[str] = Query(None, description="Clave de telemetría específica a recuperar (ej., 'temperatura')"),
    start_time: Optional[datetime] = Query(None, description="Inicio del rango de tiempo para los datos de telemetría"),
    end_time: Optional[datetime] = Query(None, description="Fin del rango de tiempo para los datos de telemetría"),
    aggregation: Optional[str] = Query(None, description="Intervalo de agregación (ej., '1m', '1h'). Aún no implementado completamente en el motor.")
):
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        # Ensure device exists
        device = simulation_engine.get_device_by_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device with id {device_id} not found")

        telemetry_data = simulation_engine.get_device_telemetry(
            device_id=device_id,
            key=key,
            start_time=start_time,
            end_time=end_time,
            aggregation=aggregation
        )
        
        if not isinstance(telemetry_data, list):
             logger.warning(f"Telemetry data for device {device_id} from engine is not a list: {telemetry_data}")
             pass

        return api_validators.TelemetryResponse(
            device_id=device_id,
            data_points=telemetry_data,
            aggregation_interval=aggregation
        )

    except SimulationError as e:
        logger.error(f"Error fetching telemetry for device {device_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error fetching telemetry for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching telemetry")

class KPIDashboardResponse(api_validators.BaseModel):
    total_consumption_live: Optional[float] = None
    active_alarms_count: Optional[int] = None
    average_temperature_building: Optional[float] = None
    devices_on_count: Optional[int] = None

@app.get(
    f"{API_PREFIX}/kpi/dashboard",
    response_model=KPIDashboardResponse,
    tags=["Data & Visualization"],
    summary="Obtener Indicadores Clave de Rendimiento para el panel de control",
    description="Recupera un conjunto de Indicadores Clave de Rendimiento (KPIs) para mostrar en un panel de control."
)
async def get_kpi_dashboard_endpoint():
    global simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    try:
        kpi_data = simulation_engine.get_kpi_dashboard_data()
        return KPIDashboardResponse(**kpi_data)

    except SimulationError as e:
        logger.error(f"Error fetching KPI dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating KPIs: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching KPI dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching KPI data")

# --- WebSocket para Telemetría en Tiempo Real ---
# El motor de simulación publicará eventos de telemetría a una cola,
# y este WebSocket los consumirá y enviará a los clientes.

# Cola para eventos de telemetría en tiempo real (se inicializa en startup_event)
# telemetry_queue: asyncio.Queue = asyncio.Queue() # Removed, now initialized in startup

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Acceder a la cola de telemetría desde la instancia global del motor de simulación
    global simulation_engine
    if not simulation_engine or not simulation_engine._telemetry_queue:
        logger.error("Telemetry queue not initialized in simulation engine.")
        raise HTTPException(status_code=503, detail="Telemetry service not available")

    try:
        while True:
            telemetry_data = await simulation_engine._telemetry_queue.get()
            await websocket.send_json(telemetry_data)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Asegurarse de que la tarea de la cola se marque como hecha
        # telemetry_queue.task_done() # This should be handled by the engine if it manages the queue
        await websocket.close()

# --- Agregaciones de Consumo (Endpoints existentes, se mantienen) ---

@app.get(
    f"{API_PREFIX}/consumption/building/{{building_id}}",
    tags=["Aggregated Consumption"],
    summary="Consumo energético agregado por edificio",
    description="Devuelve los valores agregados de consumo energético para un edificio en un rango de fechas."
)
async def get_building_aggregated_consumption(
    building_id: str,
    start_time: Optional[datetime] = Query(None, description="Inicio del rango de fechas"),
    end_time: Optional[datetime] = Query(None, description="Fin del rango de fechas"),
    period_seconds: Optional[int] = Query(None, description="Periodo de agregación en segundos (ej: 60 para 1 min)")
):
    db = next(get_db())
    query = db.query(AggregatedReading).filter_by(entity_type="building", entity_id=building_id, key="power_consumption")
    if start_time:
        query = query.filter(AggregatedReading.timestamp >= start_time)
    if end_time:
        query = query.filter(AggregatedReading.timestamp < end_time)
    if period_seconds:
        query = query.filter(AggregatedReading.period_seconds == period_seconds)
    results = query.order_by(AggregatedReading.timestamp).all()
    return [r.to_dict() for r in results]

@app.get(
    f"{API_PREFIX}/consumption/floor/{{floor_id}}",
    tags=["Aggregated Consumption"],
    summary="Consumo energético agregado por piso",
    description="Devuelve los valores agregados de consumo energético para un piso en un rango de fechas."
)
async def get_floor_aggregated_consumption(
    floor_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    period_seconds: Optional[int] = Query(None)
):
    db = next(get_db())
    query = db.query(AggregatedReading).filter_by(entity_type="floor", entity_id=floor_id, key="power_consumption")
    if start_time:
        query = query.filter(AggregatedReading.timestamp >= start_time)
    if end_time:
        query = query.filter(AggregatedReading.timestamp < end_time)
    if period_seconds:
        query = query.filter(AggregatedReading.period_seconds == period_seconds)
    results = query.order_by(AggregatedReading.timestamp).all()
    return [r.to_dict() for r in results]

@app.get(
    f"{API_PREFIX}/consumption/room/{{room_id}}",
    tags=["Aggregated Consumption"],
    summary="Consumo energético agregado por habitación",
    description="Devuelve los valores agregados de consumo energético para una habitación en un rango de fechas."
)
async def get_room_aggregated_consumption(
    room_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    period_seconds: Optional[int] = Query(None)
):
    db = next(get_db())
    query = db.query(AggregatedReading).filter_by(entity_type="room", entity_id=room_id, key="power_consumption")
    if start_time:
        query = query.filter(AggregatedReading.timestamp >= start_time)
    if end_time:
        query = query.filter(AggregatedReading.timestamp < end_time)
    if period_seconds:
        query = query.filter(AggregatedReading.period_seconds == period_seconds)
    results = query.order_by(AggregatedReading.timestamp).all()
    return [r.to_dict() for r in results]

@app.get(
    f"{API_PREFIX}/consumption/device/{{device_id}}",
    tags=["Aggregated Consumption"],
    summary="Consumo energético agregado por dispositivo",
    description="Devuelve los valores agregados de consumo energético para un dispositivo en un rango de fechas."
)
async def get_device_aggregated_consumption(
    device_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    period_seconds: Optional[int] = Query(None)
):
    db = next(get_db())
    query = db.query(AggregatedReading).filter_by(entity_type="device", entity_id=device_id, key="power_consumption")
    if start_time:
        query = query.filter(AggregatedReading.timestamp >= start_time)
    if end_time:
        query = query.filter(AggregatedReading.timestamp < end_time)
    if period_seconds:
        query = query.filter(AggregatedReading.period_seconds == period_seconds)
    results = query.order_by(AggregatedReading.timestamp).all()
    return [r.to_dict() for r in results]

# --- Endpoint para detener la simulación global ---
@app.post(f"{API_PREFIX}/simulation/stop", tags=["Simulation Control"], summary="Detener la simulación global")
async def stop_simulation_endpoint(request: Request):
    simulation_engine = request.app.state.simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    if hasattr(simulation_engine, "status") and simulation_engine.status != "running":
        return {"message": "Simulation already stopped"}
    await simulation_engine.stop_engine_main_loop()
    return {"message": "Simulation stopped"}

# --- Endpoint para consultar el estado global de la simulación ---
@app.get(f"{API_PREFIX}/simulation/status", tags=["Simulation Control"], summary="Consultar el estado global de la simulación")
async def simulation_status_endpoint(request: Request):
    simulation_engine = request.app.state.simulation_engine
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not available")
    status = getattr(simulation_engine, "status", "unknown")
    # Consultar entidades principales
    db = SessionLocal()
    try:
        buildings = db.query(db_models.Building).all()
        floors = db.query(db_models.Floor).all()
        rooms = db.query(db_models.Room).all()
        return {
            "engine_status": status,
            "buildings": [{"id": b.id, "name": b.name, "is_simulating": b.is_simulating} for b in buildings],
            "floors": [{"id": f.id, "number": f.floor_number, "is_simulating": f.is_simulating} for f in floors],
            "rooms": [{"id": r.id, "name": r.name, "is_simulating": r.is_simulating} for r in rooms],
        }
    finally:
        db.close()
