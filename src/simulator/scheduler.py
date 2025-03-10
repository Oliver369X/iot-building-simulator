from typing import Dict, List, Any, Callable, Optional
from datetime import datetime, timedelta
import heapq
import logging

class SimulationEvent:
    def __init__(
        self,
        timestamp: datetime,
        event_type: str,
        callback: Callable,
        data: Optional[Dict[str, Any]] = None,
        interval: Optional[timedelta] = None
    ):
        self.timestamp = timestamp
        self.event_type = event_type
        self.callback = callback
        self.data = data or {}
        self.interval = interval
        
    def __lt__(self, other):
        return self.timestamp < other.timestamp

class Scheduler:
    def __init__(self, time_scale: float = 1.0):
        self.events: List[SimulationEvent] = []
        self.time_scale = time_scale
        self.current_time = datetime.now()
        self.is_running = False
        self.logger = logging.getLogger(__name__)
        
    def add_event(
        self,
        event_type: str,
        callback: Callable,
        delay: timedelta,
        data: Optional[Dict[str, Any]] = None,
        interval: Optional[timedelta] = None
    ) -> None:
        """Añade un nuevo evento a la cola"""
        event_time = self.current_time + delay
        event = SimulationEvent(event_time, event_type, callback, data, interval)
        heapq.heappush(self.events, event)
        self.logger.debug(f"Evento {event_type} programado para {event_time}")
        
    def add_recurring_event(
        self,
        event_type: str,
        callback: Callable,
        interval: timedelta,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Añade un evento recurrente"""
        self.add_event(event_type, callback, interval, data, interval)
        
    def remove_events(self, event_type: str) -> None:
        """Elimina todos los eventos de un tipo específico"""
        self.events = [e for e in self.events if e.event_type != event_type]
        heapq.heapify(self.events)
        
    def process_next_event(self) -> bool:
        """Procesa el siguiente evento en la cola"""
        if not self.events:
            return False
            
        event = heapq.heappop(self.events)
        self.current_time = event.timestamp
        
        try:
            event.callback(event.data)
        except Exception as e:
            self.logger.error(f"Error procesando evento {event.event_type}: {str(e)}")
            
        # Si es un evento recurrente, reprogramarlo
        if event.interval:
            next_time = event.timestamp + event.interval
            new_event = SimulationEvent(
                next_time,
                event.event_type,
                event.callback,
                event.data,
                event.interval
            )
            heapq.heappush(self.events, new_event)
            
        return True
        
    def run_until(self, end_time: datetime) -> None:
        """Ejecuta la simulación hasta un tiempo específico"""
        self.is_running = True
        while self.is_running and self.events and self.current_time < end_time:
            if not self.process_next_event():
                break
                
    def stop(self) -> None:
        """Detiene la simulación"""
        self.is_running = False
        
    def get_next_event_time(self) -> Optional[datetime]:
        """Obtiene el tiempo del próximo evento"""
        if self.events:
            return self.events[0].timestamp
        return None
        
    def clear_all_events(self) -> None:
        """Limpia todos los eventos"""
        self.events.clear()
        
    def get_event_count(self) -> int:
        """Obtiene el número total de eventos en cola"""
        return len(self.events)
        
    def get_events_by_type(self, event_type: str) -> List[SimulationEvent]:
        """Obtiene todos los eventos de un tipo específico"""
        return [e for e in self.events if e.event_type == event_type]
