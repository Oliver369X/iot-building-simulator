# Documentación API - IoT Building Simulator

## Descripción General
El IoT Building Simulator es una API REST que permite simular y gestionar dispositivos IoT en edificios virtuales. La API proporciona endpoints para crear edificios, gestionar dispositivos y ejecutar simulaciones.

## Base URL
```
http://api.yourdomain.com
```

## Autenticación
Actualmente la API no requiere autenticación.

## Endpoints

### Edificios

#### 1. Crear Edificio
Crea un nuevo edificio en la simulación.

```http
POST /api/buildings
Content-Type: application/json

{
    "building_id": "office_01",
    "name": "Torre Corporativa A",
    "type": "office",
    "floors": 10,
    "rooms_per_floor": 8,
    "devices_per_room": {
        "temperature_sensor": 1,
        "hvac_controller": 1,
        "motion_sensor": 1,
        "smart_plug": 4
    }
}
```

**Respuesta Exitosa (200)**
```json
{
    "building_id": "office_01",
    "message": "Building created successfully"
}
```

#### 2. Obtener Edificios
Lista todos los edificios disponibles.

```http
GET /api/buildings
```

**Respuesta Exitosa (200)**
```json
{
    "buildings": [
        {
            "building_id": "office_01",
            "name": "Torre Corporativa A",
            "type": "office",
            "floors": 10
        }
    ]
}
```

### Simulación

#### 1. Iniciar Simulación
Inicia una nueva simulación.

```http
POST /api/simulation/start
Content-Type: application/json

{
    "duration_hours": 24,
    "time_scale": 1.0,
    "buildings": ["office_01"]
}
```

**Respuesta Exitosa (200)**
```json
{
    "simulation_id": "sim_123456",
    "status": "running"
}
```

#### 2. Estado de Simulación
Obtiene el estado actual de una simulación.

```http
GET /api/simulation/{simulation_id}/status
```

**Respuesta Exitosa (200)**
```json
{
    "simulation_id": "sim_123456",
    "status": "running",
    "elapsed_time": "02:30:15",
    "active_buildings": 1
}
```

### Dispositivos

#### 1. Obtener Datos de Dispositivo
Obtiene las lecturas de un dispositivo específico.

```http
GET /api/devices/{device_id}/readings
```

Parámetros de consulta:
- `start_time`: Timestamp inicial (ISO 8601)
- `end_time`: Timestamp final (ISO 8601)
- `limit`: Número máximo de lecturas

**Respuesta Exitosa (200)**
```json
{
    "device_id": "temp_sensor_01",
    "readings": [
        {
            "timestamp": "2024-03-20T14:30:00Z",
            "value": 23.5,
            "unit": "celsius"
        }
    ]
}
```

#### 2. Actualizar Configuración de Dispositivo
Actualiza la configuración de un dispositivo.

```http
PATCH /api/devices/{device_id}/config
Content-Type: application/json

{
    "update_interval": 300,
    "threshold": 25.0
}
```

### WebSocket

La API proporciona una conexión WebSocket para recibir actualizaciones en tiempo real.

```
ws://api.yourdomain.com/ws/simulation/{simulation_id}
```

Eventos emitidos:
- `device_update`: Nuevas lecturas de dispositivos
- `simulation_status`: Cambios en el estado de la simulación
- `alert`: Alertas y eventos importantes

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 400 | Solicitud inválida |
| 404 | Recurso no encontrado |
| 500 | Error interno del servidor |

## Límites de Uso
- Máximo 100 solicitudes por minuto por IP
- Máximo 1000 dispositivos por edificio
- Máximo 50 edificios por simulación

## Ejemplos de Uso

### Curl
```bash
# Crear un edificio
curl -X POST http://api.yourdomain.com/api/buildings \
  -H "Content-Type: application/json" \
  -d @building_config.json

# Iniciar simulación
curl -X POST http://api.yourdomain.com/api/simulation/start \
  -H "Content-Type: application/json" \
  -d '{"duration_hours": 24}'
```

### Python
```python
import requests

# Crear edificio
response = requests.post(
    "http://api.yourdomain.com/api/buildings",
    json={
        "name": "Edificio Test",
        "type": "office",
        "floors": 5
    }
)

# Iniciar simulación
simulation = requests.post(
    "http://api.yourdomain.com/api/simulation/start",
    json={"duration_hours": 24}
)
```

## Notas Adicionales

### Versionado
La API sigue versionado semántico. La versión actual es v1.0.0.

### Formato de Datos
- Todas las timestamps deben estar en formato ISO 8601
- Los valores numéricos usan el punto como separador decimal
- Las unidades de medida siguen el sistema métrico internacional

### Buenas Prácticas
1. Implementar manejo de errores robusto
2. Utilizar rate limiting adecuado
3. Mantener las conexiones WebSocket activas
4. Almacenar los IDs de simulación de manera segura

### Soporte
Para reportar problemas o solicitar ayuda:
- Abrir un issue en GitHub
- Contactar al equipo de desarrollo
- Consultar la documentación completa 