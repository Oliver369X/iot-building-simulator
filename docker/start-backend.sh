#!/bin/bash

# Esperar a que la base de datos esté lista
echo "Waiting for database..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done
echo "Database is ready!"

# Aplicar migraciones
echo "Applying database migrations..."
python -m src.database.migrations

# Iniciar la API
echo "Starting API server..."
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4 