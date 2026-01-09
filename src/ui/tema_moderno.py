"""
Módulo de temas modernos para Sistema Digital Comunidad
Define paletas, estilos y utilidades para una interfaz contemporánea
"""

from tkinter import font as tk_font

# ═══════════════════════════════════════════════════════════════════════════════
# PALETAS DE COLOR MODERNAS
# ═══════════════════════════════════════════════════════════════════════════════

TEMA_CLARO = {
    # Fondos
    'bg_principal': '#f5f7fa',          # Gris muy claro (más suave que blanco puro)
    'bg_secundario': '#ffffff',         # Blanco para cards/paneles (elevados)
    'bg_tertiary': '#e8ecf1',           # Gris claro para elementos alternos
    
    # Textos
    'fg_principal': '#1e293b',          # Negro azulado (más profesional)
    'fg_secundario': '#475569',         # Gris oscuro para texto secundario
    'fg_terciario': '#94a3b8',          # Gris medio para placeholders
    
    # Acentos - Paleta más moderna
    'accent_primary': '#3b82f6',        # Azul moderno vibrante
    'accent_secondary': '#2563eb',      # Azul oscuro (hover)
    'accent_light': '#dbeafe',          # Azul muy claro (backgrounds)
    'accent_gradient_start': '#3b82f6', # Inicio gradiente
    'accent_gradient_end': '#8b5cf6',   # Fin gradiente (púrpura)
    
    # Estados - Colores más vibrantes
    'success': '#10b981',               # Verde esmeralda moderno
    'success_light': '#d1fae5',         # Verde claro
    'warning': '#f59e0b',               # Naranja ámbar
    'warning_light': '#fef3c7',         # Amarillo claro
    'error': '#ef4444',                 # Rojo coral moderno
    'error_light': '#fee2e2',           # Rojo claro
    'info': '#06b6d4',                  # Cian turquesa
    'info_light': '#cffafe',            # Cian claro
    
    # Componentes específicos
    'border': '#e2e8f0',                # Gris azulado para bordes
    'border_focus': '#3b82f6',          # Azul para bordes con focus
    'button_hover': '#eff6ff',          # Azul ultra claro para hover
    'input_focus': '#3b82f6',           # Azul para focus en inputs
    'input_bg': '#ffffff',              # Blanco para campos de entrada
    'shadow_color': '#d0d0d0',          # Sombra suave (gris claro)
    
    # Cards y elevación
    'card_bg': '#ffffff',               # Fondo de cards
    'card_border': '#e2e8f0',           # Borde de cards
    'card_shadow': '#c0c0c0',           # Sombra de cards (gris)
    
    # Tabla mejorada
    'table_header': '#f8fafc',          # Encabezado gris azulado claro
    'table_header_text': '#0f172a',     # Texto header oscuro
    'table_row_even': '#ffffff',        # Filas pares
    'table_row_odd': '#f8fafc',         # Filas impares gris muy claro
    'table_hover': '#f1f5f9',           # Hover en fila
    'table_selected': '#dbeafe',        # Fila seleccionada azul claro
    'table_border': '#e2e8f0',          # Bordes de tabla
}

TEMA_OSCURO = {
    # Fondos - Paleta oscura moderna
    'bg_principal': '#0f172a',          # Azul oscuro profundo (slate)
    'bg_secundario': '#1e293b',         # Azul oscuro medio para cards
    'bg_tertiary': '#334155',           # Gris azulado para alternancia
    
    # Textos - Mayor contraste
    'fg_principal': '#f1f5f9',          # Gris claro azulado (alto contraste)
    'fg_secundario': '#cbd5e1',         # Gris medio claro
    'fg_terciario': '#64748b',          # Gris medio para placeholders
    
    # Acentos - Más vibrantes en oscuro
    'accent_primary': '#60a5fa',        # Azul cielo brillante
    'accent_secondary': '#93c5fd',      # Azul claro (hover)
    'accent_light': '#1e3a8a',          # Azul oscuro (backgrounds)
    'accent_gradient_start': '#60a5fa', # Inicio gradiente
    'accent_gradient_end': '#a78bfa',   # Fin gradiente (púrpura)
    
    # Estados - Colores neón suaves
    'success': '#34d399',               # Verde esmeralda brillante
    'success_light': '#064e3b',         # Verde oscuro
    'warning': '#fbbf24',               # Ámbar dorado
    'warning_light': '#78350f',         # Naranja oscuro
    'error': '#f87171',                 # Rojo coral brillante
    'error_light': '#7f1d1d',           # Rojo oscuro
    'info': '#22d3ee',                  # Cian brillante
    'info_light': '#164e63',            # Cian oscuro
    
    # Componentes específicos
    'border': '#334155',                # Gris azulado para bordes
    'border_focus': '#60a5fa',          # Azul brillante para focus
    'button_hover': '#1e293b',          # Azul oscuro para hover
    'input_focus': '#60a5fa',           # Azul brillante para focus
    'input_bg': '#1e293b',              # Azul oscuro para campos
    'shadow_color': '#000000',          # Sombra más pronunciada (negro)
    
    # Cards y elevación
    'card_bg': '#1e293b',               # Fondo de cards
    'card_border': '#334155',           # Borde de cards
    'card_shadow': '#000000',           # Sombra de cards más visible
    
    # Tabla mejorada
    'table_header': '#1e293b',          # Encabezado azul oscuro
    'table_header_text': '#f1f5f9',     # Texto header claro
    'table_row_even': '#0f172a',        # Filas pares
    'table_row_odd': '#1e293b',         # Filas impares
    'table_hover': '#334155',           # Hover más visible
    'table_selected': '#1e3a8a',        # Fila seleccionada azul oscuro
    'table_border': '#334155',          # Bordes de tabla
}

# ═══════════════════════════════════════════════════════════════════════════════
# DEFINICIONES DE FUENTES
# ═══════════════════════════════════════════════════════════════════════════════

FUENTES = {
    'titulo_grande': ('Segoe UI', 24, 'bold'),      # Para títulos principales (más grande)
    'titulo': ('Segoe UI', 18, 'bold'),             # Para títulos secundarios
    'subtitulo': ('Segoe UI', 14, 'bold'),          # Para subtítulos
    'normal': ('Segoe UI', 11),                     # Texto normal
    'pequeño': ('Segoe UI', 10),                    # Texto pequeño
    'monoespaciado': ('Consolas', 10),              # Para folios, IDs (Consolas más moderna)
    'botones': ('Segoe UI Semibold', 11),           # Para botones (semibold)
    'badge': ('Segoe UI', 9, 'bold'),               # Para badges/etiquetas
}

# Fuentes alternativas para efectos especiales
FUENTES_DISPLAY = {
    'hero': ('Segoe UI', 32, 'bold'),               # Para números grandes
    'stats': ('Segoe UI', 28, 'bold'),              # Para estadísticas
}

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES DE ESPACIADO Y TAMAÑOS
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

# Sombras simuladas (combinación de frames con degradado de opacidad)
SOMBRAS = {
    'sm': {'offset': 1, 'blur': 2},     # Sombra pequeña
    'md': {'offset': 2, 'blur': 4},     # Sombra media
    'lg': {'offset': 4, 'blur': 8},     # Sombra grande
    'xl': {'offset': 6, 'blur': 12},    # Sombra extra grande
}

# Transiciones (duraciones en ms)
TRANSICIONES = {
    'rapida': 150,
    'normal': 250,
    'lenta': 350,
}

# ═══════════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ═══════════════════════════════════════════════════════════════════════════════

def obtener_tema(modo):
    """Retorna la paleta de colores según el modo (claro/oscuro)"""
    return TEMA_CLARO if modo == 'claro' else TEMA_OSCURO

def obtener_color_estado(estado, modo='claro'):
    """Retorna el color para un estado específico"""
    tema = obtener_tema(modo)
    mapa = {
        'pagado': tema['success'],
        'parcial': tema['warning'],
        'pendiente': tema['error'],
        'info': tema['info'],
    }
    return mapa.get(estado, tema['fg_principal'])

def interpolar_color(color1, color2, factor):
    """
    Interpola entre dos colores hexadecimales.
    factor: 0.0 (color1) a 1.0 (color2)
    """
    c1 = color1.lstrip('#')
    c2 = color2.lstrip('#')
    
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    
    return f'#{r:02x}{g:02x}{b:02x}'

def oscurecer_color(color_hex, factor=0.15):
    """Oscurece un color hex en el factor dado (0.0 a 1.0)"""
    color_hex = color_hex.lstrip('#')
    r, g, b = int(color_hex[0:2], 16), int(color_hex[2:4], 16), int(color_hex[4:6], 16)
    r = max(0, int(r * (1 - factor)))
    g = max(0, int(g * (1 - factor)))
    b = max(0, int(b * (1 - factor)))
    return f'#{r:02x}{g:02x}{b:02x}'

def aclarar_color(color_hex, factor=0.15):
    """Aclara un color hex en el factor dado (0.0 a 1.0)"""
    color_hex = color_hex.lstrip('#')
    r, g, b = int(color_hex[0:2], 16), int(color_hex[2:4], 16), int(color_hex[4:6], 16)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f'#{r:02x}{g:02x}{b:02x}'

def hex_a_rgb(color_hex):
    """Convierte color hex a tupla RGB"""
    color_hex = color_hex.lstrip('#')
    return tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))

def rgb_a_hex(rgb):
    """Convierte tupla RGB a hex"""
    return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

def crear_estilos_ttk(estilo, tema_dict):
    """Configura estilos ttk con colores del tema"""
    # Configurar Button
    estilo.configure('TButton',
                     font=FUENTES['botones'],
                     borderwidth=1,
                     relief='solid',
                     padding=6)
    estilo.map('TButton',
               background=[('active', tema_dict['button_hover'])],
               foreground=[('active', tema_dict['fg_principal'])])
    
    # Configurar Label
    estilo.configure('TLabel',
                     background=tema_dict['bg_principal'],
                     foreground=tema_dict['fg_principal'],
                     font=FUENTES['normal'])
    
    # Configurar Entry (si existe)
    estilo.configure('TEntry',
                     fieldbackground=tema_dict['input_bg'],
                     borderwidth=1)
    
    # Configurar Frame
    estilo.configure('TFrame',
                     background=tema_dict['bg_principal'])
    
    # Configurar Treeview
    estilo.configure('Treeview',
                     background=tema_dict['table_row_even'],
                     foreground=tema_dict['fg_principal'],
                     fieldbackground=tema_dict['table_row_even'],
                     borderwidth=0)
    estilo.map('Treeview',
               background=[('selected', tema_dict['table_selected'])],
               foreground=[('selected', tema_dict['fg_principal'])])
    
    # Encabezados de Treeview
    estilo.configure('Treeview.Heading',
                     background=tema_dict['table_header'],
                     foreground=tema_dict['fg_principal'],
                     borderwidth=1,
                     relief='solid',
                     padding=6)
    estilo.map('Treeview.Heading',
               background=[('active', tema_dict['button_hover'])])

# ═══════════════════════════════════════════════════════════════════════════════
# ICONOS/SÍMBOLOS
# ═══════════════════════════════════════════════════════════════════════════════

ICONOS = {
    # Estados
    'pagado': '✓',
    'parcial': '◐',
    'pendiente': '✕',
    
    # Usuarios y acciones
    'usuario': '👤',
    'usuarios': '👥',
    'admin': '👑',
    'perfil': '🎭',
    
    # Navegación y acciones
    'buscar': '🔍',
    'filtrar': '⚗️',
    'guardar': '💾',
    'exportar': '📤',
    'importar': '📥',
    'descargar': '⬇️',
    'cargar': '⬆️',
    'sincronizar': '🔄',
    
    # Edición
    'editar': '✏️',
    'eliminar': '🗑️',
    'agregar': '➕',
    'duplicar': '📋',
    
    # UI
    'engranaje': '⚙️',
    'ajustes': '🔧',
    'luna': '🌙',
    'sol': '☀️',
    'cerrar': '✖',
    'menu': '☰',
    'expandir': '⊕',
    'contraer': '⊖',
    
    # Estado y notificaciones
    'info': 'ℹ️',
    'alerta': '⚠️',
    'error': '❌',
    'exito': '✅',
    'campana': '🔔',
    
    # Datos y reportes
    'estadisticas': '📊',
    'grafica': '📈',
    'reporte': '📄',
    'calendario': '📅',
    'reloj': '🕐',
    'dinero': '💰',
    'moneda': '💵',
    
    # Comunidad
    'casa': '🏘️',
    'edificio': '🏢',
    'herramientas': '🔨',
    'proyecto': '🏗️',
}
