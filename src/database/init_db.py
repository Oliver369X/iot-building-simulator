from sqlalchemy import text
from .models import Base
from .connection import engine
import logging

logger = logging.getLogger(__name__)

def clean_database():
    """Elimina todas las tablas existentes"""
    try:
        logger.info("Limpiando la base de datos...")
        Base.metadata.drop_all(engine) # Elimina todas las tablas definidas en Base.metadata
        logger.info("Base de datos limpiada correctamente.")
    except Exception as e:
        logger.error(f"Error limpiando base de datos: {str(e)}")
        raise

def init_db():
    """Inicializa la base de datos"""
    try:
        clean_database()  # Primero limpiamos
        Base.metadata.create_all(engine)
        logger.info("Base de datos inicializada correctamente")
        
        # Verificar la conexión
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))  # Usar text() para la consulta SQL
            version = result.scalar()
            logger.info(f"Conectado a PostgreSQL versión: {version}")
            
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
