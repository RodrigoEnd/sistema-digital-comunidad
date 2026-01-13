"""
Configuracion centralizada del sistema
Contiene todas las constantes y configuraciones globales
Usa variables de entorno para valores sensibles (.env)
"""

import os

# Intentar cargar dotenv, si no está disponible usar valores por defecto
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv no instalado, usar valores hardcoded
    pass

# API
API_URL = os.getenv("API_URL", "http://127.0.0.1:5000/api")
API_PORT = int(os.getenv("API_PORT", "5000"))
API_HOST = os.getenv("API_HOST", "127.0.0.1")

# Modo offline: si es True no se requiere la API para operar
MODO_OFFLINE = os.getenv("MODO_OFFLINE", "False").lower() == "true"

# ============================================================================
# DOCUMENTACION DE ENDPOINTS DE API LOCAL
# ============================================================================
# Todos los endpoints estan disponibles en http://127.0.0.1:5000/api
# 
# HABITANTES:
#   GET    /habitantes              - Obtener todos los habitantes
#   GET    /habitantes/buscar?q=xxx - Buscar habitantes por criterio
#   GET    /habitantes/nombre/<nom> - Obtener habitante por nombre exacto
#   POST   /habitantes              - Agregar nuevo habitante
#   PATCH  /habitantes/<folio>      - Actualizar habitante
#
# FOLIOS:
#   GET    /folio/siguiente         - Obtener siguiente folio disponible
#
# SINCRONIZACION:
#   POST   /sync/verificar          - Verificar/crear habitante si no existe
#
# SALUD:
#   GET    /ping                    - Verificar que API esta funcionando
#
# NOTAS:
#   - Todos los metodos retornan JSON
#   - Campo 'success' indica exito/error
#   - Errores retornan codigo HTTP apropiado (400, 404, 500)
# ============================================================================

# Tabla de endpoints para referencia rapida
API_ENDPOINTS = {
    'habitantes': {
        'listar': 'GET /api/habitantes',
        'buscar': 'GET /api/habitantes/buscar',
        'por_nombre': 'GET /api/habitantes/nombre/<nombre>',
        'crear': 'POST /api/habitantes',
        'actualizar': 'PATCH /api/habitantes/<folio>',
    },
    'folio': {
        'siguiente': 'GET /api/folio/siguiente',
    },
    'sincronizacion': {
        'verificar': 'POST /api/sync/verificar',
    },
    'salud': {
        'ping': 'GET /api/ping',
    }
}

# Seguridad
PASSWORD_CIFRADO = os.getenv("PASSWORD_CIFRADO", "SistemaComunidad2026")
SALT_CIFRADO = os.getenv("SALT_CIFRADO", "SistemaComunidad2026Salt").encode()
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

# Base de datos
ARCHIVO_HABITANTES = os.getenv("ARCHIVO_HABITANTES", "base_datos_habitantes.json")
ARCHIVO_PAGOS = os.getenv("ARCHIVO_PAGOS", "datos_pagos.json")
ARCHIVO_FAENAS = os.getenv("ARCHIVO_FAENAS", "datos_faenas.json")
ARCHIVO_CONFIG = os.getenv("ARCHIVO_CONFIG", "config_usuario.json")

# Sistema de archivos
def obtener_ruta_segura():
    """Obtiene la ruta segura en AppData del usuario"""
    appdata = os.getenv('LOCALAPPDATA')
    return os.path.join(appdata, 'SistemaComunidad')

RUTA_SEGURA = obtener_ruta_segura()

# Interfaz
VENTANA_MODO = os.getenv("VENTANA_MODO", "zoomed")  # 'zoomed' para pantalla completa en Windows

# Temas
TEMAS = {
    'claro': {
        'bg': '#ffffff',
        'fg': '#1a1a1a',
        'frame_bg': '#f8f9fa',
        'button_bg': '#e9ecef',
        'entrada_bg': '#ffffff',
        'titulo_fg': '#0066cc',
        'exito_fg': '#28a745',
        'alerta_fg': '#ffc107',
        'error_fg': '#dc3545',
        'tablas_even': '#ffffff',
        'tablas_odd': '#f8f9fa',
        'border': '#dee2e6',
    },
    'oscuro': {
        'bg': '#1a1a1a',
        'fg': '#e9ecef',
        'frame_bg': '#2d2d2d',
        'button_bg': '#3d3d3d',
        'entrada_bg': '#2d2d2d',
        'titulo_fg': '#4da6ff',
        'exito_fg': '#51cf66',
        'alerta_fg': '#ffd93d',
        'error_fg': '#ff6b6b',
        'tablas_even': '#1a1a1a',
        'tablas_odd': '#2d2d2d',
        'border': '#495057',
    }
}

TEMA_DEFECTO = 'claro'

# Tamaños de letra
TAMAÑOS_LETRA = {
    'pequeño': {'titulo': 10, 'normal': 8, 'grande': 9},
    'normal': {'titulo': 14, 'normal': 10, 'grande': 12},
    'grande': {'titulo': 18, 'normal': 12, 'grande': 16}
}

TAMAÑO_DEFECTO = 'normal'

# Logging
CARPETA_LOGS = os.path.join(RUTA_SEGURA, 'logs')
ARCHIVO_LOG = os.path.join(CARPETA_LOGS, 'sistema.log')
FORMATO_LOG = '[%(asctime)s] %(levelname)s: %(message)s'
FORMATO_FECHA_LOG = '%d/%m/%Y %H:%M:%S'
LIMITE_LOG_MB = 5
CANTIDAD_BACKUPS_LOG = 5

# Respaldos
CARPETA_BACKUPS = os.path.join(RUTA_SEGURA, 'backups')
INTERVALO_BACKUP_HORAS = 24

# Validacion
LONGITUD_MINIMA_NOMBRE = 3
LONGITUD_MAXIMA_NOMBRE = 100
MONTO_MINIMO = 0.01
MONTO_MAXIMO = 1000000

# Exportacion
CARPETA_REPORTES = os.path.join(RUTA_SEGURA, 'reportes')
FORMATO_FECHA_EXPORT = '%d/%m/%Y'

# Sistema de cooperaciones
MONTO_COOPERACION_DEFECTO = 100.0
PROYECTO_DEFECTO = "Proyecto Comunitario 2026"

# Sistema de faenas
DIAS_LIMITE_EDICION_FAENA = 7  # Días máximos para editar una faena después de su fecha
PESO_FAENA_MINIMO = 1
PESO_FAENA_MAXIMO = 10
PESO_FAENA_DEFECTO = 5
PESO_SUSTITUCION_HABITANTE = 0.9  # 90% para quien contrata a un habitante
PESO_SUSTITUCION_EXTERNO = 1.0  # 100% para quien contrata a externo
PESO_TRABAJADOR_CONTRATADO = 1.0  # 100% para el habitante que fue contratado

# Formato de hora por defecto para faenas
HORA_INICIO_DEFECTO = '9'
HORA_INICIO_AMPM_DEFECTO = 'AM'
HORA_FIN_DEFECTO = '1'
HORA_FIN_AMPM_DEFECTO = 'PM'

# Censo - Constantes de interfaz
CENSO_DEBOUNCE_MS = 180
CENSO_NOTA_MAX_DISPLAY = 30
CENSO_NOMBRES_SIMILARES_MIN_PALABRAS = 2
CENSO_NOMBRES_SIMILARES_MAX_RESULTADOS = 5

# Censo - Columnas del TreeView
CENSO_COLUMNAS = ['folio', 'nombre', 'fecha_registro', 'activo', 'nota']
CENSO_COLUMNAS_ANCHOS = {
    'folio': 80,
    'nombre': 280,
    'fecha_registro': 120,
    'activo': 100,
    'nota': 200
}
