"""
Script para resetear todos los datos del sistema a estado inicial
Deja el proyecto virgen con solo 10 habitantes y sin historiales
"""

import os
import json
from pathlib import Path
from datetime import datetime

def reset_datos():
    """Reset completo de datos"""
    
    # Ruta segura de AppData
    appdata = os.getenv('LOCALAPPDATA')
    ruta_segura = os.path.join(appdata, 'SistemaComunidad')
    
    print(f"\n{'='*60}")
    print("RESET DE DATOS DEL SISTEMA")
    print(f"{'='*60}")
    print(f"Ruta de datos: {ruta_segura}\n")
    
    if not os.path.exists(ruta_segura):
        print("✓ No hay datos anteriores que limpiar")
    else:
        # Eliminar archivos de datos
        archivos_eliminar = [
            'datos_pagos.json',
            'datos_faenas.json',
            'base_datos_habitantes.json',
            'config_usuario.json'
        ]
        
        for archivo in archivos_eliminar:
            ruta_archivo = os.path.join(ruta_segura, archivo)
            if os.path.exists(ruta_archivo):
                try:
                    os.remove(ruta_archivo)
                    print(f"✓ Eliminado: {archivo}")
                except Exception as e:
                    print(f"✗ Error al eliminar {archivo}: {e}")
        
        # Eliminar historiales
        historial_dir = os.path.join(ruta_segura, 'historiales')
        if os.path.exists(historial_dir):
            try:
                import shutil
                shutil.rmtree(historial_dir)
                print(f"✓ Eliminada carpeta: historiales/")
            except Exception as e:
                print(f"✗ Error al eliminar historiales: {e}")
        
        # Eliminar backups
        backups_dir = os.path.join(ruta_segura, 'backups')
        if os.path.exists(backups_dir):
            try:
                import shutil
                shutil.rmtree(backups_dir)
                print(f"✓ Eliminada carpeta: backups/")
            except Exception as e:
                print(f"✗ Error al eliminar backups: {e}")
    
    print(f"\n{'='*60}")
    print("Datos reset completados exitosamente ✓")
    print("El próximo inicio tendrá los datos frescos")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    reset_datos()
