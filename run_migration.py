#!/usr/bin/env python3
"""
Script para ejecutar la migración de client_id.
Ejecutar: python run_migration.py
"""

import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.migration_add_client_id import migrate_add_client_id

if __name__ == "__main__":
    print("🚀 Ejecutando migración para agregar client_id...")
    try:
        migrate_add_client_id()
        print("✅ Migración completada exitosamente")
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        sys.exit(1) 