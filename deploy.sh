#!/bin/bash

# Cargar variables de entorno
set -a
source .env
set +a

# Construir y desplegar
docker-compose build
docker-compose up -d

# Esperar a que los servicios estén listos
echo "Waiting for services to start..."
sleep 10

# Verificar estado de los servicios
docker-compose ps

# Mostrar logs iniciales
docker-compose logs --tail=100 