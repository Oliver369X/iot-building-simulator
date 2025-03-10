from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats
import logging

class AdvancedIoTAnalyzer:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.logger = logging.getLogger(__name__)
        
    def analyze_occupancy_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza patrones de ocupación basados en sensores de movimiento"""
        motion_data = df[df["device_type"] == "motion_sensor"].copy()
        motion_data["hour"] = motion_data["timestamp"].dt.hour
        motion_data["weekday"] = motion_data["timestamp"].dt.weekday
        
        patterns = {
            "hourly_activity": motion_data.groupby("hour")["motion_detected"].mean().to_dict(),
            "weekday_activity": motion_data.groupby("weekday")["motion_detected"].mean().to_dict(),
            "peak_hours": motion_data.groupby("hour")["motion_detected"].mean().nlargest(3).index.tolist()
        }
        
        return patterns
    
    def analyze_energy_efficiency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza la eficiencia energética del edificio"""
        energy_data = df[df["device_type"].isin(["power_meter", "hvac_controller"])].copy()
        energy_data["hour"] = energy_data["timestamp"].dt.hour
        
        # Calcula consumo por metro cuadrado
        total_area = df["area"].sum() if "area" in df.columns else 1000  # área por defecto
        consumption_per_m2 = energy_data["total_consumption"].sum() / total_area
        
        # Identifica picos de consumo
        peak_consumption = energy_data.groupby("hour")["current_power"].max()
        
        return {
            "consumption_per_m2": consumption_per_m2,
            "peak_hours": peak_consumption.nlargest(3).index.tolist(),
            "peak_values": peak_consumption.nlargest(3).values.tolist(),
            "average_daily_consumption": energy_data["total_consumption"].mean() * 24
        }
    
    def detect_anomalies(self, df: pd.DataFrame, z_threshold: float = 3.0) -> Dict[str, List[Dict[str, Any]]]:
        """Detecta anomalías en los datos de dispositivos"""
        anomalies = {}
        
        for device_type in df["device_type"].unique():
            device_data = df[df["device_type"] == device_type]
            
            if "temperature" in device_data.columns:
                # Análisis de temperatura
                z_scores = np.abs(stats.zscore(device_data["temperature"]))
                anomalies[device_type] = device_data[z_scores > z_threshold].to_dict("records")
            elif "current_power" in device_data.columns:
                # Análisis de consumo energético
                z_scores = np.abs(stats.zscore(device_data["current_power"]))
                anomalies[device_type] = device_data[z_scores > z_threshold].to_dict("records")
                
        return anomalies
    
    def generate_heatmap(self, df: pd.DataFrame, metric: str, save_path: Optional[str] = None):
        """Genera un mapa de calor para una métrica específica"""
        pivot_data = df.pivot_table(
            values=metric,
            index=df["timestamp"].dt.hour,
            columns=df["timestamp"].dt.weekday,
            aggfunc="mean"
        )
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(pivot_data, cmap="YlOrRd", annot=True, fmt=".2f")
        plt.title(f"Mapa de Calor - {metric}")
        plt.xlabel("Día de la Semana")
        plt.ylabel("Hora del Día")
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
            
    def generate_correlation_matrix(self, df: pd.DataFrame, save_path: Optional[str] = None):
        """Genera matriz de correlación entre diferentes métricas"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        corr_matrix = df[numeric_cols].corr()
        
        plt.figure(figsize=(12, 10))
        sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", center=0)
        plt.title("Matriz de Correlación de Métricas")
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
            
    def generate_report(self, df: pd.DataFrame, output_dir: str) -> str:
        """Genera un reporte completo de análisis"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"analysis_report_{timestamp}.html"
        
        # Análisis básico
        occupancy = self.analyze_occupancy_patterns(df)
        efficiency = self.analyze_energy_efficiency(df)
        anomalies = self.detect_anomalies(df)
        
        # Genera gráficos
        self.generate_heatmap(df, "temperature", str(output_dir / "temperature_heatmap.png"))
        self.generate_heatmap(df, "current_power", str(output_dir / "power_heatmap.png"))
        self.generate_correlation_matrix(df, str(output_dir / "correlation_matrix.png"))
        
        # Genera HTML
        html_content = f"""
        <html>
        <head>
            <title>Reporte de Análisis IoT - {timestamp}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .section {{ margin-bottom: 30px; }}
                .metric {{ margin: 10px 0; }}
                img {{ max-width: 100%; height: auto; }}
            </style>
        </head>
        <body>
            <h1>Reporte de Análisis IoT</h1>
            <div class="section">
                <h2>Patrones de Ocupación</h2>
                <div class="metric">Horas pico: {occupancy['peak_hours']}</div>
            </div>
            <div class="section">
                <h2>Eficiencia Energética</h2>
                <div class="metric">Consumo por m²: {efficiency['consumption_per_m2']:.2f} kWh/m²</div>
                <div class="metric">Consumo diario promedio: {efficiency['average_daily_consumption']:.2f} kWh</div>
            </div>
            <div class="section">
                <h2>Anomalías Detectadas</h2>
                <pre>{str(anomalies)}</pre>
            </div>
            <div class="section">
                <h2>Gráficos</h2>
                <img src="temperature_heatmap.png" alt="Mapa de Calor - Temperatura">
                <img src="power_heatmap.png" alt="Mapa de Calor - Consumo">
                <img src="correlation_matrix.png" alt="Matriz de Correlación">
            </div>
        </body>
        </html>
        """
        
        with open(report_file, 'w') as f:
            f.write(html_content)
            
        return str(report_file) 