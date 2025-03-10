from typing import Dict, List, Any, Optional
import yaml
from pathlib import Path
import logging
import uuid

class BuildingTemplateManager:
    def __init__(self, templates_dir: str = "config/templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
    def save_template(self, template: Dict[str, Any], name: str) -> None:
        """Guarda una plantilla de edificio"""
        template_path = self.templates_dir / f"{name}.yaml"
        with open(template_path, 'w') as f:
            yaml.safe_dump(template, f)
            
    def load_template(self, name: str) -> Dict[str, Any]:
        """Carga una plantilla de edificio"""
        template_path = self.templates_dir / f"{name}.yaml"
        with open(template_path, 'r') as f:
            return yaml.safe_load(f)
            
    def list_templates(self) -> List[str]:
        """Lista todas las plantillas disponibles"""
        return [f.stem for f in self.templates_dir.glob("*.yaml")]
        
    def create_building_from_template(
        self,
        template_name: str,
        building_name: str,
        location: Dict[str, Any],
        config_overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Crea un nuevo edificio basado en una plantilla"""
        template = self.load_template(template_name)
        building_id = str(uuid.uuid4())
        
        building = {
            "building_id": building_id,
            "name": building_name,
            "location": location,
            "config": {**template.get("config", {}), **(config_overrides or {})}
        }
        
        # Procesa la estructura del edificio según la plantilla
        building["floors"] = {}
        floor_templates = template.get("floors", {})
        room_templates = template.get("room_templates", {})
        
        for floor_num in range(1, template["config"]["floors"] + 1):
            floor_id = f"floor_{building_id}_{floor_num}"
            floor = {
                "floor_id": floor_id,
                "building_id": building_id,
                "floor_number": floor_num,
                "rooms": {}
            }
            
            # Determina qué plantilla de piso usar
            if floor_num == 1:
                floor_template = floor_templates.get("ground_floor", floor_templates["typical_floor"])
            elif floor_num == template["config"]["floors"]:
                floor_template = floor_templates.get("top_floor", floor_templates["typical_floor"])
            else:
                floor_template = floor_templates["typical_floor"]
                
            # Crea habitaciones según la plantilla
            room_number = 1
            for room_type, count in floor_template["rooms"].items():
                room_template = room_templates[room_type]
                for _ in range(count):
                    room_id = f"room_{floor_id}_{room_number}"
                    room = {
                        "room_id": room_id,
                        "floor_id": floor_id,
                        "room_type": room_type,
                        "area": room_template["area"],
                        "devices": []
                    }
                    
                    # Añade dispositivos según la plantilla
                    for device_template in room_template["devices"]:
                        count = device_template.get("count", 1)
                        for _ in range(count):
                            device = {
                                "device_id": str(uuid.uuid4()),
                                "device_type": device_template["type"],
                                "config": device_template.get("config", {}),
                                "room_id": room_id
                            }
                            room["devices"].append(device)
                            
                    floor["rooms"][room_id] = room
                    room_number += 1
                    
            building["floors"][floor_id] = floor
            
        return building 