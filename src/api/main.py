from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from .validators import BuildingCreate, SimulationStart, DeviceStatusUpdate
from .simulation import SimulationManager
import logging
import asyncio
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

app = FastAPI()

# Configuración CORS actualizada
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas para edificios
@app.post("/buildings")
async def create_building(building: BuildingCreate):
    try:
        new_building = SimulationManager.create_building(building)
        return {"building": new_building}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/buildings")
async def get_buildings():
    try:
        buildings = SimulationManager.get_buildings()
        return {"buildings": buildings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/buildings/{building_id}")
async def get_building(building_id: str):
    """
    Obtiene un edificio específico por su ID.
    """
    logger.info(f"Getting building {building_id}")
    try:
        building = SimulationManager.get_building(building_id)
        return {"building": building}
    except ValueError as e:
        logger.error(f"Building not found: {building_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting building {building_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Corregir la ruta de simulación
@app.post("/simulation/start")
async def start_simulation(params: SimulationStart):
    """
    Inicia una simulación para un edificio específico.
    """
    logger.info(f"Starting simulation for building {params.building_id}")
    try:
        simulation = await SimulationManager.start_simulation(params.building_id)
        logger.info(f"Successfully started simulation for building {params.building_id}")
        return simulation
    except ValueError as e:
        logger.error(f"Error starting simulation: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error starting simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting simulation: {str(e)}")

@app.get("/simulation/{simulation_id}/status")
async def get_simulation_status(simulation_id: str):
    try:
        status = SimulationManager.get_simulation_status(simulation_id)
        return {"status": status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Rutas para dispositivos
@app.patch("/devices/{device_id}/status")
async def update_device_status(device_id: str, status_update: DeviceStatusUpdate):
    try:
        SimulationManager.update_device_status(device_id, status_update)
        return {"message": "Status updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/devices/{device_id}/readings")
async def get_device_readings(device_id: str):
    try:
        readings = SimulationManager.get_device_readings(device_id)
        return {"readings": readings}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket para datos en tiempo real
@app.websocket("/ws/simulation/{simulation_id}")
async def websocket_endpoint(websocket: WebSocket, simulation_id: str):
    logger.info(f"New WebSocket connection request for simulation {simulation_id}")
    
    try:
        await websocket.accept()
        
        if simulation_id not in SimulationManager._simulations:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        # Agregar el cliente a la lista de conexiones
        if simulation_id not in SimulationManager._clients:
            SimulationManager._clients[simulation_id] = []
        SimulationManager._clients[simulation_id].append(websocket)
        
        try:
            while True:
                # Obtener datos actualizados
                devices = SimulationManager.get_devices_status(simulation_id)
                for device in devices:
                    await websocket.send_json({
                        "device_id": device["device_id"],
                        "type": device["type"],
                        "data": device["last_reading"],
                        "timestamp": datetime.now().isoformat()
                    })
                await asyncio.sleep(1)  # Actualizar cada segundo
        except WebSocketDisconnect:
            logger.info(f"Client disconnected from simulation {simulation_id}")
        finally:
            # Remover el cliente de la lista
            if simulation_id in SimulationManager._clients:
                SimulationManager._clients[simulation_id].remove(websocket)
    except ValueError as e:
        logger.error(f"Simulation error: {e}")
        await websocket.close()
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection: {e}")
        await websocket.close()

@app.post("/simulation/{simulation_id}/stop")
async def stop_simulation(simulation_id: str):
    try:
        SimulationManager.stop_simulation(simulation_id)
        return {"message": "Simulation stopped successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/buildings/{building_id}")
async def delete_building(building_id: str):
    """
    Elimina un edificio y sus simulaciones asociadas.
    """
    logger.info(f"Received delete request for building {building_id}")
    try:
        SimulationManager.delete_building(building_id)
        return {"message": "Building deleted successfully"}
    except ValueError as e:
        logger.error(f"Building not found: {building_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting building {building_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/buildings/{building_id}/devices")
async def get_building_devices(building_id: str):
    """
    Obtiene los datos históricos de todos los dispositivos de un edificio.
    """
    logger.info(f"Getting devices for building {building_id}")
    try:
        devices = SimulationManager.get_building_devices(building_id)
        logger.info(f"Successfully retrieved {len(devices)} devices for building {building_id}")
        return {"devices": devices}
    except ValueError as e:
        logger.error(f"Building not found: {building_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting devices for building {building_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting devices: {str(e)}")

@app.get("/buildings/{building_id}/history")
async def get_building_history(
    building_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    device_types: Optional[List[str]] = Query(None)
):
    """
    Obtiene datos históricos de los dispositivos de un edificio.
    """
    try:
        history = SimulationManager.get_building_history(
            building_id,
            start_time,
            end_time,
            device_types
        )
        return {"history": history}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") 