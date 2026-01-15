"""Limpiar registros de prueba"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.core.base_datos_sqlite import BaseDatosSQLite

bd = BaseDatosSQLite()
cursor = bd.conexion.cursor()

print("Buscando registros de prueba...")
cursor.execute("""
    SELECT folio, nombre FROM habitantes 
    WHERE folio NOT LIKE 'FOL-0%' AND folio LIKE 'FOL-%'
    ORDER BY folio
""")

registros = cursor.fetchall()
if registros:
    print(f"\nEncontrados {len(registros)} registros de prueba:")
    for r in registros:
        print(f"  {r['folio']} - {r['nombre']}")
    
    print("\n¿Eliminar estos registros? (s/n): ", end='')
    respuesta = input().strip().lower()
    
    if respuesta == 's':
        cursor.execute("""
            DELETE FROM habitantes 
            WHERE folio NOT LIKE 'FOL-0%' AND folio LIKE 'FOL-%'
        """)
        bd.conexion.commit()
        print(f"✅ {len(registros)} registros eliminados")
        
        # Verificar
        cursor.execute('SELECT COUNT(*) as total FROM habitantes WHERE activo = 1')
        total = cursor.fetchone()['total']
        print(f"Total habitantes activos restantes: {total}")
    else:
        print("Operación cancelada")
else:
    print("No se encontraron registros de prueba")

bd.desconectar()
