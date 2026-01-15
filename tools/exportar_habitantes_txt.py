"""
Script para exportar la lista de habitantes desde la base de datos SQLite a un archivo TXT
"""

import sqlite3
import os
from datetime import datetime

def exportar_habitantes_a_txt():
    """Exporta todos los habitantes de la BD a un archivo TXT"""
    
    # Ruta de la base de datos
    db_path = os.path.join(os.getenv('LOCALAPPDATA'), 'SistemaComunidad', 'sistema.db')
    
    if not os.path.exists(db_path):
        print(f"Error: No se encontró la base de datos en {db_path}")
        return False
    
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Obtener todos los habitantes
        cursor.execute("""
            SELECT folio, nombre, fecha_registro, activo, nota 
            FROM habitantes 
            ORDER BY folio
        """)
        
        habitantes = cursor.fetchall()
        
        # Ruta del archivo de salida
        output_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'datos',
            'lista_habitantes.txt'
        )
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Escribir a archivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write("LISTA DE HABITANTES - SISTEMA DIGITAL COMUNIDAD\n")
            f.write(f"Exportado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Total de habitantes: {len(habitantes)}\n")
            f.write("=" * 100 + "\n\n")
            
            activos = sum(1 for h in habitantes if h[3])
            inactivos = len(habitantes) - activos
            
            f.write(f"Activos: {activos} | Inactivos: {inactivos}\n")
            f.write("-" * 100 + "\n\n")
            
            for folio, nombre, fecha_registro, activo, nota in habitantes:
                estado = "ACTIVO" if activo else "INACTIVO"
                f.write(f"Folio: {folio}\n")
                f.write(f"Nombre: {nombre}\n")
                f.write(f"Fecha Registro: {fecha_registro}\n")
                f.write(f"Estado: {estado}\n")
                if nota:
                    f.write(f"Nota: {nota}\n")
                f.write("-" * 100 + "\n")
        
        print(f"✓ Exportación exitosa!")
        print(f"  Archivo: {output_path}")
        print(f"  Total habitantes: {len(habitantes)}")
        print(f"  Activos: {activos} | Inactivos: {inactivos}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"Error de base de datos: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    exportar_habitantes_a_txt()
