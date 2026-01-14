#!/usr/bin/env python3
"""
Script de inicialización de Base de Datos SQLite
Crea una base de datos nueva limpia con solo el usuario admin
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

def inicializar_bd_sqlite():
    """Inicializar base de datos SQLite limpia"""
    from src.config import RUTA_SEGURA
    from src.core.base_datos_sqlite import BaseDatosSQLite
    
    # Ruta de la BD
    ruta_db = os.path.join(RUTA_SEGURA, 'sistema.db')
    
    print("=" * 60)
    print("🗄️  INICIALIZADOR DE BASE DE DATOS SQLite")
    print("=" * 60)
    
    # Crear estructura de carpetas si no existe
    try:
        Path(RUTA_SEGURA).mkdir(parents=True, exist_ok=True)
        Path(RUTA_SEGURA, 'backups').mkdir(exist_ok=True)
        Path(RUTA_SEGURA, 'logs').mkdir(exist_ok=True)
        Path(RUTA_SEGURA, 'reportes').mkdir(exist_ok=True)
        print(" Estructura de carpetas lista")
    except Exception as e:
        print(f" Error creando carpetas: {e}")
        return False
    
    # Inicializar BD
    try:
        print("\n Inicializando base de datos SQLite...")
        bd = BaseDatosSQLite()
        
        # Limpiar datos (excepto admin)
        print("   Limpiando datos previos...")
        bd.vaciar_base_datos()
        
        # Verificar que el usuario admin existe
        usuario_admin = bd.obtener_usuario('admin')
        if usuario_admin:
            print(f" Usuario admin existe")
            print(f"   Email: {usuario_admin.get('email')}")
            print(f"   Rol: {usuario_admin.get('rol')}")
        else:
            print(" Error: Usuario admin no fue creado")
            return False
        
        # Obtener estadísticas
        stats = bd.obtener_estadisticas()
        print(f"\n Estadísticas iniciales:")
        print(f"   Habitantes: {stats.get('habitantes', 0)}")
        print(f"   Usuarios: {stats.get('usuarios', 0)}")
        print(f"   Pagos registrados: {stats.get('pagos', 0)}")
        print(f"   Faenas activas: {stats.get('faenas_activas', 0)}")
        
        print("\n" + "=" * 60)
        print(" Base de datos SQLite inicializada correctamente")
        print("=" * 60)
        print("\n👤 Credenciales de acceso:")
        print("   Usuario: admin")
        print("   Contraseña: admin3112")
        print("\n Sistema listo para usar!")
        
        return True
        
    except Exception as e:
        print(f"\n Error al inicializar base de datos: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    exito = inicializar_bd_sqlite()
    sys.exit(0 if exito else 1)
