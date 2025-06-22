# Guía de Usuario Avanzada - IoT Building Simulator

## 1. Introducción

Bienvenido al IoT Building Simulator, una plataforma robusta diseñada para la simulación detallada y la gestión avanzada de ecosistemas de dispositivos IoT en edificios inteligentes. Esta herramienta ha evolucionado para ofrecer un control granular sobre dispositivos individuales, capacidades de programación de encendido/apagado, simulaciones de alta fidelidad y una gestión precisa de pisos y habitaciones.

Esta guía te proporcionará los conocimientos necesarios para:
- Configurar entornos de simulación complejos.
- Gestionar y programar dispositivos IoT de forma individual.
- Ejecutar simulaciones realistas y personalizadas.
- Administrar la estructura del edificio (pisos, habitaciones) con detalle.
- Comprender la interacción con la API para control dinámico.
- Utilizar nuevos tipos de dispositivos soportados.

## 2. Requisitos Previos e Instalación

### 2.1. Requisitos del Sistema
- Python 3.8 o superior
- Git
- (Otros requisitos específicos, ej. dependencias de sistema si las hubiera)

### 2.2. Instalación
1.  Clona el repositorio:
    ```bash
    git clone https://github.com/tu-usuario/iot-building-simulator.git
    cd iot-building-simulator
    ```
2.  Crea un entorno virtual e instala las dependencias:
    ```bash
    python -m venv venv
    # En Windows: venv\Scripts\activate
    # En macOS/Linux: source venv/bin/activate
    source venv/bin/activate 
    pip install -r requirements.txt
    ```
3.  (Opcional) Configura la base de datos si es necesario para persistencia de datos de simulación (ver sección de Base de Datos).

## 3. Configuración de la Simulación

La configuración de las simulaciones se realiza principalmente a través de archivos YAML, permitiendo una definición detallada de los edificios, sus componentes y los dispositivos IoT.

### 3.1. Estructura del Archivo de Configuración Principal (`config.yaml`)
El archivo principal (ej. [`config.yaml`](../../config.yaml)) define los edificios a simular y parámetros globales.

### 3.2. Configuración del Edificio
Cada edificio se define con sus características generales, estructura de pisos y habitaciones, y plantillas de dispositivos.

**Ejemplo Básico de Definición de Edificio:**
```yaml
building_id: "smart_office_complex_a"
name: "Complejo de Oficinas Inteligentes Alfa"
location:
  address: "123 Tech Avenue"
  city: "Innovate City"
  country: "Techland"
timezone: "America/New_York"

simulation_settings:
  time_scale: 1 # 1 = tiempo real, >1 = acelerado, <1 = ralentizado
  default_update_interval_seconds: 60 # Intervalo por defecto para dispositivos

floors:
  # ... definición de pisos y habitaciones
```

### 3.3. Configuración Detallada de Pisos y Habitaciones
Permite un control granular sobre cada espacio.

```yaml
floors:
  - floor_id: "ground_floor"
    floor_number: 0
    name: "Planta Baja"
    description: "Área de recepción, lobby y servicios comunes."
    rooms:
      - room_id: "lobby_001"
        name: "Lobby Principal"
        area_m2: 150
        max_occupancy: 50
        room_type: "public_space"
        # Dispositivos específicos para esta habitación
        devices:
          - device_id: "lobby_temp_01"
            type: "temperature_sensor"
            # ... más parámetros
          - device_id: "main_door_access"
            type: "access_control"
            # ... más parámetros
      # ... más habitaciones en esta planta
  - floor_id: "first_floor_offices"
    floor_number: 1
    name: "Primera Planta - Oficinas"
    # ...
```

### 3.4. Configuración Avanzada de Dispositivos y Plantillas

Para una gestión eficiente, puedes usar plantillas de dispositivos y luego personalizarlas para instancias específicas dentro de las habitaciones.

**Definición de Plantillas de Dispositivos (Opcional, en una sección `device_templates`):**
```yaml
device_templates:
  standard_office_light:
    type: "smart_light"
    dimmable: true
    color_temperature_range_k: [2700, 5000]
    default_on_brightness: 0.7
    schedule:
      - { action: "on", value: 0.7, time: "08:00:00", days: ["mon","tue","wed","thu","fri"] }
      - { action: "off", time: "18:30:00", days: ["mon","tue","wed","thu","fri"] }
  
  meeting_room_hvac:
    type: "smart_thermostat"
    min_temp_setpoint: 18.0
    max_temp_setpoint: 26.0
    modes: ["cool", "heat", "fan_only", "off"]
    default_mode: "auto"
    initial_state: 22.0 # Setpoint inicial
    presence_detection_source_device_id: null # Se puede sobreescribir por habitación
    schedule:
      - { action: "set_temperature", value: 22.0, time: "08:30:00", days: ["mon","tue","wed","thu","fri"] }
      - { action: "set_temperature", value: 24.0, time: "17:30:00", days: ["mon","tue","wed","thu","fri"] } # Standby temp
```

**Uso y Personalización de Dispositivos en Habitaciones:**
Dentro de la definición de una habitación, puedes instanciar dispositivos usando plantillas o definiéndolos completamente. Los parámetros definidos directamente en la instancia del dispositivo en la habitación **sobrescriben** los de la plantilla.

```yaml
# ... (dentro de la definición de un piso)
    rooms:
      - room_id: "office_101"
        name: "Oficina Estándar 101"
        area_m2: 20
        devices:
          - device_id: "light_office101"
            template: "standard_office_light" # Usa la plantilla
            name: "Luz Principal Oficina 101"
            # Sin más parámetros, usa todo de la plantilla.
            
          - device_id: "hvac_office101"
            type: "smart_thermostat" # Sin plantilla, definición completa
            name: "Climatizador Oficina 101"
            initial_state: 21.5 # Setpoint inicial específico
            update_interval_seconds: 120
            schedule:
              - { action: "set_temperature", value: 21.5, time: "07:30:00", days: ["mon","tue","wed","thu","fri"] }
              - { action: "set_temperature", value: 23.0, time: "18:00:00", days: ["mon","tue","wed","thu","fri"] }

      - room_id: "meeting_room_A"
        name: "Sala de Reuniones A"
        area_m2: 35
        devices:
          - device_id: "light_meetingA_main"
            template: "standard_office_light"
            name: "Luz Principal Sala A"
            # Sobrescribir parte de la programación de la plantilla
            schedule: # Esta programación REEMPLAZA la de la plantilla para esta instancia
              - { action: "on", value: 0.9, time: "07:00:00", days: ["mon","tue","wed","thu","fri"] }
              - { action: "off", time: "20:00:00", days: ["mon","tue","wed","thu","fri"] }
              
          - device_id: "hvac_meetingA"
            template: "meeting_room_hvac"
            name: "Climatizador Sala A"
            # Sobrescribir y añadir parámetros
            initial_state: 21.0
            presence_detection_source_device_id: "motion_meetingA" # Enlazar a sensor de movimiento
            
          - device_id: "motion_meetingA"
            type: "motion_sensor"
            name: "Sensor Movimiento Sala A"
            detection_range_m: 8
```

**Parámetros Clave para Configuración Individual de Dispositivos:**
- `device_id`: Identificador único y obligatorio para cada instancia de dispositivo.
- `type`: Tipo de dispositivo (ej. `temperature_sensor`, `smart_light`). Requerido si no se usa plantilla.
- `template`: (Opcional) Nombre de una plantilla de dispositivo definida en `device_templates`.
- `name`: Nombre descriptivo (ej. "Sensor Temperatura Sala Reuniones").
- `initial_state`: (Opcional) Estado inicial del dispositivo. El formato depende del tipo:
    - Para luces/enchufes: `"on"`, `"off"`.
    - Para termostatos: un valor numérico como `22.0` (setpoint), o un modo como `"cool"`.
    - Para sensores: pueden no tener un `initial_state` controlable, o podría ser un valor inicial de lectura.
- `update_interval_seconds`: (Opcional) Frecuencia con la que el dispositivo genera/actualiza datos. Sobrescribe el default del edificio o de la plantilla.
- `schedule`: (Opcional) Una lista de acciones programadas. Si se define aquí, **reemplaza completamente** la programación de la plantilla para esta instancia.
    - **Atributos de Programación:**
        - `action`: La acción a realizar (ej. `on`, `off`, `set_value`, `set_brightness`, `change_mode`, `set_temperature`).
        - `value`: (Opcional) El valor asociado a la acción (ej. `22.5` para temperatura, `0.75` para brillo).
        - `time`: Hora de la acción en formato `HH:MM:SS`.
        - `days`: (Opcional) Lista de días (`mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`). Si se omite, se aplica todos los días.
        - `date`: (Opcional) Fecha específica `YYYY-MM-DD` para una acción única.
        - `condition`: (Opcional) Una referencia a una condición global o del edificio (ej. `building_occupied`, `room_unoccupied_for_15min`) que debe cumplirse para que la acción se ejecute. La lógica de condiciones es una característica avanzada.
- *Otros parámetros específicos del tipo de dispositivo*: Cualquier parámetro listado en la Sección 4 (Tipos de Dispositivos) puede ser definido aquí para sobrescribir valores de plantilla o defaults.

## 4. Tipos de Dispositivos Soportados (Expandido)

El simulador soporta una variedad creciente de dispositivos:

### 4.1. Sensores
- **`temperature_sensor`**: Mide la temperatura ambiente.
  - Parámetros: `min_val`, `max_val`, `accuracy`, `unit` (`C` o `F`).
- **`humidity_sensor`**: Mide la humedad relativa.
  - Parámetros: `min_val`, `max_val`, `accuracy`.
- **`motion_sensor`**: Detecta movimiento.
  - Parámetros: `detection_range_m`, `sensitivity`. Genera eventos `motion_detected`, `no_motion`.
- **`occupancy_sensor`**: Estima el número de ocupantes en un área.
  - Parámetros: `max_occupancy_count`, `detection_method` (`infrared`, `ultrasonic`, `camera_based`).
- **`light_sensor` (Luxómetro)**: Mide el nivel de luz ambiental.
  - Parámetros: `unit` (`lux`).
- **`co2_sensor`**: Mide la concentración de CO2.
  - Parámetros: `unit` (`ppm`), `normal_range` ([300, 1000]), `high_level_threshold` (2000).
- **`voc_sensor` (Compuestos Orgánicos Volátiles)**: Mide niveles de VOCs.
  - Parámetros: `unit` (`ppb` o `µg/m³`), `voc_type_sensitivity` (lista de VOCs a los que es sensible).
- **`air_quality_index_sensor` (AQI)**: Calcula un índice de calidad del aire basado en múltiples contaminantes (puede ser un dispositivo virtual que agrega datos de otros sensores como CO2, VOC, PM2.5).
  - Parámetros: `pollutants_to_monitor` ([`co2`, `voc`, `pm25`]), `calculation_standard` (`epa`, `europe`).
- **`door_window_sensor`**: Detecta si una puerta o ventana está abierta o cerrada.
  - Genera estados `open`, `closed`. Puede tener un parámetro `delay_notification_seconds`.
- **`water_leak_sensor`**: Detecta fugas de agua.
  - Genera evento `leak_detected`.
- **`smoke_detector` / `fire_detector`**: Detecta humo o indicadores de fuego.
  - Genera evento `smoke_detected` o `fire_alarm`. Puede tener `sensitivity_level`.
- **`glass_break_sensor`**: Detecta la rotura de cristales.
  - Genera evento `glass_break_detected`.
- **`power_meter_sensor`**: Sub-componente de `smart_plug` o `hvac`, o independiente para medir consumo de un circuito.
  - Parámetros: `measurement_type` (`voltage`, `current`, `power_active`, `power_apparent`, `energy_kwh`).

### 4.2. Actuadores y Controladores
- **`hvac_controller` (Climatización Estándar)**: Controla sistemas de calefacción, ventilación y aire acondicionado.
  - Parámetros: `min_temp_setpoint`, `max_temp_setpoint`, `modes` (`cool`, `heat`, `fan_only`, `auto`, `off`), `fan_speeds` (`low`, `medium`, `high`, `auto`), `deadband_celsius` (ej. 0.5).
  - Acciones programables: `set_temperature`, `set_mode`, `set_fan_speed`.
- **`smart_thermostat` (Termostato Inteligente)**: Versión avanzada del HVAC controller, puede incluir aprendizaje de patrones, detección de presencia para ahorro de energía.
  - Hereda parámetros de `hvac_controller`.
  - Parámetros Adicionales: `learning_mode` (true/false), `presence_detection_source_device_id` (ID de un `motion_sensor` o `occupancy_sensor`), `eco_mode_offset_celsius` (ej. 2 grados de offset para modo eco).
  - Lógica interna más compleja para auto-ajustes.
- **`smart_light`**: Controla la iluminación.
  - Parámetros: `dimmable` (true/false), `color_temperature_range_k` (si aplica, ej. [2700, 6500]), `max_brightness_lumens`, `default_on_brightness` (0.0-1.0).
  - Acciones: `on`, `off`, `set_brightness` (0.0-1.0), `set_color_temperature` (si aplica), `toggle`.
- **`smart_plug`**: Controla el suministro eléctrico a dispositivos conectados.
  - Parámetros: `max_power_w`, `default_state_after_power_loss` (`on`, `off`, `last_state`).
  - Acciones: `on`, `off`, `toggle`. Puede incluir `power_meter_sensor` integrado.
- **`window_actuator` / `blind_actuator` / `shade_actuator`**: Controla la apertura/cierre de ventanas, persianas o cortinas motorizadas.
  - Parámetros: `travel_time_seconds` (tiempo total para abrir/cerrar).
  - Acciones: `open`, `close`, `set_position` (0.0-1.0, donde 0.0 es cerrado y 1.0 es totalmente abierto).
- **`access_control_system`**: Gestiona el acceso a través de puertas, torniquetes, etc.
  - Parámetros: `reader_type` (`card`, `keypad`, `biometric`, `nfc`), `lock_type` (`fail_safe`, `fail_secure`), `auth_methods` (lista de métodos soportados).
  - Eventos: `access_granted`, `access_denied`, `door_forced_open`, `door_left_open`.
  - Puede interactuar con `door_window_sensor`.
- **`irrigation_controller`**: Controla sistemas de riego.
  - Parámetros: `zones` (lista de zonas, cada una con `id` y `description`), `valve_type`.
  - Acciones: `start_zone_irrigation` (con `zone_id`, `duration_minutes`), `stop_zone_irrigation`.

### 4.3. Dispositivos de Seguridad Avanzados
- **`security_camera`**: Simula cámaras de vigilancia.
  - Parámetros: `resolution` (ej. "1920x1080"), `fov_degrees` (ej. 90), `recording_mode` (`continuous`, `motion_triggered`, `scheduled`), `storage_type` (`local_sd`, `cloud`), `night_vision` (true/false), `audio_capture` (true/false).
  - Puede generar eventos (`motion_detected_in_frame`, `audio_event_detected`) o "archivos de video simulados" (metadatos como timestamp, duración, tamaño).
- **`alarm_panel`**: Panel central para sistemas de alarma.
  - Parámetros: `modes` (`armed_away`, `armed_stay`, `disarmed`), `entry_delay_seconds`, `exit_delay_seconds`.
  - Interactúa con sensores (`motion_sensor`, `door_window_sensor`, `glass_break_sensor`) para disparar alarmas.
  - Eventos: `alarm_triggered`, `panel_armed`, `panel_disarmed`.
- **`siren_strobe`**: Dispositivo de sirena y/o luz estroboscópica.
  - Acciones: `activate` (con `duration_seconds`, `sound_pattern`, `strobe_pattern`), `deactivate`.

### 4.4. Dispositivos de Gestión de Energía Avanzados
- **`ev_charger` (Cargador de Vehículo Eléctrico)**: Simula estaciones de carga para EVs.
  - Parámetros: `max_power_kw`, `connector_type` (`type2`, `ccs`, `chademo`), `charge_mode` (`smart`, `manual`).
  - Eventos: `ev_connected`, `ev_disconnected`, `charge_started`, `charge_completed`, `charge_fault`.
  - Acciones: `start_charging`, `stop_charging`, `set_charge_limit_kwh` o `set_charge_limit_soc_percent`.
- **`solar_panel_system`**: Simula la generación de energía solar.
  - Parámetros: `capacity_kwp`, `efficiency_percent`, `orientation_degrees`, `tilt_degrees`, `inverter_efficiency_percent`.
  - Su salida dependerá de un modelo de irradiancia solar simulado (puede ser un input al simulador).
- **`battery_storage_system` (BESS)**: Simula el almacenamiento de energía en baterías.
  - Parámetros: `capacity_kwh`, `max_charge_rate_kw`, `max_discharge_rate_kw`, `round_trip_efficiency_percent`, `depth_of_discharge_percent`.
  - Acciones: `charge`, `discharge`, `set_mode` (`idle`, `charge_from_grid`, `charge_from_solar`, `discharge_to_load`, `discharge_to_grid`).

*(Esta lista es representativa y puede expandirse continuamente. La configuración YAML para cada tipo definirá los parámetros específicos que el motor de simulación utilizará.)*

## 5. Ejecución de Simulaciones Realistas y Detalladas

El simulador está diseñado para ejecutar escenarios complejos que reflejen de cerca el comportamiento de edificios inteligentes reales. Esto implica no solo la configuración detallada de dispositivos y espacios, sino también la forma en que se ejecuta y gestiona la simulación.

### 5.1. Inicio de una Simulación

Las simulaciones se pueden iniciar y controlar mediante scripts de Python utilizando el motor de simulación, o a través de los endpoints de la API (ver Sección 6.3).

**Ejemplo de Script Python Avanzado:**
```python
from src.simulator.engine import SimulationEngine
from src.core.building import Building # Asumiendo clases para construir dinámicamente
# ... otras importaciones necesarias para definir edificios, pisos, habitaciones, dispositivos programáticamente
from datetime import datetime, timedelta

# Opción 1: Cargar desde archivo de configuración YAML
engine = SimulationEngine(config_path="configs/detailed_office_simulation.yaml")

# Opción 2: Construir la configuración del edificio programáticamente (ejemplo conceptual)
# building_config = { ... } # Diccionario con la estructura completa
# engine = SimulationEngine(config_data=building_config)

# Definir parámetros de la simulación
start_datetime = datetime(2024, 8, 1, 0, 0, 0) # Fecha y hora de inicio específicas
simulation_duration = timedelta(days=3)        # Duración total
time_scale_factor = 10                         # Simulación 10x más rápida que el tiempo real

print(f"Iniciando simulación desde {start_datetime} por {simulation_duration} (escala: {time_scale_factor}x)")

# Ejecutar la simulación
# El método run_simulation podría aceptar estos parámetros
engine.run_simulation(
    start_time=start_datetime,
    duration=simulation_duration,
    time_scale=time_scale_factor
)

print(f"Simulación completada. Tiempo simulado transcurrido: {engine.get_current_sim_time()}")
# engine.save_results(output_path="simulation_results/") # Ejemplo de cómo se podrían guardar resultados
```

### 5.2. Enfoque en Simulación Individual y Detallada

A diferencia de las simulaciones por lotes que podrían promediar comportamientos, este simulador se centra en:
- **Comportamiento Individual del Dispositivo:** Cada dispositivo opera según su configuración, programación y las interacciones con su entorno (ej. un termostato reacciona a la lectura de su sensor de temperatura asociado, una luz se enciende por un sensor de movimiento).
- **Alta Fidelidad:** El objetivo es modelar las operaciones de los dispositivos y las condiciones ambientales (temperatura, ocupación, niveles de luz) de la manera más realista posible dentro de los límites del modelo.
- **Interacciones Complejas:** Se pueden simular cadenas de eventos, como un sensor de ocupación que activa luces y ajusta el HVAC, o un sistema de gestión de energía que decide cargar baterías basado en la predicción de generación solar y la demanda del edificio.
- **Granularidad Temporal:** Los eventos y las lecturas de datos pueden ocurrir con una alta resolución temporal, permitiendo análisis detallados.

Si bien se pueden ejecutar simulaciones largas para generar grandes conjuntos de datos ("lotes de datos"), la simulación subyacente sigue siendo un cálculo detallado del estado de cada componente individual a lo largo del tiempo.

### 5.3. Creación de Escenarios Realistas

Para lograr simulaciones más realistas, considera:
- **Perfiles de Ocupación:** Define patrones de ocupación variables para diferentes tipos de habitaciones y momentos del día/semana. Esto puede ser parte de la configuración de la habitación o gestionado por un módulo de "eventos de ocupación".
  ```yaml
  # En la configuración de una habitación:
  occupancy_profile: "office_9_to_5_variable"
  # "office_9_to_5_variable" se definiría en otro lugar o sería interpretado por el motor
  # para generar eventos de entrada/salida de personas.
  ```
- **Eventos Externos:** Introduce eventos como cambios climáticos (temperatura exterior, irradiancia solar si se modela), fallos de red eléctrica, o eventos de seguridad manuales para observar la respuesta del sistema.
- **Comportamiento del Usuario Simulado:** Para dispositivos interactivos (ej. un usuario ajustando un termostato manualmente), se podrían modelar "agentes de usuario" o introducir estos cambios vía API.
- **Calibración y Validación:** Si es posible, compara los resultados de la simulación con datos de edificios reales para ajustar los modelos de dispositivos y los parámetros de simulación.

### 5.4. Control y Monitoreo en Tiempo Real (vía API)
Como se detalla en la Sección 6, la API permite:
- **Observar el estado** de la simulación y de dispositivos individuales en tiempo real.
- **Inyectar cambios y eventos** manualmente, lo que es crucial para probar la reactividad del sistema y para escenarios de "qué pasaría si".
- **Pausar, reanudar y detener** la simulación para análisis o ajustes.

## 6. Gestión Avanzada y Control Dinámico (vía API)

La API RESTful del simulador es la interfaz principal para la interacción dinámica durante una simulación activa. Permite un control granular sobre dispositivos, espacios y el estado general de la simulación. Asumimos que la URL base de la API es `http://localhost:8000/api/v1` (ajusta según tu configuración).

### 6.1. Endpoints de Dispositivos (CRUD y Control)

#### 6.1.1. Listar Dispositivos de una Habitación
- **Endpoint:** `GET /rooms/{room_id}/devices`
- **Respuesta Ejemplo (200 OK):**
  ```json
  [
    { "id": "dev_light_001", "room_id": "room_101", "name": "Luz Principal Oficina", "type": "smart_light", "is_active": true },
    { "id": "dev_hvac_001", "room_id": "room_101", "name": "Termostato Oficina", "type": "smart_thermostat", "is_active": true }
  ]
  ```

#### 6.1.2. Crear un Nuevo Dispositivo en una Habitación
- **Endpoint:** `POST /rooms/{room_id}/devices`
- **Request Body Ejemplo:**
  ```json
  {
    "name": "Sensor de Ventana Oficina",
    "type": "door_window_sensor",
    "config": { // Configuración específica del tipo de dispositivo
      "delay_notification_seconds": 10
    },
    "is_active": true
  }
  ```
- **Respuesta Ejemplo (201 Created):**
  ```json
  { "id": "dev_window_001", "room_id": "room_101", "name": "Sensor de Ventana Oficina", ... }
  ```

#### 6.1.3. Obtener Detalles/Estado de un Dispositivo Específico
Recupera la información actual, configuración y estado de un dispositivo.
- **Endpoint:** `GET /devices/{id}`
- **Respuesta Ejemplo (200 OK):**
  ```json
  {
    "id": "dev_light_001",
    "room_id": "room_101",
    "name": "Luz Principal Oficina",
    "type": "smart_light",
    "is_active": true,
    "state": { // Estado actual del dispositivo, leído por el motor de simulación
      "power": "ON",
      "brightness": 80 // Asumiendo porcentaje
    },
    "config": {
      "dimmable": true,
      "color_temperature_range_k": [2700, 6500]
    },
    "last_telemetry": {
      "power_consumption_w": 12.5,
      "timestamp": "2024-08-01T10:30:00Z"
    },
    "last_updated_api": "2024-08-01T10:25:00Z" // Última vez que se actualizó vía API
  }
  ```

#### 6.1.4. Actualizar un Dispositivo
Modifica propiedades generales de un dispositivo como nombre, ubicación (habitación), o su configuración específica.
- **Endpoint:** `PUT /devices/{id}`
- **Request Body Ejemplo:**
  ```json
  {
    "name": "Luz Principal Oficina (LED)",
    "room_id": "room_102", // Mover a otra habitación
    "config": {
      "dimmable": true,
      "color_temperature_range_k": [2200, 6000], // Nueva config
      "default_on_brightness": 0.75
    },
    "is_active": false // Desactivar el dispositivo de la simulación
  }
  ```
- **Respuesta Ejemplo (200 OK):**
  ```json
  { "id": "dev_light_001", "name": "Luz Principal Oficina (LED)", "room_id": "room_102", ... }
  ```

#### 6.1.5. Eliminar un Dispositivo
- **Endpoint:** `DELETE /devices/{id}`
- **Respuesta Ejemplo (204 No Content):** (Sin cuerpo de respuesta)

#### 6.1.6. Enviar Acción/Comando a un Dispositivo
Este endpoint actualiza inmediatamente el campo `state` del dispositivo en la base de datos. El motor de simulación leerá este nuevo estado en su próximo ciclo.
- **Endpoint:** `POST /devices/{id}/actions`
- **Request Body Ejemplo (Encender luz y ajustar brillo):**
  ```json
  {
    "type": "setState", // Tipo de acción genérico para actualizar el estado
    "payload": { // El payload es la nueva estructura del campo 'state'
      "power": "ON",
      "brightness": 100 // Asumiendo porcentaje o valor directo
    }
  }
  ```
- **Request Body Ejemplo (Ajustar termostato):**
  ```json
  {
    "type": "setState",
    "payload": {
      "power": "ON",
      "mode": "cool",
      "target_temp": 21.0
    }
  }
  ```
- **Respuesta Ejemplo (200 OK):**
  ```json
  {
    "device_id": "dev_light_001",
    "action_type": "setState",
    "new_state_applied": {
      "power": "ON",
      "brightness": 100
    },
    "message": "Device state updated. Simulation engine will pick up changes."
  }
  ```

#### 6.1.7. Gestión de Tareas Programadas (Schedules)

- **Obtener Tareas Programadas de un Dispositivo:**
  - **Endpoint:** `GET /devices/{id}/schedules`
  - **Respuesta Ejemplo (200 OK):**
    ```json
    [
      { "id": "sched_001", "device_id": "dev_light_001", "cron_expression": "0 8 * * MON-FRI", "action_payload": {"type": "setState", "payload": {"power": "ON", "brightness": 70}}, "is_enabled": true },
      { "id": "sched_002", "device_id": "dev_light_001", "cron_expression": "0 18 * * MON-FRI", "action_payload": {"type": "setState", "payload": {"power": "OFF"}}, "is_enabled": true }
    ]
    ```

- **Crear una Nueva Tarea Programada:**
  - **Endpoint:** `POST /devices/{id}/schedules`
  - **Request Body Ejemplo:**
    ```json
    {
      "cron_expression": "0 22 * * *", // Todos los días a las 10 PM
      "action_payload": { // Similar al endpoint /actions
        "type": "setState",
        "payload": {"power": "ON", "brightness": 10} // Luz nocturna tenue
      },
      "description": "Encender luz nocturna",
      "is_enabled": true
    }
    ```
  - **Respuesta Ejemplo (201 Created):**
    ```json
    { "id": "sched_003", "device_id": "dev_light_001", "cron_expression": "0 22 * * *", ... }
    ```

- **Actualizar una Tarea Programada:**
  - **Endpoint:** `PUT /schedules/{id}` (ID de la tarea programada)
  - **Request Body Ejemplo:**
    ```json
    {
      "cron_expression": "0 22 * * SUN-THU", // Cambiar días
      "is_enabled": false // Deshabilitar tarea
    }
    ```
  - **Respuesta Ejemplo (200 OK):**
    ```json
    { "id": "sched_003", "cron_expression": "0 22 * * SUN-THU", "is_enabled": false, ... }
    ```

- **Eliminar una Tarea Programada:**
  - **Endpoint:** `DELETE /schedules/{id}`
  - **Respuesta Ejemplo (204 No Content):**

### 6.2. Endpoints de Espacios (Habitaciones/Pisos)

#### 6.2.1. Obtener Estado de una Habitación
Recupera información sobre una habitación, incluyendo su lista de dispositivos y estado de ocupación.
- **Endpoint:** `GET /rooms/{room_id}/status`
- **Respuesta Ejemplo (200 OK):**
  ```json
  {
    "room_id": "lobby_001",
    "name": "Lobby Principal",
    "current_occupancy": 5,
    "temperature_celsius": 23.5,
    "light_level_lux": 300,
    "devices": [
      { "device_id": "lobby_temp_01", "type": "temperature_sensor", "status": {"value": 23.5} },
      { "device_id": "lobby_light_main", "type": "smart_light", "status": {"state": "on", "brightness": 0.7} }
    ]
  }
  ```

#### 6.2.2. Simular Evento en una Habitación
Permite inyectar eventos manuales en la simulación para una habitación específica.
- **Endpoint:** `POST /rooms/{room_id}/event`
- **Request Body Ejemplo (Cambio de ocupación):**
  ```json
  {
    "event_type": "occupancy_change",
    "value": 10 // Nuevo número de ocupantes
  }
  ```
- **Request Body Ejemplo (Puerta abierta):**
  ```json
  {
    "event_type": "door_opened",
    "door_id": "main_entrance_door"
  }
  ```
- **Respuesta Ejemplo (200 OK):**
  ```json
  {
    "room_id": "lobby_001",
    "event_processed": "occupancy_change",
    "details": "Occupancy set to 10",
    "message": "Event simulated successfully."
  }
  ```
*(Endpoints para pisos podrían ser similares o agregados a partir de las habitaciones)*

#### 6.2.3. Gestión de Pisos (CRUD)
Estos endpoints permiten administrar la estructura de pisos de un edificio. Asume que los pisos están referenciados dentro de un contexto de edificio (ej. `/buildings/{building_id}/floors`).

- **Listar Pisos de un Edificio:**
  - **Endpoint:** `GET /buildings/{building_id}/floors`
  - **Respuesta Ejemplo (200 OK):**
    ```json
    [
      { "id": "floor_01", "building_id": "bldg_alpha", "name": "Planta Baja", "floor_number": 0, "description": "Recepción y áreas comunes" },
      { "id": "floor_02", "building_id": "bldg_alpha", "name": "Primera Planta", "floor_number": 1, "description": "Oficinas A" }
    ]
    ```

- **Crear un Nuevo Piso en un Edificio:**
  - **Endpoint:** `POST /buildings/{building_id}/floors`
  - **Request Body Ejemplo:**
    ```json
    {
      "name": "Segunda Planta",
      "floor_number": 2,
      "description": "Oficinas B y Sala de Conferencias"
    }
    ```
  - **Respuesta Ejemplo (201 Created):**
    ```json
    { "id": "floor_03", "building_id": "bldg_alpha", "name": "Segunda Planta", "floor_number": 2, ... }
    ```

- **Obtener Detalles de un Piso Específico:**
  - **Endpoint:** `GET /floors/{id}`
  - **Respuesta Ejemplo (200 OK):**
    ```json
    { "id": "floor_02", "building_id": "bldg_alpha", "name": "Primera Planta", "floor_number": 1, ... }
    ```

- **Actualizar un Piso:**
  - **Endpoint:** `PUT /floors/{id}`
  - **Request Body Ejemplo:**
    ```json
    {
      "name": "Primera Planta (Renovada)",
      "description": "Oficinas A y nuevas áreas de descanso"
    }
    ```
  - **Respuesta Ejemplo (200 OK):**
    ```json
    { "id": "floor_02", "name": "Primera Planta (Renovada)", ... }
    ```

- **Eliminar un Piso:**
  - **Endpoint:** `DELETE /floors/{id}`
  - **Respuesta Ejemplo (204 No Content):** (Sin cuerpo de respuesta)

#### 6.2.4. Gestión de Habitaciones (CRUD)
Estos endpoints permiten administrar las habitaciones dentro de un piso específico.

- **Listar Habitaciones de un Piso:**
  - **Endpoint:** `GET /floors/{floor_id}/rooms`
  - **Respuesta Ejemplo (200 OK):**
    ```json
    [
      { "id": "room_101", "floor_id": "floor_02", "name": "Oficina 101", "room_type": "office", "area_m2": 20 },
      { "id": "room_102", "floor_id": "floor_02", "name": "Sala de Reuniones Pequeña", "room_type": "meeting_room" }
    ]
    ```

- **Crear una Nueva Habitación en un Piso:**
  - **Endpoint:** `POST /floors/{floor_id}/rooms`
  - **Request Body Ejemplo:**
    ```json
    {
      "name": "Oficina 103",
      "room_type": "office",
      "area_m2": 22.5,
      "max_occupancy": 2
    }
    ```
  - **Respuesta Ejemplo (201 Created):**
    ```json
    { "id": "room_103", "floor_id": "floor_02", "name": "Oficina 103", ... }
    ```

- **Obtener Detalles de una Habitación Específica:**
  - **Endpoint:** `GET /rooms/{id}` (Asumiendo que el ID de la habitación es globalmente único o se infiere el contexto)
  - **Respuesta Ejemplo (200 OK):**
    ```json
    { "id": "room_101", "floor_id": "floor_02", "name": "Oficina 101", ... }
    ```

- **Actualizar una Habitación:**
  - **Endpoint:** `PUT /rooms/{id}`
  - **Request Body Ejemplo:**
    ```json
    {
      "name": "Oficina Principal 101",
      "max_occupancy": 3
    }
    ```
  - **Respuesta Ejemplo (200 OK):**
    ```json
    { "id": "room_101", "name": "Oficina Principal 101", "max_occupancy": 3, ... }
    ```

- **Eliminar una Habitación:**
  - **Endpoint:** `DELETE /rooms/{id}`
  - **Respuesta Ejemplo (204 No Content):** (Sin cuerpo de respuesta)

### 6.3. Endpoints de Simulación Global

#### 6.3.1. Iniciar/Reanudar Simulación
- **Endpoint:** `POST /simulation/start`
  - **Request Body (Opcional, para nueva simulación):**
    ```json
    {
      "config_file": "path/to/specific_simulation_config.yaml", // Opcional
      "duration_hours": 72, // Opcional
      "time_scale": 2 // Opcional, simulación al doble de velocidad
    }
    ```
- **Endpoint:** `POST /simulation/resume` (Si estaba pausada)
- **Respuesta Ejemplo (200 OK):**
  ```json
  {
    "simulation_id": "sim_active_12345",
    "status": "running",
    "message": "Simulation started/resumed."
  }
  ```

#### 6.3.2. Pausar Simulación
- **Endpoint:** `POST /simulation/pause`
- **Respuesta Ejemplo (200 OK):**
  ```json
  {
    "simulation_id": "sim_active_12345",
    "status": "paused",
    "message": "Simulation paused."
  }
  ```

#### 6.3.3. Detener Simulación
- **Endpoint:** `POST /simulation/stop`
- **Respuesta Ejemplo (200 OK):**
  ```json
  {
    "simulation_id": "sim_active_12345",
    "status": "stopped",
    "message": "Simulation stopped."
  }
  ```

#### 6.3.4. Obtener Estado de la Simulación
- **Endpoint:** `GET /simulation/status`
- **Respuesta Ejemplo (200 OK):**
  ```json
  {
    "simulation_id": "sim_active_12345",
    "status": "running",
    "current_sim_time": "2024-07-21T14:35:00Z",
    "elapsed_real_time_seconds": 1800,
    "time_scale": 2,
    "active_buildings": 1,
    "total_devices": 150
  }
  ```

### 6.4. Endpoints de Datos, Telemetría y Alarmas

Estos endpoints se utilizan para recuperar datos generados por la simulación y gestionar alarmas.

#### 6.4.1. Obtener Datos Históricos (Telemetría) de un Dispositivo
- **Endpoint:** `GET /telemetry/device/{id}`
- **Query Parameters:**
    - `key`: La métrica específica a consultar (ej. `temperature`, `power_consumption_w`, `brightness`). Puede permitir múltiples claves.
    - `start_time`: Timestamp ISO 8601 de inicio del rango.
    - `end_time`: Timestamp ISO 8601 de fin del rango.
    - `aggregation`: (Opcional) Intervalo de agregación (ej. `1m`, `5m`, `1h`, `1d`). Si se provee, la API debería devolver datos agregados (promedio, suma, min/max según el `key`).
    - `limit`: (Opcional) Número máximo de puntos de datos a devolver.
- **Respuesta Ejemplo (200 OK - Datos de temperatura para un sensor):**
  ```json
  {
    "device_id": "dev_temp_sensor_001",
    "key": "temperature",
    "data_points": [
      { "timestamp": "2024-08-01T10:00:00Z", "value": 22.5 },
      { "timestamp": "2024-08-01T10:01:00Z", "value": 22.6 },
      { "timestamp": "2024-08-01T10:02:00Z", "value": 22.5 }
      // ... más puntos
    ],
    "aggregation_applied": "none" // o "1m_average" si se usó agregación
  }
  ```

#### 6.4.2. Obtener KPIs para Dashboard
Endpoint genérico para alimentar widgets en un dashboard con datos agregados o de estado actual.
- **Endpoint:** `GET /kpi/dashboard`
- **Query Parameters (Opcional):**
    - `building_id`: Para filtrar KPIs por edificio.
    - `time_window`: (ej. `last_1h`, `last_24h`) Para KPIs que dependen de un rango de tiempo.
- **Respuesta Ejemplo (200 OK):**
  ```json
  {
    "total_active_devices": 157,
    "total_energy_consumption_kwh_last_24h": 350.75,
    "active_alarms_count": {
      "critical": 2,
      "high": 5,
      "medium": 10,
      "total": 17
    },
    "average_building_temperature_celsius": 23.2,
    "hvac_systems_running_count": 25
    // ... otros KPIs relevantes
  }
  ```

#### 6.4.3. Listar Alarmas
Permite obtener una lista de alarmas, con filtros.
- **Endpoint:** `GET /alarms`
- **Query Parameters:**
    - `status`: (ej. `ACTIVE`, `ACKNOWLEDGED`, `CLEARED`, `RESOLVED`)
    - `severity`: (ej. `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `WARNING`)
    - `building_id`: Filtrar por ID de edificio.
    - `device_id`: Filtrar por ID de dispositivo que originó la alarma.
    - `start_date`, `end_date`: Rango de fechas para la creación de la alarma.
    - `limit`, `offset`: Para paginación.
- **Respuesta Ejemplo (200 OK):**
  ```json
  {
    "alarms": [
      {
        "id": "alarm_001",
        "device_id": "dev_temp_sensor_005",
        "building_id": "bldg_alpha",
        "rule_violated": "Temperature > 30C for 5min",
        "severity": "HIGH",
        "status": "ACTIVE",
        "created_at": "2024-08-01T11:05:00Z",
        "last_occurrence_at": "2024-08-01T11:10:00Z",
        "details": { "current_temp": 31.5, "threshold": 30.0 }
      }
      // ... más alarmas
    ],
    "total_count": 1,
    "limit": 20,
    "offset": 0
  }
  ```

#### 6.4.4. Marcar Alarma como Vista (Acknowledge)
- **Endpoint:** `POST /alarms/{id}/ack`
- **Request Body (Opcional):**
  ```json
  {
    "user_id": "admin_user",
    "comment": "Investigating issue."
  }
  ```
- **Respuesta Ejemplo (200 OK):**
  ```json
  {
    "id": "alarm_001",
    "status": "ACKNOWLEDGED",
    "acknowledged_by": "admin_user",
    "acknowledged_at": "2024-08-01T11:15:00Z",
    "ack_comment": "Investigating issue."
  }
  ```

### 6.5. Consideraciones Adicionales
- **Autenticación y Autorización:** En un entorno de producción, estos endpoints estarían protegidos. Para esta guía, asumimos acceso abierto.
- **Rate Limiting:** Es importante considerar límites de tasa para evitar sobrecargar el simulador y la base de datos.
- **WebSockets:** Para actualizaciones en tiempo real (ej. lecturas de sensores, nuevas alarmas), una API WebSocket complementaria sería ideal (ver Sección 8).

## 7. Lógica del Motor de Simulación (Worker Process)

El corazón del simulador es el motor de simulación, un proceso (o worker) que se ejecuta en un bucle continuo para actualizar el estado del mundo simulado. Este ciclo de trabajo se repite a intervalos definidos (ej. cada 1, 5 o 10 segundos, configurable según la granularidad deseada y el `time_scale`).

El ciclo típico del motor de simulación incluye los siguientes pasos:

### 7.1. Cargar Configuración Activa y Estado Actual
- **Dispositivos Activos:** El motor obtiene de la base de datos (o de una caché en memoria) la lista de todos los dispositivos marcados como `is_active = true`.
- **Estado Actual:** Para cada dispositivo activo, carga su último estado conocido (campo `state` en la base de datos, que puede haber sido modificado por la API o por una tarea programada anterior).

### 7.2. Ejecutar Tareas Programadas (Schedules)
- **Verificar Horarios:** El motor consulta la tabla `device_schedules` (o su equivalente en la configuración).
- **Disparar Acciones:** Para cada tarea cuyo `cron_expression` coincida con el tiempo de simulación actual, el motor ejecuta la `action_payload` definida. Esto típicamente implica actualizar el campo `state` del dispositivo afectado en la base de datos.
  - Ejemplo: Si son las 08:00 AM y una tarea tiene `cron_expression: "0 8 * * *"` y `action_payload: {"type": "setState", "payload": {"power": "ON"}}`, el estado del dispositivo se actualizará a `{"power": "ON"}`.

### 7.3. Generar Nueva Telemetría (Simulación de Dispositivos)
Esta es la fase principal de simulación. El motor itera sobre cada dispositivo activo:
1.  **Leer Estado Actual:** Obtiene el `state` actual del dispositivo (ej. `{ "power": "ON", "target_temp": 22 }` para un termostato).
2.  **Aplicar Función de Simulación:** Basado en el `type` del dispositivo y su `state` actual, se aplica una función de simulación específica para generar nuevos valores de telemetría y, potencialmente, un nuevo estado interno.
    -   **Termostato (ON):**
        -   `nueva_temp = estado.target_temp + (random() - 0.5) * 0.2;` (La temperatura fluctúa ligeramente alrededor del setpoint).
        -   `consumo_energetico = 0.1;` (Valor representativo de consumo).
    -   **Termostato (OFF):**
        -   `nueva_temp` tiende lentamente hacia una "temperatura ambiente global" o la temperatura de la habitación (si se modela de forma más compleja).
        -   `consumo_energetico = 0.01;` (Consumo mínimo en standby).
    -   **Sensor de Puerta:**
        -   `nuevo_estado_puerta = random_event_occurs(probability=0.02) ? 'OPEN' : 'CLOSED';` (La puerta tiene una pequeña probabilidad de abrirse en cada ciclo si no está controlada por otro factor).
        -   El `state` del sensor se actualiza a `{"value": "OPEN"}` o `{"value": "CLOSED"}`.
    -   **Sensor de Temperatura:**
        -   Lee la temperatura ambiente de la habitación (si se modela con física) o sigue un patrón predefinido/aleatorio.
    -   **Smart Light (ON):**
        -   `consumo_energetico = brillo_actual * consumo_max_brillo;`
    -   *Cada tipo de dispositivo tendrá su propia lógica de simulación.*
3.  **Guardar Nueva Telemetría:** Los nuevos valores generados (ej. `nueva_temp`, `consumo_energetico`, `estado_puerta`) se guardan en la tabla `telemetry` (o su equivalente) junto con el `device_id` y el `timestamp` actual de la simulación.
4.  **Actualizar Estado Interno (si aplica):** Si la función de simulación cambia el estado interno del dispositivo (no solo genera telemetría), este nuevo estado también se persiste.

### 7.4. Evaluar Reglas y Generar Alarmas
- **Comparar con Reglas:** Después de que toda la nueva telemetría ha sido generada y guardada, el motor (o un sub-proceso) compara estos nuevos valores con las reglas de alarma definidas por el usuario.
    - Las reglas pueden estar almacenadas en una tabla `alarm_rules` y podrían tener una estructura como: `SI {device_id_xyz.temperature} > {28} DURANTE {5m} ENTONCES CREAR ALARMA {severity: HIGH, message: "Alta temperatura detectada"}`.
- **Crear Alarmas:** Si una regla se cumple, se inserta un nuevo registro en la tabla `alarms` con todos los detalles relevantes (dispositivo, regla, severidad, valor que disparó la alarma, timestamp).

### 7.5. Publicar Eventos en Message Broker
Para facilitar la comunicación en tiempo real y la integración con otros sistemas (como el servicio WebSocket o sistemas de análisis externos), el motor de simulación publica eventos en un message broker (ej. RabbitMQ, Kafka, Redis Pub/Sub).
- **Telemetría Nueva:**
    - **Topic:** `telemetry.updates` (o `telemetry.{building_id}.{room_id}.{device_id}`)
    - **Payload:** Un lote de nuevos puntos de telemetría.
      ```json
      [{ "device_id": "dev_xyz", "key": "temperature", "value": 28.5, "timestamp": "..." }, ...]
      ```
- **Alarmas Nuevas:**
    - **Topic:** `alarms.new` (o `alarms.{building_id}.{severity}`)
    - **Payload:** Detalles de la nueva alarma.
      ```json
      { "alarm_id": "alm_123", "device_id": "dev_xyz", "severity": "HIGH", ... }
      ```
- **Cambios de Estado (Manuales o Programados):**
    - **Topic:** `devices.state_changes` (o `devices.state.{device_id}`)
    - **Payload:** Información sobre el cambio de estado.
      ```json
      { "device_id": "dev_abc", "new_state": { "power": "ON", "brightness": 75 }, "source": "schedule_id_456" / "api_user_xyz" }
      ```

Este ciclo se repite, avanzando el tiempo de simulación según el `time_scale` configurado.

## 8. Comunicación en Tiempo Real (WebSockets)

Para que las interfaces de usuario (frontend) y otros sistemas externos puedan reaccionar en vivo a los eventos de la simulación, se utiliza un servicio WebSocket que se integra con el Message Broker.

### 8.1. Flujo de Comunicación
1.  **Publicación de Eventos:** El Motor de Simulación (Sección 7.5) publica eventos (telemetría, alarmas, cambios de estado) en tópicos específicos del Message Broker.
2.  **Servicio WebSocket:** Un servicio dedicado (puede ser parte de la API principal o un proceso separado) está suscrito a estos tópicos en el Message Broker.
3.  **Conexión del Cliente:** El frontend (u otro cliente WebSocket) establece una conexión WebSocket con este servicio.
4.  **Suscripción a Canales/Tópicos:** Una vez conectado, el cliente WebSocket se suscribe a "canales" o "tópicos" específicos que le interesan. Estos canales en el lado del WebSocket a menudo se mapean directamente o de forma derivada a los tópicos del Message Broker.
    -   **Ejemplo 1 (Dashboard Global):** Un cliente que muestra un dashboard global podría suscribirse a:
        -   `alarms.new` (para mostrar nuevas alarmas inmediatamente).
        -   `kpi.global` (si se publican KPIs globales actualizados periódicamente).
    -   **Ejemplo 2 (Vista de una Habitación Específica):** Un cliente que visualiza la habitación `room_101` podría suscribirse a:
        -   `devices.state_changes:room_id=room_101` (para ver cambios de estado de dispositivos en esa habitación).
        -   `telemetry.updates:room_id=room_101` (para ver la telemetría en vivo de los dispositivos de esa habitación).
        -   O de forma más granular: `telemetry.updates:device_id=dev_light_001`.
5.  **Retransmisión de Eventos:** Cuando el Servicio WebSocket recibe un mensaje del Message Broker, lo filtra y lo retransmite a todos los clientes WebSocket que estén suscritos al canal correspondiente.

### 8.2. Formato de Mensajes WebSocket
Los mensajes enviados a través de WebSocket suelen ser JSON y reflejan el payload original del Message Broker, posiblemente con metadatos adicionales sobre el canal.

**Ejemplo de mensaje WebSocket para una actualización de telemetría:**
```json
{
  "channel": "telemetry.updates:device_id=dev_temp_sensor_001",
  "payload": {
    "device_id": "dev_temp_sensor_001",
    "key": "temperature",
    "value": 22.8,
    "timestamp": "2024-08-01T11:30:05Z"
  }
}
```

### 8.3. Consideraciones
- **Escalabilidad del Servicio WebSocket:** Para muchos clientes concurrentes, el servicio WebSocket debe ser escalable.
- **Seguridad de la Conexión WebSocket:** Uso de `wss://` (WebSocket Secure) en producción.
- **Autenticación y Autorización de Suscripciones:** Asegurarse de que los clientes solo puedan suscribirse a los canales a los que tienen permiso.
- **Manejo de Desconexiones y Reconexiones:** Tanto el cliente como el servidor deben manejar robustamente las interrupciones de conexión.

Esta arquitectura desacoplada (Motor -> Message Broker -> WebSocket Service -> Cliente) permite una mayor flexibilidad y escalabilidad del sistema.

## 9. Salida de Datos, Persistencia y Logging (Anteriormente Sección 7)

La información generada por la simulación es crucial para el análisis y la validación. El simulador ofrece varias formas de gestionar estos datos.

### 9.1. Formatos de Datos Generados y Exportación
Durante y después de una simulación, los datos de los dispositivos (lecturas, cambios de estado, eventos) pueden ser:
- **Consultados vía API:** Como se describe en la Sección 6, los endpoints de la API permiten obtener datos actuales o históricos (si se almacenan).
- **Exportados a Archivos:**
    - **CSV:** Formato común para análisis tabular. Cada tipo de dispositivo o evento puede generar su propio archivo CSV.
    - **JSON / JSON Lines:** Útil para datos estructurados o semi-estructurados, especialmente para logs de eventos o snapshots de estado.
    - **Parquet:** Formato columnar eficiente para grandes volúmenes de datos, ideal para análisis con herramientas como Pandas o Spark.
- **Enviados a Brokers de Mensajes en Tiempo Real:** (Ver Sección 7.5)
- **Almacenados en Bases de Datos:**
    - **Bases de Datos de Series Temporales (TSDB):** Como InfluxDB, TimescaleDB, Prometheus. Son ideales para almacenar y consultar datos de sensores y métricas a lo largo del tiempo.
    - **Bases de Datos NoSQL:** Como MongoDB, para almacenar documentos JSON con estados de dispositivos o logs.
    - **Bases de Datos Relacionales:** Para configuraciones, metadatos de simulación o resúmenes de datos.

La configuración de la salida de datos (formatos, destinos, frecuencia) se puede especificar en el archivo de configuración de la simulación o mediante parámetros del motor de simulación.

### 9.2. Logging Detallado del Simulador
El simulador utiliza un sistema de logging robusto para registrar su operación interna, eventos significativos de la simulación, acciones de dispositivos, advertencias y errores.
- **Configuración:** Generalmente se gestiona a través del módulo [`src.utils.logger_config.py`](../../src/utils/logger_config.py) (o una ruta similar). Permite definir niveles de log (DEBUG, INFO, WARNING, ERROR), formatos de salida y destinos (consola, archivo).
- **Formato de Log:** Se prefiere el formato JSON estructurado para los logs en archivo, ya que facilita el análisis y la ingesta por sistemas de monitorización de logs (ej. ELK Stack, Splunk).
  ```json
  // Ejemplo de entrada de log en JSON
  {
    "timestamp": "2024-08-01T10:15:30.123Z",
    "level": "INFO",
    "module": "simulator.device.hvac",
    "device_id": "hvac_office101",
    "message": "Setpoint changed",
    "details": {
      "old_setpoint": 22.0,
      "new_setpoint": 21.5,
      "reason": "API_REQUEST"
    }
  }
  ```
- **Contenido de los Logs:**
    - Inicio y fin de la simulación.
    - Creación e inicialización de edificios, pisos, habitaciones y dispositivos.
    - Cambios de estado importantes de los dispositivos.
    - Ejecución de acciones programadas.
    - Eventos simulados (ocupación, puertas, etc.).
    - Errores de configuración o de ejecución.
    - Interacciones vía API.

## 10. Casos de Uso y Ejemplos Prácticos (Anteriormente Sección 8)

Esta sección ilustra cómo se puede utilizar el simulador para abordar diferentes escenarios.

### 8.1. Simulación de un Día Laboral en una Oficina Inteligente
- **Objetivo:** Evaluar el consumo energético y el confort ambiental durante un día típico.
- **Configuración:**
    - Edificio de oficinas con múltiples pisos y tipos de habitaciones (oficinas individuales, salas de reuniones, áreas comunes).
    - Dispositivos: `smart_light`, `smart_thermostat`, `motion_sensor`, `occupancy_sensor`, `door_window_sensor`, `smart_plug` para equipos de oficina.
    - Programación: Luces y HVAC se ajustan según horarios laborales y detección de presencia. Perfiles de ocupación realistas.
- **Interacción:**
    - (Opcional) Simular llegadas y salidas escalonadas de empleados.
    - (Opcional) Introducir una reunión no programada en una sala para ver cómo reacciona el sistema.
- **Análisis:**
    - Consumo total de energía del edificio y desglose por tipo de dispositivo o área.
    - Variaciones de temperatura y niveles de CO2 en diferentes zonas.
    - Frecuencia de activación de luces/HVAC basada en la ocupación.

### 8.2. Prueba de un Nuevo Algoritmo de Control de Iluminación
- **Objetivo:** Validar la efectividad de un algoritmo que ajusta la intensidad de las luces (`smart_light`) basado en la luz natural (`light_sensor`) y la ocupación (`occupancy_sensor`).
- **Configuración:**
    - Una o varias habitaciones con ventanas y la configuración de sensores y luces mencionada.
    - El nuevo algoritmo se implementaría como una lógica de control que interactúa con los dispositivos simulados (potencialmente a través de la API o como un módulo del simulador).
- **Simulación:**
    - Ejecutar la simulación a lo largo de un día con variaciones de luz natural (mañana, mediodía, tarde, nublado/soleado - esto podría requerir un input de irradiancia solar).
    - Simular diferentes patrones de ocupación.
- **Análisis:**
    - Comparar el consumo energético de la iluminación con y sin el algoritmo.
    - Evaluar si los niveles de luz se mantienen dentro de rangos de confort.
    - Verificar que el algoritmo responde correctamente a los cambios de luz natural y ocupación.

### 8.3. Validación de Respuesta de un Sistema de Seguridad
- **Objetivo:** Asegurar que los sensores de seguridad, alarmas y notificaciones funcionan como se espera ante diferentes escenarios de intrusión o emergencia.
- **Configuración:**
    - Edificio con `door_window_sensor`, `motion_sensor`, `glass_break_sensor`, `security_camera`, `alarm_panel`, `siren_strobe`.
    - Sistema de alarma configurado con modos (armado/desarmado) y retardos.
- **Simulación de Eventos (vía API o scripts):**
    - Simular apertura forzada de una puerta mientras el sistema está armado.
    - Simular detección de movimiento en una zona restringida.
    - Simular activación de un `smoke_detector`.
- **Análisis:**
    - Verificar que el `alarm_panel` se activa correctamente.
    - Confirmar que la `siren_strobe` se activa.
    - (Si se modela) Verificar que se envían notificaciones o se registran eventos de `security_camera`.
    - Medir tiempos de respuesta del sistema.

### 8.4. Optimización de Horarios de HVAC para Ahorro Energético
- **Objetivo:** Encontrar horarios óptimos para el sistema HVAC que minimicen el consumo sin sacrificar el confort.
- **Configuración:**
    - Edificio con `smart_thermostat` en varias zonas, `temperature_sensor`, `occupancy_sensor`.
- **Simulación Iterativa:**
    - Ejecutar múltiples simulaciones con diferentes programaciones de HVAC (ej. pre-enfriamiento/calentamiento, diferentes setpoints fuera de horas pico, ajustes basados en predicción de ocupación).
- **Análisis:**
    - Para cada simulación, registrar el consumo energético del HVAC y métricas de confort (ej. tiempo fuera del rango de temperatura deseado).
    - Comparar resultados para identificar la programación más eficiente.

Estos son solo ejemplos; la flexibilidad del simulador permite modelar una amplia gama de escenarios para investigación, desarrollo y pruebas de sistemas IoT en edificios.

## 11. Solución de Problemas (Anteriormente Sección 9)

Aquí se listan algunos problemas comunes y sus posibles soluciones:

- **Errores de Configuración YAML:**
    - **Síntoma:** El simulador no se inicia o arroja errores relacionados con la carga de la configuración.
    - **Solución:**
        - Utiliza un validador de YAML en línea o integrado en tu editor de código para verificar la sintaxis (indentación, guiones, dos puntos).
        - Asegúrate de que todos los campos requeridos estén presentes según la documentación de cada sección (edificio, piso, habitación, dispositivo).
        - Verifica que los nombres de plantillas de dispositivos coincidan exactamente con sus definiciones.
        - Revisa las rutas a archivos de configuración externos, si los usas.

- **Dispositivos no se Comportan como Esperado:**
    - **Síntoma:** Un dispositivo no se enciende/apaga según lo programado, no reporta datos, o sus valores son incorrectos.
    - **Solución:**
        - **Revisa los Logs del Simulador:** Activa el nivel DEBUG para obtener información detallada sobre el dispositivo en cuestión. Busca mensajes de error o advertencias relacionados con su `device_id`.
        - **Verifica la Configuración del Dispositivo:** Asegúrate de que el `type` es correcto, que `initial_state` y `schedule` están bien definidos. Comprueba que los parámetros específicos del tipo de dispositivo (ej. `min_val`, `max_val` para sensores) son lógicos.
        - **Confirma las Interacciones:** Si el dispositivo depende de otro (ej. un `smart_thermostat` de un `temperature_sensor`), asegúrate de que el sensor fuente está funcionando y configurado correctamente.
        - **Aislamiento del Problema:** Intenta simplificar la configuración. Crea una simulación mínima con solo ese dispositivo o un pequeño grupo para ver si el problema persiste.

- **Problemas de Rendimiento en la Simulación:**
    - **Síntoma:** La simulación se ejecuta muy lentamente, consume excesiva CPU o memoria.
    - **Solución:**
        - **Reduce el Número de Dispositivos:** Especialmente si muchos tienen intervalos de actualización muy cortos.
        - **Aumenta los Intervalos de Actualización (`update_interval_seconds`):** No todos los dispositivos necesitan reportar datos cada segundo. Ajusta según la necesidad.
        - **Optimiza la Lógica de Control:** Si has implementado algoritmos de control complejos que interactúan frecuentemente con la API, revisa su eficiencia.
        - **Revisa el `time_scale`:** Un `time_scale` muy alto con muchos dispositivos puede ser demandante.
        - **Limita la Persistencia de Datos:** Si estás guardando cada lectura de cada sensor en una base de datos o archivo, considera agregar datos o aumentar el intervalo de escritura.
        - **Revisa los Logs:** Un log excesivo en nivel DEBUG también puede impactar el rendimiento. Ajústalo a INFO para ejecuciones largas.

- **Errores de Conexión con la API:**
    - **Síntoma:** No puedes acceder a los endpoints de la API, o recibes errores de conexión.
    - **Solución:**
        - Verifica que el servidor de la API del simulador esté en ejecución.
        - Confirma la URL base, el puerto y la ruta del endpoint.
        - Revisa si hay algún firewall bloqueando la conexión.
        - Consulta los logs del servidor de la API para mensajes de error.

- **Datos de Salida Inesperados o Faltantes:**
    - **Síntoma:** Los archivos de datos no se generan, están vacíos o tienen un formato incorrecto.
    - **Solución:**
        - Verifica la configuración de salida de datos en tu archivo de simulación.
        - Asegúrate de que el simulador tiene permisos de escritura en el directorio de salida.
        - Revisa los logs para errores relacionados con la exportación o escritura de datos.

## 12. Contribución y Desarrollo Futuro (Anteriormente Sección 10)

¡Tu contribución es bienvenida para hacer del IoT Building Simulator una herramienta aún mejor!

### 10.1. Cómo Contribuir
- **Reportando Bugs:** Si encuentras un error, por favor abre un "Issue" detallado en el repositorio de GitHub del proyecto. Incluye pasos para reproducirlo, logs relevantes y tu configuración si es posible.
- **Sugiriendo Mejoras:** ¿Tienes ideas para nuevas funcionalidades, tipos de dispositivos o mejoras en la usabilidad? Abre un "Issue" con la etiqueta "enhancement" o "feature request".
- **Desarrollando Código:**
    1. Haz un "Fork" del repositorio.
    2. Crea una nueva rama para tu característica o corrección (ej. `feature/new-device-type` o `fix/yaml-parser-bug`).
    3. Escribe tu código, asegurándote de seguir las guías de estilo del proyecto (si existen).
    4. Añade pruebas unitarias y de integración para tus cambios.
    5. Asegúrate de que todas las pruebas pasan.
    6. Actualiza la documentación relevante (como esta guía) si tus cambios la afectan.
    7. Envía un "Pull Request" (PR) a la rama principal del repositorio original. Describe claramente tus cambios en el PR.
- **Mejorando la Documentación:** Si encuentras áreas en la documentación que pueden ser mejoradas, aclaradas o expandidas, no dudes en proponer cambios.

### 10.2. Roadmap de Desarrollo Futuro (Ideas)
Esta es una lista de posibles direcciones para el desarrollo futuro, sujeta a discusión y priorización por la comunidad:
- **Interfaz Gráfica de Usuario (GUI):** Una interfaz web para configurar, ejecutar y visualizar simulaciones y sus resultados.
- **Modelos Ambientales Más Avanzados:**
    - Simulación de irradiancia solar más precisa.
    - Modelos térmicos más detallados para habitaciones y edificios.
    - Simulación de flujo de aire y ventilación natural.
- **Integración con Plataformas IoT Existentes:** Conectores para AWS IoT, Azure IoT Hub, Google Cloud IoT Core, The Things Network, etc.
- **Biblioteca Expandida de Tipos de Dispositivos:** Más sensores, actuadores y dispositivos complejos (ej. electrodomésticos inteligentes, sistemas de gestión de edificios - BMS).
- **Modelado de Comportamiento de Usuario Avanzado:** Agentes autónomos que simulan ocupantes con patrones de comportamiento más complejos e interacciones con dispositivos.
- **Capacidades de Co-simulación:** Integración con otras herramientas de simulación (ej. EnergyPlus, Modelica).
- **Módulo de Análisis de Datos Integrado:** Herramientas básicas dentro del simulador para visualizar y analizar los datos generados.
- **Soporte para Estándares IoT:** Como OCF, LwM2M, Matter.

### 10.3. Contacto y Comunidad
- **Repositorio GitHub:** [Enlace a tu repositorio GitHub aquí]
- **Lista de Correo / Foro / Canal de Discord:** (Si existe, añadir enlaces)

---
*Este documento es una guía en evolución. Consulte la documentación de la API y el código fuente para obtener los detalles más actualizados.*