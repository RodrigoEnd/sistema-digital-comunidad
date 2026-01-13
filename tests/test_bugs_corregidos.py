"""
Suite de pruebas para validar bugs encontrados y correcciones
Archivo: test_bugs_corregidos.py

Ejecutar con: pytest test_bugs_corregidos.py -v
"""

import sys
import os
from datetime import datetime

# Agregar raíz del proyecto al path
proyecto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proyecto_raiz not in sys.path:
    sys.path.insert(0, proyecto_raiz)

from src.core.validadores import validar_monto, ErrorValidacion
from src.modules.pagos.pagos_estado import GestorEstadoPago, EstadoPago
from src.modules.pagos.pagos_eliminacion_segura import GestorEliminacionSegura


class TestValidacionMontos:
    """Pruebas para BUG #2: Validación de montos"""
    
    def test_monto_positivo_valido(self):
        """✓ Debe aceptar montos positivos válidos"""
        assert validar_monto(100.0) == 100.0
        assert validar_monto(50.50) == 50.50
        assert validar_monto('75.25') == 75.25
    
    def test_monto_cero_rechazado(self):
        """✗ CRÍTICO: Debe rechazar $0.00"""
        try:
            validar_monto(0)
            assert False, "Debería lanzar ErrorValidacion para $0"
        except ErrorValidacion as e:
            assert "mayor a $0" in str(e).lower()
    
    def test_monto_negativo_rechazado(self):
        """✗ CRÍTICO: Debe rechazar montos negativos"""
        try:
            validar_monto(-50)
            assert False, "Debería lanzar ErrorValidacion para montos negativos"
        except ErrorValidacion as e:
            assert "negativo" in str(e).lower()
    
    def test_monto_cadena_invalida(self):
        """✗ Debe rechazar cadenas no numéricas"""
        try:
            validar_monto("abc")
            assert False, "Debería lanzar ErrorValidacion"
        except ErrorValidacion:
            pass
    
    def test_monto_redondeado_correctamente(self):
        """✓ Debe redondear a 2 decimales"""
        resultado = validar_monto(100.555)
        assert resultado == 100.56
        assert len(str(resultado).split('.')[-1]) <= 2


class TestGestorEstadoPago:
    """Pruebas para BUG #1 y #4: Gestión uniforme de estados"""
    
    def test_estado_pendiente(self):
        """✓ Sin pagos = Pendiente"""
        assert GestorEstadoPago.obtener_estado(0, 100) == 'pendiente'
    
    def test_estado_parcial(self):
        """✓ BUG FIX #1: Pago menor = Parcial (NO completo)"""
        # Monto esperado: $100, pagado: $30
        assert GestorEstadoPago.obtener_estado(30, 100) == 'parcial'
        assert GestorEstadoPago.obtener_estado(75, 100) == 'parcial'
        assert GestorEstadoPago.obtener_estado(99, 100) == 'parcial'
    
    def test_estado_completado(self):
        """✓ Pagado exactamente = Completado"""
        assert GestorEstadoPago.obtener_estado(100, 100) == 'completado'
    
    def test_estado_excedente(self):
        """✓ Pagado más = Excedente"""
        assert GestorEstadoPago.obtener_estado(150, 100) == 'excedente'
        assert GestorEstadoPago.obtener_estado(100.01, 100) == 'excedente'
    
    def test_obtener_datos_estado(self):
        """✓ Obtener metadatos de estado"""
        datos = GestorEstadoPago.obtener_datos_estado('parcial')
        assert datos['nombre'] == 'Parcial'
        assert datos['emoji'] == '◐'
        assert datos['color_fg'] == 'warning'
    
    def test_transicion_valida(self):
        """✓ Validar transiciones de estado válidas"""
        es_válida, _ = GestorEstadoPago.validar_transicion('pendiente', 'parcial')
        assert es_válida is True
        
        es_válida, _ = GestorEstadoPago.validar_transicion('parcial', 'completado')
        assert es_válida is True
    
    def test_transicion_invalida(self):
        """✗ Rechazar transiciones inválidas"""
        es_válida, _ = GestorEstadoPago.validar_transicion('completado', 'pendiente')
        assert es_válida is False
    
    def test_consistencia_estados_multiples_calculos(self):
        """✓ Estado debe ser consistente sin importar cuándo se calcule"""
        # Escenario: $30 pagado de $100 esperado
        total_pagado = 30
        monto_esperado = 100
        
        # Calcular estado 5 veces diferentes
        estados = [GestorEstadoPago.obtener_estado(total_pagado, monto_esperado) for _ in range(5)]
        
        # Todos deben ser 'parcial'
        assert all(e == 'parcial' for e in estados), f"Estados inconsistentes: {estados}"


class TestEliminacionSegura:
    """Pruebas para BUG #5: Eliminación segura con backup"""
    
    def test_hacer_backup_persona(self):
        """✓ BUG FIX #5: Crear backup antes de eliminar"""
        persona_test = {
            'folio': 'TEST-001',
            'nombre': 'Juan Prueba',
            'monto_esperado': 100,
            'pagos': [
                {'monto': 30, 'fecha': '01/01/2026', 'hora': '10:00:00'},
                {'monto': 20, 'fecha': '02/01/2026', 'hora': '11:00:00'}
            ]
        }
        
        backup = GestorEliminacionSegura.hacer_backup_persona(
            persona_test,
            motivo='Prueba unitaria',
            usuario='TestUser'
        )
        
        # Verificar que el backup se creó
        assert backup is not None
        assert backup['datos_persona']['folio'] == 'TEST-001'
        assert backup['datos_persona']['nombre'] == 'Juan Prueba'
        assert backup['información_audit']['total_pagado'] == 50
        assert backup['información_audit']['número_pagos'] == 2
    
    def test_recuperar_persona_eliminada(self):
        """✓ Poder recuperar datos de persona eliminada"""
        persona_test = {
            'folio': 'TEST-REC-001',
            'nombre': 'María Recuperable',
            'monto_esperado': 200,
            'pagos': []
        }
        
        # Hacer backup
        GestorEliminacionSegura.hacer_backup_persona(persona_test, 'Prueba', 'TestUser')
        
        # Recuperar
        registro = GestorEliminacionSegura.recuperar_persona_eliminada('TEST-REC-001')
        assert registro is not None
        assert registro['datos_persona']['nombre'] == 'María Recuperable'
    
    def test_resumen_eliminaciones(self):
        """✓ Obtener estadísticas de eliminaciones"""
        resumen = GestorEliminacionSegura.obtener_resumen_eliminaciones()
        
        # Verificar estructura
        assert 'total_personas_eliminadas' in resumen
        assert 'total_dinero_en_eliminadas' in resumen
        assert 'promedio_pagado_persona' in resumen
        assert 'eliminaciones_por_usuario' in resumen


class TestCasosDeUsoIntegrados:
    """Pruebas de casos de uso integrados"""
    
    def test_flujo_pago_parcial_completo(self):
        """
        ✓ BUG FIX #1: Flujo completo de pago parcial y luego completo
        
        Escenario:
        1. Crear persona con monto esperado $100
        2. Registrar pago de $30 → Debe ser "Parcial"
        3. Registrar pago de $70 → Debe ser "Completado"
        """
        persona = {
            'nombre': 'Persona Test',
            'folio': 'FLOW-001',
            'monto_esperado': 100,
            'pagos': []
        }
        
        # Registrar primer pago
        persona['pagos'].append({
            'monto': 30,
            'fecha': '01/01/2026',
            'hora': '10:00:00'
        })
        
        total_1 = sum(p['monto'] for p in persona['pagos'])
        estado_1 = GestorEstadoPago.obtener_estado(total_1, persona['monto_esperado'])
        assert estado_1 == 'parcial', f"Primer pago debe ser parcial, obtuvo: {estado_1}"
        
        # Registrar segundo pago
        persona['pagos'].append({
            'monto': 70,
            'fecha': '02/01/2026',
            'hora': '11:00:00'
        })
        
        total_2 = sum(p['monto'] for p in persona['pagos'])
        estado_2 = GestorEstadoPago.obtener_estado(total_2, persona['monto_esperado'])
        assert estado_2 == 'completado', f"Segundo pago debe completar, obtuvo: {estado_2}"
    
    def test_validacion_monto_antes_registrar(self):
        """✓ BUG FIX #2: Validar monto ANTES de registrar pago"""
        montos_invalidos = [0, -50, -0.01]
        
        for monto in montos_invalidos:
            try:
                validar_monto(monto)
                assert False, f"Debería rechazar monto: {monto}"
            except ErrorValidacion:
                pass  # Esperado
        
        # Monto válido debe pasar
        assert validar_monto(75.50) == 75.50


# Función para ejecutar pruebas manualmente
if __name__ == '__main__':
    print("=" * 80)
    print("🧪 EJECUTANDO PRUEBAS DE BUGS CORREGIDOS")
    print("=" * 80)
    
    # Pruebas de validación de montos
    print("\n[TEST SUITE 1] Validación de Montos (BUG #2)")
    print("-" * 80)
    test_validacion = TestValidacionMontos()
    
    try:
        test_validacion.test_monto_positivo_valido()
        print("✓ Montos positivos válidos: PASADO")
    except AssertionError as e:
        print(f"✗ Montos positivos válidos: FALLIDO - {e}")
    
    try:
        test_validacion.test_monto_cero_rechazado()
        print("✓ Rechazo de $0.00: PASADO")
    except AssertionError as e:
        print(f"✗ Rechazo de $0.00: FALLIDO - {e}")
    
    try:
        test_validacion.test_monto_negativo_rechazado()
        print("✓ Rechazo de montos negativos: PASADO")
    except AssertionError as e:
        print(f"✗ Rechazo de montos negativos: FALLIDO - {e}")
    
    # Pruebas de gestión de estados
    print("\n[TEST SUITE 2] Gestión de Estados (BUG #1 y #4)")
    print("-" * 80)
    test_estados = TestGestorEstadoPago()
    
    try:
        test_estados.test_estado_pendiente()
        print("✓ Detección de estado Pendiente: PASADO")
    except AssertionError as e:
        print(f"✗ Detección de estado Pendiente: FALLIDO - {e}")
    
    try:
        test_estados.test_estado_parcial()
        print("✓ Detección de estado Parcial (BUG #1 FIX): PASADO")
    except AssertionError as e:
        print(f"✗ Detección de estado Parcial: FALLIDO - {e}")
    
    try:
        test_estados.test_estado_completado()
        print("✓ Detección de estado Completado: PASADO")
    except AssertionError as e:
        print(f"✗ Detección de estado Completado: FALLIDO - {e}")
    
    try:
        test_estados.test_consistencia_estados_multiples_calculos()
        print("✓ Consistencia de estados (múltiples cálculos): PASADO")
    except AssertionError as e:
        print(f"✗ Consistencia de estados: FALLIDO - {e}")
    
    # Pruebas de eliminación segura
    print("\n[TEST SUITE 3] Eliminación Segura (BUG #5)")
    print("-" * 80)
    test_eliminacion = TestEliminacionSegura()
    
    try:
        test_eliminacion.test_hacer_backup_persona()
        print("✓ Creación de backup (BUG #5 FIX): PASADO")
    except Exception as e:
        print(f"✗ Creación de backup: FALLIDO - {e}")
    
    # Casos integrados
    print("\n[TEST SUITE 4] Casos Integrados")
    print("-" * 80)
    test_integrado = TestCasosDeUsoIntegrados()
    
    try:
        test_integrado.test_flujo_pago_parcial_completo()
        print("✓ Flujo pago parcial → completo (BUG #1 FIX): PASADO")
    except AssertionError as e:
        print(f"✗ Flujo pago parcial → completo: FALLIDO - {e}")
    
    try:
        test_integrado.test_validacion_monto_antes_registrar()
        print("✓ Validación de monto antes de registrar (BUG #2 FIX): PASADO")
    except AssertionError as e:
        print(f"✗ Validación de monto: FALLIDO - {e}")
    
    print("\n" + "=" * 80)
    print("✅ PRUEBAS COMPLETADAS")
    print("=" * 80)
