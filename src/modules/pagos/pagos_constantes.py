"""
Constantes y configuración centralizada para el módulo de pagos
Organiza todos los valores de configuración reutilizables
"""

import tkinter as tk
from src.config import (
    TEMAS,
    TAMAÑOS_LETRA,
    PASSWORD_CIFRADO,
    ARCHIVO_PAGOS,
    UI_DEBOUNCE_SEARCH,
    UI_DEBOUNCE_SAVE,
    FORMATO_FECHA_EXPORT,
    FORMATO_FECHA_LOG,
    MONTO_MINIMO,
    LONGITUD_MAXIMA_NOMBRE,
    MONTO_COOPERACION_DEFECTO,
    PROYECTO_DEFECTO,
)
from src.ui.tema_moderno import FUENTES, FUENTES_DISPLAY, ESPACIADO, ICONOS

CONFIG_DATOS = {
    'archivo_pagos': ARCHIVO_PAGOS,
    'password_archivo': PASSWORD_CIFRADO,
}

# ===== CONFIGURACIÓN INICIAL =====
CONFIG_INICIAL = {
    'monto_cooperacion_default': MONTO_COOPERACION_DEFECTO,
    'proyecto_default': PROYECTO_DEFECTO,
    'tamaño_letra_default': 'normal',
    'titulo_ventana_principal': 'Sistema de Control de Pagos - Proyectos Comunitarios',
}

# ===== CONFIGURACIÓN DE UI =====
CONFIG_UI = {
    'temas': TEMAS,
    'tamaños': TAMAÑOS_LETRA,
    'fuentes': FUENTES,
    'fuentes_display': FUENTES_DISPLAY,
    'espaciado': ESPACIADO,
    'iconos': ICONOS,
}

# ===== CONFIGURACIÓN DE COLUMNAS TABLA =====
COLUMNAS_TABLA = {
    'folio': {'width': 95, 'anchor': tk.CENTER, 'text': 'Folio'},
    'nombre': {'width': 260, 'anchor': tk.W, 'text': 'Nombre Completo'},
    'monto_esperado': {'width': 120, 'anchor': tk.CENTER, 'text': 'Monto Esperado'},
    'pagado': {'width': 110, 'anchor': tk.CENTER, 'text': 'Pagado'},
    'pendiente': {'width': 110, 'anchor': tk.CENTER, 'text': 'Pendiente'},
    'estado': {'width': 110, 'anchor': tk.CENTER, 'text': 'Estado'},
    'ultimo_pago': {'width': 170, 'anchor': tk.CENTER, 'text': 'Ultimo Pago'},
    'notas': {'width': 240, 'anchor': tk.W, 'text': 'Notas'},
}

# ===== ESTADOS Y ESTILOS DE FILAS =====
ESTILOS_ESTADOS = {
    'pagado': {
        'background': '#E8F5E9',
        'foreground': '#1B5E20',
        'estado': 'estado_pagado'
    },
    'parcial': {
        'background': '#FFF9E6',
        'foreground': '#F57C00',
        'estado': 'estado_parcial'
    },
    'pendiente': {
        'background': '#FFEBEE',
        'foreground': '#C62828',
        'estado': 'estado_pendiente'
    },
    'excedente': {
        'background': '#E3F2FD',
        'foreground': '#0D47A1',
        'estado': 'estado_excedente'
    },
    'inactivo': {
        'background': '#F5F5F5',
        'foreground': '#757575',
        'estado': 'estado_inactivo'
    }
}

# ===== FILTROS RÁPIDOS =====
FILTROS_RAPIDOS = [
    ('Todos', 'todos'),
    ('Al corriente', 'pagado'),
    ('Atrasados', 'atrasado'),
    ('Sin pagar', 'sin_pagar'),
    ('Inactivos', 'inactivo')
]

# ===== ATAJOS DE TECLADO =====
ATAJOS_TECLADO = {
    '<Control-f>': 'busqueda',
    '<Control-p>': 'pago',
    '<Control-e>': 'editar',
    '<Control-h>': 'historial',
    '<Control-s>': 'guardar',
    '<F5>': 'actualizar',
    '<Delete>': 'eliminar',
    '<Escape>': 'limpiar_busqueda',
    '<Control-1>': 'cooperacion_1',
    '<Control-2>': 'cooperacion_2',
    '<Control-3>': 'cooperacion_3',
}

# ===== PERMISOS POR ACCIÓN =====
PERMISOS_ACCIONES = {
    'crear': 'crear',
    'editar': 'editar',
    'pagar': 'pagar',
    'eliminar': 'editar',
    'exportar': 'exportar',
    'crear_coop': 'crear',
}

# ===== TIMERS Y DEBOUNCES (ms) =====
TIMERS = {
    'debounce_guardado': UI_DEBOUNCE_SAVE,
    'debounce_busqueda': UI_DEBOUNCE_SEARCH,
    'timeout_api': 5000,
    'watchdog_api_intervalo': 30000,  # 30 segundos
    'pulso_animacion': 100,
}

# ===== PATRONES Y FORMATOS =====
PATRONES = {
    'folio_local_prefix': 'LOC',
    'folio_format': 'LOC-{counter}',
    'id_cooperacion_general': 'general',
    'fecha_formato': FORMATO_FECHA_EXPORT,
    'datetime_formato': FORMATO_FECHA_LOG,
}

# ===== MENSAJES ESTÁNDAR =====
MENSAJES = {
    'sin_seleccion': 'Debe seleccionar una persona primero',
    'sin_cooperacion': 'No hay cooperación activa seleccionada',
    'sin_datos': 'No hay datos para mostrar',
    'permiso_denegado': 'Tu rol no permite realizar esta acción ({})',
    'contrasena_requerida': 'Ingrese la contraseña para modificar el monto',
    'contrasena_incorrecta': 'Contraseña incorrecta',
    'error_guardado': 'Error al guardar los datos',
    'exito_guardado': 'Datos guardados correctamente',
    'error_exportar': 'Error al exportar: {}',
    'exito_backup': 'Backup creado correctamente:\n{}',
}

# ===== MÁXIMOS Y MÍNIMOS =====
LIMITES = {
    'max_resultados_busqueda': 5,
    'max_backups_mantener': 10,
    'min_monto_pago': MONTO_MINIMO,
    'max_longitud_nombre': LONGITUD_MAXIMA_NOMBRE,
    'max_longitud_notas': 500,
}

# ===== PALETA DE COLORES GENERAL =====
COLORES_ANIMACION = {
    'completado': '#4CAF50',
    'warning': '#FFC107',
    'error': '#F44336',
    'info': '#2196F3',
}
