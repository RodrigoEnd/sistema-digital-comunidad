"""
Sistema de Optimización de Interfaz de Usuario
Proporciona debouncing, threading, caché y virtualización para mejorar la fluidez de la UI
"""

import threading
import time
from typing import Callable, Any, Optional, Dict, List
from functools import lru_cache
import hashlib
import json


class DebounceManager:
    """
    Gestor de debouncing para evitar ejecuciones excesivas
    Retrasa la ejecución de funciones hasta que el usuario deja de interactuar
    """
    
    def __init__(self):
        self._timers: Dict[str, Any] = {}
        self._locks: Dict[str, threading.Lock] = {}
    
    def debounce(self, key: str, delay_ms: int, callback: Callable, *args, **kwargs):
        """
        Ejecuta callback después de delay_ms sin nuevas llamadas
        
        Args:
            key: Identificador único para este debounce
            delay_ms: Tiempo de espera en milisegundos
            callback: Función a ejecutar
            *args, **kwargs: Argumentos para el callback
        """
        # Cancelar timer anterior si existe
        if key in self._timers and self._timers[key]:
            try:
                self._timers[key].cancel()
            except:
                pass
        
        # Crear nuevo timer
        timer = threading.Timer(
            delay_ms / 1000.0,
            callback,
            args=args,
            kwargs=kwargs
        )
        timer.daemon = True
        self._timers[key] = timer
        timer.start()
    
    def cancel(self, key: str):
        """Cancelar un debounce específico"""
        if key in self._timers and self._timers[key]:
            try:
                self._timers[key].cancel()
                self._timers[key] = None
            except:
                pass
    
    def cancel_all(self):
        """Cancelar todos los debounces activos"""
        for key in list(self._timers.keys()):
            self.cancel(key)


class CacheManager:
    """
    Gestor de caché para resultados de búsqueda y filtrado
    Evita recalcular resultados idénticos
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple] = {}  # key -> (timestamp, data)
        self._lock = threading.Lock()
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generar clave única para argumentos"""
        data = {
            'args': str(args),
            'kwargs': str(sorted(kwargs.items()))
        }
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def get(self, *args, **kwargs) -> Optional[Any]:
        """Obtener valor del caché si existe y es válido"""
        key = self._generate_key(*args, **kwargs)
        
        with self._lock:
            if key in self._cache:
                timestamp, data = self._cache[key]
                # Verificar si el caché sigue siendo válido
                if time.time() - timestamp < self.ttl_seconds:
                    return data
                else:
                    # Expirado, eliminar
                    del self._cache[key]
        
        return None
    
    def set(self, data: Any, *args, **kwargs):
        """Guardar valor en caché"""
        key = self._generate_key(*args, **kwargs)
        
        with self._lock:
            # Limpiar caché si está lleno
            if len(self._cache) >= self.max_size:
                # Eliminar entradas más antiguas
                oldest_keys = sorted(
                    self._cache.keys(),
                    key=lambda k: self._cache[k][0]
                )[:self.max_size // 4]
                for old_key in oldest_keys:
                    del self._cache[old_key]
            
            self._cache[key] = (time.time(), data)
    
    def clear(self):
        """Limpiar todo el caché"""
        with self._lock:
            self._cache.clear()
    
    def invalidate_pattern(self, pattern: str):
        """Invalidar entradas que contengan un patrón"""
        with self._lock:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self._cache[key]


class BackgroundWorker:
    """
    Ejecutor de tareas en background para no bloquear la UI
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._active_workers: Dict[str, threading.Thread] = {}
        self._cancel_flags: Dict[str, bool] = {}
        self._lock = threading.Lock()
    
    def run_async(self, key: str, task: Callable, callback: Optional[Callable] = None,
                  *args, **kwargs):
        """
        Ejecutar tarea en background
        
        Args:
            key: Identificador único para esta tarea
            task: Función a ejecutar en background
            callback: Función a ejecutar en UI thread con el resultado
            *args, **kwargs: Argumentos para task
        """
        # Cancelar tarea anterior con la misma key
        self.cancel(key)
        
        # Flag de cancelación
        self._cancel_flags[key] = False
        
        def _worker():
            try:
                # Ejecutar tarea
                result = task(*args, **kwargs)
                
                # Si no fue cancelada, ejecutar callback
                if not self._cancel_flags.get(key, True) and callback:
                    callback(result)
            except Exception as e:
                print(f"Error en worker {key}: {e}")
            finally:
                # Limpiar
                with self._lock:
                    if key in self._active_workers:
                        del self._active_workers[key]
                    if key in self._cancel_flags:
                        del self._cancel_flags[key]
        
        # Crear y lanzar thread
        thread = threading.Thread(target=_worker, daemon=True)
        
        with self._lock:
            self._active_workers[key] = thread
        
        thread.start()
    
    def cancel(self, key: str):
        """Cancelar una tarea específica"""
        with self._lock:
            if key in self._cancel_flags:
                self._cancel_flags[key] = True
            
            if key in self._active_workers:
                # No podemos forzar la cancelación del thread,
                # pero el flag indicará que debe detenerse
                pass
    
    def cancel_all(self):
        """Cancelar todas las tareas activas"""
        with self._lock:
            for key in list(self._cancel_flags.keys()):
                self._cancel_flags[key] = True
    
    def is_cancelled(self, key: str) -> bool:
        """Verificar si una tarea fue cancelada"""
        return self._cancel_flags.get(key, True)


class VirtualTable:
    """
    Helper para virtualización de tablas
    Solo renderiza las filas visibles en el viewport
    """
    
    def __init__(self, total_items: int, visible_rows: int = 20, buffer_rows: int = 5):
        self.total_items = total_items
        self.visible_rows = visible_rows
        self.buffer_rows = buffer_rows
        self.scroll_position = 0
    
    def get_visible_range(self) -> tuple:
        """
        Obtener rango de items a renderizar
        Returns: (start_index, end_index)
        """
        start = max(0, self.scroll_position - self.buffer_rows)
        end = min(self.total_items, self.scroll_position + self.visible_rows + self.buffer_rows)
        return (start, end)
    
    def update_scroll(self, scroll_position: int):
        """Actualizar posición del scroll"""
        self.scroll_position = max(0, min(scroll_position, self.total_items - self.visible_rows))
    
    def should_render(self, index: int) -> bool:
        """Verificar si un item debería renderizarse"""
        start, end = self.get_visible_range()
        return start <= index < end


class UIOptimizer:
    """
    Clase principal que integra todas las optimizaciones
    Uso:
        optimizer = UIOptimizer()
        optimizer.debounce_search('mi_busqueda', 500, mi_funcion_busqueda, criterio)
    """
    
    def __init__(self):
        self.debounce = DebounceManager()
        self.cache = CacheManager(max_size=200, ttl_seconds=600)
        self.worker = BackgroundWorker(max_workers=4)
    
    def debounce_search(self, widget_id: str, delay_ms: int, search_func: Callable,
                       *args, **kwargs):
        """
        Búsqueda con debouncing
        
        Args:
            widget_id: ID único del widget de búsqueda
            delay_ms: Delay en milisegundos
            search_func: Función de búsqueda
            *args, **kwargs: Argumentos para la búsqueda
        """
        self.debounce.debounce(f"search_{widget_id}", delay_ms, search_func, *args, **kwargs)
    
    def cached_filter(self, filter_func: Callable, data: List, criteria: Any) -> List:
        """
        Filtrado con caché
        
        Args:
            filter_func: Función que filtra los datos
            data: Lista de datos a filtrar
            criteria: Criterio de filtrado
        
        Returns:
            Lista filtrada
        """
        # Intentar obtener del caché
        cached_result = self.cache.get('filter', len(data), str(criteria))
        if cached_result is not None:
            return cached_result
        
        # Ejecutar filtrado
        result = filter_func(data, criteria)
        
        # Guardar en caché
        self.cache.set(result, 'filter', len(data), str(criteria))
        
        return result
    
    def async_update(self, key: str, update_func: Callable, ui_callback: Callable,
                    *args, **kwargs):
        """
        Actualización asíncrona con callback en UI thread
        
        Args:
            key: Identificador único
            update_func: Función a ejecutar en background
            ui_callback: Función a ejecutar en UI con el resultado
            *args, **kwargs: Argumentos para update_func
        """
        self.worker.run_async(key, update_func, ui_callback, *args, **kwargs)
    
    def cleanup(self):
        """Limpiar recursos"""
        self.debounce.cancel_all()
        self.cache.clear()
        self.worker.cancel_all()


# Instancia global para usar en toda la aplicación
_global_optimizer = None

def get_ui_optimizer() -> UIOptimizer:
    """Obtener instancia global del optimizador"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = UIOptimizer()
    return _global_optimizer


def reset_ui_optimizer():
    """Resetear el optimizador global"""
    global _global_optimizer
    if _global_optimizer:
        _global_optimizer.cleanup()
    _global_optimizer = None
