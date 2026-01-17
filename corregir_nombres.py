"""
Corregir: Eliminar Miguel (incorrecto) y agregar Daniel (correcto)
"""
import sqlite3
from pathlib import Path

db_path = Path.home() / 'AppData' / 'Local' / 'SistemaComunidad' / 'sistema.db'
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("="*80)
print("CORREGIR: Remover Miguel, agregar Daniel")
print("="*80 + "\n")

# Verificar si existe Miguel
cursor.execute('SELECT id, folio, nombre FROM habitantes WHERE nombre LIKE "%Miguel%" ORDER BY id DESC LIMIT 1')
miguel = cursor.fetchone()

if miguel:
    print(f"Encontrado: {miguel[2]} (Folio: {miguel[1]})")
    # Eliminar de cooperaciones
    cursor.execute('DELETE FROM personas_cooperacion WHERE habitante_id = ?', (miguel[0],))
    # Eliminar de habitantes
    cursor.execute('DELETE FROM habitantes WHERE id = ?', (miguel[0],))
    conn.commit()
    print("✅ Eliminado\n")

# Ahora agregar Daniel
cursor.execute('SELECT MAX(CAST(SUBSTR(folio, 5) AS INTEGER)) FROM habitantes WHERE folio LIKE "FOL-%"')
max_num_result = cursor.fetchone()
max_num = max_num_result[0] if max_num_result and max_num_result[0] else 0
folio = f"FOL-{max_num + 1:04d}"

nombre = "* Daniel Sanchez Mendoza"
nota = "Rectificar persona - Diferente del registro anterior"

# Insertar Daniel en habitantes
cursor.execute('''
    INSERT INTO habitantes (folio, nombre, nota, fecha_registro)
    VALUES (?, ?, ?, datetime('now'))
''', (folio, nombre, nota))

conn.commit()
habitante_id = cursor.lastrowid

print(f"Agregado Daniel Sanchez Mendoza")
print(f"  ID: {habitante_id}")
print(f"  Folio: {folio}")
print(f"  Nombre: {nombre}\n")

# Agregar a cooperación activa
cursor.execute('''
    SELECT id, nombre, monto_cooperacion 
    FROM cooperaciones 
    WHERE activa = 1 
    LIMIT 1
''')
coop = cursor.fetchone()

if coop:
    coop_id, coop_nombre, monto = coop
    cursor.execute('''
        INSERT INTO personas_cooperacion 
        (cooperacion_id, habitante_id, monto_esperado, estado, fecha_agregado)
        VALUES (?, ?, ?, 'pendiente', datetime('now'))
    ''', (coop_id, habitante_id, monto))
    conn.commit()
    print(f"✅ Agregado a cooperación: {coop_nombre}")

print("\n" + "="*80)

conn.close()
