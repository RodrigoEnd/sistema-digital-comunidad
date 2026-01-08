"""
Configuracion centralizada del sistema
Contiene todas las constantes y configuraciones globales
"""

import os

# API
API_URL = "http://127.0.0.1:5000/api"
API_PORT = 5000
API_HOST = "127.0.0.1"

# Modo offline: si es True no se requiere la API para operar
MODO_OFFLINE = False

# Seguridad
PASSWORD_CIFRADO = "SistemaComunidad2026"
SALT_CIFRADO = b'SistemaComunidad2026Salt'
BCRYPT_ROUNDS = 12

# Base de datos
ARCHIVO_HABITANTES = "base_datos_habitantes.json"
ARCHIVO_PAGOS = "datos_pagos.json"
ARCHIVO_CONFIG = "config_usuario.json"

# Interfaz
VENTANA_MODO = 'zoomed'  # 'zoomed' para pantalla completa en Windows

# Temas
TEMAS = {
    'claro': {
        'bg': '#f0f0f0',
        'fg': '#000000',
        'frame_bg': '#ffffff',
        'button_bg': '#e0e0e0',
        'entrada_bg': '#ffffff',
        'titulo_fg': '#1a1a1a',
        'exito_fg': '#2e7d32',
        'alerta_fg': '#f57f17',
        'error_fg': '#c62828',
        'tablas_even': '#f5f5f5',
        'tablas_odd': '#ffffff'
    },
    'oscuro': {
        'bg': '#1e1e1e',
        'fg': '#e0e0e0',
        'frame_bg': '#2d2d2d',
        'button_bg': '#404040',
        'entrada_bg': '#3a3a3a',
        'titulo_fg': '#f0f0f0',
        'exito_fg': '#66bb6a',
        'alerta_fg': '#ffa726',
        'error_fg': '#ef5350',
        'tablas_even': '#252525',
        'tablas_odd': '#2d2d2d'
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

# Sistema de archivos
def obtener_ruta_segura():
    """Obtiene la ruta segura en AppData del usuario"""
    appdata = os.getenv('LOCALAPPDATA')
    return os.path.join(appdata, 'SistemaComunidad')

RUTA_SEGURA = obtener_ruta_segura()

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
