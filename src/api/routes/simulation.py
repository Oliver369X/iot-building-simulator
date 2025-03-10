from fastapi import APIRouter, WebSocket, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import asyncio
import json

from src.simulator.engine import SimulationEngine
from src.database.db_manager import DatabaseManager
from src.templates.building_templates import BuildingTemplateManager

router = APIRouter()
db = DatabaseManager()
template_manager = BuildingTemplateManager()

@router.post("/simulations/start")
async def start_simulation(config: Dict[str, Any]):
    """Inicia una nueva simulación"""
    try:
        # Crear edificio desde plantilla
        building = template_manager.create_building_from_template(
            template_name=config["template"],
            building_name=config["name"],
            location=config["location"]
        )
        
        # Guardar en base de datos
        db.save_building(building)
        
        # Iniciar simulación
        engine = SimulationEngine()
        engine.add_building(building)
        simulation_id = engine.start_simulation(
            duration=config.get("duration", 3600)  # 1 hora por defecto
        )
        
        return {"simulation_id": simulation_id, "building_id": building["building_id"]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/simulations/{simulation_id}/status")
async def get_simulation_status(simulation_id: str):
    """Obtiene el estado de una simulación"""
    status = db.get_simulation_status(simulation_id)
    if not status:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return status

@router.get("/buildings/{building_id}/data")
async def get_building_data(
    building_id: str,
    start_time: datetime = None,
    end_time: datetime = None
):
    """Obtiene datos históricos de un edificio"""
    data = db.get_device_data(
        building_id=building_id,
        start_time=start_time,
        end_time=end_time
    )
    return data

@router.websocket("/ws/simulation/{simulation_id}")
async def websocket_endpoint(websocket: WebSocket, simulation_id: str):
    """Endpoint WebSocket para datos en tiempo real"""
    await websocket.accept()
    try:
        while True:
            # Obtener datos más recientes
            data = db.get_latest_device_data(simulation_id)
            if data:
                await websocket.send_json(data)
            await asyncio.sleep(1)  # Actualizar cada segundo
    except:
        await websocket.close() 