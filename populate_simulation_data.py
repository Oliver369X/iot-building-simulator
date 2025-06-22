import uuid
from datetime import datetime
from random import choice
from src.database.connection import SessionLocal
from src.database.models import Building, Floor, Room, Device, DeviceType

db = SessionLocal()

# 1. Crear tipos de dispositivos
device_types_data = [
    {"type_name": "Sensor de Temperatura"},
    {"type_name": "Sensor de Humedad"},
    {"type_name": "Actuador de Luz"},
    {"type_name": "Medidor de Energía"},
    {"type_name": "Sensor de Movimiento"}
]
device_type_ids = []
for dt in device_types_data:
    device_type = DeviceType(
        id=str(uuid.uuid4()),
        type_name=dt["type_name"],
        properties=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(device_type)
    device_type_ids.append(device_type.id)
db.commit()
print("Tipos de dispositivo creados:", device_type_ids)

# 2. Crear edificio
building = Building(
    id=str(uuid.uuid4()),
    name="Edificio Simulado",
    address="Calle Falsa 123",
    geolocation=None,
    is_simulating=True,
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)
db.add(building)
db.commit()
print("Edificio creado:", building.id)

# 3. Crear pisos, habitaciones y dispositivos
floor_ids = []
room_ids = []
device_ids = []

for floor_num in range(1, 21):  # 20 pisos
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
    db.commit()

    for room_num in range(1, 7):  # 6 habitaciones por piso
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

        for dev_num in range(1, 6):  # 5 dispositivos por habitación
            device = Device(
                id=str(uuid.uuid4()),
                name=f"Dispositivo {dev_num} Hab {room_num} Piso {floor_num}",
                device_type_id=choice(device_type_ids),
                room_id=room.id,
                state={"power": "ON"},
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(device)
            device_ids.append(device.id)
        db.commit()

print("Pisos creados:", floor_ids)
print("Habitaciones creadas:", room_ids)
print("Dispositivos creados:", device_ids)
print("¡Base de datos poblada exitosamente!")

db.close()