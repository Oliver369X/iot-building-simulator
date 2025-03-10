FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY src/ src/
COPY database/ database/
COPY config/ config/

# Crear directorio para logs
RUN mkdir -p /var/log/iot-simulator

# Script de inicio
COPY docker/start-backend.sh /start-backend.sh
RUN chmod +x /start-backend.sh

CMD ["/start-backend.sh"] 