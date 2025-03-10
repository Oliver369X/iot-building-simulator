import click
import json
from pathlib import Path
from ..simulator.engine import SimulationEngine

@click.group()
def cli():
    """Herramienta de gestión de simulaciones IoT"""
    pass

@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='Archivo de configuración')
@click.option('--duration', '-d', default=60, help='Duración en minutos')
def run(config, duration):
    """Ejecuta una simulación con la configuración especificada"""
    with open(config) as f:
        config_data = json.load(f)
    
    engine = SimulationEngine()
    
    # Configura edificios
    for building_config in config_data['buildings']:
        engine.create_building(building_config)
    
    # Inicia simulación
    simulation_id = engine.start(duration)
    click.echo(f"Simulación iniciada: {simulation_id}")

@cli.command()
@click.option('--template', '-t', type=click.Choice(['office', 'residential', 'mixed']), 
              default='office', help='Tipo de edificio')
@click.option('--floors', '-f', default=5, help='Número de pisos')
@click.option('--rooms-per-floor', '-r', default=4, help='Habitaciones por piso')
def generate_config(template, floors, rooms_per_floor):
    """Genera una configuración de simulación basada en parámetros"""
    config = {
        "simulation": {"time_scale": 1.0},
        "buildings": [{
            "id": f"building_{template}",
            "name": f"Edificio {template.title()}",
            "floors": []
        }]
    }
    
    # Genera configuración según template
    for floor in range(floors):
        floor_config = {"floor_number": floor + 1, "rooms": []}
        for room in range(rooms_per_floor):
            room_config = generate_room_config(template)
            floor_config["rooms"].append(room_config)
        config["buildings"][0]["floors"].append(floor_config)
    
    output_file = f"config_{template}_{floors}f_{rooms_per_floor}r.json"
    with open(output_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    click.echo(f"Configuración generada en: {output_file}") 