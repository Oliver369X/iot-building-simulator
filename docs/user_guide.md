# Guía de Usuario - IoT Building Simulator

## Introducción

El IoT Building Simulator es una herramienta para simular dispositivos IoT en edificios, permitiendo generar datos realistas para pruebas y desarrollo. Esta guía te ayudará a configurar y ejecutar simulaciones.

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