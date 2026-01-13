"""
Configuracion global de pytest
Define fixtures y configuraciones comunes para todos los tests
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path

# Agregar ruta del proyecto al path
proyecto_raiz = Path(__file__).parent
sys.path.insert(0, str(proyecto_raiz))


# ============================================================================
# FIXTURES GLOBALES
# ============================================================================

@pytest.fixture(scope="session")
def proyecto_dir():
    """Directorio raiz del proyecto"""
    return Path(__file__).parent


@pytest.fixture(scope="function")
def temp_dir():
    """Directorio temporal para tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture(scope="function")
def temp_file():
    """Archivo temporal para tests"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


# ============================================================================
# FIXTURES PARA BASE DE DATOS DE PRUEBA
# ============================================================================

@pytest.fixture(scope="function")
def datos_habitantes_prueba():
    """Datos de prueba para habitantes"""
    return [
        {
            'folio': 'HAB-0001',
            'nombre': 'Juan Perez',
            'fecha_registro': '01/01/2026',
            'activo': True,
            'nota': 'Habitante de prueba'
        },
        {
            'folio': 'HAB-0002',
            'nombre': 'Maria Garcia',
            'fecha_registro': '02/01/2026',
            'activo': True,
            'nota': 'Segunda prueba'
        },
        {
            'folio': 'HAB-0003',
            'nombre': 'Carlos Lopez',
            'fecha_registro': '03/01/2026',
            'activo': False,
            'nota': 'Inactivo'
        }
    ]


@pytest.fixture(scope="function")
def datos_pagos_prueba():
    """Datos de prueba para pagos"""
    return [
        {
            'id': 'PAG-0001',
            'habitante_folio': 'HAB-0001',
            'monto': 500.00,
            'fecha': '05/01/2026',
            'estado': 'completo'
        },
        {
            'id': 'PAG-0002',
            'habitante_folio': 'HAB-0002',
            'monto': 250.00,
            'fecha': '06/01/2026',
            'estado': 'parcial'
        }
    ]


@pytest.fixture(scope="function")
def datos_faenas_prueba():
    """Datos de prueba para faenas"""
    return [
        {
            'id': 'FAE-0001',
            'fecha': '07/01/2026',
            'tipo': 'Limpieza',
            'participantes': ['HAB-0001', 'HAB-0002'],
            'horas': 4.0
        },
        {
            'id': 'FAE-0002',
            'fecha': '08/01/2026',
            'tipo': 'Reparacion',
            'participantes': ['HAB-0001'],
            'horas': 6.0
        }
    ]


# ============================================================================
# FIXTURES PARA VALIDACION
# ============================================================================

@pytest.fixture(scope="function")
def nombres_validos():
    """Nombres validos para pruebas"""
    return [
        "Juan Perez",
        "Maria Garcia",
        "José María",
        "Ana-Paula",
        "Carlos Luis Alberto"
    ]


@pytest.fixture(scope="function")
def nombres_invalidos():
    """Nombres invalidos para pruebas"""
    return [
        "Jo",  # Muy corto
        "A" * 101,  # Muy largo
        "Juan@123",  # Caracteres invalidos
        "",  # Vacio
        "   "  # Solo espacios
    ]


@pytest.fixture(scope="function")
def montos_validos():
    """Montos validos para pruebas"""
    return [
        10.00,
        100.50,
        1000.99,
        0.01
    ]


@pytest.fixture(scope="function")
def montos_invalidos():
    """Montos invalidos para pruebas"""
    return [
        0,  # Cero
        -50,  # Negativo
        -0.01,  # Negativo pequeño
        "abc"  # Invalido
    ]


# ============================================================================
# FIXTURES PARA CACHE
# ============================================================================

@pytest.fixture(scope="function")
def cache_limpio():
    """Cache limpio para tests"""
    from src.core.cache import limpiar_cache_global
    limpiar_cache_global()
    yield
    limpiar_cache_global()


# ============================================================================
# HOOKS GLOBALES
# ============================================================================

def pytest_configure(config):
    """Configuracion inicial de pytest"""
    print("\n" + "="*70)
    print("INICIANDO SUITE DE TESTS - SISTEMA DIGITAL COMUNITARIO")
    print("="*70 + "\n")


def pytest_sessionfinish(session, exitstatus):
    """Al terminar la sesion de tests"""
    print("\n" + "="*70)
    if exitstatus == 0:
        print("TODOS LOS TESTS PASARON EXITOSAMENTE!")
    else:
        print("ALGUNOS TESTS FALLARON - REVISAR SALIDA ARRIBA")
    print("="*70 + "\n")


@pytest.fixture(autouse=True)
def reset_datos_entre_tests():
    """Reset de datos entre cada test"""
    yield
    # Cleanup despues de cada test
    from src.core.cache import limpiar_cache_global
    try:
        limpiar_cache_global()
    except:
        pass
