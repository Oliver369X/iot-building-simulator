# Manejo de Errores - IoT Building Simulator

## Estructura de Errores
Todos los errores siguen esta estructura:

```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Descripción del error",
        "details": {
            "field": "Campo específico con error",
            "reason": "Razón específica"
        }
    }
}
```

## Códigos de Error Específicos

### Errores de Edificio (400-499)
| Código | Mensaje | Descripción |
|--------|---------|-------------|
| 400 | INVALID_BUILDING_CONFIG | Configuración de edificio inválida |
| 401 | BUILDING_NOT_FOUND | Edificio no encontrado |
| 402 | DUPLICATE_BUILDING_ID | ID de edificio duplicado |
| 403 | MAX_FLOORS_EXCEEDED | Número máximo de pisos excedido |

### Errores de Dispositivo (500-599)
| Código | Mensaje | Descripción |
|--------|---------|-------------|
| 500 | DEVICE_NOT_FOUND | Dispositivo no encontrado |
| 501 | INVALID_DEVICE_TYPE | Tipo de dispositivo no soportado |
| 502 | DEVICE_OFFLINE | Dispositivo fuera de línea |
| 503 | MAX_DEVICES_EXCEEDED | Límite de dispositivos excedido |

### Errores de Simulación (600-699)
| Código | Mensaje | Descripción |
|--------|---------|-------------|
| 600 | SIMULATION_NOT_FOUND | Simulación no encontrada |
| 601 | INVALID_DURATION | Duración de simulación inválida |
| 602 | SIMULATION_ALREADY_RUNNING | Ya existe una simulación activa |
| 603 | RESOURCE_EXHAUSTED | Recursos de simulación agotados |

## Ejemplos de Manejo de Errores

### Python
```python
try:
    response = requests.post(
        "http://api.yourdomain.com/api/buildings",
        json=building_config
    )
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    error_data = e.response.json()
    print(f"Error {error_data['error']['code']}: {error_data['error']['message']}")
```

### JavaScript
```javascript
fetch('http://api.yourdomain.com/api/buildings', {
    method: 'POST',
    body: JSON.stringify(buildingConfig)
})
.then(response => {
    if (!response.ok) {
        return response.json().then(err => {
            throw new Error(`${err.error.code}: ${err.error.message}`);
        });
    }
    return response.json();
})
.catch(error => console.error('Error:', error));
```

## Buenas Prácticas

1. **Validación Preventiva**
   - Validar datos antes de enviar requests
   - Verificar formatos y tipos de datos
   - Comprobar límites y restricciones

2. **Manejo de Reintentos**
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
   def create_building(config):
       response = requests.post(
           "http://api.yourdomain.com/api/buildings",
           json=config
       )
       response.raise_for_status()
       return response.json()
   ```

3. **Logging de Errores**
   ```python
   import logging

   logging.error(f"Error en simulación: {error_data['error']['code']}", extra={
       'error_details': error_data['error']['details'],
       'simulation_id': sim_id
   })
   ```

4. **Manejo de Timeout**
   ```python
   try:
       response = requests.post(
           "http://api.yourdomain.com/api/simulation/start",
           json=config,
           timeout=(5, 30)  # (connect timeout, read timeout)
       )
   except requests.exceptions.Timeout:
       logger.error("Timeout al iniciar simulación")
   ``` 