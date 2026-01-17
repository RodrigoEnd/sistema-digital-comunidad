"""
Script complejo para cargar la lista de habitantes consolidada en el sistema
Carga nombres del archivo lista_habitantes_consolidada.txt en:
1. Base de datos de habitantes (censo)
2. Cooperación activa (Control de Pagos)
"""
import sys
import os
import re
from datetime import datetime

# Configurar path
sys.path.insert(0, os.path.dirname(__file__))

from src.core.base_datos_sqlite import obtener_bd
from src.core.gestor_datos_global import obtener_gestor
from src.core.logger import registrar_operacion, registrar_error


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
            
            # Remover el número de la lista (ej: "1. Virginia De la Cruz Guzman" -> "Virginia De la Cruz Guzman")
            match = re.match(r'^\d+\.\s*\*?\s*(.+)$', linea)
            if match:
                nombre = match.group(1).strip()
                
                # Validar nombre (no muy corto, no números puros)
                if nombre and len(nombre) > 3 and not nombre.isdigit():
                    nombres.append(nombre)
                    print(f"  ✓ {nombre}")
        
        print(f"\n[CARGA] Total de nombres leídos: {len(nombres)}")
        return nombres
    
    except Exception as e:
        print(f"[ERROR] No se pudo leer el archivo: {e}")
        return []


def cargar_habitantes_en_bd(nombres):
    """Carga los habitantes en la base de datos SQLite"""
    print("\n" + "="*80)
    print("FASE 1: Cargando habitantes en la base de datos")
    print("="*80)
    
    bd = obtener_bd()
    gestor = obtener_gestor()
    
    if not bd or not gestor:
        print("[ERROR] No se pudo obtener gestor o BD")
        return []
    
    habitantes_creados = []
    duplicados = 0
    errores = 0
    
    for idx, nombre in enumerate(nombres, 1):
        try:
            # Verificar si ya existe
            existente = gestor.obtener_habitante_por_nombre(nombre)
            if existente:
                print(f"  [{idx:3d}] ⚠ DUPLICADO: {nombre}")
                duplicados += 1
                habitantes_creados.append(existente)
                continue
            
            # Crear habitante
            habitante, msg = gestor.agregar_habitante(nombre)
            
            if habitante:
                habitantes_creados.append(habitante)
                folio = habitante.get('folio', 'SIN-FOLIO')
                print(f"  [{idx:3d}] ✓ CREADO: {nombre} (Folio: {folio})")
            else:
                print(f"  [{idx:3d}] ✗ ERROR: {nombre} - {msg}")
                errores += 1
        
        except Exception as e:
            print(f"  [{idx:3d}] ✗ EXCEPCIÓN: {nombre} - {str(e)}")
            errores += 1
    
    print(f"\n[RESUMEN FASE 1]")
    print(f"  Creados: {len(habitantes_creados) - duplicados}")
    print(f"  Duplicados: {duplicados}")
    print(f"  Errores: {errores}")
    print(f"  Total procesados: {len(nombres)}")
    
    return habitantes_creados


def agregar_a_cooperacion(habitantes, coop_id=None, monto_cooperacion=300.0):
    """Agrega los habitantes a la cooperación activa"""
    print("\n" + "="*80)
    print("FASE 2: Agregando habitantes a la cooperación")
    print("="*80)
    
    bd = obtener_bd()
    
    if not bd:
        print("[ERROR] No se pudo obtener BD")
        return 0
    
    # Obtener cooperación activa si no se especifica ID
    if not coop_id:
        cursor = bd.conexion.cursor()
        cursor.execute('SELECT id, nombre FROM cooperaciones WHERE activa = 1 LIMIT 1')
        resultado = cursor.fetchone()
        if resultado:
            coop_id = resultado[0]
            coop_nombre = resultado[1]
        else:
            print("[ERROR] No hay cooperación activa")
            return 0
    else:
        cursor = bd.conexion.cursor()
        cursor.execute('SELECT nombre FROM cooperaciones WHERE id = ? LIMIT 1', (coop_id,))
        resultado = cursor.fetchone()
        coop_nombre = resultado[0] if resultado else "Desconocida"
    
    print(f"\n📋 Cooperación destino: {coop_nombre} (ID: {coop_id})")
    print(f"💰 Monto por persona: ${monto_cooperacion:.2f}")
    print(f"👥 Total de habitantes a agregar: {len(habitantes)}\n")
    
    agregados = 0
    duplicados_coop = 0
    errores = 0
    
    for idx, habitante in enumerate(habitantes, 1):
        try:
            habitante_id = habitante.get('id')
            nombre = habitante.get('nombre')
            folio = habitante.get('folio')
            
            # Verificar si ya está en esta cooperación
            cursor = bd.conexion.cursor()
            cursor.execute('''
                SELECT id FROM personas_cooperacion 
                WHERE cooperacion_id = ? AND habitante_id = ?
            ''', (coop_id, habitante_id))
            
            if cursor.fetchone():
                print(f"  [{idx:3d}] ⚠ EN COOP: {nombre}")
                duplicados_coop += 1
                continue
            
            # Agregar a cooperación
            persona_coop_id = bd.agregar_persona_coop_bd(
                coop_id,
                habitante_id,
                monto_cooperacion,
                notas=f"Cargado desde lista consolidada el {datetime.now().strftime('%d/%m/%Y')}"
            )
            
            if persona_coop_id:
                agregados += 1
                print(f"  [{idx:3d}] ✓ AGREGADO: {nombre} (Folio: {folio})")
            else:
                print(f"  [{idx:3d}] ✗ ERROR: No se pudo agregar {nombre}")
                errores += 1
        
        except Exception as e:
            print(f"  [{idx:3d}] ✗ EXCEPCIÓN: {str(e)}")
            errores += 1
    
    print(f"\n[RESUMEN FASE 2]")
    print(f"  Agregados a cooperación: {agregados}")
    print(f"  Ya estaban en cooperación: {duplicados_coop}")
    print(f"  Errores: {errores}")
    
    return agregados


def registrar_carga_en_log(nombres_count, agregados):
    """Registra la operación de carga en el log"""
    try:
        registrar_operacion(
            'CARGA_MASIVA',
            'Carga masiva de habitantes desde lista consolidada',
            {
                'archivo': 'datos/lista_habitantes_consolidada.txt',
                'total_nombres_leidos': nombres_count,
                'habitantes_agregados_coop': agregados,
                'fecha_carga': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            },
            'sistema'
        )
    except Exception as e:
        print(f"[ADVERTENCIA] No se pudo registrar en log: {e}")


def main():
    print("\n" + "="*80)
    print("CARGA MASIVA DE HABITANTES - Sistema Digital Comunidad")
    print("="*80 + "\n")
    
    # Ruta del archivo
    archivo = os.path.join(os.path.dirname(__file__), 
                          'datos', 'lista_habitantes_consolidada.txt')
    
    print(f"📂 Archivo: {archivo}")
    print(f"⏰ Inicio: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    # Verificar que el archivo existe
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
    
    # FASE 1: Cargar en BD
    habitantes = cargar_habitantes_en_bd(nombres)
    
    if not habitantes:
        print("[ERROR] No se cargaron habitantes en BD")
        return
    
    # FASE 2: Agregar a cooperación
    agregados = agregar_a_cooperacion(habitantes)
    
    # FASE 3: Registrar en log
    registrar_carga_en_log(len(nombres), agregados)
    
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
