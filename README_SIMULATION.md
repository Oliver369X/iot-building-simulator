# Informe y Plan de Implementación: Simulación, Monitoreo y Exposición de Datos para Dashboard

## 1. Diagnóstico del Estado Actual

### a) Core de Simulación
- El core está en `src/simulator/engine.py` (clase `SimulationEngine`).
- Usa un `Scheduler` para eventos recurrentes (ver `src/simulator/scheduler.py`).
- Genera telemetría simulada por dispositivo según su tipo (temperatura, humedad, consumo, etc.).
- La función `get_kpi_dashboard_data` existe pero devuelve datos "placeholder" (aleatorios), no datos reales agregados de la simulación.
- La telemetría se almacena en la base de datos (modelo `SensorReading`).

### b) API
- La API principal está en `src/api/main.py`.
- Hay endpoint para KPIs: `/api/v1/kpi/dashboard` (GET), pero actualmente responde con datos simulados, no reales.
- Hay endpoint para telemetría histórica de dispositivos: `/api/v1/telemetry/device/{device_id}` (GET).
- Hay WebSocket para telemetría en tiempo real: `/ws/telemetry`.

### c) Frontend
- El frontend puede consumir los endpoints REST y WebSocket para mostrar datos en gráficos.
- Actualmente, los datos de consumo energético y KPIs no reflejan la simulación real.

## 2. Plan de Implementación

### Paso 1: Mejorar la generación y almacenamiento de telemetría
- Asegurarse de que la función de simulación (`run_continuous_simulation_loop` y `generate_telemetry_for_simulating_devices`) almacene correctamente los datos de consumo energético (por dispositivo, habitación, piso, edificio).
- Validar que los dispositivos relevantes (ej. medidores de energía) generen la clave `power_consumption` en la telemetría.

### Paso 2: Agregación de Consumo Energético
- Implementar funciones en `SimulationEngine` para calcular el consumo energético:
  - Por dispositivo (ya existe vía telemetría).
  - Por habitación: sumar el consumo de todos los dispositivos de la habitación.
  - Por piso: sumar el consumo de todas las habitaciones del piso.
  - Por edificio: sumar el consumo de todos los pisos.
- Estas funciones deben consultar la base de datos de telemetría (`SensorReading`) y devolver los valores agregados para un rango de tiempo.

### Paso 3: Exponer los datos en la API
- Crear o mejorar endpoints REST:
  - `/api/v1/consumption/building/{building_id}`: Consumo total y por piso/habitación/dispositivo.
  - `/api/v1/consumption/floor/{floor_id}`: Consumo total y por habitación/dispositivo.
  - `/api/v1/consumption/room/{room_id}`: Consumo total y por dispositivo.
  - `/api/v1/consumption/device/{device_id}`: Consumo histórico del dispositivo.
- Permitir filtros por rango de fechas (`start_time`, `end_time`).
- Mejorar `/api/v1/kpi/dashboard` para que use datos reales agregados.

### Paso 4: Consumo desde el Frontend
- El frontend debe consumir los endpoints de consumo y KPIs para mostrar gráficos comparativos:
  - Gráficos de consumo energético por edificio, piso, habitación, dispositivo.
  - KPIs en tarjetas o widgets.
- Para datos en tiempo real, usar el WebSocket (`/ws/telemetry`).
- Para históricos y comparativos, usar los endpoints REST.

### Paso 5: Documentación y Ejemplo de Consumo
- Documentar los endpoints y el formato de respuesta esperado.
- Proveer ejemplos de cómo consumir los endpoints desde el frontend (fetch/Axios, etc.).

---

## 3. Monitoreo en Tiempo Real y Estado del Sistema

### a) Monitoreo en Tiempo Real
- Usar el WebSocket `/ws/telemetry` para enviar al frontend:
  - Telemetría en vivo de dispositivos (ejemplo: consumo, temperatura, estado ON/OFF).
  - Cambios de estado relevantes (ejemplo: dispositivo encendido/apagado, alarma activada).
- Estructura sugerida del mensaje:
  ```json
  {
    "device_id": "...",
    "key": "power_consumption",
    "value": 0.123,
    "timestamp": "2024-06-01T12:00:00Z"
  }
  ```
- El frontend debe suscribirse y actualizar gráficos/estados en tiempo real.

### b) Monitoreo de Estados y Alarmas
- Endpoints REST para consultar el estado actual de:
  - Dispositivos (ON/OFF, valores actuales, última telemetría).
  - Habitaciones, pisos, edificios (resumen de estados de sus dispositivos).
- Endpoints para consultar alarmas activas y su severidad:
  - `/api/v1/alarms?status=NEW` para alarmas activas.
  - `/api/v1/alarms` para histórico y filtrado.

### c) KPIs de Monitoreo
- KPIs de salud del sistema:
  - Dispositivos activos/inactivos.
  - Dispositivos que no han reportado datos recientemente (posible fallo).
  - Número de alarmas activas por severidad.
- Exponer estos KPIs en `/api/v1/kpi/dashboard`.

### d) Ejemplo de Consumo desde el Frontend
- **WebSocket:**
  ```js
  const ws = new WebSocket('ws://localhost:8000/ws/telemetry');
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Actualizar gráficos o estados en la UI
  };
  ```
- **REST:**
  ```js
  // Obtener consumo energético de un edificio
  fetch('/api/v1/consumption/building/{building_id}?start_time=...&end_time=...')
    .then(res => res.json())
    .then(data => {
      // Renderizar gráfico
    });
  // Obtener alarmas activas
  fetch('/api/v1/alarms?status=NEW')
    .then(res => res.json())
    .then(data => {
      // Mostrar alarmas
    });
  ```

---

## 4. Siguientes pasos sugeridos
1. Implementar la agregación real de consumo energético en el backend.
2. Exponer los endpoints REST para consumo agregado y monitoreo.
3. Mejorar el WebSocket para enviar telemetría y estados relevantes.
4. Actualizar el frontend para consumir y graficar estos datos en tiempo real e histórico.
5. Validar con datos simulados y reales.

---

**Este documento debe ser revisado antes de implementar cambios.** 