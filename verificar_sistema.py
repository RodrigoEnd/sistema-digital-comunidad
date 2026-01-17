"""
Script de prueba final - Verifica que TODO funciona correctamente
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.core.base_datos_sqlite import obtener_bd


def verificar_sistema():
    """Verifica el estado del sistema"""
    
    print("\n" + "="*80)
    print("VERIFICACIÓN DEL SISTEMA - 17/01/2026")
    print("="*80 + "\n")
    
    bd = obtener_bd()
    cursor = bd.conexion.cursor()
    
    # 1. Verificar habitantes
    cursor.execute('SELECT COUNT(*) as total FROM habitantes')
    total_habitantes = cursor.fetchone()[0]
    
    cursor.execute('SELECT MAX(CAST(SUBSTR(folio, 5) AS INTEGER)) FROM habitantes WHERE folio LIKE "FOL-%"')
    max_folio_result = cursor.fetchone()
    max_folio = max_folio_result[0] if max_folio_result and max_folio_result[0] else 0
    
    print(f"📊 CENSO:")
    print(f"   Total habitantes: {total_habitantes}")
    print(f"   Folio máximo: FOL-{max_folio:04d}")
    print(f"   Últimos 5 habitantes:")
    
    cursor.execute('SELECT nombre, folio FROM habitantes ORDER BY folio DESC LIMIT 5')
    for nombre, folio in cursor.fetchall():
        print(f"     - {nombre} ({folio})")
    
    # 2. Verificar cooperaciones
    cursor.execute('SELECT id, nombre, activa FROM cooperaciones ORDER BY activa DESC')
    coops = cursor.fetchall()
    
    print(f"\n📋 COOPERACIONES:")
    for coop_id, nombre, activa in coops:
        estado = "✓ ACTIVA" if activa else "⊘ Inactiva"
        print(f"   [{coop_id}] {nombre} {estado}")
    
    # 3. Verificar personas en cooperaciones
    cursor.execute('''
        SELECT c.nombre, COUNT(pc.id) as total
        FROM cooperaciones c
        LEFT JOIN personas_cooperacion pc ON c.id = pc.cooperacion_id
        GROUP BY c.id
        ORDER BY c.nombre
    ''')
    
    print(f"\n👥 PERSONAS POR COOPERACIÓN:")
    for coop, total in cursor.fetchall():
        print(f"   {coop}: {total} personas")
    
    # 4. Verificar persona especial
    cursor.execute('SELECT folio, nombre, nota FROM habitantes WHERE nombre LIKE "%Miguel%" ORDER BY folio DESC LIMIT 2')
    
    print(f"\n🔍 PERSONAS CON NOMBRE 'MIGUEL':")
    for folio, nombre, nota in cursor.fetchall():
        print(f"   {folio} | {nombre}")
        if nota:
            print(f"      Nota: {nota}")
    
    # 5. Verificar totales
    cursor.execute('SELECT COUNT(*) as total FROM personas_cooperacion')
    total_personas_coop = cursor.fetchone()[0]
    
    print(f"\n📈 TOTALES:")
    print(f"   Total habitantes en BD: {total_habitantes}")
    print(f"   Total personas en cooperaciones: {total_personas_coop}")
    print(f"   Cobertura: {(total_personas_coop/total_habitantes*100):.1f}%" if total_habitantes > 0 else "   Cobertura: N/A")
    
    print("\n" + "="*80)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("="*80 + "\n")


if __name__ == "__main__":
    verificar_sistema()
