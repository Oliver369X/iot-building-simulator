from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from src.templates.building_templates import BuildingTemplateManager

router = APIRouter()
template_manager = BuildingTemplateManager()

@router.get("/templates")
async def list_templates():
    """Lista todas las plantillas disponibles"""
    return template_manager.list_templates()

@router.get("/templates/{name}")
async def get_template(name: str):
    """Obtiene una plantilla específica"""
    try:
        return template_manager.load_template(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")

@router.post("/templates/{name}")
async def save_template(name: str, template: Dict[str, Any]):
    """Guarda una nueva plantilla"""
    try:
        template_manager.save_template(template, name)
        return {"message": "Template saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 