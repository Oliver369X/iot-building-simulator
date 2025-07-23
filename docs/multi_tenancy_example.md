# Multi-Tenancy en IoT Building Simulator

## 📋 Descripción

El sistema ahora soporta **multi-tenancy** (multi-inquilino), permitiendo que múltiples clientes usen la misma instancia del sistema de forma aislada. Cada edificio pertenece a un cliente específico identificado por `client_id`.

## 🔧 Implementación

### Base de Datos
- Campo `client_id` agregado a la tabla `buildings`
- Índice creado para optimizar consultas por cliente
- Filtrado automático en todas las consultas

### API
- Header `X-Client-ID` requerido en todas las peticiones
- Filtrado automático por cliente en todos los endpoints
- Validación de pertenencia de recursos al cliente

## 🚀 Uso de la API

### Headers Requeridos
```bash
X-Client-ID: your_client_id_here
```

### Ejemplos de Uso

#### 1. Crear un Edificio
```bash
curl -X POST "http://localhost:8000/api/v1/buildings" \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: client_123" \
  -d '{
    "name": "Edificio Principal",
    "address": "Calle Principal 123",
    "geolocation": {"latitude": 40.7128, "longitude": -74.0060}
  }'
```

#### 2. Listar Edificios del Cliente
```bash
curl -X GET "http://localhost:8000/api/v1/buildings" \
  -H "X-Client-ID: client_123"
```

#### 3. Obtener KPIs del Cliente
```bash
curl -X GET "http://localhost:8000/api/v1/kpi/dashboard" \
  -H "X-Client-ID: client_123"
```

#### 4. Listar Alarmas del Cliente
```bash
curl -X GET "http://localhost:8000/api/v1/alarms" \
  -H "X-Client-ID: client_123"
```

## 🔒 Seguridad

### Filtrado Automático
- Todos los endpoints filtran automáticamente por `client_id`
- Un cliente no puede acceder a recursos de otro cliente
- Validación en cada operación CRUD

### Validación de Headers
```python
# Middleware automático
async def get_client_id(x_client_id: Optional[str] = Header(None, alias="X-Client-ID")) -> str:
    if not x_client_id:
        raise HTTPException(status_code=400, detail="X-Client-ID header is required")
    return x_client_id
```

## 📊 Integración con Frontend

### JavaScript/TypeScript
```javascript
// Configurar headers por defecto
const API_BASE = 'http://localhost:8000/api/v1';
const CLIENT_ID = 'client_123'; // Obtener del sistema de autenticación

const apiClient = {
  headers: {
    'Content-Type': 'application/json',
    'X-Client-ID': CLIENT_ID
  },
  
  async getBuildings() {
    const response = await fetch(`${API_BASE}/buildings`, {
      headers: this.headers
    });
    return response.json();
  },
  
  async createBuilding(buildingData) {
    const response = await fetch(`${API_BASE}/buildings`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(buildingData)
    });
    return response.json();
  }
};
```

### React Hook Example
```javascript
import { useState, useEffect } from 'react';

const useBuildings = (clientId) => {
  const [buildings, setBuildings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchBuildings = async () => {
      try {
        const response = await fetch('/api/v1/buildings', {
          headers: {
            'X-Client-ID': clientId
          }
        });
        const data = await response.json();
        setBuildings(data);
      } catch (error) {
        console.error('Error fetching buildings:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchBuildings();
  }, [clientId]);

  return { buildings, loading };
};
```

## 🔄 Migración

### Ejecutar Migración
```bash
# Ejecutar la migración para agregar client_id
python run_migration.py
```

### Datos Existentes
- Los edificios existentes se asignan automáticamente a `default_client`
- Actualizar manualmente los `client_id` según sea necesario

## 🎯 Beneficios

1. **Aislamiento**: Cada cliente ve solo sus propios datos
2. **Escalabilidad**: Múltiples clientes en una sola instancia
3. **Seguridad**: Filtrado automático en todas las consultas
4. **Flexibilidad**: Fácil integración con sistemas de autenticación externos
5. **Facturación**: Facilita el cobro por cliente

## 🔮 Próximos Pasos

1. **Autenticación JWT**: Integrar con sistema de autenticación
2. **Rate Limiting**: Límites por cliente
3. **Quotas**: Límites de recursos por cliente
4. **Billing**: Integración con sistema de facturación
5. **Audit Logs**: Logs de acceso por cliente 