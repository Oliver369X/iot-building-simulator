# Guía de Usuario - IoT Building Simulator

## Introducción

El IoT Building Simulator es una herramienta avanzada para la simulación de ecosistemas IoT en edificios inteligentes. Permite no solo generar datos realistas para pruebas y desarrollo, sino también gestionar individualmente dispositivos, programar su encendido y apagado, ejecutar simulaciones más realistas y detalladas, y administrar de forma granular habitaciones y pisos. Esta guía te ayudará a configurar, ejecutar y gestionar simulaciones complejas, aprovechando la capacidad de simulación individualizada y el soporte para una gama más amplia de tipos de dispositivos.

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/tu-usuario/iot-building-simulator.git
cd iot-building-simulator
```

2. Crea un entorno virtual e instala las dependencias:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuración

### Estructura de Configuración

Los edificios se configuran mediante archivos YAML en el directorio `config/buildings/`. Cada archivo define:

- Información básica del edificio
- Configuración de pisos y habitaciones
- Tipos de dispositivos y sus parámetros
- Patrones de tráfico y ocupación

Ejemplo básico:
```yaml
building_id: "office_01"
name: "Edificio de Oficinas"
location:
  city: "Madrid"
  country: "España"

config:
  floors: 5
  max_occupancy: 200

room_templates:
  office:
    area: 25
    devices:
      - type: "temperature_sensor"
      - type: "motion_sensor"
```

### Configuración Avanzada de Dispositivos

Además de la configuración básica por tipo, puedes definir parámetros específicos para dispositivos individuales dentro de las plantillas de habitación o directamente en la definición de una habitación.

**Ejemplo de Configuración de Dispositivo Individual:**
```yaml
room_templates:
 office_conference:
   area: 40
   devices:
     - type: "hvac_controller"
       id: "hvac_conf_01"
       initial_state: "on" # 'on', 'off'
       set_point: 22.5
       schedule: # Programación de encendido/apagado
         - action: "on"
           time: "08:00:00" # Hora de encendido
           days: ["mon", "tue", "wed", "thu", "fri"]
         - action: "off"
           time: "18:00:00" # Hora de apagado
           days: ["mon", "tue", "wed", "thu", "fri"]
     - type: "smart_plug"
       id: "plug_printer_01"
       initial_state: "off"
       # Otros parámetros específicos del smart_plug
```

**Parámetros Comunes para Configuración Avanzada:**
- `id`: (Opcional) Un identificador único para el dispositivo si necesitas referenciarlo específicamente.
- `initial_state`: Define el estado inicial del dispositivo (`on` o `off`).
- `schedule`: Una lista de acciones programadas. Cada acción incluye:
   - `action`: `"on"` o `"off"`.
   - `time`: Hora de la acción en formato `HH:MM:SS`.
   - `days`: (Opcional) Lista de días de la semana para aplicar la acción (ej: `["mon", "fri"]`). Si se omite, se aplica todos los días.
   - `date`: (Opcional) Fecha específica en formato `YYYY-MM-DD` para una acción única.

### Gestión Detallada de Espacios (Pisos y Habitaciones)

Puedes definir propiedades más específicas para pisos y habitaciones para simulaciones más realistas.

**Ejemplo de Configuración Detallada de Piso/Habitación:**
```yaml
floors_config:
 - floor_number: 1
   name: "Planta Baja"
   occupancy_profile: "office_hours_ground" # Perfil de ocupación específico
   rooms:
     - room_id: "lobby_01"
       name: "Recepción Principal"
       template: "lobby_template"
       area: 100
       max_occupants: 15
       # Dispositivos específicos para esta habitación, sobreescribiendo o añadiendo a la plantilla
       devices:
         - type: "access_control"
           id: "main_entrance_access"
## Gestión Avanzada de Dispositivos y Espacios

Una de las mejoras clave del simulador es la capacidad de gestionar dispositivos y espacios de forma individual y dinámica durante una simulación activa. Esto se logra principalmente a través de la API (ver [`API Documentation`](api_documentation.md)).

### Control Individual de Dispositivos

Puedes encender, apagar o modificar parámetros de dispositivos específicos en tiempo real.

**Ejemplos de Acciones (vía API):**
- **Encender/Apagar un dispositivo:**
  - `PATCH /api/devices/{device_id}/state` con `{"state": "on"}` o `{"state": "off"}`.
- **Ajustar el setpoint de un termostato:**
  - `PATCH /api/devices/{hvac_id}/config` con `{"set_point": 23.0}`.
- **Modificar la programación de un dispositivo:**
  - `PUT /api/devices/{device_id}/schedule` con la nueva estructura de programación.

### Gestión Dinámica de Espacios

Aunque la estructura del edificio (pisos, habitaciones) se define inicialmente, ciertos aspectos pueden ser influenciados o consultados dinámicamente.

**Ejemplos (vía API):**
- **Obtener el estado actual de una habitación (ocupación, dispositivos activos):**
  - `GET /api/rooms/{room_id}/status`
- **Simular eventos en una habitación (ej. entrada/salida de ocupantes):**
  - `POST /api/rooms/{room_id}/event` con `{"event_type": "occupancy_change", "occupants": 5}`

Estas capacidades permiten crear escenarios de simulación mucho más interactivos y realistas, donde puedes reaccionar a eventos simulados o probar la respuesta del sistema a cambios manuales.
           rules: "employees_only_after_hours"
 - floor_number: 2
   name: "Oficinas Ejecutivas"
   # ... más configuraciones de piso
```
Esto permite un control más fino sobre la estructura y el comportamiento de cada parte del edificio.

### Tipos de Dispositivos Soportados

1. **Sensores de Clima**:
   - `temperature_sensor`: Temperatura ambiente
   - `humidity_sensor`: Humedad relativa
   - `hvac_controller`: Control de climatización

2. **Dispositivos de Seguridad**:
   - `motion_sensor`: Detección de movimiento
   - `security_camera`: Cámaras de vigilancia
   - `access_control`: Control de acceso

3. **Dispositivos de Energía**:
   - `power_meter`: Medidor de consumo
   - `smart_plug`: Enchufes inteligentes
   - `solar_panel`: Paneles solares

## Ejecución de Simulaciones

### Ejemplo Básico

```python
from src.simulator.engine import SimulationEngine
from datetime import timedelta

# Inicializa el motor
engine = SimulationEngine(config_path="config/buildings/office_building.yaml")

# Ejecuta simulación por 24 horas
engine.start(duration=timedelta(hours=24))
```

### Script de Ejemplo

Puedes usar el script de ejemplo incluido:
```bash
python examples/run_simulation.py
```

## Análisis de Datos

### Carga y Análisis de Datos

```python
from utils.data_analyzer import IoTDataAnalyzer

analyzer = IoTDataAnalyzer("./data")
df = analyzer.load_device_data(start_date, end_date)

# Analiza patrones de temperatura
temp_patterns = analyzer.analyze_temperature_patterns(df)
print(f"Temperatura promedio: {temp_patterns['average_temp']}°C")

# Genera gráficos
analyzer.plot_temperature_distribution(df, "temp_distribution.png")
analyzer.plot_energy_over_time(df, "energy_consumption.png")
```

## Logging y Monitoreo

Los logs se almacenan en el directorio `logs/` en formato JSON, incluyendo:
- Eventos de dispositivos
- Estados de simulación
- Errores y advertencias

Ejemplo de configuración de logging:
```python
from src.utils.logger_config import setup_logging

setup_logging(
    log_dir="logs",
    level="INFO",
    json_format=True
)
```

## Solución de Problemas

### Problemas Comunes

1. **Error al cargar configuración**:
   - Verifica la sintaxis YAML
   - Asegúrate de que todos los campos requeridos estén presentes

2. **Datos no generados**:
   - Revisa los permisos del directorio de datos
   - Verifica la configuración de dispositivos

3. **Rendimiento lento**:
   - Reduce el número de dispositivos
   - Ajusta los intervalos de actualización
   - Considera usar un time_scale mayor

### Contacto y Soporte

Para reportar problemas o solicitar ayuda:
- Abre un issue en GitHub
- Consulta la documentación completa
- Contacta al equipo de desarrollo

## Próximos Pasos

- Explora configuraciones más complejas
- Implementa patrones de tráfico personalizados
- Integra con sistemas externos
- Contribuye al desarrollo 