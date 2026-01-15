"""
Script para cargar nombres de faenas_pagos.txt al censo
Genera folios automáticos y evita duplicados
"""

import sys
import os
import re
from datetime import datetime

# Agregar el directorio raíz al path
proyecto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, proyecto_raiz)

from src.core.base_datos_sqlite import BaseDatosSQLite
from src.core.logger import registrar_operacion, registrar_error


def limpiar_nombre(nombre_completo):
    """
    Limpia y normaliza el nombre completo
    
    Args:
        nombre_completo: Texto del nombre a limpiar
        
    Returns:
        str: Nombre limpio
    """
    # Remover caracteres especiales y marcadores como (?)
    nombre = re.sub(r'\s*\(\?\)\s*', '', nombre_completo)
    
    # Normalizar espacios
    nombre = ' '.join(nombre.split())
    
    # Capitalizar correctamente
    palabras = nombre.split()
    nombre_final = ' '.join([
        palabra.capitalize() if palabra.lower() not in ['de', 'la', 'del', 'los', 'las']
        else palabra.lower()
        for palabra in palabras
    ])
    
    return nombre_final


def extraer_nombres_de_archivo(archivo_path):
    """
    Extrae nombres del archivo faenas_pagos.txt
    
    Args:
        archivo_path: Ruta al archivo
        
    Returns:
        list: Lista de nombres únicos
    """
    nombres = []
    
    try:
        with open(archivo_path, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        
        # Saltar líneas de comentarios y encabezados
        for linea in lineas:
            linea = linea.strip()
            
            # Ignorar líneas vacías y comentarios
            if not linea or linea.startswith('#'):
                continue
            
            # Buscar patrón: numero. Nombre - Monto
            match = re.match(r'^\d+\.\s*(.+?)\s*-\s*\d+', linea)
            if match:
                nombre_completo = match.group(1).strip()
                nombre_limpio = limpiar_nombre(nombre_completo)
                
                if nombre_limpio and nombre_limpio not in nombres:
                    nombres.append(nombre_limpio)
        
        return nombres
        
    except Exception as e:
        print(f"❌ Error al leer archivo: {e}")
        registrar_error('cargar_faenas_a_censo', 'extraer_nombres_de_archivo', str(e))
        return []


def verificar_duplicado(bd, nombre):
    """
    Verifica si un nombre ya existe en la base de datos
    
    Args:
        bd: Instancia de BaseDatosSQLite
        nombre: Nombre a verificar
        
    Returns:
        bool: True si ya existe, False si no
    """
    resultados = bd.buscar_habitante(nombre)
    
    for resultado in resultados:
        nombre_bd = resultado.get('nombre', '').strip().lower()
        nombre_buscar = nombre.strip().lower()
        
        # Comparación exacta
        if nombre_bd == nombre_buscar:
            return True
    
    return False


def generar_siguiente_folio(bd):
    """
    Genera el siguiente folio disponible
    
    Args:
        bd: Instancia de BaseDatosSQLite
        
    Returns:
        str: Folio en formato FOL-XXXX
    """
    try:
        cursor = bd.conexion.cursor()
        
        # Obtener el folio más alto
        cursor.execute("""
            SELECT folio FROM habitantes 
            WHERE folio LIKE 'FOL-%'
            ORDER BY CAST(SUBSTR(folio, 5) AS INTEGER) DESC
            LIMIT 1
        """)
        
        resultado = cursor.fetchone()
        
        if resultado:
            ultimo_folio = resultado['folio']
            # Extraer número del folio FOL-0001 -> 1
            numero = int(ultimo_folio.split('-')[1])
            siguiente_numero = numero + 1
        else:
            siguiente_numero = 1
        
        return f"FOL-{siguiente_numero:04d}"
        
    except Exception as e:
        print(f"⚠️ Error al generar folio, usando conteo: {e}")
        # Fallback: contar todos los habitantes
        try:
            cursor = bd.conexion.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM habitantes")
            row = cursor.fetchone()
            total = row['total'] if row else 0
            return f"FOL-{total + 1:04d}"
        except:
            # Último fallback: usar timestamp
            import time
            return f"FOL-{int(time.time() % 10000):04d}"


def cargar_nombres_a_censo(archivo_path, dry_run=False):
    """
    Carga nombres del archivo al censo con folios automáticos
    
    Args:
        archivo_path: Ruta al archivo faenas_pagos.txt
        dry_run: Si es True, solo muestra qué se haría sin modificar BD
        
    Returns:
        dict: Estadísticas de la operación
    """
    print("=" * 70)
    print("🔄 CARGA DE NOMBRES DE FAENAS A CENSO")
    print("=" * 70)
    
    if dry_run:
        print("⚠️ MODO PRUEBA - No se modificará la base de datos")
        print()
    
    # Extraer nombres del archivo
    print(f"📄 Leyendo archivo: {archivo_path}")
    nombres = extraer_nombres_de_archivo(archivo_path)
    print(f"✅ Encontrados {len(nombres)} nombres únicos en el archivo")
    print()
    
    # Conectar a BD
    print("🔌 Conectando a base de datos...")
    bd = BaseDatosSQLite()
    bd.conectar()  # Asegurar que está conectado
    
    # Estadísticas
    stats = {
        'total': len(nombres),
        'agregados': 0,
        'duplicados': 0,
        'errores': 0
    }
    
    # Procesar cada nombre
    print("📝 Procesando nombres...")
    print("-" * 70)
    
    for i, nombre in enumerate(nombres, 1):
        try:
            # Verificar duplicados
            if verificar_duplicado(bd, nombre):
                print(f"⏭️  [{i:3d}/{len(nombres)}] Ya existe: {nombre}")
                stats['duplicados'] += 1
                continue
            
            if dry_run:
                print(f"🔍 [{i:3d}/{len(nombres)}] Se agregaría: {nombre}")
                stats['agregados'] += 1
            else:
                # Generar folio
                folio = generar_siguiente_folio(bd)
                
                # Crear habitante
                habitante, mensaje = bd.crear_habitante(
                    folio=folio,
                    nombre=nombre,
                    apellidos="",
                    nota=f"Importado desde faenas_pagos.txt el {datetime.now().strftime('%Y-%m-%d')}"
                )
                
                if habitante:
                    print(f"✅ [{i:3d}/{len(nombres)}] {folio} - {nombre}")
                    stats['agregados'] += 1
                    registrar_operacion('IMPORTACION_FAENAS', 
                                      f'Habitante importado desde faenas_pagos.txt',
                                      {'folio': folio, 'nombre': nombre})
                else:
                    print(f"❌ [{i:3d}/{len(nombres)}] Error: {nombre} - {mensaje}")
                    stats['errores'] += 1
                    
        except Exception as e:
            print(f"❌ [{i:3d}/{len(nombres)}] Error procesando {nombre}: {e}")
            stats['errores'] += 1
            registrar_error('cargar_faenas_a_censo', 'cargar_nombres', str(e), 
                          contexto=f"nombre={nombre}")
    
    # Resumen
    print()
    print("=" * 70)
    print("📊 RESUMEN DE IMPORTACIÓN")
    print("=" * 70)
    print(f"Total de nombres en archivo: {stats['total']}")
    print(f"✅ Agregados al censo:       {stats['agregados']}")
    print(f"⏭️  Ya existían (duplicados): {stats['duplicados']}")
    print(f"❌ Errores:                  {stats['errores']}")
    print("=" * 70)
    
    if not dry_run and stats['agregados'] > 0:
        print(f"✨ Se agregaron {stats['agregados']} habitantes al censo con folios automáticos")
    
    bd.desconectar()
    return stats


def main():
    """Función principal"""
    # Ruta al archivo
    archivo_faenas = os.path.join(proyecto_raiz, 'datos', 'faenas_pagos.txt')
    
    # Verificar que existe el archivo
    if not os.path.exists(archivo_faenas):
        print(f"❌ Error: No se encuentra el archivo {archivo_faenas}")
        return
    
    print()
    print("Este script agregará los nombres de faenas_pagos.txt al censo.")
    print("Se generarán folios automáticos para cada habitante nuevo.")
    print()
    
    # Primero hacer un dry run para mostrar qué se haría
    print("Ejecutando análisis previo...")
    print()
    cargar_nombres_a_censo(archivo_faenas, dry_run=True)
    
    print()
    respuesta = input("¿Desea proceder con la importación? (s/n): ").strip().lower()
    
    if respuesta == 's':
        print()
        print("Iniciando importación real...")
        print()
        cargar_nombres_a_censo(archivo_faenas, dry_run=False)
        print()
        print("✅ Proceso completado!")
    else:
        print()
        print("❌ Operación cancelada")


if __name__ == "__main__":
    main()
