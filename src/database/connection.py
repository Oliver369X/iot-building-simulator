import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

def get_database_url():
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', '071104')
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'iot_simulator')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

try:
    engine = create_engine(
        get_database_url(),
        pool_size=5,
        max_overflow=10,
        echo=True  # Para ver las consultas SQL
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Conexión a la base de datos establecida correctamente")
except Exception as e:
    logger.error(f"Error conectando a la base de datos: {str(e)}")
    raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 