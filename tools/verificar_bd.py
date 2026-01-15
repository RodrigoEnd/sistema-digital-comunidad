"""Verificar estado de la BD"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.core.base_datos_sqlite import BaseDatosSQLite

bd = BaseDatosSQLite()
cursor = bd.conexion.cursor()

cursor.execute('SELECT COUNT(*) as total FROM habitantes WHERE activo = 1')
total = cursor.fetchone()['total']
print(f'Total habitantes activos: {total}')

cursor.execute('SELECT folio, nombre FROM habitantes WHERE folio = "FOL-0001"')
r = cursor.fetchone()
if r:
    print(f'Primer registro: {r["folio"]} - {r["nombre"]}')
else:
    print('FOL-0001 no encontrado')

cursor.execute('SELECT folio, nombre FROM habitantes ORDER BY CAST(SUBSTR(folio, 5) AS INTEGER) ASC LIMIT 5')
print('\nPrimeros 5 registros ordenados por folio:')
for row in cursor.fetchall():
    print(f'  {row["folio"]} - {row["nombre"]}')

bd.desconectar()
