"""
Utilidades de UI moderna para control_pagos
Componentes reutilizables con tema moderno
"""

import tkinter as tk
from tkinter import ttk
from tema_moderno import TEMA_CLARO, TEMA_OSCURO, FUENTES, ESPACIADO, ICONOS

class BarraSuperior:
    """Barra superior con logo, usuario y controles de tema"""
    
    def __init__(self, parent, usuario, callback_cambio_tema):
        self.parent = parent
        self.usuario = usuario
        self.callback_cambio_tema = callback_cambio_tema
        self.tema = TEMA_CLARO
        self.frame = tk.Frame(parent, bg=self.tema['accent_primary'], height=60)
        self.crear_barra()
    
    def crear_barra(self):
        """Crear elementos de la barra"""
        # Logo/título a la izquierda
        logo_frame = tk.Frame(self.frame, bg=self.tema['accent_primary'])
        logo_frame.pack(side=tk.LEFT, padx=ESPACIADO['lg'], pady=ESPACIADO['md'])
        
        tk.Label(logo_frame, text="🏘️", font=('Arial', 20),
                bg=self.tema['accent_primary']).pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        
        tk.Label(logo_frame, text="Sistema Digital Comunidad",
                font=FUENTES['subtitulo'], fg='#ffffff',
                bg=self.tema['accent_primary']).pack(side=tk.LEFT)
        
        # Usuario y controles a la derecha
        control_frame = tk.Frame(self.frame, bg=self.tema['accent_primary'])
        control_frame.pack(side=tk.RIGHT, padx=ESPACIADO['lg'], pady=ESPACIADO['md'])
        
        # Usuario info
        user_text = f"{ICONOS['usuario']} {self.usuario.get('nombre_completo', self.usuario.get('nombre', 'Usuario'))}"
        tk.Label(control_frame, text=user_text, font=FUENTES['pequeño'],
                fg='#ffffff', bg=self.tema['accent_primary']).pack(side=tk.LEFT, padx=(0, ESPACIADO['lg']))
        
        # Toggle tema (sol/luna)
        self.btn_tema = tk.Button(control_frame, text=f"{ICONOS['luna']} Noche",
                     font=FUENTES['pequeño'], bg='#ffffff', fg=self.tema['accent_primary'],
                     relief=tk.FLAT, padx=ESPACIADO['md'], pady=ESPACIADO['sm'],
                     cursor='hand2', command=self.callback_cambio_tema)
        self.btn_tema.pack(side=tk.LEFT)
    
    def actualizar_tema(self, tema_dict):
        """Actualizar colores según tema"""
        self.tema = tema_dict
        self.frame.config(bg=tema_dict['accent_primary'])
        for widget in self.frame.winfo_children():
            widget.config(bg=tema_dict['accent_primary'])
    
    def pack(self, **kwargs):
        # Evitar duplicar argumento fill cuando el caller lo pasa
        fill_value = kwargs.pop('fill', tk.X)
        self.frame.pack(fill=fill_value, **kwargs)
    
    def update_button_text(self, texto):
        """Actualizar texto del botón de tema"""
        self.btn_tema.config(text=texto)


class PanelModerno(tk.Frame):
    """Frame con estilo moderno para agrupar elementos"""
    
    def __init__(self, parent, titulo="", tema=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.tema = tema or TEMA_CLARO
        self.titulo = titulo
        self.config(bg=self.tema['bg_secundario'])
        self.crear_panel()
    
    def crear_panel(self):
        """Crear estructura del panel"""
        if self.titulo:
            titulo_label = tk.Label(self, text=self.titulo, font=FUENTES['subtitulo'],
                                   bg=self.tema['bg_secundario'], fg=self.tema['accent_primary'])
            titulo_label.pack(anchor=tk.W, padx=ESPACIADO['lg'], pady=(ESPACIADO['lg'], ESPACIADO['sm']))
            
            sep = tk.Frame(self, bg=self.tema['accent_primary'], height=1)
            sep.pack(fill=tk.X, padx=ESPACIADO['lg'], pady=(0, ESPACIADO['md']))
        
        self.content_frame = tk.Frame(self, bg=self.tema['bg_secundario'])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['lg'], pady=ESPACIADO['lg'])
    
    def actualizar_tema(self, tema_dict):
        """Actualizar tema del panel"""
        self.tema = tema_dict
        self.config(bg=tema_dict['bg_secundario'])
        self.content_frame.config(bg=tema_dict['bg_secundario'])


class CampoEntrada(tk.Frame):
    """Campo de entrada moderno con label"""
    
    def __init__(self, parent, label_text, tema=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.tema = tema or TEMA_CLARO
        self.config(bg=self.tema['bg'])
        
        label = tk.Label(self, text=label_text, font=FUENTES['normal'],
                        bg=self.tema['bg'], fg=self.tema['fg_principal'])
        label.pack(anchor=tk.W, pady=(0, ESPACIADO['sm']))
        
        self.entry = tk.Entry(self, font=FUENTES['normal'],
                             bg=self.tema['input_bg'], fg=self.tema['fg_principal'],
                             relief=tk.SOLID, bd=1, insertbackground=self.tema['accent_primary'])
        self.entry.pack(fill=tk.X)
        self.entry.bind('<FocusIn>', lambda e: self._on_focus(True))
        self.entry.bind('<FocusOut>', lambda e: self._on_focus(False))
    
    def _on_focus(self, is_focus):
        """Cambiar border al focus"""
        if is_focus:
            self.entry.config(bd=2, relief=tk.SOLID)
        else:
            self.entry.config(bd=1, relief=tk.SOLID)
    
    def get(self):
        return self.entry.get()
    
    def set(self, valor):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, valor)


class BotonModerno(tk.Button):
    """Botón moderno con hover effects"""
    
    def __init__(self, parent, texto, tema=None, tipo='primary', **kwargs):
        self.tema = tema or TEMA_CLARO
        color_map = {
            'primary': (self.tema['accent_primary'], '#ffffff'),
            'success': (self.tema['success'], '#ffffff'),
            'error': (self.tema['error'], '#ffffff'),
            'secondary': (self.tema['fg_terciario'], '#ffffff'),
        }
        bg, fg = color_map.get(tipo, color_map['primary'])
        
        super().__init__(parent, text=texto, font=FUENTES['botones'],
                        bg=bg, fg=fg, relief=tk.FLAT, padx=ESPACIADO['lg'],
                        pady=ESPACIADO['md'], cursor='hand2',
                        activebackground=self._oscurecer_color(bg),
                        activeforeground=fg, **kwargs)
        self.tipo = tipo
        self.color_original = bg
    
    @staticmethod
    def _oscurecer_color(color_hex):
        """Oscurecer un color hex para hover"""
        color_hex = color_hex.lstrip('#')
        r, g, b = int(color_hex[0:2], 16), int(color_hex[2:4], 16), int(color_hex[4:6], 16)
        r, g, b = max(0, r - 30), max(0, g - 30), max(0, b - 30)
        return f'#{r:02x}{g:02x}{b:02x}'
