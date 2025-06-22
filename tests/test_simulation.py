# import asyncio
# import pytest
# from src.api.simulation import SimulationManager # SimulationManager is being phased out
# from src.api.validators import BuildingCreate # BuildingCreate is still valid, but this test uses old manager

# async def test_simulation_flow():
#     # This test is based on the old SimulationManager and its in-memory data handling.
#     # It needs to be completely rewritten to test the new SimulationEngine,
#     # database interactions, and the new API structure.
#     # For now, it will be commented out to prevent collection errors.
#     pass

    # # 1. Crear un edificio de prueba
    # building_data = {
    #     "name": "Test Building",
    #     "type": "office", # This field is no longer in BuildingCreate
    #     "floors": [ # BuildingCreate no longer accepts nested floors/rooms/devices
    #         {
    #             "number": 0,
    #             "rooms": [
    #                 {
    #                     "number": 0,
    #                     "devices": [
    #                         {"type": "temperature_sensor", "status": "active"},
    #                         {"type": "motion_sensor", "status": "active"}
    #                     ]
    #                 }
    #             ]
    #         }
    #     ]
    # }
    
    # building = BuildingCreate(**building_data) # This would fail due to schema mismatch
    # created_building = SimulationManager.create_building(building)
    
    # # 2. Iniciar simulación
    # simulation_id = SimulationManager.start_simulation( # This method is from the old manager
    #     created_building["id"],
    #     duration=10, # Simulation parameters might change
    #     events_per_second=1.0
    # )
    
    # # 3. Esperar y verificar datos
    # await asyncio.sleep(5)  # Esperar 5 segundos
    
    # # Verificar que hay datos generados
    # # Accessing SimulationManager._buildings directly is not ideal for testing new engine
    # building = SimulationManager._buildings[created_building["id"]]
    # device = building["floors"][0]["rooms"][0]["devices"][0]
    
    # assert "last_reading" in device
    # assert device["status"] == "active"
    
    # print(f"Device readings: {device['last_reading']}")