import logging
import logging.config
import json
from pathlib import Path
from pythonjsonlogger import jsonlogger
from datetime import datetime

def setup_logging(
    log_dir: str = "logs",
    level: str = "INFO",
    json_format: bool = True
) -> None:
    """Configura el sistema de logging"""
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Nombre del archivo de log basado en la fecha
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"simulator_{timestamp}.log"
    
    # Formato para logs JSON
    class CustomJsonFormatter(jsonlogger.JsonFormatter):
        def add_fields(self, log_record, record, message_dict):
            super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
            log_record['timestamp'] = datetime.now().isoformat()
            log_record['level'] = record.levelname
            log_record['module'] = record.module
            log_record['function'] = record.funcName
            
    # Configuración de logging
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': CustomJsonFormatter,
                'format': '%(timestamp)s %(level)s %(name)s %(message)s'
            },
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'json' if json_format else 'standard',
                'level': level
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': str(log_file),
                'formatter': 'json' if json_format else 'standard',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'level': level
            }
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console', 'file'],
                'level': level,
                'propagate': True
            },
            'src.simulator': {
                'handlers': ['console', 'file'],
                'level': level,
                'propagate': False
            },
            'src.devices': {
                'handlers': ['console', 'file'],
                'level': level,
                'propagate': False
            }
        }
    }
    
    logging.config.dictConfig(config) 