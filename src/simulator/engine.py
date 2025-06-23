from typing import Dict, List, Any, Optional, Type
from datetime import datetime, timedelta, timezone
import logging
import json
import uuid
from pathlib import Path
import asyncio
import random # Keep for simulation logic if needed later
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, Session, selectinload # Importar selectinload
from sqlalchemy import func, String, cast

# Import core building class if it's used for internal logic, otherwise rely on DB models
# from ..core.building import Building as CoreBuilding # Example if core classes are distinct
from .scheduler import Scheduler
# from .traffic import BuildingTrafficSimulator # To be re-evaluated based on new spec

# Updated database model imports
from ..database.models import Base
from ..database.models import Building, Floor, Room, Device, DeviceType, DeviceSchedule, Alarm, AggregatedReading
from ..database.models import SensorReading # Kept for now
from ..database.connection import SessionLocal

# Import Pydantic models for type hinting in CRUD operations
from ..api import validators as api_validators


class SimulationError(Exception):
    """Error base para excepciones de simulación"""
    pass

class DeviceError(SimulationError):
    """Error relacionado con dispositivos"""
    pass

class SimulationNotFoundError(SimulationError): # May not be relevant with continuous simulation
    """Error cuando no se encuentra una simulación"""
    pass

class SimulationEngine:
    def __init__(
        self,
        db_session_local: sessionmaker, # Changed from db=None
        config_path: Optional[str] = None,
        time_scale: float = 1.0, # For scheduler, if used
        data_dir: str = "./data" # May be deprecated if all data goes to DB
    ):
        self.engine_id = str(uuid.uuid4()) # ID for this engine instance
        self.db_session_local = db_session_local
        
        # self.buildings: Dict[str, CoreBuilding] = {} # If using core classes for logic
        # For now, direct DB interaction is prioritized.
        
        self.scheduler = Scheduler(time_scale) # For device_schedules and simulation ticks
        # self.traffic_simulators: Dict[str, BuildingTrafficSimulator] = {} # Re-evaluate
        
        self.data_dir = Path(data_dir) # For any non-DB file storage if needed
        # self.data_dir.mkdir(parents=True, exist_ok=True) # Create if still used
        
        self.logger = logging.getLogger(__name__)
        
        self.status = "initialized" # Engine status
        self._telemetry_queue: Optional[asyncio.Queue] = None # For real-time telemetry via WebSocket
        self._main_loop_task: Optional[asyncio.Task] = None  # Referencia a la tarea principal
        self._aggregation_worker_task: Optional[asyncio.Task] = None  # Referencia al worker de agregación
        self._aggregation_worker_running: bool = False  # Flag de control para el worker
        
        if config_path:
            self.load_config(config_path) # If there's a global engine config
        
        self.logger.info(f"SimulationEngine instance {self.engine_id} initialized.")

            
    def load_config(self, config_path: str) -> None:
        """Carga la configuración global del motor de simulación si existe"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            self.config = config # Store global engine config
            self.logger.info(f"Engine configuration loaded from {config_path}")
        except Exception as e:
            self.logger.error(f"Error loading engine configuration: {str(e)}")
            # Decide if this is a critical error or can proceed with defaults
            # raise

    # --- Database Session Management ---
    def _get_db(self, db: Optional[Session] = None) -> Session:
        """Retorna uma sessão de DB, usando a inyectada se está disponível, ou criando uma nova."""
        if db:
            return db
        return self.db_session_local()

    # --- CRUD Operations for Buildings ---
    def create_building(self, building_data: api_validators.BuildingCreate, db: Optional[Session] = None) -> Building:
        db = self._get_db(db)
        try:
            db_building = Building(
                id=str(uuid.uuid4()), # Generate UUID for the building
                name=building_data.name,
                address=building_data.address,
                geolocation=building_data.geolocation
                # created_at and updated_at have defaults in the model
            )
            db.add(db_building)
            db.commit()
            db.refresh(db_building)
            self.logger.info(f"Building created with ID: {db_building.id}")
            return db_building
        except IntegrityError as e:
            db.rollback()
            self.logger.error(f"Error creating building (IntegrityError): {e}")
            raise SimulationError(f"Database integrity error: {e.orig}")
        except Exception as e:
            db.rollback()
            self.logger.error(f"Unexpected error creating building: {e}")
            raise SimulationError(f"Could not create building: {e}")
        finally:
            db.close()

    def get_building_by_id(self, building_id: str, db: Optional[Session] = None) -> Optional[Building]:
        db = self._get_db(db)
        try:
            building = db.query(Building).filter(Building.id == building_id).first()
            return building
        finally:
            if not db: db.close() # Close only if session was created internally

    def get_all_buildings(self, skip: int = 0, limit: int = 100, db: Optional[Session] = None) -> List[Building]:
        db = self._get_db(db)
        try:
            buildings = db.query(Building).offset(skip).limit(limit).all()
            return buildings
        finally:
            if not db: db.close()

    def update_building(self, building_id: str, building_update_data: api_validators.BuildingUpdate, db: Optional[Session] = None) -> Optional[Building]:
        db = self._get_db(db)
        try:
            db_building = db.query(Building).filter(Building.id == building_id).first()
            if not db_building:
                return None

            update_data = building_update_data.dict(exclude_unset=True) # Pydantic v1 style
            
            for key, value in update_data.items():
                setattr(db_building, key, value)
            
            # Manually update the updated_at timestamp
            db_building.updated_at = datetime.now(timezone.utc)

            db.add(db_building) # Add to session if it was detached or to mark as dirty
            db.commit()
            db.refresh(db_building)
            self.logger.info(f"Building with ID: {building_id} updated.")
            return db_building
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating building {building_id}: {e}")
            raise SimulationError(f"Could not update building {building_id}: {e}")
        finally:
            db.close()

    def delete_building(self, building_id: str, db: Optional[Session] = None) -> bool:
        db = self._get_db(db)
        try:
            db_building = db.query(Building).filter(Building.id == building_id).first()
            if not db_building:
                self.logger.warning(f"Attempted to delete non-existent building with ID: {building_id}")
                return False
            
            db.delete(db_building)
            db.commit()
            self.logger.info(f"Building with ID: {building_id} and its hierarchy deleted.")
            return True
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error deleting building {building_id}: {e}")
            # Depending on the exception, you might want to raise SimulationError or just return False
            # For now, let's raise to make it visible if something unexpected happens during delete.
            raise SimulationError(f"Could not delete building {building_id}: {e}")
        finally:
            db.close()

    # --- CRUD Operations for Floors ---
    def create_floor(self, building_id: str, floor_data: api_validators.FloorCreate, db: Optional[Session] = None) -> Floor:
        db = self._get_db(db)
        try:
            db_floor = Floor(
                id=str(uuid.uuid4()),
                building_id=building_id,
                floor_number=floor_data.floor_number,
                plan_url=floor_data.plan_url
            )
            db.add(db_floor)
            db.commit()
            db.refresh(db_floor)
            self.logger.info(f"Floor created with ID: {db_floor.id} for building {building_id}")
            return db_floor
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating floor for building {building_id}: {e}")
            raise SimulationError(f"Could not create floor: {e}")
        finally:
            db.close()

    def get_floors_by_building_id(self, building_id: str, skip: int = 0, limit: int = 100, db: Optional[Session] = None) -> List[Floor]:
        db = self._get_db(db)
        try:
            return db.query(Floor).filter(Floor.building_id == building_id).offset(skip).limit(limit).all()
        finally:
            if not db:
                db.close()

    def get_floor_by_id(self, floor_id: str, db: Optional[Session] = None) -> Optional[Floor]:
        db = self._get_db(db)
        try:
            return db.query(Floor).filter(Floor.id == floor_id).first()
        finally:
            if not db:
                db.close()

    def update_floor(self, floor_id: str, floor_data: api_validators.FloorUpdate, db: Optional[Session] = None) -> Optional[Floor]:
        db = self._get_db(db)
        try:
            db_floor = db.query(Floor).filter(Floor.id == floor_id).first()
            if not db_floor: return None
            update_data = floor_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_floor, key, value)
            db_floor.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_floor)
            return db_floor
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not update floor: {e}")
        finally: db.close()

    def update_floor_simulation_status(self, floor_id: str, is_simulating: bool, db: Optional[Session] = None) -> Optional[Floor]:
        db = self._get_db(db)
        try:
            db_floor = db.query(Floor).filter(Floor.id == floor_id).first()
            if not db_floor: return None
            db_floor.is_simulating = is_simulating
            db_floor.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_floor)
            self.logger.info(f"Floor {floor_id} simulation status set to {is_simulating}.")
            return db_floor
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not update floor simulation status: {e}")
        finally: db.close()

    def update_floor_simulation_status(self, floor_id: str, is_simulating: bool, db: Optional[Session] = None) -> Optional[Floor]:
        db = self._get_db(db)
        try:
            db_floor = db.query(Floor).filter(Floor.id == floor_id).first()
            if not db_floor: return None
            db_floor.is_simulating = is_simulating
            db_floor.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_floor)
            self.logger.info(f"Floor {floor_id} simulation status set to {is_simulating}.")
            return db_floor
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not update floor simulation status: {e}")
        finally: db.close()

    def delete_floor(self, floor_id: str, db: Optional[Session] = None) -> bool:
        db = self._get_db(db)
        try:
            db_floor = db.query(Floor).filter(Floor.id == floor_id).first()
            if not db_floor: return False
            db.delete(db_floor); db.commit()
            return True
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not delete floor: {e}")
        finally: db.close()

    # --- CRUD Operations for Rooms ---
    def create_room(self, floor_id: str, room_data: api_validators.RoomCreate, db: Optional[Session] = None) -> Room:
        db = self._get_db(db)
        try:
            db_room = Room(id=str(uuid.uuid4()), floor_id=floor_id, name=room_data.name)
            db.add(db_room); db.commit(); db.refresh(db_room)
            return db_room
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not create room: {e}")
        finally: db.close()

    def get_rooms_by_floor_id(self, floor_id: str, skip: int = 0, limit: int = 100, db: Optional[Session] = None) -> List[Room]:
        db = self._get_db(db)
        try:
            return db.query(Room).filter(Room.floor_id == floor_id).offset(skip).limit(limit).all()
        finally:
            if not db:
                db.close()

    def get_room_by_id(self, room_id: str, db: Optional[Session] = None) -> Optional[Room]:
        db = self._get_db(db)
        try:
            return db.query(Room).filter(Room.id == room_id).first()
        finally:
            if not db:
                db.close()

    def update_room(self, room_id: str, room_data: api_validators.RoomUpdate, db: Optional[Session] = None) -> Optional[Room]:
        db = self._get_db(db)
        try:
            db_room = db.query(Room).filter(Room.id == room_id).first()
            if not db_room: return None
            update_data = room_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_room, key, value)
            db_room.updated_at = datetime.now(timezone.utc)
            db.commit(); db.refresh(db_room)
            return db_room
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not update room: {e}")
        finally: db.close()

    def update_room_simulation_status(self, room_id: str, is_simulating: bool, db: Optional[Session] = None) -> Optional[Room]:
        db = self._get_db(db)
        try:
            db_room = db.query(Room).filter(Room.id == room_id).first()
            if not db_room: return None
            db_room.is_simulating = is_simulating
            db_room.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_room)
            self.logger.info(f"Room {room_id} simulation status set to {is_simulating}.")
            return db_room
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not update room simulation status: {e}")
        finally: db.close()

    def update_room_simulation_status(self, room_id: str, is_simulating: bool, db: Optional[Session] = None) -> Optional[Room]:
        db = self._get_db(db)
        try:
            db_room = db.query(Room).filter(Room.id == room_id).first()
            if not db_room: return None
            db_room.is_simulating = is_simulating
            db_room.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_room)
            self.logger.info(f"Room {room_id} simulation status set to {is_simulating}.")
            return db_room
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not update room simulation status: {e}")
        finally: db.close()

    def delete_room(self, room_id: str, db: Optional[Session] = None) -> bool:
        db = self._get_db(db)
        try:
            db_room = db.query(Room).filter(Room.id == room_id).first()
            if not db_room: return False
            db.delete(db_room); db.commit()
            return True
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not delete room: {e}")
        finally: db.close()

    # --- CRUD Operations for DeviceTypes ---
    def create_device_type(self, device_type_data: api_validators.DeviceTypeCreate, db: Optional[Session] = None) -> DeviceType:
        db = self._get_db(db)
        try:
            # Use provided ID or generate new one if not present and model allows
            type_id = device_type_data.id if device_type_data.id else str(uuid.uuid4())
            db_device_type = DeviceType(
                id=type_id,
                type_name=device_type_data.type_name,
                properties=device_type_data.properties
            )
            db.add(db_device_type); db.commit(); db.refresh(db_device_type)
            return db_device_type
        except IntegrityError as e: # Catch if ID is duplicate and unique constraint exists
            db.rollback()
            self.logger.error(f"Error creating device type (IntegrityError, possibly duplicate ID {device_type_data.id}): {e}")
            raise SimulationError(f"Device type with ID {device_type_data.id} may already exist or other integrity issue.")
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not create device type: {e}")
        finally: db.close()

    def get_device_type_by_id(self, device_type_id: str, db: Optional[Session] = None) -> Optional[DeviceType]:
        db = self._get_db(db)
        try:
            return db.query(DeviceType).filter(DeviceType.id == device_type_id).first()
        finally:
            if not db:
                db.close()

    def get_all_device_types(self, skip: int = 0, limit: int = 100, db: Optional[Session] = None) -> List[DeviceType]:
        db = self._get_db(db)
        try:
            return db.query(DeviceType).offset(skip).limit(limit).all()
        finally:
            if not db:
                db.close()

    def update_device_type(self, device_type_id: str, device_type_data: api_validators.DeviceTypeUpdate, db: Optional[Session] = None) -> Optional[DeviceType]:
        db = self._get_db(db)
        try:
            db_dt = db.query(DeviceType).filter(DeviceType.id == device_type_id).first()
            if not db_dt: return None
            update_data = device_type_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_dt, key, value)
            db_dt.updated_at = datetime.now(timezone.utc)
            db.commit(); db.refresh(db_dt)
            return db_dt
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not update device type: {e}")
        finally: db.close()

    def delete_device_type(self, device_type_id: str, db: Optional[Session] = None) -> bool:
        db = self._get_db(db)
        try:
            # Check if any device uses this type
            device_using_type = db.query(Device).filter(Device.device_type_id == device_type_id).first()
            if device_using_type:
                self.logger.warning(f"Attempt to delete device type {device_type_id} which is in use by device {device_using_type.id}")
                raise SimulationError(f"DeviceType {device_type_id} is in use and cannot be deleted.")

            db_dt = db.query(DeviceType).filter(DeviceType.id == device_type_id).first()
            if not db_dt: return False
            db.delete(db_dt); db.commit()
            return True
        except IntegrityError as e: # Should be caught by the check above, but as a safeguard
            db.rollback()
            self.logger.error(f"Integrity error deleting device type {device_type_id}: {e}")
            raise SimulationError(f"Cannot delete device type {device_type_id} due to database constraints (likely still in use).")
        except SimulationError: # Re-raise specific SimulationError
            raise
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not delete device type: {e}")
        finally: db.close()

    # --- CRUD Operations for Devices ---
    def create_device(self, room_id: str, device_data: api_validators.DeviceCreate, db: Optional[Session] = None) -> Device:
        db = self._get_db(db)
        try:
            db_device = Device(
                id=str(uuid.uuid4()), room_id=room_id, name=device_data.name,
                device_type_id=device_data.device_type_id, state=device_data.state,
                is_active=device_data.is_active
            )
            db.add(db_device); db.commit(); db.refresh(db_device)
            return db_device
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not create device: {e}")
        finally: db.close()

    def get_devices_by_room_id(self, room_id: str, skip: int = 0, limit: int = 100, db: Optional[Session] = None) -> List[Device]:
        db = self._get_db(db)
        try:
            return db.query(Device).filter(Device.room_id == room_id).offset(skip).limit(limit).all()
        finally:
            if not db:
                db.close()

    def get_device_by_id(self, device_id: str, db: Optional[Session] = None) -> Optional[Device]:
        db = self._get_db(db)
        try:
            return db.query(Device).filter(Device.id == device_id).first()
        finally:
            if not db:
                db.close()

    def update_device(self, device_id: str, device_data: api_validators.DeviceUpdate, db: Optional[Session] = None) -> Optional[Device]:
        db = self._get_db(db)
        try:
            db_device = db.query(Device).filter(Device.id == device_id).first()
            if not db_device: return None
            update_data = device_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_device, key, value)
            db_device.updated_at = datetime.now(timezone.utc)
            db.commit(); db.refresh(db_device)
            return db_device
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not update device: {e}")
        finally: db.close()

    def delete_device(self, device_id: str, db: Optional[Session] = None) -> bool:
        db = self._get_db(db)
        try:
            db_device = db.query(Device).filter(Device.id == device_id).first()
            if not db_device: return False
            db.delete(db_device); db.commit()
            return True
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not delete device: {e}")
        finally: db.close()

    def execute_device_action(self, device_id: str, action_data: api_validators.DeviceAction, db: Optional[Session] = None) -> Optional[Device]:
        db = self._get_db(db)
        try:
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                raise SimulationError(f"Device {device_id} not found for action.")

            if action_data.type == "setState":
                if device.state is None: device.state = {} # Ensure state is a dict
                # Actualizar el estado y reasignar para que SQLAlchemy detecte el cambio
                new_state = device.state.copy()
                new_state.update(action_data.payload)
                device.state = new_state # Reasignar el objeto para marcarlo como modificado
                
                device.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(device)
                self.logger.info(f"Device {device_id} state updated by action: {action_data.payload}")
                # TODO: Publish device.state_change event to message broker
                return device
            else:
                self.logger.warning(f"Unsupported action type '{action_data.type}' for device {device_id}")
                raise SimulationError(f"Unsupported action type: {action_data.type}")
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error executing action for device {device_id}: {e}")
            raise SimulationError(f"Could not execute action on device {device_id}: {e}")
        finally:
            db.close()

    # --- CRUD Operations for DeviceSchedules ---
    def create_device_schedule(self, device_id: str, schedule_data: api_validators.DeviceScheduleCreate, db: Optional[Session] = None) -> DeviceSchedule:
        db = self._get_db(db)
        try:
            db_schedule = DeviceSchedule(
                id=str(uuid.uuid4()), device_id=device_id,
                cron_expression=schedule_data.cron_expression,
                action=schedule_data.action, is_enabled=schedule_data.is_enabled
            )
            db.add(db_schedule); db.commit(); db.refresh(db_schedule)
            return db_schedule
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not create schedule: {e}")
        finally: db.close()

    def get_schedules_by_device_id(self, device_id: str, skip: int = 0, limit: int = 100, db: Optional[Session] = None) -> List[DeviceSchedule]:
        db = self._get_db(db)
        try:
            return db.query(DeviceSchedule).filter(DeviceSchedule.device_id == device_id).offset(skip).limit(limit).all()
        finally:
            if not db:
                db.close()

    def get_schedule_by_id(self, schedule_id: str, db: Optional[Session] = None) -> Optional[DeviceSchedule]:
        db = self._get_db(db)
        try:
            return db.query(DeviceSchedule).filter(DeviceSchedule.id == schedule_id).first()
        finally:
            if not db:
                db.close()

    def update_device_schedule(self, schedule_id: str, schedule_data: api_validators.DeviceScheduleUpdate, db: Optional[Session] = None) -> Optional[DeviceSchedule]:
        db = self._get_db(db)
        try:
            db_schedule = db.query(DeviceSchedule).filter(DeviceSchedule.id == schedule_id).first()
            if not db_schedule: return None
            update_data = schedule_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_schedule, key, value)
            db_schedule.updated_at = datetime.now(timezone.utc)
            db.commit(); db.refresh(db_schedule)
            return db_schedule
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not update schedule: {e}")
        finally: db.close()

    def delete_device_schedule(self, schedule_id: str, db: Optional[Session] = None) -> bool:
        db = self._get_db(db)
        try:
            db_schedule = db.query(DeviceSchedule).filter(DeviceSchedule.id == schedule_id).first()
            if not db_schedule: return False
            db.delete(db_schedule); db.commit()
            return True
        except Exception as e:
            db.rollback(); raise SimulationError(f"Could not delete schedule: {e}")
        finally: db.close()

    # --- Alarm Operations ---
    def get_alarms(self, status: Optional[str], severity: Optional[str], building_id: Optional[str],
                   start_date: Optional[datetime], end_date: Optional[datetime],
                   skip: int, limit: int, db: Optional[Session] = None) -> List[Alarm]:
        db = self._get_db(db)
        try:
            query = db.query(Alarm)
            if status: query = query.filter(Alarm.status == status)
            if severity: query = query.filter(Alarm.severity == severity)
            if start_date: query = query.filter(Alarm.triggered_at >= start_date)
            if end_date: query = query.filter(Alarm.triggered_at <= end_date)
            if building_id: # This requires joining through Device, Room, Floor to Building
                query = query.join(Device, Alarm.device_id == Device.id)\
                               .join(Room, Device.room_id == Room.id)\
                               .join(Floor, Room.floor_id == Floor.id)\
                               .filter(Floor.building_id == building_id)
            return query.order_by(Alarm.triggered_at.desc()).offset(skip).limit(limit).all()
        finally:
            if not db:
                db.close()

    def acknowledge_alarm(self, alarm_id: str, db: Optional[Session] = None) -> Optional[Alarm]:
        db = self._get_db(db)
        try:
            alarm = db.query(Alarm).filter(Alarm.id == alarm_id).first()
            if not alarm:
                self.logger.warning(f"Alarm {alarm_id} not found for acknowledgement.")
                return None
            if alarm.status != "NEW":
                self.logger.info(f"Alarm {alarm_id} is already in status {alarm.status}, cannot acknowledge.")
                # Depending on strictness, could return None or raise SimulationError
                raise SimulationError(f"Alarm already {alarm.status.lower()} or resolved.")
            alarm.status = "ACK"
            alarm.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(alarm)
            self.logger.info(f"Alarm {alarm_id} acknowledged.")
            # TODO: Publish alarm.update event
            return alarm
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error acknowledging alarm {alarm_id}: {e}")
            raise SimulationError(f"Could not acknowledge alarm {alarm_id}: {e}")
        finally:
            db.close()

    # --- Data & Visualization ---
    def get_device_telemetry(self, device_id: str, key: Optional[str],
                             start_time: Optional[datetime], end_time: Optional[datetime],
                             aggregation: Optional[str]) -> List[api_validators.TelemetryDataPoint]:
        # This method should query the time-series database (e.g., TimescaleDB)
        # For now, returning a placeholder.
        self.logger.warning("get_device_telemetry is a placeholder and does not query a real telemetry store.")
        if key == "temperature_sample": # Sample data for testing
            return [
                api_validators.TelemetryDataPoint(timestamp=datetime.now(timezone.utc) - timedelta(minutes=2), value=22.0, key="temperature"),
                api_validators.TelemetryDataPoint(timestamp=datetime.now(timezone.utc) - timedelta(minutes=1), value=22.5, key="temperature"),
                api_validators.TelemetryDataPoint(timestamp=datetime.now(timezone.utc), value=22.3, key="temperature"),
            ]
        return []

    def get_kpi_dashboard_data(self, db: Optional[Session] = None) -> Dict[str, Any]:
        # This method should calculate or retrieve KPIs.
        # For now, returning placeholder data.
        db = self._get_db(db)
        try:
            active_alarms_count = db.query(Alarm).filter(Alarm.status == "NEW").count()
            # More complex KPIs would involve more queries/calculations
            return {
                "total_consumption_live": random.uniform(5.0, 15.0), # Placeholder
                "active_alarms_count": active_alarms_count,
                "average_temperature_building": random.uniform(18.0, 25.0), # Placeholder
                "devices_on_count": db.query(Device).filter(Device.is_active == True).count() # Example
            }
        finally:
            if not db:
                db.close()

    # --- Simulation Logic (to be significantly refactored) ---

    def setup_simulation_events(self) -> None:
        """Configura los eventos recurrentes de la simulación (e.g., for scheduler)"""
        # This will involve scheduling tasks like:
        # - Checking device_schedules
        # - Generating telemetry for active devices
        # - Evaluating rules for alarms
        
        # Example: Schedule telemetry generation every 5 seconds
        # self.scheduler.add_recurring_event(
        #     "generate_telemetry_tick",
        #     self.generate_telemetry_for_active_devices,
        #     timedelta(seconds=5) # Configurable
        # )
        # self.scheduler.add_recurring_event(
        #     "execute_scheduled_tasks_tick",
        #     self.execute_scheduled_device_tasks,
        #     timedelta(minutes=1) # Check cron expressions every minute
        # )
        # self.scheduler.add_recurring_event(
        #     "evaluate_rules_tick",
        #     self.evaluate_rules_and_create_alarms,
        #     timedelta(seconds=10) # Configurable
        # )
        self.logger.info("Simulation event hooks configured (placeholder).")


    def _generate_new_telemetry_for_device(self, device: Device, current_state: Dict[str, Any], db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """
        Generates new telemetry data for a single device based on its type and current state.
        This is a placeholder for the detailed simulation logic per device type.
        Returns a list of telemetry entries, e.g., [{'key': 'temperature', 'value': 22.5}, {'key': 'power_consumption', 'value': 0.1}]
        """
        telemetry_data = []
        
        # Fetch device_type properties to guide simulation using the provided session (db)
        # No crear una nueva sesión aquí, usar la que ya se pasó
        device_type = db.query(DeviceType).filter(DeviceType.id == device.device_type_id).first()
        
        if not device_type:
            self.logger.warning(f"Device type {device.device_type_id} not found for device {device.id}. Cannot generate realistic telemetry.")
            return []

        # Use device_type.type_name and properties for more realistic simulation
        # Obtener propiedades de simulación del tipo de dispositivo, si existen
        type_properties = device_type.properties if device_type.properties else {}

        if device_type.type_name == "temperature_sensor":
            target_temp = current_state.get("target_temp", type_properties.get("default_target_temp", 22.0))
            current_temp = current_state.get("current_temp", type_properties.get("default_current_temp", 20.0))
            
            # Parámetros de simulación configurables
            change_speed = type_properties.get("change_speed", 0.1)
            fluctuation_magnitude = type_properties.get("fluctuation_magnitude", 0.5)
            ambient_temp = type_properties.get("ambient_temp", 20.0)
            min_temp = type_properties.get("min_temp", 15.0)
            max_temp = type_properties.get("max_temp", 30.0)

            if current_state.get("power") == "ON":
                delta = (target_temp - current_temp) * change_speed
                new_temp = current_temp + delta + (random.random() - 0.5) * fluctuation_magnitude
            else: # Power OFF, slowly return to ambient
                delta = (ambient_temp - current_temp) * (change_speed / 2) # Más lento al volver al ambiente
                new_temp = current_temp + delta + (random.random() - 0.5) * (fluctuation_magnitude / 2)
            
            new_temp = round(max(min_temp, min(max_temp, new_temp)), 2)
            telemetry_data.append({"key": "temperature", "value": new_temp})
            
            if device.state is None: device.state = {}
            device.state["current_temp"] = new_temp
            
        elif device_type.type_name == "humidity_sensor":
            humidity = current_state.get("humidity", type_properties.get("default_humidity", 50.0))
            
            # Parámetros de simulación configurables
            mean_humidity = type_properties.get("mean_humidity", 50.0)
            change_to_mean_factor = type_properties.get("change_to_mean_factor", 0.05)
            fluctuation_magnitude = type_properties.get("fluctuation_magnitude", 0.8)
            min_humidity = type_properties.get("min_humidity", 30.0)
            max_humidity = type_properties.get("max_humidity", 70.0)

            delta_to_mean = (mean_humidity - humidity) * change_to_mean_factor
            fluctuation = (random.random() - 0.5) * fluctuation_magnitude
            
            new_humidity = humidity + delta_to_mean + fluctuation
            new_humidity = round(max(min_humidity, min(max_humidity, new_humidity)), 2)
            telemetry_data.append({"key": "humidity", "value": new_humidity})
            if device.state is None: device.state = {}
            device.state["humidity"] = new_humidity

        elif device_type.type_name == "light_sensor":
            current_hour = datetime.now(timezone.utc).hour
            
            # Parámetros de simulación configurables
            day_start_hour = type_properties.get("day_start_hour", 6)
            day_end_hour = type_properties.get("day_end_hour", 18)
            morning_peak_hour = type_properties.get("morning_peak_hour", 10)
            evening_peak_hour = type_properties.get("evening_peak_hour", 22) # Used for evening transition
            
            light_day_min = type_properties.get("light_day_min", 400)
            light_day_max = type_properties.get("light_day_max", 800)
            light_night_min = type_properties.get("light_night_min", 10)
            light_night_max = type_properties.get("light_night_max", 100)
            light_transition_min = type_properties.get("light_transition_min", 100)
            light_transition_max = type_properties.get("light_transition_max", 400)
            fluctuation_magnitude = type_properties.get("fluctuation_magnitude", 50)
            
            base_light = 0
            if day_start_hour <= current_hour < morning_peak_hour: # Mañana (amanecer)
                base_light = random.uniform(light_transition_min, light_transition_max)
            elif morning_peak_hour <= current_hour < day_end_hour: # Día (pico)
                base_light = random.uniform(light_day_min, light_day_max)
            elif day_end_hour <= current_hour < evening_peak_hour: # Tarde (anochecer)
                base_light = random.uniform(light_transition_min, light_transition_max)
            else: # Noche
                base_light = random.uniform(light_night_min, light_night_max)
            
            fluctuation = (random.random() - 0.5) * fluctuation_magnitude
            
            new_light_intensity = base_light + fluctuation
            new_light_intensity = round(max(0, min(1000, new_light_intensity)), 0)
            telemetry_data.append({"key": "light_intensity", "value": new_light_intensity})
            if device.state is None: device.state = {}
            device.state["light_intensity"] = new_light_intensity

        elif device_type.type_name == "occupancy_sensor":
            current_occupancy = current_state.get("occupancy", type_properties.get("default_occupancy", 0))
            
            # Parámetros de simulación configurables
            change_probability = type_properties.get("change_probability", 0.1) 
            
            new_occupancy = current_occupancy
            if random.random() < change_probability:
                new_occupancy = 1 - current_occupancy # Flip the state
            
            telemetry_data.append({"key": "occupancy", "value": new_occupancy})
            if device.state is None: device.state = {}
            device.state["occupancy"] = new_occupancy

        elif device_type.type_name == "power_meter":
            power_consumption = 0.0
            
            # Parámetros de simulación configurables
            base_consumption_on = type_properties.get("base_consumption_on", 0.2) # kW
            fluctuation_on = type_properties.get("fluctuation_on", 0.02)
            min_consumption_on = type_properties.get("min_consumption_on", 0.05)
            
            base_consumption_off = type_properties.get("base_consumption_off", 0.001) # kW
            fluctuation_off = type_properties.get("fluctuation_off", 0.009) # Max fluctuation for off state
            
            if current_state.get("power") == "ON":
                fluctuation = random.uniform(-fluctuation_on, fluctuation_on)
                power_consumption = base_consumption_on + fluctuation
                power_consumption = round(max(min_consumption_on, power_consumption), 3)
            else:
                fluctuation = random.uniform(0, fluctuation_off) # Solo fluctuación positiva para standby
                power_consumption = base_consumption_off + fluctuation
                power_consumption = round(power_consumption, 3)
            
            telemetry_data.append({"key": "power_consumption", "value": power_consumption})
            if device.state is None: device.state = {}
            device.state["power_consumption"] = power_consumption

        else:
            self.logger.warning(f"Device type '{device_type.type_name}' not explicitly handled for telemetry generation. Generating default data.")
            # Generar un valor por defecto para tipos no reconocidos
            default_value = random.uniform(0.0, 100.0)
            telemetry_data.append({"key": "unknown_metric", "value": default_value})
            if device.state is None: device.state = {}
            device.state["unknown_metric"] = default_value

        return telemetry_data

    async def store_telemetry_data(self, device_id: str, key: str, value: float, unit: str, timestamp: datetime, db: Optional[Session] = None):
        """Stores a single telemetry data point."""
        _db_session_created_internally = (db is None)
        db_session = self._get_db(db) # Use injected db session if available
        try:
            reading = SensorReading(
                device_id=device_id,
                timestamp=timestamp,
                value=value,
                unit=unit,
                extra_data={"key": key}
            )
            db_session.add(reading)
            db_session.commit()
            self.logger.debug(f"Stored telemetry for {device_id}: {key}={value} {unit}")

            # Publish to real-time telemetry queue if available
            if self._telemetry_queue:
                try:
                    telemetry_message = {
                        "device_id": device_id,
                        "key": key,
                        "value": value,
                        "unit": unit,
                        "timestamp": timestamp.isoformat().replace("+00:00", "Z")
                    }
                    await self._telemetry_queue.put(telemetry_message)
                except Exception as q_e:
                    self.logger.error(f"Error putting telemetry on queue: {q_e}")

        except IntegrityError as e:
            db_session.rollback()
            self.logger.error(f"IntegrityError storing telemetry for {device_id}: {e.orig}", exc_info=True)
        except Exception as e:
            db_session.rollback()
            self.logger.error(f"Unexpected error storing telemetry for {device_id}: {e}", exc_info=True)
        finally:
            if _db_session_created_internally:
                db_session.close()

    async def run_continuous_simulation_loop(self):
        """Loop de simulación continuo: genera telemetría y se detiene solo al recibir una señal de stop."""
        self.logger.info(f"SimulationEngine {self.engine_id} continuous loop started.")
        self.status = "running"
        
        while self.status == "running": # Loop continuo
            current_loop_time = datetime.now(timezone.utc)
            self.logger.debug(f"Simulation loop tick at {current_loop_time}")

            # 1. Generar telemetría para dispositivos activos y simulando
            # Pasar la sesión de la base de datos para que no se cierre prematuramente
            with self.db_session_local() as db_session:
                await self.generate_telemetry_for_simulating_devices(current_loop_time, db_session)
            # 2. (Opcional) Ejecutar otras tareas si quieres

            await asyncio.sleep(5) # Pausa configurable para el siguiente tick de simulación (e.g., cada 5 segundos)

        self.logger.info(f"SimulationEngine {self.engine_id} continuous loop stopped.")
        self.status = "stopped"

    # Old methods like update_devices, generate_traffic, store_device_data (old version),
    # store_traffic_data, save_simulation_data, get_all_devices, start, get_status,
    # _run_simulation, stop_simulation need to be removed or completely refactored
    # to align with the new database-centric, continuous simulation model.
    # For example, `get_all_devices` should query the database.
    # `start`/`stop` might refer to the engine's main loop, not discrete simulations.
    
    # Example of how an old method might be refactored or replaced:
    def update_building_simulation_status(self, building_id: str, is_simulating: bool, db: Optional[Session] = None) -> Optional[Building]:
        _db_session_created_internally = (db is None)
        db_session = self._get_db(db)
        try:
            db_building = db_session.query(Building).filter(Building.id == building_id).first()
            if not db_building: return None
            db_building.is_simulating = is_simulating
            db_building.updated_at = datetime.now(timezone.utc)
            db_session.commit()
            db_session.refresh(db_building)
            self.logger.info(f"Building {building_id} simulation status set to {is_simulating}.")
            return db_building
        except Exception as e:
            db_session.rollback(); raise SimulationError(f"Could not update building simulation status: {e}")
        finally:
            if _db_session_created_internally:
                db_session.close()

    async def generate_telemetry_for_simulating_devices(self, current_time: datetime, db: Optional[Session] = None):
        """
        Genera telemetría para dispositivos activos en edificios, pisos o habitaciones que están simulando.
        """
        _db_session_created_internally = (db is None)
        db_session = self._get_db(db) # Use injected db session if available
        try:
            # Obtener todos los edificios que están simulando
            simulating_buildings = db_session.query(Building).filter(Building.is_simulating == True).all()
            
            # Obtener todos los pisos que están simulando (independientemente del edificio)
            simulating_floors = db_session.query(Floor).filter(Floor.is_simulating == True).all()
            
            # Obtener todas las habitaciones que están simulando (independientemente del piso)
            simulating_rooms = db_session.query(Room).filter(Room.is_simulating == True).all()

            # Conjuntos para almacenar IDs de entidades que están simulando
            simulating_building_ids = {b.id for b in simulating_buildings}
            simulating_floor_ids = {f.id for f in simulating_floors}
            simulating_room_ids = {r.id for r in simulating_rooms}

            # Consulta para obtener dispositivos activos
            # Un dispositivo simula si su edificio, su piso O su habitación están simulando.
            # Prioridad: Room > Floor > Building
            # Cargar relaciones de forma eager para evitar DetachedInstanceError
            devices_to_simulate = db_session.query(Device)\
                .options(
                    selectinload(Device.room).selectinload(Room.floor).selectinload(Floor.building)
                )\
                .filter(Device.is_active == True)\
                .filter(
                    (Device.room.has(Room.is_simulating == True)) |
                    (Device.room.has(Room.floor.has(Floor.is_simulating == True))) |
                    (Device.room.has(Room.floor.has(Floor.building.has(Building.is_simulating == True))))
                ).all()
            
            self.logger.debug(f"Found {len(devices_to_simulate)} devices to simulate.")
            generated_readings_count = 0

            for device in devices_to_simulate:
                # Las relaciones room, floor, building ya están cargadas gracias a selectinload
                # Acceder directamente a las relaciones cargadas
                room = device.room
                floor = room.floor
                building = floor.building

                should_simulate = False
                # Verificar si la entidad (habitación, piso o edificio) está simulando
                if room and room.is_simulating:
                    should_simulate = True
                elif floor and floor.is_simulating:
                    should_simulate = True
                elif building and building.is_simulating:
                    should_simulate = True

                if should_simulate:
                    self.logger.debug(f"Generating telemetry for device {device.id} ({device.name}) in room {room.name}, floor {floor.floor_number}, building {building.name}.")
                    telemetry_data = self._generate_new_telemetry_for_device(device, device.state or {}, db_session) # Pass db_session
                    
                    # Asegurarse de que los cambios en device.state se persistan
                    db_session.add(device) 

                    for data_point in telemetry_data:
                        # Determinar la unidad según el key
                        key = data_point["key"]
                        if key == "temperature":
                            unit = "°C"
                        elif key == "humidity":
                            unit = "%"
                        elif key == "light_intensity":
                            unit = "lux"
                        elif key == "occupancy":
                            unit = ""
                        elif key == "power_consumption":
                            unit = "kWh"
                        else:
                            unit = ""
                        await self.store_telemetry_data(device.id, key, data_point["value"], unit, current_time, db_session)
                        generated_readings_count += 1
                else:
                    self.logger.debug(f"Device {device.id} ({device.name}) is active but its hierarchy is not set to simulate.")
            
            # Commit de todos los cambios (incluyendo device.state y sensor_readings) al final del tick
            db_session.commit() 
            self.logger.info(f"Generated {generated_readings_count} telemetry readings in this tick.")
        except Exception as e:
            db_session.rollback()
            self.logger.error(f"Error generating telemetry for simulating devices: {e}", exc_info=True) # Added exc_info=True for full traceback
        finally:
            # La sesión se cierra en run_continuous_simulation_loop si fue creada allí
            if _db_session_created_internally:
                db_session.close()

    def get_all_db_devices(self, db: Optional[Session] = None) -> List[Device]:
        db = self._get_db(db)
        try:
            devices = db.query(Device).filter(Device.is_active == True).all()
            return devices
        finally:
            if not db:
                db.close()

    # The old `start`, `get_status`, `_run_simulation`, `stop_simulation` methods
    # managed discrete simulation runs. These are largely superseded by the
    # continuous worker model. The engine itself can be "started" or "stopped".
    async def start_engine_main_loop(self):
        if self.status != "running":
            self.status = "running"
            if not self._main_loop_task or self._main_loop_task.done():
                self._main_loop_task = asyncio.create_task(self.run_continuous_simulation_loop())
            # Iniciar el worker de agregación si no está corriendo
            if not self._aggregation_worker_task or self._aggregation_worker_task.done():
                self._aggregation_worker_running = True
                self._aggregation_worker_task = asyncio.create_task(self.start_aggregation_worker(60))
        else:
            self.logger.info("Engine main loop is already running.")

    def set_telemetry_queue(self, queue: asyncio.Queue):
        """Sets the asyncio.Queue for real-time telemetry updates."""
        self._telemetry_queue = queue
        self.logger.info("Telemetry queue set for SimulationEngine.")

    async def stop_engine_main_loop(self):
        self.logger.info("Stopping engine main loop and aggregation worker...")
        self.status = "stopped"
        # Detener el worker de agregación
        self._aggregation_worker_running = False
        if self._aggregation_worker_task and not self._aggregation_worker_task.done():
            self._aggregation_worker_task.cancel()
            try:
                await self._aggregation_worker_task
            except asyncio.CancelledError:
                self.logger.info("Aggregation worker task cancelled.")
            self._aggregation_worker_task = None
        
        # Esperar a que la tarea principal termine si existe
        if self._main_loop_task and not self._main_loop_task.done():
            self._main_loop_task.cancel()
            try:
                await self._main_loop_task
            except asyncio.CancelledError:
                self.logger.info("Main simulation loop task cancelled.")
            self._main_loop_task = None
        
        self.logger.info("Engine main loop and aggregation worker stopped.")
        # Add any other cleanup needed

    async def start_aggregation_worker(self, interval_seconds: int = 60):
        """
        Worker asíncrono que cada 'interval_seconds' calcula y guarda valores agregados
        (consumo energético, KPIs, etc.) en la tabla AggregatedReading.
        """
        self.logger.info(f"Aggregation worker started (interval: {interval_seconds}s)")
        while self._aggregation_worker_running:
            try:
                await self.aggregate_and_store_all(interval_seconds)
            except Exception as e:
                self.logger.error(f"Error in aggregation worker: {e}")
            await asyncio.sleep(interval_seconds)
        self.logger.info("Aggregation worker stopped.")

    async def aggregate_and_store_all(self, period_seconds: int):
        """
        Calcula y guarda los valores agregados de consumo y KPIs para edificio, piso, habitación y dispositivo.
        """
        db = self._get_db()
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(seconds=period_seconds)
        try:
            # --- Agregación por edificio ---
            buildings = db.query(Building).all()
            for building in buildings:
                device_ids = [d.id for d in db.query(Device).join(Room).join(Floor).filter(Floor.building_id == building.id).all()]
                if not device_ids:
                    continue
                total_consumption = db.query(func.sum(SensorReading.value)).filter(
                    SensorReading.device_id.in_(device_ids),
                    SensorReading.timestamp >= start_time,
                    SensorReading.timestamp < now,
                    cast(SensorReading.extra_data['key'], String) == "power_consumption"
                ).scalar() or 0.0
                agg = AggregatedReading(
                    entity_type="building",
                    entity_id=building.id,
                    timestamp=now,
                    key="power_consumption",
                    value=total_consumption,
                    unit="kWh",
                    period_seconds=period_seconds,
                    extra_data=None
                )
                db.add(agg)
            # --- Agregación por piso ---
            floors = db.query(Floor).all()
            for floor in floors:
                device_ids = [d.id for d in db.query(Device).join(Room).filter(Room.floor_id == floor.id).all()]
                if not device_ids:
                    continue
                total_consumption = db.query(func.sum(SensorReading.value)).filter(
                    SensorReading.device_id.in_(device_ids),
                    SensorReading.timestamp >= start_time,
                    SensorReading.timestamp < now,
                    cast(SensorReading.extra_data['key'], String) == "power_consumption"
                ).scalar() or 0.0
                agg = AggregatedReading(
                    entity_type="floor",
                    entity_id=floor.id,
                    timestamp=now,
                    key="power_consumption",
                    value=total_consumption,
                    unit="kWh",
                    period_seconds=period_seconds,
                    extra_data=None
                )
                db.add(agg)
            # --- Agregación por habitación ---
            rooms = db.query(Room).all()
            for room in rooms:
                device_ids = [d.id for d in db.query(Device).filter(Device.room_id == room.id).all()]
                if not device_ids:
                    continue
                total_consumption = db.query(func.sum(SensorReading.value)).filter(
                    SensorReading.device_id.in_(device_ids),
                    SensorReading.timestamp >= start_time,
                    SensorReading.timestamp < now,
                    cast(SensorReading.extra_data['key'], String) == "power_consumption"
                ).scalar() or 0.0
                agg = AggregatedReading(
                    entity_type="room",
                    entity_id=room.id,
                    timestamp=now,
                    key="power_consumption",
                    value=total_consumption,
                    unit="kWh",
                    period_seconds=period_seconds,
                    extra_data=None
                )
                db.add(agg)
            # --- Agregación por dispositivo ---
            devices = db.query(Device).all()
            for device in devices:
                total_consumption = db.query(func.sum(SensorReading.value)).filter(
                    SensorReading.device_id == device.id,
                    SensorReading.timestamp >= start_time,
                    SensorReading.timestamp < now,
                    cast(SensorReading.extra_data['key'], String) == "power_consumption"
                ).scalar() or 0.0
                agg = AggregatedReading(
                    entity_type="device",
                    entity_id=device.id,
                    timestamp=now,
                    key="power_consumption",
                    value=total_consumption,
                    unit="kWh",
                    period_seconds=period_seconds,
                    extra_data=None
                )
                db.add(agg)
            db.commit()
            self.logger.info(f"Aggregated readings stored for period {period_seconds}s at {now}")
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error in aggregate_and_store_all: {e}")
        finally:
            db.close()
