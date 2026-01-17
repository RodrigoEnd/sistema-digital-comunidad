"""
Script mejorado para cargar la lista de habitantes consolidada
Maneja conflictos, caracteres especiales y bloqueos de BD
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
from src.core.logger import registrar_operacion


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
    """Lee y parsea la lista de habitantes del archivo"""
    nombres = []
    
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        
        # Procesar líneas
        for linea in lineas:
            linea = linea.strip()
            
            # Saltar comentarios y líneas vacías
            if not linea or linea.startswith('#'):
                continue
            
            # Remover el número de la lista
            match = re.match(r'^\d+\.\s*\*?\s*(.+)$', linea)
            if match:
                nombre = match.group(1).strip()
                
                # Validar nombre
                if nombre and len(nombre) > 3 and not nombre.isdigit():
                    nombres.append(nombre)
                    print(f"  ✓ {nombre}")
        
        print(f"\n[CARGA] Total de nombres leídos: {len(nombres)}")
        return nombres
    
    except Exception as e:
        print(f"[ERROR] No se pudo leer el archivo: {e}")
        return []


def cargar_habitantes_en_bd_directo(nombres):
    """Carga directamente en la BD SQLite evitando bloqueos"""
    print("\n" + "="*80)
    print("FASE 1: Cargando habitantes en la base de datos (método directo)")
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
            # Limpiar nombre
            nombre = limpiar_nombre(nombre_original)
            
            if not nombre or len(nombre) < 3:
                print(f"  [{idx:3d}] ⚠ INVÁLIDO: {nombre_original} (después de limpiar: '{nombre}')")
                errores += 1
                continue
            
            # Verificar si existe
            cursor = bd.conexion.cursor()
            cursor.execute('SELECT id, folio FROM habitantes WHERE LOWER(nombre) = LOWER(?)', (nombre,))
            resultado = cursor.fetchone()
            
            if resultado:
                habitante_id, folio = resultado
                print(f"  [{idx:3d}] ⚠ DUPLICADO: {nombre} (ID: {habitante_id}, Folio: {folio})")
                duplicados += 1
                habitantes_creados.append({
                    'id': habitante_id,
                    'nombre': nombre,
                    'folio': folio
                })
                continue
            
            # Generar folio
            cursor.execute('SELECT MAX(CAST(SUBSTR(folio, 5) AS INTEGER)) FROM habitantes WHERE folio LIKE "FOL-%"')
            max_num = cursor.fetchone()[0] or 0
            folio = f"FOL-{max_num + 1:04d}"
            
            # Insertar
            try:
                cursor.execute('''
                    INSERT INTO habitantes (nombre, folio, fecha_creacion)
                    VALUES (?, ?, ?)
                ''', (nombre, folio, datetime.now().isoformat()))
                
                bd.conexion.commit()
                habitante_id = cursor.lastrowid
                
                print(f"  [{idx:3d}] ✓ CREADO: {nombre} (Folio: {folio})")
                
                habitantes_creados.append({
                    'id': habitante_id,
                    'nombre': nombre,
                    'folio': folio
                })
            
            except sqlite3.IntegrityError as e:
                if 'UNIQUE constraint failed' in str(e):
                    print(f"  [{idx:3d}] ⚠ DUPLICADO (clave única): {nombre}")
                    duplicados += 1
                else:
                    print(f"  [{idx:3d}] ✗ ERROR: {nombre} - {str(e)}")
                    errores += 1
            
            # Pequeño delay para evitar bloqueos
            time.sleep(0.01)
        
        except Exception as e:
            print(f"  [{idx:3d}] ✗ EXCEPCIÓN: {nombre_original} - {str(e)}")
            errores += 1
    
    print(f"\n[RESUMEN FASE 1]")
    print(f"  Creados: {len(habitantes_creados) - duplicados}")
    print(f"  Duplicados: {duplicados}")
    print(f"  Errores: {errores}")
    print(f"  Total procesados: {len(nombres)}")
    
    return habitantes_creados


def agregar_a_cooperacion_directo(habitantes):
    """Agrega directamente a la cooperación en la BD"""
    print("\n" + "="*80)
    print("FASE 2: Agregando habitantes a la cooperación (método directo)")
    print("="*80)
    
    bd = obtener_bd()
    
    if not bd or not bd.conexion:
        print("[ERROR] No se pudo obtener conexión a BD")
        return 0
    
    # Obtener cooperación activa
    cursor = bd.conexion.cursor()
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
    
    print(f"\n📋 Cooperación destino: {coop_nombre} (ID: {coop_id})")
    print(f"💰 Monto por persona: ${monto_coop:.2f}")
    print(f"👥 Total de habitantes a procesar: {len(habitantes)}\n")
    
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
                print(f"  [{idx:3d}] ⚠ EN COOP: {nombre}")
                ya_estaban += 1
                continue
            
            # Insertar
            try:
                cursor.execute('''
                    INSERT INTO personas_cooperacion 
                    (cooperacion_id, habitante_id, monto_esperado, estado, fecha_agregado)
                    VALUES (?, ?, ?, ?, ?)
                ''', (coop_id, habitante_id, monto_coop, 'pendiente', datetime.now().isoformat()))
                
                bd.conexion.commit()
                agregados += 1
                print(f"  [{idx:3d}] ✓ AGREGADO: {nombre} (Folio: {folio})")
            
            except sqlite3.IntegrityError:
                print(f"  [{idx:3d}] ⚠ YA EXISTE: {nombre}")
                ya_estaban += 1
            
            # Pequeño delay
            time.sleep(0.01)
        
        except Exception as e:
            print(f"  [{idx:3d}] ✗ EXCEPCIÓN: {str(e)}")
            errores += 1
    
    print(f"\n[RESUMEN FASE 2]")
    print(f"  Agregados a cooperación: {agregados}")
    print(f"  Ya estaban en cooperación: {ya_estaban}")
    print(f"  Errores: {errores}")
    
    return agregados


def main():
    print("\n" + "="*80)
    print("CARGA MASIVA DE HABITANTES (Método Directo SQLite)")
    print("Sistema Digital Comunidad")
    print("="*80 + "\n")
    
    archivo = os.path.join(os.path.dirname(__file__), 
                          'datos', 'lista_habitantes_consolidada.txt')
    
    print(f"📂 Archivo: {archivo}")
    print(f"⏰ Inicio: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    if not os.path.exists(archivo):
        print(f"[ERROR] El archivo no existe: {archivo}")
        return
    
    # FASE 0: Leer archivo
    print("FASE 0: Leyendo archivo de lista consolidada")
    print("-" * 80)
    nombres = leer_lista_habitantes(archivo)
    
    if not nombres:
        print("[ERROR] No se pudo leer ningún nombre del archivo")
        return
    
    # FASE 1: Cargar en BD (método directo)
    habitantes = cargar_habitantes_en_bd_directo(nombres)
    
    if not habitantes:
        print("[ERROR] No se cargaron habitantes en BD")
        return
    
    # FASE 2: Agregar a cooperación (método directo)
    agregados = agregar_a_cooperacion_directo(habitantes)
    
    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN FINAL")
    print("="*80)
    print(f"✅ Nombres leídos del archivo: {len(nombres)}")
    print(f"✅ Habitantes creados en BD: {len(habitantes)}")
    print(f"✅ Agregados a cooperación: {agregados}")
    print(f"⏰ Fin: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
