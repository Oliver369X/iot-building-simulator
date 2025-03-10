import asyncio
import websockets
import json
import logging
from datetime import datetime
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def monitor_simulation(simulation_id: str):
    uri = f"ws://localhost:8000/ws/simulation/{simulation_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info(f"🔌 Conectado a simulación {simulation_id}")
            
            while True:
                try:
                    data = await websocket.recv()
                    data = json.loads(data)
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    # Formatear la salida para mejor visualización
                    print("\n" + "="*50)
                    print(f"⏰ {timestamp}")
                    print(f"📍 Device: {data.get('device_id', 'N/A')} ({data.get('type', 'unknown')})")
                    print("📊 Readings:")
                    for key, value in data.get('data', {}).items():
                        print(f"   - {key}: {value}")
                    print("="*50)
                    
                except websockets.ConnectionClosed:
                    logger.error("❌ Conexión cerrada")
                    break
                except Exception as e:
                    logger.error(f"❌ Error: {e}")
    except Exception as e:
        logger.error(f"❌ Error al conectar: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python monitor_simulation.py <simulation_id>")
        sys.exit(1)
        
    simulation_id = sys.argv[1]
    try:
        asyncio.run(monitor_simulation(simulation_id))
    except KeyboardInterrupt:
        print("\n👋 Monitoreo terminado") 