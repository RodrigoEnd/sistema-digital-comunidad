"""
Script de prueba para verificar el sistema de optimización UI
Ejecutar: python tests/test_optimizador_ui.py
"""

import sys
import os
import time
import threading

# Agregar ruta del proyecto
proyecto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, proyecto_raiz)

from src.core.optimizador_ui import (
    get_ui_optimizer,
    DebounceManager,
    CacheManager,
    BackgroundWorker,
    VirtualTable
)


def test_debounce():
    """Test 1: Verificar que el debouncing funciona correctamente"""
    print("🧪 Test 1: Debouncing...")
    
    contador = {'valor': 0}
    
    def incrementar():
        contador['valor'] += 1
    
    debouncer = DebounceManager()
    
    # Llamar 10 veces rápidamente
    for i in range(10):
        debouncer.debounce('test', 100, incrementar)
        time.sleep(0.01)  # 10ms entre llamadas
    
    # Esperar a que se ejecute
    time.sleep(0.2)
    
    # Debería ejecutarse solo 1 vez
    assert contador['valor'] == 1, f"❌ Esperado 1, obtenido {contador['valor']}"
    print("✅ Debouncing funciona correctamente")


def test_cache():
    """Test 2: Verificar que el caché funciona"""
    print("\n🧪 Test 2: Caché...")
    
    cache = CacheManager(max_size=10, ttl_seconds=60)
    
    # Guardar datos
    cache.set("resultado1", "busqueda", "juan")
    cache.set("resultado2", "busqueda", "maria")
    
    # Recuperar datos
    r1 = cache.get("busqueda", "juan")
    r2 = cache.get("busqueda", "maria")
    r3 = cache.get("busqueda", "pedro")  # No existe
    
    assert r1 == "resultado1", "❌ Caché no devolvió valor correcto"
    assert r2 == "resultado2", "❌ Caché no devolvió valor correcto"
    assert r3 is None, "❌ Caché devolvió valor cuando debería ser None"
    
    print("✅ Caché funciona correctamente")


def test_background_worker():
    """Test 3: Verificar que el worker en background funciona"""
    print("\n🧪 Test 3: Background Worker...")
    
    worker = BackgroundWorker()
    resultado_final = {'valor': None}
    evento = threading.Event()
    
    def tarea_larga():
        time.sleep(0.1)
        return "tarea completada"
    
    def callback(resultado):
        resultado_final['valor'] = resultado
        evento.set()
    
    worker.run_async('test', tarea_larga, callback)
    
    # Esperar a que termine (máximo 1 segundo)
    evento.wait(timeout=1.0)
    
    assert resultado_final['valor'] == "tarea completada", "❌ Worker no ejecutó correctamente"
    print("✅ Background Worker funciona correctamente")


def test_virtual_table():
    """Test 4: Verificar virtualización de tabla"""
    print("\n🧪 Test 4: Virtual Table...")
    
    virtual = VirtualTable(total_items=1000, visible_rows=25, buffer_rows=5)
    
    # Inicio
    start, end = virtual.get_visible_range()
    assert start == 0, "❌ Inicio incorrecto"
    assert end == 30, f"❌ Fin incorrecto, esperado 30, obtenido {end}"  # 25 + 5 buffer
    
    # Scroll al medio
    virtual.update_scroll(500)
    start, end = virtual.get_visible_range()
    assert 495 <= start <= 500, "❌ Inicio después de scroll incorrecto"
    
    print("✅ Virtual Table funciona correctamente")


def test_ui_optimizer():
    """Test 5: Verificar integración completa del UIOptimizer"""
    print("\n🧪 Test 5: UIOptimizer Completo...")
    
    optimizer = get_ui_optimizer()
    
    # Test debounce search
    contador = {'valor': 0}
    def buscar(criterio):
        contador['valor'] += 1
    
    for i in range(5):
        optimizer.debounce_search('widget1', 100, buscar, "juan")
        time.sleep(0.01)
    
    time.sleep(0.2)
    assert contador['valor'] == 1, "❌ Debounce search no funciona"
    
    # Test cached filter
    def filtrar(data, criterio):
        return [d for d in data if criterio in d]
    
    datos = ["juan", "maria", "jose", "juan carlos"]
    
    # Primera vez - calcula
    r1 = optimizer.cached_filter(filtrar, datos, "juan")
    # Segunda vez - usa caché
    r2 = optimizer.cached_filter(filtrar, datos, "juan")
    
    assert r1 == r2, "❌ Cached filter no funciona"
    assert len(r1) == 2, "❌ Filtro incorrecto"
    
    # Test async update
    evento = threading.Event()
    resultado = {'valor': None}
    
    def tarea():
        return "async completado"
    
    def callback(r):
        resultado['valor'] = r
        evento.set()
    
    optimizer.async_update('test', tarea, callback)
    evento.wait(timeout=1.0)
    
    assert resultado['valor'] == "async completado", "❌ Async update no funciona"
    
    print("✅ UIOptimizer completo funciona correctamente")


def test_performance():
    """Test 6: Verificar mejora de rendimiento"""
    print("\n🧪 Test 6: Performance...")
    
    # Simular búsqueda sin optimización
    inicio = time.time()
    datos = list(range(10000))
    resultados_sin_opt = []
    
    for i in range(10):
        # Simular búsqueda pesada
        resultado = [d for d in datos if d % 2 == 0]
        resultados_sin_opt.append(len(resultado))
    
    tiempo_sin_opt = time.time() - inicio
    
    # Con optimización (caché)
    optimizer = get_ui_optimizer()
    
    def filtrar_pares(data, _):
        return [d for d in data if d % 2 == 0]
    
    inicio = time.time()
    resultados_con_opt = []
    
    for i in range(10):
        resultado = optimizer.cached_filter(filtrar_pares, datos, "criterio")
        resultados_con_opt.append(len(resultado))
    
    tiempo_con_opt = time.time() - inicio
    
    mejora = ((tiempo_sin_opt - tiempo_con_opt) / tiempo_sin_opt) * 100
    
    print(f"   Sin optimización: {tiempo_sin_opt:.4f}s")
    print(f"   Con optimización: {tiempo_con_opt:.4f}s")
    print(f"   Mejora: {mejora:.1f}%")
    
    assert tiempo_con_opt < tiempo_sin_opt, "❌ Optimización no mejoró el tiempo"
    print("✅ Performance mejorada significativamente")


def main():
    """Ejecutar todos los tests"""
    print("=" * 60)
    print("🚀 TESTS DE OPTIMIZACIÓN DE UI")
    print("=" * 60)
    
    try:
        test_debounce()
        test_cache()
        test_background_worker()
        test_virtual_table()
        test_ui_optimizer()
        test_performance()
        
        print("\n" + "=" * 60)
        print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 60)
        print("\n💡 El sistema de optimización está funcionando correctamente")
        print("   Puedes ejecutar la aplicación con confianza.")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    exito = main()
    sys.exit(0 if exito else 1)
