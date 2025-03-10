from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import logging

class IoTDataAnalyzer:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.logger = logging.getLogger(__name__)
        
    def load_device_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Carga datos de dispositivos en un DataFrame"""
        data_rows = []
        
        # Busca archivos de datos en el rango de fechas
        for data_file in self.data_dir.glob("device_data_*.jsonl"):
            try:
                with open(data_file, 'r') as f:
                    for line in f:
                        record = json.loads(line)
                        timestamp = datetime.fromisoformat(record["timestamp"])
                        
                        if start_date <= timestamp <= end_date:
                            data_rows.append({
                                "timestamp": timestamp,
                                "building_id": record["building_id"],
                                "device_id": record["device_id"],
                                **record["data"]
                            })
            except Exception as e:
                self.logger.error(f"Error leyendo {data_file}: {str(e)}")
                
        return pd.DataFrame(data_rows)
    
    def analyze_temperature_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza patrones de temperatura por edificio"""
        temp_data = df[df["unit"] == "celsius"].copy()
        
        results = {
            "average_temp": temp_data["temperature"].mean(),
            "max_temp": temp_data["temperature"].max(),
            "min_temp": temp_data["temperature"].min(),
            "std_temp": temp_data["temperature"].std(),
            "by_building": temp_data.groupby("building_id")["temperature"].agg([
                "mean", "max", "min", "std"
            ]).to_dict()
        }
        
        return results
    
    def analyze_energy_consumption(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza el consumo de energía"""
        energy_data = df[df["unit"] == "kWh"].copy()
        energy_data["hour"] = energy_data["timestamp"].dt.hour
        
        results = {
            "total_consumption": energy_data["total_consumption"].sum(),
            "average_power": energy_data["current_power"].mean(),
            "peak_power": energy_data["current_power"].max(),
            "by_hour": energy_data.groupby("hour")["current_power"].mean().to_dict(),
            "by_building": energy_data.groupby("building_id")["total_consumption"].sum().to_dict()
        }
        
        return results
    
    def plot_temperature_distribution(self, df: pd.DataFrame, save_path: Optional[str] = None):
        """Genera gráfico de distribución de temperaturas"""
        temp_data = df[df["unit"] == "celsius"]
        
        plt.figure(figsize=(10, 6))
        for building_id in temp_data["building_id"].unique():
            building_temps = temp_data[temp_data["building_id"] == building_id]["temperature"]
            plt.hist(building_temps, alpha=0.5, label=building_id, bins=20)
            
        plt.xlabel("Temperatura (°C)")
        plt.ylabel("Frecuencia")
        plt.title("Distribución de Temperaturas por Edificio")
        plt.legend()
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
            
    def plot_energy_over_time(self, df: pd.DataFrame, save_path: Optional[str] = None):
        """Genera gráfico de consumo de energía en el tiempo"""
        energy_data = df[df["unit"] == "kWh"].copy()
        energy_data.set_index("timestamp", inplace=True)
        
        plt.figure(figsize=(12, 6))
        for building_id in energy_data["building_id"].unique():
            building_data = energy_data[energy_data["building_id"] == building_id]
            plt.plot(building_data.index, building_data["current_power"], 
                    label=building_id, alpha=0.7)
            
        plt.xlabel("Tiempo")
        plt.ylabel("Potencia (kW)")
        plt.title("Consumo de Energía por Edificio")
        plt.legend()
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show() 