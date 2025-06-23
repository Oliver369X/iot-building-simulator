FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Puerto por defecto para la API
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD python -m src.database.init_db && uvicorn src.api.main:app --host 0.0.0.0 --port 8000