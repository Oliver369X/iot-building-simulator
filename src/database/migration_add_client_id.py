"""
Script de migración para agregar el campo client_id a la tabla buildings.
Este script debe ejecutarse después de actualizar el modelo Building.
"""

from sqlalchemy import text
from .connection import engine
import logging

logger = logging.getLogger(__name__)

def migrate_add_client_id():
    """
    Migración para agregar el campo client_id a la tabla buildings.
    Asigna un client_id por defecto a edificios existentes.
    """
    try:
        with engine.connect() as conn:
            # Verificar si la columna ya existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'buildings' AND column_name = 'client_id'
            """))
            
            if result.fetchone():
                logger.info("Column client_id already exists in buildings table")
                return
            
            # Agregar la columna client_id
            logger.info("Adding client_id column to buildings table...")
            conn.execute(text("""
                ALTER TABLE buildings 
                ADD COLUMN client_id VARCHAR NOT NULL DEFAULT 'default_client'
            """))
            
            # Crear índice para mejorar rendimiento de consultas por cliente
            logger.info("Creating index on client_id column...")
            conn.execute(text("""
                CREATE INDEX idx_buildings_client_id ON buildings(client_id)
            """))
            
            # Actualizar edificios existentes con un client_id por defecto
            # En producción, esto debería asignar client_ids reales basados en lógica de negocio
            logger.info("Updating existing buildings with default client_id...")
            conn.execute(text("""
                UPDATE buildings 
                SET client_id = 'default_client' 
                WHERE client_id IS NULL OR client_id = ''
            """))
            
            conn.commit()
            logger.info("Migration completed successfully")
            
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_add_client_id() 