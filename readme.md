Entiendo que estás buscando orientación para crear una simulación modular para dispositivos IoT en edificios, con flexibilidad para simular diferentes configuraciones sin reescribir código. También necesitas recomendaciones sobre la estructura de base de datos y tecnologías para implementarlo, considerando la posterior integración con APIs y servicios en la nube como GCP o AWS.

## Estructura conceptual de la solución

### Estructura de carpetas
```
/iot-building-simulator/
├── config/                  # Configuraciones de simulación 
│   ├── buildings/           # Definiciones de edificios (JSON/YAML)
│   ├── devices/             # Tipos de dispositivos IoT (JSON/YAML)
│   └── scenarios/           # Escenarios de simulación predefinidos
├── src/                     # Código fuente
│   ├── core/                # Núcleo de la simulación
│   │   ├── building.py      # Modelo de edificio
│   │   ├── floor.py         # Modelo de piso
│   │   ├── room.py          # Modelo de habitación/oficina
│   │   └── device.py        # Modelo base de dispositivo
│   ├── devices/             # Implementaciones específicas de dispositivos
│   │   ├── sensor.py        # Sensores genéricos
│   │   ├── climate.py       # Dispositivos de clima
│   │   ├── security.py      # Dispositivos de seguridad
│   │   └── energy.py        # Dispositivos de energía
│   ├── simulator/           # Motor de simulación
│   │   ├── engine.py        # Motor principal
│   │   ├── scheduler.py     # Programador de eventos
│   │   └── traffic.py       # Simulación de tráfico de datos
│   ├── connectors/          # Conectores para servicios externos
│   │   ├── aws/             # Conectores para AWS
│   │   ├── gcp/             # Conectores para GCP
│   │   └── api/             # Implementación de API REST
│   └── utils/               # Utilidades generales
├── database/                # Esquemas y migraciones
│   ├── models/              # Modelos de datos
│   ├── migrations/          # Migraciones 
│   └── seeds/               # Datos iniciales
└── tests/                   # Pruebas
```

### Mapa conceptual de la base de datos

#### Entidades principales:
- Building (Edificio)
- Floor (Piso)
- Room (Habitación/Oficina)
- DeviceType (Tipo de dispositivo)
- Device (Dispositivo)
- DataPoint (Punto de datos)
- SimulationConfig (Configuración de simulación)
- SimulationRun (Ejecución de simulación)

#### Relaciones:
- Un Building tiene múltiples Floors
- Un Floor tiene múltiples Rooms
- Una Room tiene múltiples Devices
- Cada Device tiene un DeviceType
- Cada Device genera múltiples DataPoints
- Cada SimulationRun utiliza una SimulationConfig
- Cada SimulationRun puede incluir múltiples Buildings

## Tecnologías recomendadas

### Para la simulación:
- **Lenguaje**: Python (por su flexibilidad y abundantes bibliotecas)
- **Framework de simulación**: SimPy (para simulación de eventos discretos)
- **Generación de datos**: Pandas, NumPy (para manipulación y generación de datos)

### Para la base de datos:
- **Base de datos primaria**: PostgreSQL o MongoDB
  - PostgreSQL: Si necesitas relaciones estrictas y consultas complejas
  - MongoDB: Si prefieres flexibilidad en el esquema para adaptarse a diferentes tipos de dispositivos
- **TimeSeries DB**: InfluxDB o TimescaleDB (para datos de series temporales de sensores)
- **ORM/ODM**: SQLAlchemy (para PostgreSQL) o Mongoose (para MongoDB con Node.js)

### Para la API y conectividad:
- **API Framework**: FastAPI o Flask (Python)
- **Documentación API**: Swagger/OpenAPI
- **Mensajería**: Kafka o RabbitMQ (para manejo de grandes volúmenes de datos en tiempo real)

### Para integración con la nube:
- **AWS**: 
  - S3 para almacenamiento
  - AWS IoT Core para simulación de dispositivos
  - Amazon Timestream para datos de series temporales
  - Lambda para procesamiento
- **GCP**:
  - Cloud Storage para almacenamiento
  - Cloud IoT Core para dispositivos
  - BigQuery para análisis
  - Pub/Sub para mensajería

## Enfoque de implementación

1. **Diseño modular**: 
   - Define interfaces claras entre componentes
   - Usa inyección de dependencias para intercambiar implementaciones

2. **Configuración basada en archivos**:
   - Usa archivos YAML/JSON para definir edificios, pisos, habitaciones
   - Define tipos de dispositivos con sus características y patrones de generación de datos

3. **Simulación escalable**:
   - Diseña el simulador para ejecutarse en paralelo
   - Considera un enfoque distribuido para simulaciones a gran escala

4. **Almacenamiento eficiente**:
   - Usa compresión y particionamiento para datos históricos
   - Implementa políticas de retención para datos antiguos

5. **APIs RESTful**:
   - Diseña endpoints para controlar simulaciones
   - Implementa endpoints para consultar resultados
   - Considera GraphQL para consultas complejas y flexibles

## Consideraciones técnicas adicionales

- **Escalabilidad**: Diseña la arquitectura para escalar horizontalmente
- **Tolerancia a fallos**: Implementa reintentos y manejo de errores robusto
- **Observabilidad**: Integra logging, métricas y trazabilidad
- **Seguridad**: Implementa autenticación y autorización para acceso a la API
- **Pruebas**: Crea pruebas unitarias e integración para validar simulaciones

¿Te gustaría que profundice en alguna parte específica de esta propuesta? ¿O hay aspectos adicionales que quieras considerar para tu simulador IoT?


# Mapa Conceptual de la Base de Datos

Voy a desarrollar una propuesta detallada para la estructura de la base de datos de tu simulador IoT, explicando cada componente y su justificación.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">
  <!-- Background -->
  <rect width="800" height="600" fill="#f8f9fa" />
  
  <!-- Entities -->
  <!-- Building -->
  <rect x="50" y="50" width="160" height="140" rx="5" fill="#e6f2ff" stroke="#0066cc" stroke-width="2" />
  <text x="130" y="75" font-family="Arial" font-size="16" text-anchor="middle" font-weight="bold">Building</text>
  <line x1="50" y1="85" x2="210" y2="85" stroke="#0066cc" stroke-width="2" />
  <text x="60" y="105" font-family="Arial" font-size="12">building_id (PK)</text>
  <text x="60" y="125" font-family="Arial" font-size="12">name</text>
  <text x="60" y="145" font-family="Arial" font-size="12">location</text>
  <text x="60" y="165" font-family="Arial" font-size="12">total_floors</text>
  <text x="60" y="185" font-family="Arial" font-size="12">metadata (JSON)</text>
  
  <!-- Floor -->
  <rect x="300" y="50" width="160" height="120" rx="5" fill="#e6f2ff" stroke="#0066cc" stroke-width="2" />
  <text x="380" y="75" font-family="Arial" font-size="16" text-anchor="middle" font-weight="bold">Floor</text>
  <line x1="300" y1="85" x2="460" y2="85" stroke="#0066cc" stroke-width="2" />
  <text x="310" y="105" font-family="Arial" font-size="12">floor_id (PK)</text>
  <text x="310" y="125" font-family="Arial" font-size="12">building_id (FK)</text>
  <text x="310" y="145" font-family="Arial" font-size="12">floor_number</text>
  <text x="310" y="165" font-family="Arial" font-size="12">floor_plan (JSON)</text>
  
  <!-- Room -->
  <rect x="550" y="50" width="160" height="140" rx="5" fill="#e6f2ff" stroke="#0066cc" stroke-width="2" />
  <text x="630" y="75" font-family="Arial" font-size="16" text-anchor="middle" font-weight="bold">Room</text>
  <line x1="550" y1="85" x2="710" y2="85" stroke="#0066cc" stroke-width="2" />
  <text x="560" y="105" font-family="Arial" font-size="12">room_id (PK)</text>
  <text x="560" y="125" font-family="Arial" font-size="12">floor_id (FK)</text>
  <text x="560" y="145" font-family="Arial" font-size="12">room_number</text>
  <text x="560" y="165" font-family="Arial" font-size="12">room_type</text>
  <text x="560" y="185" font-family="Arial" font-size="12">area_sqm</text>
  
  <!-- Device Type -->
  <rect x="50" y="250" width="160" height="140" rx="5" fill="#e6f7e6" stroke="#008800" stroke-width="2" />
  <text x="130" y="275" font-family="Arial" font-size="16" text-anchor="middle" font-weight="bold">DeviceType</text>
  <line x1="50" y1="285" x2="210" y2="285" stroke="#008800" stroke-width="2" />
  <text x="60" y="305" font-family="Arial" font-size="12">device_type_id (PK)</text>
  <text x="60" y="325" font-family="Arial" font-size="12">type_name</text>
  <text x="60" y="345" font-family="Arial" font-size="12">category</text>
  <text x="60" y="365" font-family="Arial" font-size="12">data_schema (JSON)</text>
  <text x="60" y="385" font-family="Arial" font-size="12">sampling_rate</text>
  
  <!-- Device -->
  <rect x="300" y="250" width="160" height="160" rx="5" fill="#e6f7e6" stroke="#008800" stroke-width="2" />
  <text x="380" y="275" font-family="Arial" font-size="16" text-anchor="middle" font-weight="bold">Device</text>
  <line x1="300" y1="285" x2="460" y2="285" stroke="#008800" stroke-width="2" />
  <text x="310" y="305" font-family="Arial" font-size="12">device_id (PK)</text>
  <text x="310" y="325" font-family="Arial" font-size="12">room_id (FK)</text>
  <text x="310" y="345" font-family="Arial" font-size="12">device_type_id (FK)</text>
  <text x="310" y="365" font-family="Arial" font-size="12">serial_number</text>
  <text x="310" y="385" font-family="Arial" font-size="12">status</text>
  <text x="310" y="405" font-family="Arial" font-size="12">config (JSON)</text>
  
  <!-- DataPoint -->
  <rect x="550" y="250" width="160" height="140" rx="5" fill="#fff0e6" stroke="#cc6600" stroke-width="2" />
  <text x="630" y="275" font-family="Arial" font-size="16" text-anchor="middle" font-weight="bold">DataPoint</text>
  <line x1="550" y1="285" x2="710" y2="285" stroke="#cc6600" stroke-width="2" />
  <text x="560" y="305" font-family="Arial" font-size="12">data_id (PK)</text>
  <text x="560" y="325" font-family="Arial" font-size="12">device_id (FK)</text>
  <text x="560" y="345" font-family="Arial" font-size="12">timestamp</text>
  <text x="560" y="365" font-family="Arial" font-size="12">value (JSON)</text>
  <text x="560" y="385" font-family="Arial" font-size="12">simulation_run_id (FK)</text>
  
  <!-- SimulationConfig -->
  <rect x="50" y="450" width="160" height="120" rx="5" fill="#f2e6ff" stroke="#6600cc" stroke-width="2" />
  <text x="130" y="475" font-family="Arial" font-size="16" text-anchor="middle" font-weight="bold">SimulationConfig</text>
  <line x1="50" y1="485" x2="210" y2="485" stroke="#6600cc" stroke-width="2" />
  <text x="60" y="505" font-family="Arial" font-size="12">config_id (PK)</text>
  <text x="60" y="525" font-family="Arial" font-size="12">name</text>
  <text x="60" y="545" font-family="Arial" font-size="12">duration</text>
  <text x="60" y="565" font-family="Arial" font-size="12">parameters (JSON)</text>
  
  <!-- SimulationRun -->
  <rect x="300" y="450" width="160" height="140" rx="5" fill="#f2e6ff" stroke="#6600cc" stroke-width="2" />
  <text x="380" y="475" font-family="Arial" font-size="16" text-anchor="middle" font-weight="bold">SimulationRun</text>
  <line x1="300" y1="485" x2="460" y2="485" stroke="#6600cc" stroke-width="2" />
  <text x="310" y="505" font-family="Arial" font-size="12">run_id (PK)</text>
  <text x="310" y="525" font-family="Arial" font-size="12">config_id (FK)</text>
  <text x="310" y="545" font-family="Arial" font-size="12">start_time</text>
  <text x="310" y="565" font-family="Arial" font-size="12">end_time</text>
  <text x="310" y="585" font-family="Arial" font-size="12">status</text>
  
  <!-- BuildingSimMap -->
  <rect x="550" y="450" width="160" height="100" rx="5" fill="#ffe6e6" stroke="#cc0000" stroke-width="2" />
  <text x="630" y="475" font-family="Arial" font-size="16" text-anchor="middle" font-weight="bold">BuildingSimMap</text>
  <line x1="550" y1="485" x2="710" y2="485" stroke="#cc0000" stroke-width="2" />
  <text x="560" y="505" font-family="Arial" font-size="12">map_id (PK)</text>
  <text x="560" y="525" font-family="Arial" font-size="12">run_id (FK)</text>
  <text x="560" y="545" font-family="Arial" font-size="12">building_id (FK)</text>
  
  <!-- Relationships -->
  <!-- Building to Floor -->
  <line x1="210" y1="120" x2="300" y2="120" stroke="#0066cc" stroke-width="2" />
  <polygon points="295,115 300,120 295,125" fill="#0066cc" stroke="#0066cc" stroke-width="1" />
  
  <!-- Floor to Room -->
  <line x1="460" y1="120" x2="550" y2="120" stroke="#0066cc" stroke-width="2" />
  <polygon points="545,115 550,120 545,125" fill="#0066cc" stroke="#0066cc" stroke-width="1" />
  
  <!-- Room to Device -->
  <line x1="630" y1="190" x2="630" y2="250" stroke="#008800" stroke-width="2" />
  <line x1="630" y1="250" x2="460" y2="320" stroke="#008800" stroke-width="2" />
  <polygon points="465,325 460,320 465,315" fill="#008800" stroke="#008800" stroke-width="1" />
  
  <!-- DeviceType to Device -->
  <line x1="210" y1="320" x2="300" y2="320" stroke="#008800" stroke-width="2" />
  <polygon points="295,315 300,320 295,325" fill="#008800" stroke="#008800" stroke-width="1" />
  
  <!-- Device to DataPoint -->
  <line x1="460" y1="320" x2="550" y2="320" stroke="#cc6600" stroke-width="2" />
  <polygon points="545,315 550,320 545,325" fill="#cc6600" stroke="#cc6600" stroke-width="1" />
  
  <!-- SimulationConfig to SimulationRun -->
  <line x1="210" y1="520" x2="300" y2="520" stroke="#6600cc" stroke-width="2" />
  <polygon points="295,515 300,520 295,525" fill="#6600cc" stroke="#6600cc" stroke-width="1" />
  
  <!-- SimulationRun to BuildingSimMap -->
  <line x1="460" y1="520" x2="550" y2="520" stroke="#cc0000" stroke-width="2" />
  <polygon points="545,515 550,520 545,525" fill="#cc0000" stroke="#cc0000" stroke-width="1" />
  
  <!-- BuildingSimMap to Building -->
  <line x1="630" y1="450" x2="630" y2="400" stroke="#cc0000" stroke-width="2" />
  <line x1="630" y1="400" x2="130" y2="400" stroke="#cc0000" stroke-width="2" />
  <line x1="130" y1="400" x2="130" y2="190" stroke="#cc0000" stroke-width="2" />
  <polygon points="125,195 130,190 135,195" fill="#cc0000" stroke="#cc0000" stroke-width="1" />
  
  <!-- SimulationRun to DataPoint -->
  <line x1="380" y1="450" x2="380" y2="400" stroke="#cc6600" stroke-width="2" />
  <line x1="380" y1="400" x2="630" y2="400" stroke="#cc6600" stroke-width="2" />
  <line x1="630" y1="400" x2="630" y2="390" stroke="#cc6600" stroke-width="2" />
  <polygon points="625,395 630,390 635,395" fill="#cc6600" stroke="#cc6600" stroke-width="1" />
</svg>

```

## Justificación del Diseño de la Base de Datos

### 1. Estructura Jerárquica para Ubicaciones Físicas
He diseñado la base de datos con una estructura jerárquica clara (Building → Floor → Room → Device) por varias razones:

- **Modularidad**: Facilita agregar o quitar edificios completos, pisos o habitaciones
- **Navegación natural**: Refleja la estructura física real
- **Consultas eficientes**: Permite localizar datos siguiendo la jerarquía natural
- **Escalabilidad**: Soporta desde pequeños edificios hasta grandes complejos

### 2. Separación de Tipos de Dispositivos y Dispositivos

La entidad `DeviceType` está separada de `Device` por estas razones:

- **Reutilización**: Múltiples dispositivos pueden compartir el mismo tipo
- **Configuración centralizada**: Cambios en un tipo afectan a todos los dispositivos de ese tipo
- **Consistencia**: Garantiza que dispositivos similares tengan comportamientos similares
- **Reducción de redundancia**: Evita duplicar información de configuración

### 3. Almacenamiento de Datos de Series Temporales

La entidad `DataPoint` está diseñada específicamente para datos IoT:

- **Estructura de valores flexible**: Usa JSON para almacenar diferentes tipos de datos según el dispositivo
- **Indexado por tiempo**: Optimizado para consultas por rangos temporales
- **Vinculación a simulaciones**: Permite filtrar datos por ejecución de simulación
- **Particionamiento potencial**: Facilita particionar datos por tiempo para mejor rendimiento

### 4. Separación de Configuración y Ejecución de Simulación

Las entidades `SimulationConfig` y `SimulationRun` están separadas porque:

- **Reutilización de configuraciones**: Permite ejecutar la misma configuración múltiples veces
- **Experimentación**: Facilita comparar resultados usando la misma configuración
- **Auditoría**: Mantiene un registro de todas las ejecuciones y sus parámetros
- **Planificación**: Permite programar simulaciones futuras

### 5. Tabla de Mapeo Building-Simulation

La entidad `BuildingSimMap` es una tabla de relación muchos a muchos que:

- **Flexibilidad**: Permite incluir cualquier combinación de edificios en una simulación
- **Reutilización**: Un edificio puede participar en múltiples simulaciones
- **Configuración dinámica**: Facilita agregar o quitar edificios de una simulación

## Tecnologías de Base de Datos Recomendadas

Recomiendo un enfoque híbrido para la base de datos:

### PostgreSQL como Base de Datos Principal
- Para almacenar la estructura jerárquica (edificios, pisos, habitaciones) y metadatos
- Ventajas: ACID, relaciones sólidas, consultas complejas con SQL, extensiones JSON

### TimescaleDB como Extensión para Series Temporales
- Para almacenar los datos de `DataPoint` de manera eficiente
- Ventajas: Optimizado para series temporales, compatible con PostgreSQL, compresión automática

### Redis para Caché y Estado de Simulación
- Para almacenar estado temporal durante la simulación
- Ventajas: Alta velocidad, estructuras de datos en memoria, pub/sub para eventos

## Aspectos Pendientes de Planificación del Proyecto

Para completar la planificación de tu proyecto, considera estos aspectos adicionales:

1. **Diseño de Interfaces y APIs**
   - Definir endpoints REST para control de simulaciones
   - Diseñar interfaces para visualización de datos y resultados
   - Establecer formatos de intercambio de datos (JSON schemas)

2. **Estrategia de Despliegue**
   - Arquitectura de microservicios vs monolito
   - Contenedores y orquestación (Docker, Kubernetes)
   - Estrategia de CI/CD para actualizaciones continuas

3. **Escalabilidad y Rendimiento**
   - Estrategias de particionamiento de datos
   - Balanceo de carga para simulaciones grandes
   - Políticas de retención y archivado de datos

4. **Seguridad**
   - Autenticación y autorización para APIs
   - Cifrado de datos sensibles
   - Auditoría de acceso y cambios

5. **Diseño de Patrones de Simulación**
   - Patrones realistas de comportamiento de dispositivos
   - Escenarios de falla y degradación
   - Modelado de interacciones entre dispositivos

6. **Integración Externa**
   - Especificaciones detalladas para conectores de nube (AWS, GCP)
   - Requisitos para ingesta y exportación de datos
   - Formatos de interoperabilidad con otros sistemas

7. **Plan de Pruebas**
   - Estrategia de pruebas unitarias e integración
   - Validación de patrones de generación de datos
   - Pruebas de carga y rendimiento

8. **Documentación**
   - Guías técnicas para desarrolladores
   - Documentación de APIs
   - Ejemplos de configuración y uso

9. **Roadmap de Características**
   - Priorización de funcionalidades
   - Fases de implementación
   - Hitos y entregables

¿Te gustaría que profundice en alguno de estos aspectos de planificación? ¿O prefieres información más detallada sobre algún componente específico del diseño de base de datos?



# Diseño de Interfaces y APIs

## Endpoints REST para Control de Simulaciones

### Gestión de Simulaciones
```
POST   /api/v1/simulations           # Crear nueva simulación
GET    /api/v1/simulations           # Listar simulaciones
GET    /api/v1/simulations/{id}      # Obtener detalles de simulación
PUT    /api/v1/simulations/{id}      # Actualizar configuración
DELETE /api/v1/simulations/{id}      # Eliminar simulación

POST   /api/v1/simulations/{id}/run  # Iniciar ejecución
PUT    /api/v1/simulations/{id}/stop # Detener ejecución
GET    /api/v1/simulations/{id}/status # Obtener estado
```

### Gestión de Edificios y Componentes
```
POST   /api/v1/buildings             # Crear edificio
GET    /api/v1/buildings             # Listar edificios
GET    /api/v1/buildings/{id}        # Obtener detalles de edificio
PUT    /api/v1/buildings/{id}        # Actualizar edificio
DELETE /api/v1/buildings/{id}        # Eliminar edificio

GET    /api/v1/buildings/{id}/floors # Obtener pisos de un edificio
GET    /api/v1/floors/{id}/rooms     # Obtener habitaciones de un piso
GET    /api/v1/rooms/{id}/devices    # Obtener dispositivos de una habitación
```

### Gestión de Tipos de Dispositivos
```
POST   /api/v1/device-types          # Crear tipo de dispositivo
GET    /api/v1/device-types          # Listar tipos de dispositivos
GET    /api/v1/device-types/{id}     # Obtener detalles de tipo
PUT    /api/v1/device-types/{id}     # Actualizar tipo
DELETE /api/v1/device-types/{id}     # Eliminar tipo
```

### Consulta de Datos
```
GET    /api/v1/data                  # Consultar datos con filtros
GET    /api/v1/data/metrics          # Obtener métricas agregadas
GET    /api/v1/data/export           # Exportar datos en CSV/JSON
```

## Formatos de Intercambio de Datos (JSON Schemas)

### Ejemplo de Schema para Configuración de Simulación
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Nombre de la simulación"
    },
    "description": {
      "type": "string"
    },
    "duration": {
      "type": "object",
      "properties": {
        "value": {"type": "integer"},
        "unit": {"type": "string", "enum": ["seconds", "minutes", "hours", "days"]}
      }
    },
    "buildings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "building_id": {"type": "string"},
          "traffic_multiplier": {"type": "number", "minimum": 0.1, "maximum": 10.0}
        }
      }
    },
    "time_scale": {
      "type": "number",
      "description": "Factor de aceleración de tiempo. 1.0 = tiempo real"
    },
    "scenario": {
      "type": "string",
      "enum": ["normal", "peak_usage", "weekend", "holiday", "custom"]
    }
  },
  "required": ["name", "duration", "buildings"]
}
```

### Ejemplo de Schema para Datos de Dispositivo
```json
{
  "type": "object",
  "properties": {
    "device_id": {"type": "string"},
    "timestamp": {"type": "string", "format": "date-time"},
    "values": {
      "type": "object",
      "additionalProperties": true
    },
    "metadata": {
      "type": "object",
      "properties": {
        "building_id": {"type": "string"},
        "floor_id": {"type": "string"},
        "room_id": {"type": "string"},
        "simulation_id": {"type": "string"}
      }
    }
  }
}
```

## Interfaces para Visualización de Datos

### Dashboard Principal
- Panel de control con métricas clave
- Estado de simulaciones en ejecución
- Gráficos de resumen de datos generados
- Alertas y notificaciones

### Visualizador de Edificios
- Vista 3D/2D de edificios
- Navegación jerárquica (edificio → piso → habitación)
- Código de colores por tipo de dispositivo o valores
- Filtros por tipo de dispositivo y métricas

### Análisis de Datos
- Gráficos de series temporales
- Comparación entre simulaciones
- Análisis de patrones y anomalías
- Exportación de datos y reportes

# Estrategia de Despliegue

## Arquitectura: Microservicios vs Monolito

### Enfoque Recomendado: Microservicios Moderados
Propongo un enfoque de "microservicios moderados" con estos componentes principales:

1. **API Gateway** - Punto de entrada único, gestión de autenticación
2. **Servicio de Configuración** - Gestión de edificios, dispositivos y configuraciones
3. **Motor de Simulación** - Ejecución de simulaciones
4. **Servicio de Almacenamiento** - Gestión de datos generados
5. **Servicio de Análisis** - Procesamiento y agregación de datos
6. **Interfaz de Usuario** - Frontend para visualización y control

Justificación:
- Permite escalar independientemente el motor de simulación y el almacenamiento
- Facilita actualizar componentes individuales sin afectar al sistema completo
- Mantiene un balance entre complejidad y flexibilidad

## Contenedores y Orquestación

### Tecnologías Recomendadas:
- **Docker** - Contenedores para cada microservicio
- **Kubernetes** - Orquestación para despliegue y escalado
- **Helm** - Gestión de despliegues en Kubernetes

### Arquitectura de Despliegue:
```
|-- Namespace: iot-simulator
|   |-- StatefulSet: database (PostgreSQL + TimescaleDB)
|   |-- Deployment: redis
|   |-- Deployment: api-gateway
|   |-- Deployment: config-service
|   |-- Deployment: simulation-engine
|       |-- HorizontalPodAutoscaler (basado en carga)
|   |-- Deployment: storage-service
|   |-- Deployment: analytics-service
|   |-- Deployment: frontend
|-- Services, ConfigMaps, Secrets, etc.
```

## Estrategia CI/CD

### Pipeline de CI/CD:
1. **Integración Continua**:
   - Pruebas unitarias automatizadas
   - Análisis de código estático
   - Construcción de imágenes Docker

2. **Entrega Continua**:
   - Despliegue automático en entorno de desarrollo
   - Pruebas de integración automatizadas
   - Generación de artefactos para producción

3. **Despliegue Continuo**:
   - Despliegue en entorno de pruebas
   - Pruebas de aceptación automatizadas
   - Promoción a producción (manual o automatizada)

### Herramientas Recomendadas:
- **GitLab CI/Jenkins** - Automatización de pipeline
- **ArgoCD** - Despliegue continuo en Kubernetes
- **Prometheus/Grafana** - Monitoreo y alertas

# Cantidad de Dispositivos IoT por Tipo de Espacio

## Habitación/Oficina Estándar (20-30 m²)
- 1-2 sensores de temperatura/humedad
- 1-2 sensores de presencia/ocupación
- 3-6 luminarias inteligentes
- 1 controlador de HVAC (aire acondicionado)
- 1-2 sensores de calidad de aire (CO2, VOC)
- 1 cerradura inteligente
- 1-3 enchufes/tomacorrientes inteligentes
- 1 sensor de apertura de ventana (si aplica)
- 1-2 cámaras de seguridad (en espacios comunes)
- 1-2 altavoces/micrófonos (salas de reuniones)

**Total por habitación estándar**: 10-20 dispositivos

## Sistemas Centrales de Edificio (por piso o edificio)

### Sistema de Ventilación/HVAC
- 1 unidad central de tratamiento de aire (AHU)
- 2-4 sensores de temperatura de conducto
- 2-4 sensores de flujo de aire
- 1-2 sensores de presión diferencial
- 2-4 actuadores de compuerta
- 1-2 controladores de velocidad de ventilador
- 1 sistema de recuperación de calor (si aplica)
- 1 controlador principal de HVAC
- 2-4 sensores de calidad de aire en retorno

**Total HVAC por piso**: 12-22 dispositivos

### Sistema Eléctrico
- 1 medidor inteligente principal (por edificio)
- 1-2 medidores por piso
- 1 sistema de monitoreo de panel eléctrico
- 4-8 sensores de consumo en circuitos principales
- 1-2 sistemas de control de demanda
- 1-2 inversores para energía renovable (si aplica)
- 1 sistema de almacenamiento de energía (si aplica)
- 2-4 detectores de fallas eléctricas

**Total eléctrico por piso**: 10-20 dispositivos

### Sistema de Agua
- 1 medidor principal de agua (por edificio)
- 1-2 medidores de consumo por piso
- 2-4 sensores de presión de agua
- 1-2 sensores de calidad de agua
- 2-4 válvulas automatizadas
- 1-2 sensores de temperatura de agua caliente
- 1-2 detectores de fugas

**Total agua por piso**: 8-16 dispositivos

### Sistema de Iluminación (áreas comunes)
- 1 controlador central de iluminación
- 10-20 luminarias inteligentes en pasillos/áreas comunes
- 3-6 sensores de presencia en áreas comunes
- 2-4 sensores de luz ambiental
- 1-2 controladores de escenas

**Total iluminación áreas comunes por piso**: 17-33 dispositivos

### Sistema de Seguridad
- 4-8 cámaras de seguridad por piso
- 2-4 controles de acceso (puertas)
- 1 panel de alarma
- 4-8 sensores de movimiento
- 2-4 sensores de apertura de puertas/ventanas
- 1 sistema de intercomunicación
- 1-2 estaciones de pánico

**Total seguridad por piso**: 15-27 dispositivos

### Sistema de Detección de Incendios
- 4-8 detectores de humo por piso
- 2-4 detectores de temperatura
- 1-2 paneles de control de incendios
- 2-4 estaciones manuales de alarma
- 4-8 rociadores inteligentes
- 1-2 módulos de control de puertas cortafuego
- 1 sistema de monitoreo de presión de agua contra incendios

**Total incendios por piso**: 15-28 dispositivos

## Resumen de Cantidades

### Por Habitación/Oficina: 10-20 dispositivos

### Por Piso (Sistemas Centrales):
- HVAC: 12-22 dispositivos
- Eléctrico: 10-20 dispositivos
- Agua: 8-16 dispositivos
- Iluminación (áreas comunes): 17-33 dispositivos
- Seguridad: 15-27 dispositivos
- Incendios: 15-28 dispositivos

**Total sistemas centrales por piso**: 77-146 dispositivos

### Edificio Típico (10 pisos, 20 habitaciones por piso):
- Habitaciones/oficinas: 2,000-4,000 dispositivos
- Sistemas centrales: 770-1,460 dispositivos
- Sistemas adicionales de edificio completo: ~100-200 dispositivos

**Total edificio típico**: ~3,000-5,500 dispositivos

Esta cantidad justifica la necesidad de una arquitectura escalable y modular para manejar el volumen de datos generados durante las simulaciones, especialmente cuando se simulan múltiples edificios simultáneamente.

# IoT Building Simulator API

API para simular dispositivos IoT en edificios virtuales.

## Endpoints

### Edificios

#### GET /buildings
Obtiene la lista de todos los edificios.

**Respuesta**
```json
{
  "buildings": [
    {
      "id": "string",
      "name": "string",
      "type": "string",
      "floors": [...],
      "devices_count": 0
    }
  ]
}
```

#### POST /buildings
Crea un nuevo edificio.

**Body**
```json
{
  "name": "string",
  "type": "string",
  "floors": [
    {
      "number": 0,
      "rooms": [
        {
          "number": 0,
          "devices": [
            {
              "type": "temperature_sensor | motion_sensor | smart_plug | hvac_controller"
            }
          ]
        }
      ]
    }
  ]
}
```

#### DELETE /buildings/{building_id}
Elimina un edificio y detiene sus simulaciones.

### Simulaciones

#### POST /simulation/start
Inicia una nueva simulación.

**Body**
```json
{
  "building_id": "string",
  "duration": 3600,
  "events_per_second": 1.0
}
```

#### POST /simulation/{simulation_id}/stop
Detiene una simulación en curso.

#### GET /simulation/{simulation_id}/status
Obtiene el estado de una simulación.

### WebSocket

#### WS /simulation/{simulation_id}
Conexión WebSocket para recibir datos en tiempo real.

**Mensajes recibidos**
```json
{
  "simulation_id": "string",
  "status": "running | stopped | completed",
  "active_devices": 0,
  "events_per_second": 1.0,
  "devices": [
    {
      "device_id": "string",
      "type": "string",
      "status": "active | inactive",
      "last_reading": {
        // Varía según el tipo de dispositivo
      }
    }
  ]
}
```

## Tipos de Dispositivos

### Temperature Sensor
```json
{
  "temperature": 23.5,
  "humidity": 45.0
}
```

### Motion Sensor
```json
{
  "motion_detected": true,
  "signal_strength": 95.5
}
```

### Smart Plug
```json
{
  "power_consumption": 120.5,
  "voltage": 115.0,
  "current": 1.05
}
```

### HVAC Controller
```json
{
  "mode": "heating | cooling | off",
  "target_temperature": 22.0,
  "fan_speed": "low | medium | high",
  "power_consumption": 1500.0
}
```

## Códigos de Error

- 400: Bad Request - Datos inválidos
- 404: Not Found - Recurso no encontrado
- 500: Internal Server Error - Error del servidor

## Ejemplos de Uso

### Crear un edificio
```bash
curl -X POST http://localhost:8000/buildings \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Office Building",
    "type": "commercial",
    "floors": [
      {
        "number": 1,
        "rooms": [
          {
            "number": 101,
            "devices": [
              {"type": "temperature_sensor"},
              {"type": "motion_sensor"}
            ]
          }
        ]
      }
    ]
  }'
```
