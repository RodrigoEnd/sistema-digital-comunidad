"""
Tooltips informativos para UI mejorada
Muestra información cuando el usuario pasa el mouse sobre elementos
"""
import tkinter as tk
from tkinter import font as tkFont
import threading
import time


class TooltipModerno:
    """Tooltip moderno que aparece con delay al pasar el mouse"""
    
    def __init__(self, widget, texto, tema_global, delay=500):
        """
        Args:
            widget: Widget sobre el cual mostrar el tooltip
            texto: Texto a mostrar en el tooltip
            tema_global: Dict con colores del tema
            delay: Delay en ms antes de mostrar (default 500ms)
        """
        self.widget = widget
        self.texto = texto
        self.tema_global = tema_global
        self.delay = delay
        self.tooltip = None
        self.timer = None
        self.tooltip_visible = False
        
        # Colores
        self.bg_tooltip = tema_global.get('bg_tertiary', '#333333')
        self.fg_tooltip = tema_global.get('fg_principal', '#ffffff')
        
        # Bindings
        self.widget.bind('<Enter>', self._on_enter, add=True)
        self.widget.bind('<Leave>', self._on_leave, add=True)
    
    def _on_enter(self, event=None):
        """Cuando mouse entra al widget"""
        if not self.timer:
            self.timer = self.widget.after(self.delay, self._mostrar_tooltip)
    
    def _on_leave(self, event=None):
        """Cuando mouse sale del widget"""
        if self.timer:
            self.widget.after_cancel(self.timer)
            self.timer = None
        self._ocultar_tooltip()
    
    def _mostrar_tooltip(self):
        """Mostrar el tooltip"""
        if self.tooltip_visible:
            return
        
        try:
            # Crear ventana tooltip
            self.tooltip = tk.Toplevel(self.widget)
            self.tooltip.wm_overrideredirect(True)
            
            # Label con el texto
            label = tk.Label(self.tooltip, 
                           text=self.texto,
                           background=self.bg_tooltip,
                           foreground=self.fg_tooltip,
                           font=('Arial', 9),
                           padx=8,
                           pady=4,
                           relief=tk.FLAT,
                           wraplength=300)
            label.pack()
            
            # Posicionar bajo el widget
            self.widget.update()
            x = self.widget.winfo_rootx()
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
            
            self.tooltip.wm_geometry(f"+{x}+{y}")
            self.tooltip_visible = True
            self.timer = None
        except:
            pass
    
    def _ocultar_tooltip(self):
        """Ocultar el tooltip"""
        if self.tooltip:
            try:
                self.tooltip.destroy()
            except:
                pass
            self.tooltip = None
            self.tooltip_visible = False
    
    def destruir(self):
        """Limpieza"""
        if self.timer:
            self.widget.after_cancel(self.timer)
        self._ocultar_tooltip()


def agregar_tooltips_tabla(tree, tema_global):
    """Agrega tooltips a los headers de la tabla"""
    tooltips_headers = {
        'folio': 'Número de folio o ID único de la persona',
        'nombre': 'Nombre completo del participante',
        'monto_esperado': 'Monto de cooperación requerido',
        'pagado': 'Cantidad total pagada hasta ahora',
        'pendiente': 'Monto que falta por pagar',
        'estado': '● Pagado | ◐ Parcial | ○ Pendiente',
        'ultimo_pago': 'Fecha y hora del último pago registrado',
        'notas': 'Observaciones o comentarios sobre la persona'
    }
    
    # Los headers son identificados por su nombre de columna
    # En Tkinter, tenemos que usar un workaround para tooltips en headers
    # Por ahora creamos tooltips para los botones en su lugar
    
    return tooltips_headers


def agregar_tooltips_botones(frame_botones, tema_global):
    """Agrega tooltips informativos a botones principales"""
    # Esta función será llamada después de crear los botones
    # en el método configurar_interfaz
    pass
