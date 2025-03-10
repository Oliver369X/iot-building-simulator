# Documentación WebSocket - IoT Building Simulator

## Conexión WebSocket

### URL de Conexión
```
ws://api.yourdomain.com/ws/simulation/{simulation_id}
```

### Eventos Emitidos

#### 1. device_update
```json
{
    "event": "device_update",
    "data": {
        "device_id": "temp_sensor_01",
        "timestamp": "2024-03-20T14:30:00Z",
        "readings": {
            "temperature": 23.5,
            "humidity": 45
        }
    }
}
```

#### 2. simulation_status
```json
{
    "event": "simulation_status",
    "data": {
        "simulation_id": "sim_123",
        "status": "running",
        "elapsed_time": "02:30:15",
        "devices_active": 150
    }
}
```

#### 3. alert
```json
{
    "event": "alert",
    "data": {
        "type": "device_offline",
        "severity": "warning",
        "device_id": "temp_sensor_01",
        "message": "Dispositivo sin respuesta"
    }
}
```

## Ejemplos de Implementación

### JavaScript
```javascript
const ws = new WebSocket(`ws://api.yourdomain.com/ws/simulation/${simulationId}`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch(data.event) {
        case 'device_update':
            handleDeviceUpdate(data.data);
            break;
        case 'simulation_status':
            updateSimulationStatus(data.data);
            break;
        case 'alert':
            showAlert(data.data);
            break;
    }
};

// Mantener conexión activa
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
    }
}, 30000);
```

### Python
```python
import websockets
import asyncio
import json

async def connect_websocket(simulation_id):
    uri = f"ws://api.yourdomain.com/ws/simulation/{simulation_id}"
    async with websockets.connect(uri) as websocket:
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                
                if data['event'] == 'device_update':
                    handle_device_update(data['data'])
                elif data['event'] == 'simulation_status':
                    update_simulation_status(data['data'])
                elif data['event'] == 'alert':
                    handle_alert(data['data'])
                    
            except websockets.exceptions.ConnectionClosed:
                print("Conexión cerrada. Reintentando...")
                break

asyncio.get_event_loop().run_until_complete(
    connect_websocket('sim_123')
) 