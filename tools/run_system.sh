#!/bin/bash

# Iniciar el backend
echo "🚀 Iniciando backend..."
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Esperar a que el backend esté listo
sleep 3

# Crear un edificio y obtener su ID
echo "🏢 Creando edificio de prueba..."
BUILDING_RESPONSE=$(curl -s -X POST http://localhost:8000/buildings \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Building","type":"office","floors":[{"number":0,"rooms":[{"number":0,"devices":[{"type":"temperature_sensor","status":"active"}]}]}]}')

if [ -z "$BUILDING_RESPONSE" ]; then
    echo "❌ Error: No se recibió respuesta al crear el edificio"
    kill $BACKEND_PID
    exit 1
fi

# Extraer ID usando Python
BUILDING_ID=$(python -c "
import json
try:
    data = json.loads('$BUILDING_RESPONSE')
    print(data['building']['id'])
except Exception as e:
    print(f'Error: {e}')
    exit(1)
")

echo "🏢 ID del Edificio: $BUILDING_ID"

# Iniciar simulación
echo "▶️ Iniciando simulación..."
SIMULATION_RESPONSE=$(curl -s -X POST http://localhost:8000/simulation/start \
  -H "Content-Type: application/json" \
  -d "{\"building_id\":\"$BUILDING_ID\",\"duration\":3600,\"events_per_second\":1.0}")

if [ -z "$SIMULATION_RESPONSE" ]; then
    echo "❌ Error: No se recibió respuesta al iniciar la simulación"
    kill $BACKEND_PID
    exit 1
fi

# Extraer ID usando Python
SIMULATION_ID=$(python -c "
import json
try:
    data = json.loads('$SIMULATION_RESPONSE')
    print(data['simulation_id'])
except Exception as e:
    print(f'Error: {e}')
    exit(1)
")

if [ -z "$SIMULATION_ID" ]; then
    echo "❌ Error: No se pudo obtener el ID de simulación"
    kill $BACKEND_PID
    exit 1
fi

echo "🔍 ID de Simulación: $SIMULATION_ID"

# Iniciar monitor
echo "📊 Iniciando monitor..."
python tools/monitor_simulation.py $SIMULATION_ID &
MONITOR_PID=$!

# Esperar input del usuario
echo "⏸️ Presiona ENTER para detener..."
read

# Limpiar procesos
kill $BACKEND_PID $MONITOR_PID 2>/dev/null 