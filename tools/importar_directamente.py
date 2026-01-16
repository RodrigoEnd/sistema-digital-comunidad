"""
Importación DIRECTA de habitantes a SQLite
Sin usar el gestor, directamente a la base de datos
"""

import sqlite3
import re
from datetime import datetime
from pathlib import Path

# Ruta de la base de datos
DB_PATH = Path.home() / "AppData" / "Local" / "SistemaComunidad" / "sistema.db"


def extraer_nombres_desde_lista(ruta_archivo: str) -> list[str]:
    """Extrae solo los nombres de la lista en orden"""
    nombres = []
    
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        contenido = f.read()
    
    # Dividir por los separadores
    bloques = re.split(r'-{50,}', contenido)
    
    for bloque in bloques:
        bloque = bloque.strip()
        if not bloque or "Nombre:" not in bloque:
            continue
        
        # Extraer nombre
        nombre_match = re.search(r'Nombre:\s*(.+?)(?:\n|$)', bloque)
        if nombre_match:
            nombre = nombre_match.group(1).strip()
            nombres.append(nombre)
    
    return nombres


def limpiar_y_importar(nombres: list[str]):
    """Limpia la tabla e importa todos los nombres"""
    
    print(f"\n{'='*70}")
    print(f"IMPORTACIÓN DIRECTA A SQLite")
    print(f"Base de datos: {DB_PATH}")
    print(f"Total de nombres: {len(nombres)}")
    print(f"{'='*70}\n")
    
    # Crear directorio si no existe
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Conectar a la base de datos
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habitantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folio TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                fecha_registro TEXT NOT NULL,
                activo INTEGER DEFAULT 1,
                nota TEXT
            )
        """)
        
        # ELIMINAR TODOS LOS HABITANTES EXISTENTES
        print("🗑️  Limpiando tabla de habitantes...")
        cursor.execute("DELETE FROM habitantes")
        conn.commit()
        print(f"✅ Tabla limpia\n")
        
        # Resetear el contador de autoincrement
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='habitantes'")
        conn.commit()
        
        # Importar cada nombre
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        creados = 0
        
        print("📥 Importando habitantes...\n")
        
        for i, nombre in enumerate(nombres, 1):
            try:
                # Generar folio correlativo
                folio = f"FOL-{i:04d}"
                
                # Insertar directamente
                cursor.execute("""
                    INSERT INTO habitantes (folio, nombre, fecha_registro, activo, nota)
                    VALUES (?, ?, ?, 1, 'Importado desde lista_habitantes.txt')
                """, (folio, nombre, fecha_actual))
                
                creados += 1
                
                # Mostrar progreso cada 20 habitantes
                if i % 20 == 0 or i == len(nombres):
                    print(f"[{i}/{len(nombres)}] ✅ {folio} - {nombre}")
                
            except sqlite3.IntegrityError as e:
                print(f"[{i}/{len(nombres)}] ⚠️  Duplicado: {nombre}")
            except Exception as e:
                print(f"[{i}/{len(nombres)}] ❌ Error: {nombre} -> {str(e)}")
        
        # Guardar cambios
        conn.commit()
        
        # Verificar resultado
        cursor.execute("SELECT COUNT(*) as total FROM habitantes")
        total_final = cursor.fetchone()['total']
        
        print(f"\n{'='*70}")
        print(f"RESUMEN")
        print(f"{'='*70}")
        print(f"✅ Creados:        {creados}")
        print(f"📊 Total en BD:    {total_final}")
        print(f"{'='*70}\n")
        
        # Mostrar primeros y últimos
        cursor.execute("SELECT folio, nombre FROM habitantes ORDER BY id LIMIT 3")
        print("📋 Primeros habitantes:")
        for row in cursor.fetchall():
            print(f"  • {row['folio']} - {row['nombre']}")
        
        cursor.execute("SELECT folio, nombre FROM habitantes ORDER BY id DESC LIMIT 3")
        print("\n📋 Últimos habitantes:")
        for row in cursor.fetchall():
            print(f"  • {row['folio']} - {row['nombre']}")
        
        print(f"\n✅ Importación completada exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error fatal: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("❌ Error: Proporciona la ruta del archivo")
        print(f"Uso: python {sys.argv[0]} ruta/lista_habitantes.txt")
        sys.exit(1)
    
    ruta_archivo = sys.argv[1]
    
    print(f"📄 Leyendo archivo: {ruta_archivo}")
    nombres = extraer_nombres_desde_lista(ruta_archivo)
    
    if not nombres:
        print("❌ No se encontraron nombres en el archivo")
        sys.exit(1)
    
    print(f"✅ Se encontraron {len(nombres)} nombres")
    print(f"  Primero: {nombres[0]}")
    print(f"  Último: {nombres[-1]}")
    
    respuesta = input("\n¿Continuar? Esto ELIMINARÁ todos los habitantes actuales (s/n): ").strip().lower()
    if respuesta != 's':
        print("❌ Cancelado")
        sys.exit(0)
    
    limpiar_y_importar(nombres)


if __name__ == "__main__":
    main()
