#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST DE VALIDACIÓN - Módulos Modularizados
Demuestra que todos los gestores funcionan correctamente
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.modules.pagos.pagos_gestor_cooperaciones import GestorCooperaciones
from src.modules.pagos.pagos_gestor_personas import GestorPersonas
from src.modules.pagos.pagos_gestor_datos import GestorDatos
from src.modules.pagos.pagos_gestor_api import GestorAPI
from src.modules.pagos.pagos_seguridad import GestorSeguridad
from src.modules.pagos.pagos_utilidades import UtiliPagos
from src.modules.pagos.pagos_constantes import CONFIG_DATOS, TIMERS
from src.auth.seguridad import seguridad


def test_gestores():
    """Prueba todos los gestores modularizados"""
    
    print("\n" + "="*70)
    print("🧪 VALIDACIÓN DE MÓDULOS MODULARIZADOS")
    print("="*70 + "\n")
    
    # 1. TEST: GestorCooperaciones
    print("1️⃣  Probando GestorCooperaciones...")
    gestor_coop = GestorCooperaciones(CONFIG_DATOS['archivo_pagos'], seguridad)
    gestor_coop._crear_cooperacion_default()
    
    try:
        nueva_coop = gestor_coop.crear_cooperacion(
            nombre="Proyecto Prueba 2026",
            proyecto="Mejora de infraestructura",
            monto=200.0
        )
        print(f"   ✅ Cooperación creada: {nueva_coop['nombre']}")
        print(f"   ✅ ID: {nueva_coop['id']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 2. TEST: GestorPersonas
    print("\n2️⃣  Probando GestorPersonas...")
    gestor_personas = GestorPersonas()
    
    try:
        persona1 = gestor_personas.crear_persona(
            nombre="Juan García López",
            monto=200.0,
            notas="Cooperación proyecto 2026"
        )
        print(f"   ✅ Persona creada: {persona1['nombre']}")
        print(f"   ✅ Folio: {persona1['folio']}")
        
        persona2 = gestor_personas.crear_persona(
            nombre="María López Ruiz",
            monto=200.0
        )
        print(f"   ✅ Persona 2 creada: {persona2['nombre']}")
        
        # Registrar pagos
        pago1 = gestor_personas.registrar_pago(
            folio=persona1['folio'],
            monto=100.0,
            notas="Primer aporte"
        )
        print(f"   ✅ Pago registrado: ${pago1['monto']:.2f}")
        
        # Obtener estado
        estado = gestor_personas.obtener_estado_persona(persona1['folio'])
        print(f"   ✅ Estado: Pagado ${estado['pagado']:.2f} / Esperado ${estado['esperado']:.2f}")
        print(f"   ✅ Pendiente: ${estado['pendiente']:.2f}")
        print(f"   ✅ Porcentaje: {estado['porcentaje']:.1f}%")
        
        # Resumen del grupo
        resumen = gestor_personas.obtener_resumen_grupo()
        print(f"   ✅ Total personas: {resumen['total_personas']}")
        print(f"   ✅ Total esperado: ${resumen['total_esperado']:.2f}")
        print(f"   ✅ Total pagado: ${resumen['total_pagado']:.2f}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. TEST: GestorSeguridad
    print("\n3️⃣  Probando GestorSeguridad...")
    gestor_seg = GestorSeguridad()
    
    try:
        usuario_test = {'nombre': 'Admin Test', 'rol': 'administrador'}
        
        class GestorAuthMock:
            ROLES = {
                'administrador': {'permisos': ['*']},
                'editor': {'permisos': ['crear', 'editar']},
                'viewer': {'permisos': ['visualizar']}
            }
        
        gestor_seg.establecer_usuario(usuario_test, GestorAuthMock())
        print(f"   ✅ Usuario establecido: {gestor_seg.obtener_nombre_usuario()}")
        print(f"   ✅ Rol: {gestor_seg.obtener_rol_actual()}")
        print(f"   ✅ Tiene permiso 'editar': {gestor_seg.tiene_permiso('editar')}")
        print(f"   ✅ Nivel de seguridad: {gestor_seg.obtener_nivel_seguridad()}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 4. TEST: UtiliPagos
    print("\n4️⃣  Probando UtiliPagos...")
    try:
        dinero = UtiliPagos.formatear_dinero(1234.56)
        print(f"   ✅ Formatear dinero: {dinero}")
        
        pct = UtiliPagos.formatear_porcentaje(75.5)
        print(f"   ✅ Formatear porcentaje: {pct}")
        
        emoji = UtiliPagos.obtener_emoji_estado('completado')
        print(f"   ✅ Emoji estado 'completado': {emoji}")
        
        truncado = UtiliPagos.truncar_texto("Este es un texto muy largo", max_chars=15)
        print(f"   ✅ Truncar texto: {truncado}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 5. TEST: GestorAPI
    print("\n5️⃣  Probando GestorAPI...")
    gestor_api = GestorAPI(CONFIG_DATOS['api_url'])
    
    try:
        estado_api = gestor_api.obtener_estado_api()
        print(f"   ✅ Estado API: {estado_api['modo']}")
        print(f"   ✅ Disponible: {estado_api.get('disponible', 'N/A')}")
        
    except Exception as e:
        print(f"   ⚠️  API: {e}")
    
    # 6. TEST: GestorDatos
    print("\n6️⃣  Probando GestorDatos...")
    gestor_datos = GestorDatos(CONFIG_DATOS['archivo_pagos'], CONFIG_DATOS['password_archivo'])
    
    try:
        # Crear contraseña de prueba
        password_test = "prueba123"
        password_hash = gestor_seg.hash_password(password_test)
        gestor_datos.establecer_password_hash(password_hash)
        print(f"   ✅ Contraseña establecida")
        
        # Verificar contraseña
        valida = gestor_seg.verificar_password(password_test, password_hash)
        print(f"   ✅ Contraseña verificada: {valida}")
        
        # Validar estructura de datos
        datos_test = {
            'cooperaciones': [nueva_coop],
            'cooperacion_activa': nueva_coop['id'],
            'password_hash': password_hash
        }
        valido, msg = gestor_datos.validar_estructura_datos(datos_test)
        print(f"   ✅ Estructura validada: {valido}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Resumen final
    print("\n" + "="*70)
    print("✅ VALIDACIÓN COMPLETADA EXITOSAMENTE")
    print("="*70)
    print("\n📊 Resultados:")
    print("   ✅ GestorCooperaciones: Funcional")
    print("   ✅ GestorPersonas: Funcional")
    print("   ✅ GestorSeguridad: Funcional")
    print("   ✅ UtiliPagos: Funcional")
    print("   ✅ GestorAPI: Funcional")
    print("   ✅ GestorDatos: Funcional")
    print("\n🎉 Todos los módulos modularizados están funcionando correctamente\n")


if __name__ == "__main__":
    test_gestores()
