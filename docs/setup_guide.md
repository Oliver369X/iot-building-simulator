# Guía de Configuración y Ejecución - IoT Building Simulator

## 1. Configuración Inicial

### 1.1 Variables de Entorno
Crea o modifica el archivo `.env`:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/iot_simulator
DB_HOST=localhost
DB_PORT=5432
DB_NAME=iot_simulator
DB_USER=postgres
DB_PASSWORD=your_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### 1.2 Configuración de Edificios
Modifica `config/buildings/office_building.yaml`:

```yaml
building:
  name: "Edificio Principal"
  type: "office"
  floors: 5  # Modifica el número de pisos
  rooms_per_floor: 4  # Modifica habitaciones por piso
  devices_per_room:
    temperature_sensor: 1  # Cantidad de sensores de temperatura por habitación
    hvac_controller: 1     # Cantidad de controladores HVAC
    motion_sensor: 1       # Sensores de movimiento
    smart_plug: 2          # Enchufes inteligentes

simulation:
  time_scale: 1.0         # Velocidad de simulación (2.0 = doble velocidad)
  update_interval: 300    # Intervalo de actualización en segundos
```

## 2. Instalación

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Inicializar base de datos
python -m src.database.init_db
```

## 3. Ejecución

### 3.1 Iniciar el Servidor API
```bash
# En una terminal
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3.2 Ejecutar una Simulación
```bash
# En otra terminal
python run_simulation.py -c config/buildings/office_building.yaml
```

## 4. Monitoreo

### 4.1 Dashboard Web
Accede al dashboard en:
```
http://localhost:8000/dashboard
```

### 4.2 API Endpoints
- Lista de edificios: `http://localhost:8000/api/buildings`
- Estado de simulación: `http://localhost:8000/api/simulation/status`
- Datos de dispositivos: `http://localhost:8000/api/devices/{device_id}/readings`

### 4.3 Logs
Los logs se encuentran en:
```
logs/simulation.log
```

## 5. Modificación de Parámetros

### 5.1 Límites del Sistema
Modifica `src/config/limits.py`:

```python
SYSTEM_LIMITS = {
    'max_buildings': 50,          # Máximo número de edificios
    'max_floors_per_building': 100,  # Máximo pisos por edificio
    'max_rooms_per_floor': 50,    # Máximo habitaciones por piso
    'max_devices_per_room': 20,   # Máximo dispositivos por habitación
    'max_total_devices': 10000    # Máximo dispositivos en total
}
```

### 5.2 Configuración de Dispositivos
Modifica `src/config/devices.py`:

```python
DEVICE_CONFIGS = {
    'temperature_sensor': {
        'update_interval': 300,    # Intervalo de actualización en segundos
        'range_min': 18,          # Temperatura mínima
        'range_max': 30           # Temperatura máxima
    },
    'hvac_controller': {
        'power_consumption': {
            'idle': 50,           # Consumo en modo espera (W)
            'active': 1500        # Consumo en modo activo (W)
        }
    }
    # ... otros dispositivos
}
```

## 6. Visualización de Dispositivos

### 6.1 Consola de Monitoreo
```bash
python src/tools/monitor.py --building-id building_01
```

### 6.2 Exportar Datos
```bash
python src/tools/export_data.py --format csv --output-dir ./data
```

## 7. Solución de Problemas

### 7.1 Verificar Estado del Sistema
```bash
python src/tools/system_check.py
```

### 7.2 Problemas Comunes

1. **Error de Conexión a Base de Datos**
   ```bash
   python src/database/init_db.py --check-connection
   ```

2. **Reiniciar Simulación**
   ```bash
   python src/tools/simulation_manager.py --reset
   ```

3. **Limpiar Datos**
   ```bash
   python src/tools/cleanup.py --all
   ```

## 8. Desarrollo

### 8.1 Ejecutar Tests
```bash
pytest tests/
```

### 8.2 Generar Datos de Prueba
```bash
python src/tools/generate_test_data.py
``` 