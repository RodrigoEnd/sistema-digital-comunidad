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
    'bg_principal': '#ffffff',          # Blanco puro para fondo principal
    'bg_secundario': '#f8f9fa',         # Gris ultra claro para paneles
    'bg_tertiary': '#e9ecef',           # Gris claro para elementos alternos
    
    # Textos
    'fg_principal': '#1a1a1a',          # Negro muy oscuro (legible)
    'fg_secundario': '#495057',         # Gris oscuro para texto secundario
    'fg_terciario': '#868e96',          # Gris medio para placeholders
    
    # Acentos
    'accent_primary': '#0066cc',        # Azul moderno (botones, links)
    'accent_secondary': '#0052a3',      # Azul oscuro (hover)
    'accent_light': '#cce5ff',          # Azul muy claro (backgrounds)
    
    # Estados
    'success': '#28a745',               # Verde para éxito
    'warning': '#ffc107',               # Amarillo/naranja para advertencias
    'error': '#dc3545',                 # Rojo para errores
    'info': '#17a2b8',                  # Cian para información
    
    # Componentes específicos
    'border': '#dee2e6',                # Gris claro para bordes
    'button_hover': '#f1f3f5',          # Gris muy claro para hover en botones
    'input_focus': '#0066cc',           # Azul para focus en inputs
    'input_bg': '#ffffff',              # Blanco para campos de entrada
    
    # Tabla
    'table_header': '#f8f9fa',          # Encabezado de tabla
    'table_row_even': '#ffffff',        # Filas pares
    'table_row_odd': '#f8f9fa',         # Filas impares
    'table_hover': '#e9ecef',           # Hover en fila
    'table_selected': '#cce5ff',        # Fila seleccionada
}

TEMA_OSCURO = {
    # Fondos
    'bg_principal': '#1a1a1a',          # Casi negro para fondo principal
    'bg_secundario': '#2d2d2d',         # Gris oscuro para paneles
    'bg_tertiary': '#3d3d3d',           # Gris más claro para alternancia
    
    # Textos
    'fg_principal': '#e9ecef',          # Gris claro (legible en oscuro)
    'fg_secundario': '#adb5bd',         # Gris medio para texto secundario
    'fg_terciario': '#868e96',          # Gris oscuro para placeholders
    
    # Acentos
    'accent_primary': '#4da6ff',        # Azul claro para oscuro (botones)
    'accent_secondary': '#66b3ff',      # Azul más claro (hover)
    'accent_light': '#1a4d99',          # Azul oscuro (backgrounds)
    
    # Estados
    'success': '#51cf66',               # Verde claro para éxito
    'warning': '#ffd93d',               # Amarillo claro para advertencias
    'error': '#ff6b6b',                 # Rojo claro para errores
    'info': '#4ecdc4',                  # Cian claro para información
    
    # Componentes específicos
    'border': '#495057',                # Gris para bordes
    'button_hover': '#3d3d3d',          # Gris un poco más claro para hover
    'input_focus': '#4da6ff',           # Azul claro para focus
    'input_bg': '#2d2d2d',              # Gris oscuro para campos
    
    # Tabla
    'table_header': '#2d2d2d',          # Encabezado de tabla
    'table_row_even': '#1a1a1a',        # Filas pares
    'table_row_odd': '#2d2d2d',         # Filas impares
    'table_hover': '#3d3d3d',           # Hover en fila
    'table_selected': '#1a4d99',        # Fila seleccionada
}

# ═══════════════════════════════════════════════════════════════════════════════
# DEFINICIONES DE FUENTES
# ═══════════════════════════════════════════════════════════════════════════════

FUENTES = {
    'titulo_grande': ('Segoe UI', 20, 'bold'),      # Para títulos principales
    'titulo': ('Segoe UI', 16, 'bold'),             # Para títulos secundarios
    'subtitulo': ('Segoe UI', 13, 'bold'),          # Para subtítulos
    'normal': ('Segoe UI', 11),                     # Texto normal
    'pequeño': ('Segoe UI', 9),                     # Texto pequeño
    'monoespaciado': ('Courier New', 10),           # Para folios, IDs
    'botones': ('Segoe UI', 10, 'bold'),            # Para botones
}

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES DE ESPACIADO Y TAMAÑOS
# ═══════════════════════════════════════════════════════════════════════════════

ESPACIADO = {
    'xs': 4,
    'sm': 8,
    'md': 12,
    'lg': 16,
    'xl': 24,
    'xxl': 32,
}

RADIOS_BORDE = {
    'sm': 2,
    'md': 4,
    'lg': 6,
    'xl': 8,
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
    'pagado': '✓',
    'parcial': '◐',
    'pendiente': '✕',
    'usuario': '👤',
    'engranaje': '⚙',
    'buscar': '🔍',
    'guardar': '💾',
    'eliminar': '🗑',
    'editar': '✎',
    'cerrar': '✖',
    'descargar': '⬇',
    'cargar': '⬆',
    'luna': '🌙',
    'sol': '☀',
}
