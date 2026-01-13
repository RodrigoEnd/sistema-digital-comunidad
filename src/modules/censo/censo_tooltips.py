"""
Tooltips e interacciones del módulo de censo
"""

import tkinter as tk
from src.config import CENSO_NOTA_MAX_DISPLAY


def configurar_tooltips(tree, habitantes, root):
    """
    Configura los tooltips para notas y otros elementos
    
    Args:
        tree: TreeView
        habitantes: Lista de habitantes
        root: Ventana raíz
    
    Returns:
        Diccionario con referencias a tooltips
    """
    tooltip_window = None
    
    def on_hover_nota(event):
        """Muestra tooltip con nota completa cuando se pasa el mouse sobre una nota truncada"""
        nonlocal tooltip_window
        
        # Identificar celda bajo el mouse
        item_id = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        
        # Solo mostrar tooltip para la columna de notas (#5)
        if column != '#5':
            ocultar_tooltip()
            return
        
        if not item_id:
            ocultar_tooltip()
            return
        
        # Obtener valores de la fila
        valores = tree.item(item_id, 'values')
        if len(valores) < 5:
            return
        
        folio = valores[0]
        
        # Buscar nota completa del habitante
        habitante = next((h for h in habitantes if h['folio'] == folio), None)
        if not habitante:
            return
        
        nota_completa = habitante.get('nota', '')
        
        # Solo mostrar tooltip si la nota está truncada
        if len(nota_completa) <= CENSO_NOTA_MAX_DISPLAY:
            ocultar_tooltip()
            return
        
        # Crear tooltip si no existe o si cambió
        if tooltip_window:
            tooltip_window.destroy()
        
        # Crear ventana de tooltip
        tooltip_window = tk.Toplevel(root)
        tooltip_window.wm_overrideredirect(True)
        tooltip_window.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
        
        label = tk.Label(tooltip_window, text=nota_completa, 
                        background="#ffffcc", relief=tk.SOLID, borderwidth=1,
                        font=('Arial', 9), justify=tk.LEFT, padx=5, pady=3,
                        wraplength=300)
        label.pack()
    
    def ocultar_tooltip():
        """Oculta el tooltip de nota"""
        nonlocal tooltip_window
        if tooltip_window:
            tooltip_window.destroy()
            tooltip_window = None
    
    # Configurar eventos
    tree.bind('<Motion>', on_hover_nota)
    tree.bind('<Leave>', lambda e: ocultar_tooltip())
    
    return {
        'tooltip_window': tooltip_window,
        'on_hover_nota': on_hover_nota,
        'ocultar_tooltip': ocultar_tooltip
    }


def mostrar_tooltip_indicador(root, texto, x, y):
    """
    Muestra un tooltip genérico en una posición específica
    
    Args:
        root: Ventana raíz
        texto: Texto a mostrar
        x, y: Coordenadas
    
    Returns:
        Widget del tooltip
    """
    tooltip_label = tk.Label(root, text=texto, bg='#333', fg='#fff', font=('Arial', 9),
                             padx=8, pady=4, relief=tk.FLAT, borderwidth=1)
    tooltip_label.place(x=x, y=y)
    return tooltip_label


def ocultar_tooltip_indicador(tooltip_label):
    """Oculta un tooltip de indicador"""
    if tooltip_label:
        tooltip_label.destroy()
