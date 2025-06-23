#!/usr/bin/env python3
"""
Script para poblar la base de datos de producción/demo con 2 edificios:
- Edificio Demo 1: 3 pisos, 5 habitaciones por piso, 4 dispositivos por habitación
- Edificio Demo 2: 6 pisos, 8 habitaciones por piso, 6 dispositivos por habitación
"""

import uuid
import random
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Building, Floor, Room, Device, DeviceType, Base

# Configuración de la base de datos (ajusta la URL si es necesario)
PRODUCTION_DATABASE_URL = "postgresql://iot_simulator_user:njsoSS2LgNFawnH69x84SSiRUwxKGPp3@dpg-d1c6tip5pdvs73ei8b30-a.oregon-postgres.render.com/iot_simulator"

print("🚀 Iniciando población DEMO de base de datos...")
print(f"🌐 Conectando a: {PRODUCTION_DATABASE_URL[:50]}...")

engine = create_engine(PRODUCTION_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def create_device_types():
    """Crear un subconjunto de tipos de dispositivos IoT para demo"""
    device_types_data = [
        {"type_name": "temperature_sensor", "properties": {"unit": "°C"}},
        {"type_name": "humidity_sensor", "properties": {"unit": "%"}},
        {"type_name": "power_meter", "properties": {"unit": "kWh"}},
        {"type_name": "light_sensor", "properties": {"unit": "lux"}},
        {"type_name": "occupancy_sensor", "properties": {"unit": "binary"}},
    ]
    device_type_ids = []
    for dt in device_types_data:
        device_type = DeviceType(
            id=str(uuid.uuid4()),
            type_name=dt["type_name"],
            properties=dt["properties"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(device_type)
        device_type_ids.append(device_type.id)
    db.commit()
    print(f"✅ {len(device_type_ids)} tipos de dispositivos creados")
    return device_type_ids, [dt["type_name"] for dt in device_types_data]

def create_demo_building(name, address, floors, rooms_per_floor, devices_per_room, device_type_ids, device_type_names):
    building = Building(
        id=str(uuid.uuid4()),
        name=name,
        address=address,
        geolocation=None,
        is_simulating=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(building)
    db.commit()
    print(f"🏢 Creando {name} ({floors} pisos, {rooms_per_floor} habitaciones/piso)")
    floor_ids = []
    room_ids = []
    device_ids = []
    for floor_num in range(1, floors + 1):
        floor = Floor(
            id=str(uuid.uuid4()),
            building_id=building.id,
            floor_number=floor_num,
            plan_url=None,
            is_simulating=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(floor)
        floor_ids.append(floor.id)
        for room_num in range(1, rooms_per_floor + 1):
            room = Room(
                id=str(uuid.uuid4()),
                floor_id=floor.id,
                name=f"Habitación {room_num} Piso {floor_num}",
                is_simulating=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(room)
            room_ids.append(room.id)
    db.commit()
    print(f"   ✅ {len(floor_ids)} pisos y {len(room_ids)} habitaciones creados")
    for floor_num in range(1, floors + 1):
        floor_id = floor_ids[floor_num - 1]
        floor_rooms = db.query(Room).filter(Room.floor_id == floor_id).all()
        for room in floor_rooms:
            for dev_num in range(1, devices_per_room + 1):
                device_type_idx = random.randint(0, len(device_type_ids) - 1)
                device = Device(
                    id=str(uuid.uuid4()),
                    name=f"Dispositivo {dev_num} Hab {room.name}",
                    device_type_id=device_type_ids[device_type_idx],
                    room_id=room.id,
                    state={"power": "ON", "status": "active"},
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(device)
                device_ids.append(device.id)
    db.commit()
    print(f"   ✅ {len(device_ids)} dispositivos creados")
    return {
        "building_id": building.id,
        "floors": len(floor_ids),
        "rooms": len(room_ids),
        "devices": len(device_ids)
    }

def main():
    print("🚀 Iniciando población DEMO...")
    try:
        print("\n📱 Creando tipos de dispositivos demo...")
        device_type_ids, device_type_names = create_device_types()
        print("\n🏢 Creando edificios demo...")
        buildings = []
        buildings.append(create_demo_building(
            name="Casa Grande 1",
            address="Calle Demo 123",
            floors=3,
            rooms_per_floor=5,
            devices_per_room=4,
            device_type_ids=device_type_ids,
            device_type_names=device_type_names
        ))
        buildings.append(create_demo_building(
            name="Edificio PCT",
            address="Avenida Prueba 456",
            floors=5,
            rooms_per_floor=8,
            devices_per_room=4,
            device_type_ids=device_type_ids,
            device_type_names=device_type_names
        ))
        print("\n" + "="*50)
        print("✅ POBLACIÓN DEMO COMPLETADA")
        print("="*50)
        total_floors = sum(b["floors"] for b in buildings)
        total_rooms = sum(b["rooms"] for b in buildings)
        total_devices = sum(b["devices"] for b in buildings)
        print(f"📊 RESUMEN:")
        print(f"   • Edificios creados: {len(buildings)}")
        print(f"   • Pisos totales: {total_floors}")
        print(f"   • Habitaciones totales: {total_rooms}")
        print(f"   • Dispositivos totales: {total_devices}")
    except Exception as e:
        print(f"❌ Error durante la población DEMO: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main() 