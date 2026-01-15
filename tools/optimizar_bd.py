"""
Script para aplicar optimizaciones a la base de datos existente
"""

import sys
import os

proyecto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, proyecto_raiz)

from src.core.base_datos_sqlite import BaseDatosSQLite


def aplicar_optimizaciones():
    print("=" * 80)
    print("APLICANDO OPTIMIZACIONES A LA BASE DE DATOS")
    print("=" * 80)
    print()
    
    bd = BaseDatosSQLite()
    cursor = bd.conexion.cursor()
    
    print("📊 Creando índices para mejorar rendimiento...")
    
    try:
        # Índice en nombre
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_habitantes_nombre 
            ON habitantes(nombre)
        ''')
        print("✅ Índice creado: idx_habitantes_nombre")
        
        # Índice en folio
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_habitantes_folio 
            ON habitantes(folio)
        ''')
        print("✅ Índice creado: idx_habitantes_folio")
        
        # Índice en activo
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_habitantes_activo 
            ON habitantes(activo)
        ''')
        print("✅ Índice creado: idx_habitantes_activo")
        
        bd.conexion.commit()
        
        print()
        print("🔧 Optimizando base de datos...")
        cursor.execute("VACUUM")
        print("✅ Base de datos optimizada")
        
        print()
        print("📈 Analizando estadísticas...")
        cursor.execute("ANALYZE")
        print("✅ Estadísticas actualizadas")
        
        bd.conexion.commit()
        
        print()
        print("=" * 80)
        print("OPTIMIZACIONES APLICADAS EXITOSAMENTE")
        print("=" * 80)
        print()
        print("Mejoras aplicadas:")
        print("  • Índices en columnas clave para búsquedas más rápidas")
        print("  • Base de datos compactada (VACUUM)")
        print("  • Estadísticas actualizadas para mejor planificación de consultas")
        print()
        print("Resultado esperado:")
        print("  • Búsquedas hasta 10x más rápidas")
        print("  • Menor uso de memoria")
        print("  • Mejor rendimiento general del sistema")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        bd.conexion.rollback()
    
    bd.desconectar()


if __name__ == "__main__":
    aplicar_optimizaciones()
