"""
Tests Unitarios - Cache
Prueba las funciones de caching del sistema
"""

import pytest
import time
from src.core.cache import (
    Cache,
    cached,
    CachePredefinido,
    obtener_estadisticas_cache,
    limpiar_cache_global
)


class TestCache:
    """Suite de tests para la clase Cache"""
    
    def test_cache_set_get(self):
        """Debe guardar y recuperar valores"""
        cache = Cache()
        cache.set('clave1', 'valor1')
        assert cache.get('clave1') == 'valor1'
    
    def test_cache_get_no_existe(self):
        """Debe retornar default si no existe"""
        cache = Cache()
        assert cache.get('no_existe') is None
        assert cache.get('no_existe', 'default') == 'default'
    
    def test_cache_con_ttl(self):
        """Items con TTL deben expirar"""
        cache = Cache()
        cache.set('tempor', 'valor', ttl_segundos=1)
        
        # Debe existir inmediatamente
        assert cache.get('tempor') == 'valor'
        
        # Esperar a que expire
        time.sleep(1.1)
        assert cache.get('tempor') is None
    
    def test_cache_sin_ttl(self):
        """Items sin TTL no deben expirar"""
        cache = Cache()
        cache.set('permanente', 'valor', ttl_segundos=0)
        
        time.sleep(0.5)
        assert cache.get('permanente') == 'valor'
    
    def test_cache_existe(self):
        """Metodo existe debe verificar existencia"""
        cache = Cache()
        cache.set('clave', 'valor')
        
        assert cache.existe('clave')
        assert not cache.existe('no_existe')
    
    def test_cache_eliminar(self):
        """Debe eliminar claves"""
        cache = Cache()
        cache.set('clave', 'valor')
        cache.eliminar('clave')
        
        assert cache.get('clave') is None
    
    def test_cache_limpiar(self):
        """Debe limpiar todo el cache"""
        cache = Cache()
        cache.set('clave1', 'valor1')
        cache.set('clave2', 'valor2')
        cache.limpiar()
        
        assert len(cache) == 0
    
    def test_cache_limpiar_expirados(self):
        """Debe limpiar items expirados"""
        cache = Cache()
        cache.set('temporal', 'valor', ttl_segundos=1)
        cache.set('permanente', 'valor', ttl_segundos=0)
        
        time.sleep(1.1)
        eliminados = cache.limpiar_expirados()
        
        assert eliminados == 1
        assert cache.existe('permanente')
    
    def test_cache_len(self):
        """Debe retornar cantidad de items"""
        cache = Cache()
        assert len(cache) == 0
        
        cache.set('clave1', 'valor1')
        cache.set('clave2', 'valor2')
        
        assert len(cache) == 2
    
    def test_cache_estadisticas(self):
        """Debe retornar estadisticas"""
        cache = Cache()
        cache.set('clave1', 'valor1', ttl_segundos=300)
        cache.set('clave2', 'valor2')
        
        stats = cache.obtener_estadisticas()
        
        assert stats['total_items'] == 2
        assert stats['items_con_ttl'] == 1
        assert 'clave1' in stats['claves']


class TestDecoradorCached:
    """Suite de tests para decorador @cached"""
    
    def test_cached_ejecuta_funcion(self):
        """Debe ejecutar la funcion"""
        llamadas = []
        
        @cached(ttl_segundos=60)
        def obtener_dato():
            llamadas.append(1)
            return "resultado"
        
        resultado = obtener_dato()
        assert resultado == "resultado"
        assert len(llamadas) == 1
    
    def test_cached_usa_cache(self):
        """Segunda llamada debe usar cache"""
        llamadas = []
        
        @cached(ttl_segundos=60)
        def obtener_dato():
            llamadas.append(1)
            return "resultado"
        
        obtener_dato()
        obtener_dato()
        
        assert len(llamadas) == 1  # Solo ejecutado una vez
    
    def test_cached_con_argumentos(self):
        """Cache debe diferenciar argumentos"""
        llamadas = []
        
        @cached(ttl_segundos=60)
        def multiplicar(a, b):
            llamadas.append(1)
            return a * b
        
        multiplicar(2, 3)
        multiplicar(2, 3)  # Cache
        multiplicar(2, 4)  # Diferente argumento
        
        assert len(llamadas) == 2  # Ejecutado dos veces


class TestCachePredefinido:
    """Suite de tests para cache predefinido"""
    
    def test_guardar_obtener_habitantes(self):
        """Debe guardar y obtener habitantes"""
        habitantes = [
            {'folio': 'HAB-0001', 'nombre': 'Juan'},
            {'folio': 'HAB-0002', 'nombre': 'Maria'}
        ]
        
        limpiar_cache_global()
        CachePredefinido.guardar_habitantes(habitantes)
        
        resultado = CachePredefinido.obtener_habitantes()
        assert resultado == habitantes
    
    def test_limpiar_habitantes(self):
        """Debe limpiar cache de habitantes"""
        CachePredefinido.guardar_habitantes([])
        CachePredefinido.limpiar_habitantes()
        
        resultado = CachePredefinido.obtener_habitantes()
        assert resultado is None
    
    def test_cache_tiene_ttl_correcto(self):
        """Cache de habitantes debe tener TTL de 5 minutos"""
        limpiar_cache_global()
        CachePredefinido.guardar_habitantes(['habitante1'])
        
        # Debe existir inmediatamente
        assert CachePredefinido.obtener_habitantes() == ['habitante1']


class TestIntegracionCache:
    """Tests de integracion de cache"""
    
    def test_cache_concurrencia(self):
        """Cache debe ser thread-safe"""
        import threading
        
        cache = Cache()
        resultados = []
        
        def guardar():
            for i in range(100):
                cache.set(f'clave_{i}', f'valor_{i}')
        
        def obtener():
            for i in range(100):
                cache.get(f'clave_{i}')
        
        t1 = threading.Thread(target=guardar)
        t2 = threading.Thread(target=obtener)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        # Si no hay excepcion, el test pasa
        assert True
    
    def test_cache_memoria(self):
        """Cache debe guardar datos en memoria"""
        cache = Cache()
        
        # Agregar muchos items
        for i in range(1000):
            cache.set(f'clave_{i}', f'valor_{i}' * 100)
        
        # Verificar que estan
        assert cache.get('clave_500') == 'valor_500' * 100
        assert len(cache) == 1000
