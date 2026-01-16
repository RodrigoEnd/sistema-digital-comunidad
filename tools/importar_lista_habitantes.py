"""
Importa habitantes desde lista_habitantes.txt en el orden exacto
Solo importa nombres, sin notas, asegurando folios correctos

Uso:
    python tools/importar_lista_habitantes.py ruta/lista_habitantes.txt
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime

# Agregar directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.gestor_datos_global import obtener_gestor
from src.core.logger import registrar_operacion, registrar_error


def extraer_habitantes_desde_lista(ruta_archivo: str) -> list[dict]:
    """
    Extrae habitantes del archivo lista_habitantes.txt
    Retorna lista de diccionarios con folio y nombre en orden
    """
    habitantes = []
    
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        contenido = f.read()
    
    # Dividir por los separadores "----...----"
    bloques = re.split(r'-{50,}', contenido)
    
    for bloque in bloques:
        bloque = bloque.strip()
        if not bloque or not "Folio:" in bloque:
            continue
        
        # Extraer folio
        folio_match = re.search(r'Folio:\s*(FOL-\d+)', bloque)
        if not folio_match:
            continue
        folio = folio_match.group(1)
        
        # Extraer nombre
        nombre_match = re.search(r'Nombre:\s*(.+?)(?:\n|$)', bloque)
        if not nombre_match:
            continue
        nombre = nombre_match.group(1).strip()
        
        # Extraer estado (opcional)
        estado_match = re.search(r'Estado:\s*(ACTIVO|INACTIVO)', bloque)
        estado = estado_match.group(1) if estado_match else "ACTIVO"
        
        habitantes.append({
            'folio': folio,
            'nombre': nombre,
            'activo': estado == "ACTIVO"
        })
    
    return habitantes


def importar_habitantes_a_bd(habitantes: list[dict]) -> None:
    """
    Importa habitantes a la base de datos usando el gestor global
    """
    gestor = obtener_gestor()
    total = len(habitantes)
    
    print(f"\n{'='*60}")
    print(f"IMPORTANDO {total} HABITANTES A LA BASE DE DATOS")
    print(f"{'='*60}\n")
    
    creados = 0
    actualizados = 0
    errores = 0
    
    for i, hab in enumerate(habitantes, 1):
        try:
            folio = hab['folio']
            nombre = hab['nombre']
            activo = hab['activo']
            
            # Verificar si ya existe por folio
            existe = gestor.obtener_habitante_por_folio(folio)
            
            if existe:
                # Ya existe, solo actualizar si es necesario
                print(f"[{i}/{total}] ⚠️  Ya existe: {folio} - {nombre}")
                actualizados += 1
            else:
                # Crear nuevo habitante usando solo el nombre
                # El folio se generará automáticamente por la BD
                habitante, mensaje = gestor.agregar_habitante(nombre)
                
                if habitante:
                    print(f"[{i}/{total}] ✅ Creado: {habitante.get('folio')} - {nombre}")
                    creados += 1
                else:
                    print(f"[{i}/{total}] ❌ Error: {folio} - {nombre} -> {mensaje}")
                    errores += 1
                    
        except Exception as e:
            print(f"[{i}/{total}] ❌ Excepción: {hab['folio']} - {hab['nombre']} -> {str(e)}")
            registrar_error("importar_lista_habitantes", "importar_habitantes_a_bd", str(e))
            errores += 1
    
    print(f"\n{'='*60}")
    print(f"RESUMEN DE IMPORTACIÓN")
    print(f"{'='*60}")
    print(f"✅ Creados:      {creados}")
    print(f"⚠️  Ya existían:  {actualizados}")
    print(f"❌ Errores:      {errores}")
    print(f"📊 Total:        {total}")
    print(f"{'='*60}\n")
    
    registrar_operacion(
        "IMPORTACION_MASIVA",
        f"Importados {creados} habitantes desde lista_habitantes.txt"
    )


def main():
    if len(sys.argv) < 2:
        print("❌ Error: Debes proporcionar la ruta del archivo")
        print(f"Uso: python {sys.argv[0]} ruta/lista_habitantes.txt")
        sys.exit(1)
    
    ruta_archivo = sys.argv[1]
    
    if not os.path.exists(ruta_archivo):
        print(f"❌ Error: El archivo '{ruta_archivo}' no existe")
        sys.exit(1)
    
    try:
        # Extraer habitantes del archivo
        habitantes = extraer_habitantes_desde_lista(ruta_archivo)
        
        if not habitantes:
            print("❌ No se encontraron habitantes en el archivo")
            sys.exit(1)
        
        print(f"\n✅ Se encontraron {len(habitantes)} habitantes en el archivo")
        print(f"📄 Primer habitante: {habitantes[0]['folio']} - {habitantes[0]['nombre']}")
        print(f"📄 Último habitante: {habitantes[-1]['folio']} - {habitantes[-1]['nombre']}")
        
        # Confirmar antes de proceder
        respuesta = input("\n¿Deseas continuar con la importación? (s/n): ").strip().lower()
        if respuesta != 's':
            print("❌ Importación cancelada")
            sys.exit(0)
        
        # Importar a la base de datos
        importar_habitantes_a_bd(habitantes)
        
        print("\n✅ Proceso completado exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error fatal: {str(e)}")
        registrar_error("importar_lista_habitantes", "main", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
