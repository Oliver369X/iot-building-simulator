from typing import Dict
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Carga configuración desde variables de entorno"""
        import os
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'iot_simulator'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )

TIMESCALE_TABLES = {
    'device_data': {
        'time_column': 'timestamp',
        'partition_interval': '1 day'
    }
} 