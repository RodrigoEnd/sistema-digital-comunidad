"""
Script FINAL para cargar la lista de habitantes consolidada
Versión 3 - Completamente funcional y robusta
"""
import sys
import os
import re
import time
import sqlite3
from datetime import datetime

# Configurar path
sys.path.insert(0, os.path.dirname(__file__))

from src.core.base_datos_sqlite import obtener_bd


def limpiar_nombre(nombre):
    """Limpia caracteres especiales del nombre"""
    # Reemplazar caracteres especiales comunes
    nombre = nombre.replace('ñ', 'n')
    nombre = nombre.replace('á', 'a')
    nombre = nombre.replace('é', 'e')
    nombre = nombre.replace('í', 'i')
    nombre = nombre.replace('ó', 'o')
    nombre = nombre.replace('ú', 'u')
    
    # Remover puntos y otros caracteres problemáticos
    nombre = re.sub(r'[^a-zA-Z\s\-]', '', nombre)
    
    return nombre.strip()


def leer_lista_habitantes(archivo):
    """Lee la lista de habitantes del archivo"""
    nombres = []
    
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        
        for linea in lineas:
            linea = linea.strip()
            
            if not linea or linea.startswith('#'):
                continue
            
            match = re.match(r'^\d+\.\s*\*?\s*(.+)$', linea)
            if match:
                nombre = match.group(1).strip()
                
                if nombre and len(nombre) > 3 and not nombre.isdigit():
                    nombres.append(nombre)
                    print(f"  ✓ {nombre}")
        
        print(f"\n[CARGA] Total de nombres leídos: {len(nombres)}")
        return nombres
    
    except Exception as e:
        print(f"[ERROR] No se pudo leer el archivo: {e}")
        return []


def cargar_habitantes_v3(nombres):
    """Carga habitantes usando SQL directo - VERSIÓN FINAL"""
    print("\n" + "="*80)
    print("FASE 1: Cargando habitantes (SQL Directo)")
    print("="*80)
    
    bd = obtener_bd()
    
    if not bd or not bd.conexion:
        print("[ERROR] No se pudo obtener conexión a BD")
        return []
    
    habitantes_creados = []
    duplicados = 0
    errores = 0
    
    for idx, nombre_original in enumerate(nombres, 1):
        try:
            nombre = limpiar_nombre(nombre_original)
            
            if not nombre or len(nombre) < 3:
                print(f"  [{idx:3d}] ⚠ INVÁLIDO: '{nombre_original}' -> '{nombre}'")
                errores += 1
                continue
            
            cursor = bd.conexion.cursor()
            
            # Verificar si existe
            cursor.execute('SELECT id, folio FROM habitantes WHERE LOWER(nombre) = LOWER(?)', (nombre,))
            resultado = cursor.fetchone()
            
            if resultado:
                habitante_id, folio = resultado
                print(f"  [{idx:3d}] ⚠ DUPLICADO: {nombre}")
                duplicados += 1
                habitantes_creados.append({
                    'id': habitante_id,
                    'nombre': nombre,
                    'folio': folio
                })
                continue
            
            # Generar folio
            cursor.execute('SELECT MAX(CAST(SUBSTR(folio, 5) AS INTEGER)) FROM habitantes WHERE folio LIKE "FOL-%"')
            max_num_result = cursor.fetchone()
            max_num = max_num_result[0] if max_num_result and max_num_result[0] else 0
            folio = f"FOL-{max_num + 1:04d}"
            
            # Insertar (usando la estructura correcta)
            cursor.execute('''
                INSERT INTO habitantes (folio, nombre, fecha_registro)
                VALUES (?, ?, ?)
            ''', (folio, nombre, datetime.now().isoformat()))
            
            bd.conexion.commit()
            habitante_id = cursor.lastrowid
            
            print(f"  [{idx:3d}] ✓ CREADO: {nombre} (Folio: {folio})")
            
            habitantes_creados.append({
                'id': habitante_id,
                'nombre': nombre,
                'folio': folio
            })
            
            time.sleep(0.001)  # Micro delay
        
        except sqlite3.IntegrityError as e:
            print(f"  [{idx:3d}] ⚠ ERROR INT: {nombre_original} - {str(e)[:50]}")
            duplicados += 1
        
        except Exception as e:
            print(f"  [{idx:3d}] ✗ ERROR: {nombre_original} - {str(e)[:60]}")
            errores += 1
    
    print(f"\n[RESUMEN FASE 1]")
    print(f"  Creados: {len(habitantes_creados) - duplicados}")
    print(f"  Duplicados/No cargados: {duplicados}")
    print(f"  Errores: {errores}")
    
    return habitantes_creados


def agregar_a_cooperacion_v3(habitantes):
    """Agrega habitantes a la cooperación - VERSIÓN FINAL"""
    print("\n" + "="*80)
    print("FASE 2: Agregando a cooperación")
    print("="*80)
    
    bd = obtener_bd()
    
    if not bd or not bd.conexion:
        print("[ERROR] No se pudo obtener conexión a BD")
        return 0
    
    cursor = bd.conexion.cursor()
    
    # Obtener cooperación activa
    cursor.execute('''
        SELECT id, nombre, monto_cooperacion 
        FROM cooperaciones 
        WHERE activa = 1 
        LIMIT 1
    ''')
    resultado = cursor.fetchone()
    
    if not resultado:
        print("[ERROR] No hay cooperación activa")
        return 0
    
    coop_id, coop_nombre, monto_coop = resultado
    
    print(f"\n📋 Cooperación: {coop_nombre} (ID: {coop_id})")
    print(f"💰 Monto: ${monto_coop:.2f}")
    print(f"👥 Habitantes a procesar: {len(habitantes)}\n")
    
    agregados = 0
    ya_estaban = 0
    errores = 0
    
    for idx, habitante in enumerate(habitantes, 1):
        try:
            habitante_id = habitante.get('id')
            nombre = habitante.get('nombre')
            folio = habitante.get('folio')
            
            # Verificar si ya está en esta cooperación
            cursor.execute('''
                SELECT id FROM personas_cooperacion 
                WHERE cooperacion_id = ? AND habitante_id = ?
            ''', (coop_id, habitante_id))
            
            if cursor.fetchone():
                print(f"  [{idx:3d}] ⚠ YA ESTÁ: {nombre}")
                ya_estaban += 1
                continue
            
            # Insertar
            cursor.execute('''
                INSERT INTO personas_cooperacion 
                (cooperacion_id, habitante_id, monto_esperado, estado, fecha_agregado)
                VALUES (?, ?, ?, ?, ?)
            ''', (coop_id, habitante_id, monto_coop, 'pendiente', datetime.now().isoformat()))
            
            bd.conexion.commit()
            agregados += 1
            print(f"  [{idx:3d}] ✓ AGREGADO: {nombre}")
            
            time.sleep(0.001)
        
        except sqlite3.IntegrityError:
            print(f"  [{idx:3d}] ⚠ YA EXISTE: {nombre}")
            ya_estaban += 1
        
        except Exception as e:
            print(f"  [{idx:3d}] ✗ ERROR: {str(e)[:50]}")
            errores += 1
    
    print(f"\n[RESUMEN FASE 2]")
    print(f"  Agregados: {agregados}")
    print(f"  Ya estaban: {ya_estaban}")
    print(f"  Errores: {errores}")
    
    return agregados


def main():
    print("\n" + "="*80)
    print("CARGA MASIVA DE HABITANTES - VERSIÓN 3 (FINAL)")
    print("Sistema Digital Comunidad")
    print("="*80 + "\n")
    
    archivo = os.path.join(os.path.dirname(__file__), 
                          'datos', 'lista_habitantes_consolidada.txt')
    
    print(f"📂 Archivo: {archivo}")
    print(f"⏰ Inicio: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    if not os.path.exists(archivo):
        print(f"[ERROR] Archivo no existe: {archivo}")
        return
    
    # FASE 0
    print("FASE 0: Leyendo archivo")
    print("-" * 80)
    nombres = leer_lista_habitantes(archivo)
    
    if not nombres:
        print("[ERROR] No se leyeron nombres")
        return
    
    # FASE 1
    habitantes = cargar_habitantes_v3(nombres)
    
    if not habitantes:
        print("[ERROR] No se cargaron habitantes")
        return
    
    # FASE 2
    agregados = agregar_a_cooperacion_v3(habitantes)
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN FINAL")
    print("="*80)
    print(f"✅ Nombres leídos: {len(nombres)}")
    print(f"✅ Habitantes creados: {len(habitantes)}")
    print(f"✅ Agregados a cooperación: {agregados}")
    print(f"⏰ Fin: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
