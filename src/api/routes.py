from fastapi import FastAPI, HTTPException
from typing import Dict
from ..simulator.engine import SimulationEngine
from datetime import timedelta

app = FastAPI()
engine = SimulationEngine()

@app.post("/buildings/")
async def add_building(building_config: Dict):
    try:
        building_id = engine.add_building(building_config)
        return {"message": "Building added", "building_id": building_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/simulation/start")
async def start_simulation(simulation_data: SimulationStart):
    try:
        simulation_id = engine.start(timedelta(minutes=simulation_data.duration_minutes))
        return {"message": "Simulation started", "simulation_id": simulation_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/simulation/status/{simulation_id}")
async def get_simulation_status(simulation_id: str):
    status = engine.get_simulation_status(simulation_id)
    if status["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Simulation not found")
    return status

@router.delete("/buildings/{building_id}")
async def delete_building(building_id: str):
    # ... código de eliminación
    return {"message": "Building deleted", "building_id": building_id}
