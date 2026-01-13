"""
Sistema de Cache en Memoria
Proporciona caching con TTL (Time To Live) para optimizar performance
Reduce accesos a disco y BD
"""

from datetime import datetime, timedelta
from functools import wraps
import threading


class Cache:
    """Cache en memoria con soporte para TTL (expiracion)"""
    
    def __init__(self):
        self._cache = {}
        self._ttl = {}
        self._lock = threading.Lock()
    
    def set(self, clave, valor, ttl_segundos=300):
        """
        Guardar valor en cache con TTL opcional
        
        Args:
            clave (str): Clave del item
            valor: Valor a cachear
            ttl_segundos (int): Tiempo de vida en segundos (0 = sin expiracion)
        """
        with self._lock:
            self._cache[clave] = valor
            
            if ttl_segundos > 0:
                self._ttl[clave] = datetime.now() + timedelta(seconds=ttl_segundos)
            else:
                self._ttl.pop(clave, None)  # Sin expiracion
    
    def get(self, clave, default=None):
        """
        Obtener valor del cache
        
        Args:
            clave (str): Clave del item
            default: Valor por defecto si no existe o expiro
            
        Returns:
            Valor cacheado o default
        """
        with self._lock:
            # Verificar si existe
            if clave not in self._cache:
                return default
            
            # Verificar si expiro
            if clave in self._ttl:
                if datetime.now() > self._ttl[clave]:
                    # Expiro, eliminar y retornar default
                    del self._cache[clave]
                    del self._ttl[clave]
                    return default
            
            return self._cache[clave]
    
    def existe(self, clave):
        """Verificar si una clave existe y no expiro"""
        return self.get(clave) is not None
    
    def eliminar(self, clave):
        """Eliminar una clave del cache"""
        with self._lock:
            self._cache.pop(clave, None)
            self._ttl.pop(clave, None)
    
    def limpiar(self):
        """Limpiar todo el cache"""
        with self._lock:
            self._cache.clear()
            self._ttl.clear()
    
    def limpiar_expirados(self):
        """Eliminar items expirados"""
        with self._lock:
            ahora = datetime.now()
            claves_expiradas = [
                clave for clave, expiracion in self._ttl.items()
                if ahora > expiracion
            ]
            
            for clave in claves_expiradas:
                del self._cache[clave]
                del self._ttl[clave]
            
            return len(claves_expiradas)
    
    def obtener_estadisticas(self):
        """Obtener estadisticas del cache"""
        with self._lock:
            return {
                'total_items': len(self._cache),
                'items_con_ttl': len(self._ttl),
                'claves': list(self._cache.keys())
            }
    
    def __len__(self):
        """Retornar cantidad de items en cache"""
        return len(self._cache)
    
    def __repr__(self):
        """Representacion del cache"""
        return f"Cache(items={len(self._cache)}, con_ttl={len(self._ttl)})"


# Instancia global de cache
_cache_global = Cache()


def cached(ttl_segundos=300, clave_custom=None):
    """
    Decorador para cachear resultados de funciones
    
    Args:
        ttl_segundos (int): Tiempo de vida del cache en segundos
        clave_custom (function): Funcion para generar clave personalizada
        
    Ejemplo:
        @cached(ttl_segundos=600)
        def obtener_habitantes():
            return db.obtener_todos()
    """
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave de cache
            if clave_custom:
                clave = clave_custom(*args, **kwargs)
            else:
                # Usar nombre de funcion + argumentos
                args_str = str(args) + str(kwargs)
                clave = f"{func.__name__}:{args_str}"
            
            # Intentar obtener del cache
            resultado = _cache_global.get(clave)
            
            if resultado is not None:
                return resultado
            
            # Si no esta en cache, ejecutar funcion
            resultado = func(*args, **kwargs)
            
            # Guardar en cache
            _cache_global.set(clave, resultado, ttl_segundos)
            
            return resultado
        
        # Agregar metodos para control manual
        wrapper.cache_clear = lambda: _cache_global.limpiar()
        wrapper.cache_invalidate = lambda *args, **kwargs: _cache_global.eliminar(
            f"{func.__name__}:{str(args) + str(kwargs)}"
        )
        
        return wrapper
    
    return decorador


# Cache predefinidos para datos frecuentes
class CachePredefinido:
    """Cache predefinido para datos comunes del sistema"""
    
    # Tiempos de expiracion (en segundos)
    TTL_HABITANTES = 300  # 5 minutos
    TTL_PAGOS_PENDIENTES = 300  # 5 minutos
    TTL_ESTADISTICAS = 1800  # 30 minutos
    TTL_COOPERACIONES = 600  # 10 minutos
    TTL_FAENAS_ACTIVAS = 120  # 2 minutos
    TTL_REPORTES = 3600  # 1 hora
    
    @staticmethod
    def obtener_habitantes():
        """Obtener lista de habitantes cacheada"""
        return _cache_global.get('habitantes_list')
    
    @staticmethod
    def guardar_habitantes(habitantes):
        """Guardar lista de habitantes en cache"""
        _cache_global.set('habitantes_list', habitantes, CachePredefinido.TTL_HABITANTES)
    
    @staticmethod
    def limpiar_habitantes():
        """Limpiar cache de habitantes"""
        _cache_global.eliminar('habitantes_list')
    
    @staticmethod
    def obtener_pagos_pendientes():
        """Obtener pagos pendientes cacheados"""
        return _cache_global.get('pagos_pendientes')
    
    @staticmethod
    def guardar_pagos_pendientes(pagos):
        """Guardar pagos pendientes en cache"""
        _cache_global.set('pagos_pendientes', pagos, CachePredefinido.TTL_PAGOS_PENDIENTES)
    
    @staticmethod
    def limpiar_pagos_pendientes():
        """Limpiar cache de pagos pendientes"""
        _cache_global.eliminar('pagos_pendientes')
    
    @staticmethod
    def obtener_estadisticas(tipo):
        """Obtener estadisticas cacheadas"""
        return _cache_global.get(f'estadisticas_{tipo}')
    
    @staticmethod
    def guardar_estadisticas(tipo, datos):
        """Guardar estadisticas en cache"""
        _cache_global.set(f'estadisticas_{tipo}', datos, CachePredefinido.TTL_ESTADISTICAS)
    
    @staticmethod
    def limpiar_todo():
        """Limpiar todo el cache predefinido"""
        _cache_global.limpiar()


def invalidar_cache_al_cambiar(claves_cache):
    """
    Decorador para invalidar cache automaticamente al cambiar datos
    
    Args:
        claves_cache (list): Lista de claves de cache a invalidar
        
    Ejemplo:
        @invalidar_cache_al_cambiar(['habitantes_list', 'estadisticas_censo'])
        def agregar_habitante(nombre):
            ...
    """
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Ejecutar funcion
            resultado = func(*args, **kwargs)
            
            # Invalidar cache especificado
            for clave in claves_cache:
                if clave.startswith('estadisticas_'):
                    tipo = clave.split('_')[1]
                    CachePredefinido.limpiar_estadisticas(tipo)
                elif clave == 'habitantes_list':
                    CachePredefinido.limpiar_habitantes()
                elif clave == 'pagos_pendientes':
                    CachePredefinido.limpiar_pagos_pendientes()
                else:
                    _cache_global.eliminar(clave)
            
            return resultado
        
        return wrapper
    
    return decorador


# Funciones utilitarias
def obtener_estadisticas_cache():
    """Obtener estadisticas del sistema de cache"""
    return _cache_global.obtener_estadisticas()


def limpiar_cache_global():
    """Limpiar todo el cache global"""
    _cache_global.limpiar()


def limpiar_expirados():
    """Limpiar items expirados del cache"""
    return _cache_global.limpiar_expirados()
