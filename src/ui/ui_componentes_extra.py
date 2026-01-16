"""
Componentes UI extras y avanzados para el sistema
Incluye badges, cards de estadísticas, alerts y más
"""

import tkinter as tk
from tkinter import ttk
from src.ui.tema_moderno import (TEMA_CLARO, TEMA_OSCURO, FUENTES, FUENTES_DISPLAY,
                          ESPACIADO, ICONOS, oscurecer_color, aclarar_color)
from src.core.optimizador_ui import get_ui_optimizer
from src.config import UI_DEBOUNCE_SEARCH


class Badge(tk.Label):
    """Badge/etiqueta pequeña con color de estado"""
    
    def __init__(self, parent, texto, tipo='info', tema=None, **kwargs):
        self.tema = tema or TEMA_CLARO
        
        # Colores según tipo
        color_map = {
            'success': (self.tema['success_light'], self.tema['success']),
            'warning': (self.tema['warning_light'], self.tema['warning']),
            'error': (self.tema['error_light'], self.tema['error']),
            'info': (self.tema['accent_light'], self.tema['accent_primary']),
            'default': (self.tema['bg_tertiary'], self.tema['fg_secundario']),
        }
        
        bg, fg = color_map.get(tipo, color_map['default'])
        
        super().__init__(parent, text=texto, font=FUENTES['badge'],
                        bg=bg, fg=fg, padx=ESPACIADO['sm'], pady=ESPACIADO['xs'],
                        relief=tk.FLAT, **kwargs)


class CardEstadistica(tk.Frame):
    """Card para mostrar estadísticas con número grande y descripción"""
    
    def __init__(self, parent, titulo, valor, icono=None, color='primary', tema=None):
        super().__init__(parent)
        self.tema = tema or TEMA_CLARO
        
        # Colores según tipo
        color_map = {
            'primary': self.tema['accent_primary'],
            'success': self.tema['success'],
            'warning': self.tema['warning'],
            'error': self.tema['error'],
            'info': self.tema['info'],
        }
        
        accent_color = color_map.get(color, color_map['primary'])
        card_bg = self.tema.get('card_bg', self.tema['bg_secundario'])
        
        # Card principal
        self.config(bg=card_bg, relief=tk.FLAT, bd=1, 
                   highlightthickness=1, highlightbackground=self.tema.get('card_border', self.tema['border']))
        
        # Padding interno
        inner = tk.Frame(self, bg=card_bg)
        inner.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['lg'], pady=ESPACIADO['lg'])
        
        # Header con icono
        header = tk.Frame(inner, bg=card_bg)
        header.pack(fill=tk.X, pady=(0, ESPACIADO['sm']))
        
        if icono:
            tk.Label(header, text=icono, font=('Arial', 24), 
                    bg=card_bg, fg=accent_color).pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        
        tk.Label(header, text=titulo, font=FUENTES['pequeño'],
                bg=card_bg, fg=self.tema['fg_secundario']).pack(side=tk.LEFT)
        
        # Valor grande
        tk.Label(inner, text=str(valor), font=FUENTES_DISPLAY['stats'],
                bg=card_bg, fg=accent_color).pack(anchor=tk.W)


class AlertBox(tk.Frame):
    """Caja de alerta/mensaje con icono y estilo según tipo"""
    
    def __init__(self, parent, mensaje, tipo='info', tema=None, dismissible=False):
        super().__init__(parent)
        self.tema = tema or TEMA_CLARO
        self.dismissible = dismissible
        
        # Configuración según tipo
        config_map = {
            'success': (self.tema['success_light'], self.tema['success'], ICONOS['exito']),
            'warning': (self.tema['warning_light'], self.tema['warning'], ICONOS['alerta']),
            'error': (self.tema['error_light'], self.tema['error'], ICONOS['error']),
            'info': (self.tema['info_light'], self.tema['info'], ICONOS['info']),
        }
        
        bg, fg, icono = config_map.get(tipo, config_map['info'])
        
        self.config(bg=bg, relief=tk.FLAT, bd=1, highlightthickness=1, highlightbackground=fg)
        
        # Padding interno
        inner = tk.Frame(self, bg=bg)
        inner.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['md'], pady=ESPACIADO['md'])
        
        # Icono
        tk.Label(inner, text=icono, font=('Arial', 16),
                bg=bg, fg=fg).pack(side=tk.LEFT, padx=(0, ESPACIADO['md']))
        
        # Mensaje
        tk.Label(inner, text=mensaje, font=FUENTES['normal'],
                bg=bg, fg=oscurecer_color(fg, 0.3), wraplength=400, justify=tk.LEFT).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Botón cerrar si es dismissible
        if dismissible:
            close_btn = tk.Label(inner, text=ICONOS['cerrar'], font=FUENTES['pequeño'],
                               bg=bg, fg=fg, cursor='hand2')
            close_btn.pack(side=tk.RIGHT)
            close_btn.bind('<Button-1>', lambda e: self.destroy())


class SearchBox(tk.Frame):
    """Campo de búsqueda moderno con icono y optimización automática"""
    
    def __init__(self, parent, placeholder="Buscar...", tema=None, callback=None, debounce_ms=None):
        super().__init__(parent)
        self.tema = tema or TEMA_CLARO
        self.callback = callback
        self.placeholder = placeholder
        self.has_placeholder = True
        self.debounce_ms = debounce_ms or UI_DEBOUNCE_SEARCH
        self._optimizer = get_ui_optimizer()
        self._widget_id = f"search_{id(self)}"
        
        card_bg = self.tema.get('card_bg', self.tema['bg_secundario'])
        self.config(bg=card_bg, relief=tk.FLAT, bd=1,
                   highlightthickness=1, highlightbackground=self.tema['border'])
        
        # Frame interno
        inner = tk.Frame(self, bg=card_bg)
        inner.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['sm'], pady=ESPACIADO['xs'])
        
        # Icono buscar
        tk.Label(inner, text=ICONOS['buscar'], font=('Arial', 14),
                bg=card_bg, fg=self.tema['fg_terciario']).pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        
        # Entry
        self.entry = tk.Entry(inner, font=FUENTES['normal'], bg=card_bg,
                             fg=self.tema['fg_principal'], relief=tk.FLAT,
                             insertbackground=self.tema['accent_primary'], bd=0)
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Placeholder
        self._set_placeholder()
        
        # Bindings
        self.entry.bind('<FocusIn>', self._on_focus_in)
        self.entry.bind('<FocusOut>', self._on_focus_out)
        self.entry.bind('<KeyRelease>', self._on_key_release)
    
    def _set_placeholder(self):
        """Establecer placeholder"""
        self.entry.insert(0, self.placeholder)
        self.entry.config(fg=self.tema['fg_terciario'])
        self.has_placeholder = True
    
    def _remove_placeholder(self):
        """Remover placeholder"""
        if self.has_placeholder:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=self.tema['fg_principal'])
            self.has_placeholder = False
    
    def _on_focus_in(self, event):
        """Evento focus in"""
        # Si tiene placeholder, limpiarlo
        if self.has_placeholder:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=self.tema['fg_principal'])
            self.has_placeholder = False
        self.config(highlightbackground=self.tema['accent_primary'], highlightthickness=2)
    
    def _on_focus_out(self, event):
        """Evento focus out"""
        texto_actual = self.entry.get().strip()
        # Solo poner placeholder si está realmente vacío o es el placeholder mismo
        if not texto_actual or texto_actual == self.placeholder:
            self._set_placeholder()
        else:
            # Hay contenido válido, asegurar que no está marcado como placeholder
            self.has_placeholder = False
        self.config(highlightbackground=self.tema['border'], highlightthickness=1)
    
    def _on_key_release(self, event):
        """Evento tecla liberada con debouncing automático"""
        # Si hay placeholder, verificar si el usuario empezó a escribir
        texto_actual = self.entry.get()
        
        # Si el texto ya no es el placeholder, marcar que no hay placeholder
        if self.has_placeholder and texto_actual != self.placeholder:
            self.has_placeholder = False
            self.entry.config(fg=self.tema['fg_principal'])
        
        # Ejecutar callback si hay y no es placeholder
        if self.callback and not self.has_placeholder:
            # El callback debe obtener el valor por sí mismo usando self.search_box.get()
            self._optimizer.debounce_search(
                self._widget_id,
                self.debounce_ms,
                self.callback,
                None  # No pasar valor, el callback lo obtiene
            )
    
    def get(self):
        """Obtener valor real, nunca el placeholder"""
        texto = self.entry.get().strip()
        # Si el texto es el placeholder o está marcado como tal, retornar vacío
        if self.has_placeholder or texto == self.placeholder:
            return ""
        return texto
    
    def set(self, valor):
        """Establecer valor"""
        self._remove_placeholder()
        self.entry.delete(0, tk.END)
        if valor:
            self.entry.insert(0, valor)
        else:
            self._set_placeholder()
    
    def clear(self):
        """Limpiar el contenido completamente"""
        self.has_placeholder = False  # Resetear flag primero
        self.entry.delete(0, tk.END)
        self._set_placeholder()


class Separator(tk.Frame):
    """Separador visual horizontal o vertical"""
    
    def __init__(self, parent, orientation='horizontal', tema=None):
        super().__init__(parent)
        self.tema = tema or TEMA_CLARO
        
        if orientation == 'horizontal':
            self.config(bg=self.tema['border'], height=1)
        else:
            self.config(bg=self.tema['border'], width=1)


class TooltipLabel(tk.Label):
    """Label con tooltip al pasar el mouse"""
    
    def __init__(self, parent, text, tooltip_text, **kwargs):
        super().__init__(parent, text=text, **kwargs)
        self.tooltip_text = tooltip_text
        self.tooltip = None
        
        self.bind('<Enter>', self._show_tooltip)
        self.bind('<Leave>', self._hide_tooltip)
    
    def _show_tooltip(self, event):
        """Mostrar tooltip"""
        x, y, _, _ = self.bbox("insert")
        x += self.winfo_rootx() + 25
        y += self.winfo_rooty() + 20
        
        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip, text=self.tooltip_text,
                        background="#333333", foreground="#ffffff",
                        relief=tk.SOLID, borderwidth=1,
                        font=('Segoe UI', 9), padx=8, pady=4)
        label.pack()
    
    def _hide_tooltip(self, event):
        """Ocultar tooltip"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class ToggleSwitch(tk.Canvas):
    """Switch toggle moderno estilo iOS"""
    
    def __init__(self, parent, initial_state=False, callback=None, tema=None):
        self.tema = tema or TEMA_CLARO
        self.state = initial_state
        self.callback = callback
        
        # Dimensiones
        self.width = 50
        self.height = 26
        
        super().__init__(parent, width=self.width, height=self.height,
                        bg=self.tema.get('card_bg', self.tema['bg_secundario']),
                        highlightthickness=0, cursor='hand2')
        
        self.draw()
        self.bind('<Button-1>', self.toggle)
    
    def draw(self):
        """Dibujar el switch"""
        self.delete('all')
        
        # Colores según estado
        if self.state:
            track_color = self.tema['success']
            thumb_x = self.width - 15
        else:
            track_color = self.tema['bg_tertiary']
            thumb_x = 10
        
        # Track (fondo)
        self.create_oval(2, 2, self.height-2, self.height-2, fill=track_color, outline='')
        self.create_oval(self.width-self.height+2, 2, self.width-2, self.height-2, fill=track_color, outline='')
        self.create_rectangle(self.height//2, 2, self.width-self.height//2, self.height-2, fill=track_color, outline='')
        
        # Thumb (círculo)
        self.create_oval(thumb_x-8, 5, thumb_x+8, self.height-5, fill='#ffffff', outline='')
    
    def toggle(self, event=None):
        """Cambiar estado"""
        self.state = not self.state
        self.draw()
        
        if self.callback:
            self.callback(self.state)
    
    def get_state(self):
        """Obtener estado actual"""
        return self.state
    
    def set_state(self, state):
        """Establecer estado"""
        self.state = state
        self.draw()
