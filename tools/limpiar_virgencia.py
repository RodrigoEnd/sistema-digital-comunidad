"""
Script para limpiar registros problemáticos y agregar Virgencia
"""

import sys
import os

proyecto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, proyecto_raiz)

from src.core.base_datos_sqlite import BaseDatosSQLite
from datetime import datetime


def limpiar_y_agregar():
    print("=" * 80)
    print("LIMPIEZA Y CORRECCIÓN DE REGISTRO")
    print("=" * 80)
    print()
    
    bd = BaseDatosSQLite()
    cursor = bd.conexion.cursor()
    
    # Buscar todos los registros de Virgencia
    print("🔍 Buscando registros de 'Virgencia de la Cruz Guzman'...")
    cursor.execute("""
        SELECT id, folio, nombre, activo FROM habitantes 
        WHERE LOWER(nombre) LIKE '%virgencia%'
    """)
    
    registros = cursor.fetchall()
    
    if registros:
        print(f"Encontrados {len(registros)} registros:")
        for reg in registros:
            print(f"  - ID: {reg['id']}, Folio: {reg['folio']}, Nombre: {reg['nombre']}, Activo: {reg['activo']}")
        
        print()
        print("🗑️ Eliminando todos los registros...")
        cursor.execute("DELETE FROM habitantes WHERE LOWER(nombre) LIKE '%virgencia%'")
        bd.conexion.commit()
        print("✅ Registros eliminados")
    else:
        print("No se encontraron registros previos")
    
    print()
    print("➕ Agregando 'Virgencia de la Cruz Guzman' con FOL-0001...")
    
    try:
        cursor.execute("""
            INSERT INTO habitantes 
            (folio, nombre, apellidos, activo, fecha_registro, nota)
            VALUES (?, ?, '', 1, ?, ?)
        """, (
            "FOL-0001",
            "Virgencia de la Cruz Guzman",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Importado desde faenas_pagos.txt"
        ))
        
        bd.conexion.commit()
        print("✅ Registro agregado correctamente")
        
        # Verificar
        cursor.execute("SELECT folio, nombre FROM habitantes WHERE folio = 'FOL-0001'")
        resultado = cursor.fetchone()
        
        if resultado:
            print(f"✅ Verificación: {resultado['folio']} - {resultado['nombre']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        bd.conexion.rollback()
    
    bd.desconectar()
    print()
    print("=" * 80)
    print("PROCESO COMPLETADO")
    print("=" * 80)


if __name__ == "__main__":
    limpiar_y_agregar()
