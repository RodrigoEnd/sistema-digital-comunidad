"""
Script directo para importar nombres de faenas_pagos.txt al censo
Versión simplificada y robusta
"""

import sys
import os
import re

# Configurar path
proyecto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, proyecto_raiz)

from src.core.base_datos_sqlite import BaseDatosSQLite
from datetime import datetime


def extraer_nombres_unicos(archivo_path):
    """Extrae nombres únicos del archivo"""
    nombres = []
    
    with open(archivo_path, 'r', encoding='utf-8') as f:
        for linea in f:
            linea = linea.strip()
            
            # Ignorar comentarios y líneas vacías
            if not linea or linea.startswith('#'):
                continue
            
            # Patrón: numero. Nombre - Monto
            match = re.match(r'^\d+\.\s*(.+?)\s*-\s*\d+', linea)
            if match:
                nombre = match.group(1).strip()
                # Limpiar marcadores como (?)
                nombre = re.sub(r'\s*\(\?\)\s*', '', nombre)
                nombre = ' '.join(nombre.split())
                
                # Capitalizar correctamente
                palabras = nombre.split()
                nombre_final = ' '.join([
                    p.capitalize() if p.lower() not in ['de', 'la', 'del', 'los', 'las']
                    else p.lower()
                    for p in palabras
                ])
                
                if nombre_final and nombre_final not in nombres:
                    nombres.append(nombre_final)
    
    return nombres


def main():
    print("=" * 80)
    print("IMPORTACIÓN DE NOMBRES DE FAENAS AL CENSO")
    print("=" * 80)
    print()
    
    # Archivo de origen
    archivo = os.path.join(proyecto_raiz, 'datos', 'faenas_pagos.txt')
    
    # Extraer nombres
    print(f"📄 Leyendo: {archivo}")
    nombres = extraer_nombres_unicos(archivo)
    print(f"✅ Encontrados {len(nombres)} nombres únicos")
    print()
    
    # Conectar a BD
    print("🔌 Conectando a base de datos...")
    bd = BaseDatosSQLite()
    cursor = bd.conexion.cursor()
    print()
    
    # Estadísticas
    agregados = 0
    duplicados = 0
    errores = 0
    
    print("📝 Procesando nombres...")
    print("-" * 80)
    
    for i, nombre in enumerate(nombres, 1):
        try:
            # Verificar si ya existe
            cursor.execute("""
                SELECT folio, nombre FROM habitantes 
                WHERE LOWER(nombre) = LOWER(?)
                LIMIT 1
            """, (nombre,))
            
            existe = cursor.fetchone()
            
            if existe:
                print(f"⏭️  [{i:3d}/{len(nombres)}] Ya existe: {nombre}")
                duplicados += 1
                continue
            
            # Obtener siguiente folio
            cursor.execute("SELECT COUNT(*) as total FROM habitantes")
            total = cursor.fetchone()['total']
            folio = f"FOL-{total + 1:04d}"
            
            # Insertar habitante
            cursor.execute("""
                INSERT INTO habitantes 
                (folio, nombre, apellidos, activo, fecha_registro, nota)
                VALUES (?, ?, '', 1, ?, ?)
            """, (
                folio,
                nombre,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                f"Importado desde faenas_pagos.txt"
            ))
            
            bd.conexion.commit()
            
            print(f"✅ [{i:3d}/{len(nombres)}] {folio} - {nombre}")
            agregados += 1
            
        except Exception as e:
            print(f"❌ [{i:3d}/{len(nombres)}] Error en {nombre}: {e}")
            errores += 1
            bd.conexion.rollback()
    
    # Cerrar conexión
    bd.desconectar()
    
    # Resumen
    print()
    print("=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"Total en archivo:    {len(nombres)}")
    print(f"✅ Agregados:        {agregados}")
    print(f"⏭️  Ya existían:      {duplicados}")
    print(f"❌ Errores:          {errores}")
    print("=" * 80)
    
    if agregados > 0:
        print(f"\n✨ Se agregaron {agregados} habitantes al censo exitosamente!")


if __name__ == "__main__":
    main()
