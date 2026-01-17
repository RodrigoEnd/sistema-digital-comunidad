"""
Script para agregar una persona diferente con el mismo nombre
Miguel Sanchez Mendoza (diferenciado con asterisco y nota)
"""
import sys
import os
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from src.core.base_datos_sqlite import obtener_bd


def agregar_persona_especial():
    """Agrega Miguel Sanchez Mendoza (persona diferente) a censo y cooperación"""
    
    print("\n" + "="*80)
    print("AGREGAR PERSONA ESPECIAL: Miguel Sanchez Mendoza (Diferente)")
    print("="*80 + "\n")
    
    bd = obtener_bd()
    
    if not bd or not bd.conexion:
        print("[ERROR] No se pudo obtener conexión a BD")
        return
    
    cursor = bd.conexion.cursor()
    
    # Datos de la persona
    nombre = "* Miguel Sanchez Mendoza"  # Con asterisco para diferenciar
    nota = "Rectificar persona - Diferente del registro anterior"
    
    print(f"📝 Nombre: {nombre}")
    print(f"📌 Nota: {nota}\n")
    
    try:
        # Verificar si ya existe
        cursor.execute('SELECT id, folio FROM habitantes WHERE LOWER(nombre) = LOWER(?)', (nombre,))
        resultado = cursor.fetchone()
        
        if resultado:
            habitante_id, folio = resultado
            print(f"⚠ La persona ya existe")
            print(f"  ID: {habitante_id}")
            print(f"  Folio: {folio}")
            print(f"  Nombre: {nombre}")
        else:
            # Generar folio
            cursor.execute('SELECT MAX(CAST(SUBSTR(folio, 5) AS INTEGER)) FROM habitantes WHERE folio LIKE "FOL-%"')
            max_num_result = cursor.fetchone()
            max_num = max_num_result[0] if max_num_result and max_num_result[0] else 0
            folio = f"FOL-{max_num + 1:04d}"
            
            # Insertar en habitantes
            cursor.execute('''
                INSERT INTO habitantes (folio, nombre, nota, fecha_registro)
                VALUES (?, ?, ?, ?)
            ''', (folio, nombre, nota, datetime.now().isoformat()))
            
            bd.conexion.commit()
            habitante_id = cursor.lastrowid
            
            print(f"✅ CREADO EN CENSO")
            print(f"   ID: {habitante_id}")
            print(f"   Folio: {folio}")
            print(f"   Nombre: {nombre}")
            print(f"   Nota: {nota}\n")
            
            # Obtener cooperación activa
            cursor.execute('''
                SELECT id, nombre, monto_cooperacion 
                FROM cooperaciones 
                WHERE activa = 1 
                LIMIT 1
            ''')
            coop_resultado = cursor.fetchone()
            
            if coop_resultado:
                coop_id, coop_nombre, monto_coop = coop_resultado
                
                # Verificar si ya está en la cooperación
                cursor.execute('''
                    SELECT id FROM personas_cooperacion 
                    WHERE cooperacion_id = ? AND habitante_id = ?
                ''', (coop_id, habitante_id))
                
                if not cursor.fetchone():
                    # Insertar en cooperación
                    cursor.execute('''
                        INSERT INTO personas_cooperacion 
                        (cooperacion_id, habitante_id, monto_esperado, estado, fecha_agregado)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (coop_id, habitante_id, monto_coop, 'pendiente', datetime.now().isoformat()))
                    
                    bd.conexion.commit()
                    
                    print(f"✅ AGREGADO A COOPERACIÓN")
                    print(f"   Cooperación: {coop_nombre}")
                    print(f"   Monto: ${monto_coop:.2f}")
                else:
                    print(f"⚠ Ya estaba en la cooperación {coop_nombre}")
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    agregar_persona_especial()
