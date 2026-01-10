"""
Estilos Globales Centralizados
Gestión única de temas, colores y fuentes para toda la aplicación.
Elimina duplicación de código y facilita mantenimiento.
"""

from tkinter import font as tk_font

# ═══════════════════════════════════════════════════════════════════════════════
# TEMA ÚNICO - ESTILO CLARO MODERNO
# ═══════════════════════════════════════════════════════════════════════════════

TEMA_GLOBAL = {
    # Fondos
    'bg_principal': '#f5f7fa',          # Gris muy claro (fondo principal)
    'bg_secundario': '#ffffff',         # Blanco para cards/paneles
    'bg_tertiary': '#e8ecf1',           # Gris claro para alternancia
    
    # Textos
    'fg_principal': '#1e293b',          # Negro azulado (texto principal)
    'fg_secundario': '#475569',         # Gris oscuro (texto secundario)
    'fg_terciario': '#94a3b8',          # Gris medio (placeholders)
    
    # Acentos
    'accent_primary': '#3b82f6',        # Azul moderno principal
    'accent_secondary': '#2563eb',      # Azul oscuro (hover)
    'accent_light': '#dbeafe',          # Azul muy claro (backgrounds)
    'accent_gradient_start': '#3b82f6',
    'accent_gradient_end': '#8b5cf6',
    
    # Estados
    'success': '#10b981',               # Verde esmeralda
    'success_light': '#d1fae5',
    'warning': '#f59e0b',               # Naranja ámbar
    'warning_light': '#fef3c7',
    'error': '#ef4444',                 # Rojo coral
    'error_light': '#fee2e2',
    'info': '#06b6d4',                  # Cian turquesa
    'info_light': '#cffafe',
    
    # Componentes
    'border': '#e2e8f0',
    'border_focus': '#3b82f6',
    'button_hover': '#eff6ff',
    'input_focus': '#3b82f6',
    'input_bg': '#ffffff',
    'shadow_color': '#d0d0d0',
    
    # Cards
    'card_bg': '#ffffff',
    'card_border': '#e2e8f0',
    'card_shadow': '#c0c0c0',
    
    # Tabla
    'table_header': '#f8fafc',
    'table_header_text': '#0f172a',
    'table_row_even': '#ffffff',
    'table_row_odd': '#f8fafc',
    'table_hover': '#f1f5f9',
    'table_selected': '#dbeafe',
    'table_border': '#e2e8f0',
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUENTES GLOBALES
# ═══════════════════════════════════════════════════════════════════════════════

FUENTES = {
    'titulo_grande': ('Segoe UI', 24, 'bold'),
    'titulo': ('Segoe UI', 18, 'bold'),
    'subtitulo': ('Segoe UI', 14, 'bold'),
    'normal': ('Segoe UI', 11),
    'pequeño': ('Segoe UI', 10),
    'monoespaciado': ('Consolas', 10),
    'botones': ('Segoe UI Semibold', 11),
    'badge': ('Segoe UI', 9, 'bold'),
}

FUENTES_DISPLAY = {
    'hero': ('Segoe UI', 32, 'bold'),
    'stats': ('Segoe UI', 28, 'bold'),
}

# ═══════════════════════════════════════════════════════════════════════════════
# ESPACIADO Y DISEÑO
# ═══════════════════════════════════════════════════════════════════════════════

ESPACIADO = {
    'xs': 4,
    'sm': 8,
    'md': 12,
    'lg': 16,
    'xl': 20,
    'xxl': 28,
    'xxxl': 36,
}

RADIOS_BORDE = {
    'sm': 4,
    'md': 6,
    'lg': 8,
    'xl': 12,
}

SOMBRAS = {
    'sm': {'offset': 1, 'blur': 2},
    'md': {'offset': 2, 'blur': 4},
    'lg': {'offset': 4, 'blur': 8},
    'xl': {'offset': 6, 'blur': 12},
}

TRANSICIONES = {
    'rapida': 150,
    'normal': 250,
    'lenta': 350,
}

# ═══════════════════════════════════════════════════════════════════════════════
# ICONOS
# ═══════════════════════════════════════════════════════════════════════════════

ICONOS = {
    'casa': '🏘️',
    'usuario': '👤',
    'luna': '🌙',
    'sol': '☀️',
    'dinero': '💰',
    'trabajo': '🛠️',
    'historial': '📋',
    'buscar': '🔍',
    'guardar': '💾',
    'eliminar': '🗑️',
    'editar': '✏️',
    'descargar': '⬇️',
    'subir': '⬆️',
    'mas': '➕',
    'menos': '➖',
    'ok': '✓',
    'error': '✕',
    'advertencia': '⚠️',
    'info': 'ℹ️',
    'cerrar': '✕',
    'atras': '←',
    'adelante': '→',
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES UTILIDAD
# ═══════════════════════════════════════════════════════════════════════════════

def obtener_color_estado(estado):
    """
    Retorna el color para un estado específico.
    
    Args:
        estado: 'pagado', 'parcial', 'pendiente', 'info'
    
    Returns:
        Color hexadecimal
    """
    mapa = {
        'pagado': TEMA_GLOBAL['success'],
        'parcial': TEMA_GLOBAL['warning'],
        'pendiente': TEMA_GLOBAL['error'],
        'info': TEMA_GLOBAL['info'],
    }
    return mapa.get(estado, TEMA_GLOBAL['fg_principal'])

def interpolar_color(color1, color2, factor):
    """
    Interpola entre dos colores hexadecimales.
    
    Args:
        color1: Color inicial (hexadecimal)
        color2: Color final (hexadecimal)
        factor: 0.0 (color1) a 1.0 (color2)
    
    Returns:
        Color interpolado (hexadecimal)
    """
    c1 = color1.lstrip('#')
    c2 = color2.lstrip('#')
    
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    
    return f'#{r:02x}{g:02x}{b:02x}'

def aclarar_color(color, factor=0.2):
    """
    Aclara un color interpolando hacia blanco.
    
    Args:
        color: Color hexadecimal
        factor: Intensidad del aclaramiento (0.0-1.0)
    
    Returns:
        Color aclarado
    """
    return interpolar_color(color, '#ffffff', factor)

def oscurecer_color(color, factor=0.2):
    """
    Oscurece un color interpolando hacia negro.
    
    Args:
        color: Color hexadecimal
        factor: Intensidad del oscurecimiento (0.0-1.0)
    
    Returns:
        Color oscurecido
    """
    return interpolar_color(color, '#000000', factor)

# ═══════════════════════════════════════════════════════════════════════════════
# ALIAS PARA COMPATIBILIDAD
# ═══════════════════════════════════════════════════════════════════════════════

# Mantener compatibilidad con código antiguo que usa TEMA_CLARO
TEMA_CLARO = TEMA_GLOBAL
TEMA_OSCURO = TEMA_GLOBAL  # Mismo tema (no hay modo oscuro)
