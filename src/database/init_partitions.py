from sqlalchemy import text
from .connection import engine
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def create_partitions():
    """Crea particiones mensuales para los próximos 12 meses"""
    try:
        with engine.connect() as conn:
            # Primero crear la tabla base para particionamiento
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sensor_readings_base (
                    id SERIAL,
                    device_id VARCHAR,
                    timestamp TIMESTAMP NOT NULL,
                    value FLOAT,
                    unit VARCHAR,
                    quality FLOAT,
                    extra_data JSON,
                    PRIMARY KEY (id, timestamp)
                ) PARTITION BY RANGE (timestamp);
            """))
            
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            for i in range(12):
                partition_start = start_date + timedelta(days=32*i)
                partition_start = partition_start.replace(day=1)
                partition_end = (partition_start + timedelta(days=32)).replace(day=1)
                
                partition_name = f"sensor_readings_{partition_start.strftime('%Y_%m')}"
                
                sql = text(f"""
                CREATE TABLE IF NOT EXISTS {partition_name}
                PARTITION OF sensor_readings_base
                FOR VALUES FROM ('{partition_start}') TO ('{partition_end}')
                """)
                
                conn.execute(sql)
                conn.commit()
                logger.info(f"Creada partición {partition_name}")
            
    except Exception as e:
        logger.error(f"Error creando particiones: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_partitions() 