"""
Utilidades de UI moderna para control_pagos
Componentes reutilizables con tema moderno y efectos visuales avanzados
"""

import tkinter as tk
from tkinter import ttk
from src.ui.tema_moderno import (TEMA_CLARO, TEMA_OSCURO, FUENTES, FUENTES_DISPLAY, 
                          ESPACIADO, ICONOS, TRANSICIONES, SOMBRAS,
                          oscurecer_color, aclarar_color, interpolar_color)

class BarraSuperior:
    """Barra superior con logo, usuario y controles de tema con degradado"""
    
    def __init__(self, parent, usuario, callback_cambio_tema):
        self.parent = parent
        self.usuario = usuario
        self.callback_cambio_tema = callback_cambio_tema
        self.tema = TEMA_CLARO
        
        # Frame principal con efecto degradado simulado
        self.frame = tk.Frame(parent, bg=self.tema['accent_primary'], height=70)
        self.crear_barra()
    
    def crear_barra(self):
        """Crear elementos de la barra con mejor diseño"""
        # Logo/título a la izquierda con mejor espaciado
        logo_frame = tk.Frame(self.frame, bg=self.tema['accent_primary'])
        logo_frame.pack(side=tk.LEFT, padx=ESPACIADO['xl'], pady=ESPACIADO['lg'])
        
        # Icono más grande
        tk.Label(logo_frame, text=ICONOS['casa'], font=('Arial', 28),
                bg=self.tema['accent_primary']).pack(side=tk.LEFT, padx=(0, ESPACIADO['md']))
        
        # Contenedor de texto
        text_container = tk.Frame(logo_frame, bg=self.tema['accent_primary'])
        text_container.pack(side=tk.LEFT)
        
        tk.Label(text_container, text="Sistema Digital Comunidad",
                font=FUENTES['titulo'], fg='#ffffff',
                bg=self.tema['accent_primary']).pack(anchor=tk.W)
        
        tk.Label(text_container, text="Gestión Comunitaria Integrada",
                font=FUENTES['pequeño'], fg='#e0e0e0',
                bg=self.tema['accent_primary']).pack(anchor=tk.W)
        
        # Usuario y controles a la derecha con mejor diseño
        control_frame = tk.Frame(self.frame, bg=self.tema['accent_primary'])
        control_frame.pack(side=tk.RIGHT, padx=ESPACIADO['xl'], pady=ESPACIADO['lg'])
        
        # Card de usuario con fondo semitransparente
        user_card = tk.Frame(control_frame, bg='#6699cc', relief=tk.FLAT)
        user_card.pack(side=tk.LEFT, padx=(0, ESPACIADO['lg']))
        
        user_inner = tk.Frame(user_card, bg='#6699cc')
        user_inner.pack(padx=ESPACIADO['md'], pady=ESPACIADO['sm'])
        
        # Icono usuario
        tk.Label(user_inner, text=ICONOS['usuario'], font=('Arial', 16),
                fg='#ffffff', bg='#6699cc').pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        
        # Info usuario
        user_text_frame = tk.Frame(user_inner, bg='#6699cc')
        user_text_frame.pack(side=tk.LEFT)
        
        nombre = self.usuario.get('nombre_completo', self.usuario.get('nombre', 'Usuario'))
        tk.Label(user_text_frame, text=nombre, font=FUENTES['normal'],
                fg='#ffffff', bg='#6699cc').pack(anchor=tk.W)
        
        rol = self.usuario.get('rol', 'operador').upper()
        tk.Label(user_text_frame, text=rol, font=FUENTES['pequeño'],
                fg='#d0d0d0', bg='#6699cc').pack(anchor=tk.W)
        
        # Botón de tema deshabilitado (modo noche removido)
        # tema_container = tk.Frame(control_frame, bg='#ffffff', relief=tk.FLAT)
        # tema_container.pack(side=tk.LEFT)
        # self.btn_tema = tk.Button(...)
        
        # Efectos hover (removido junto con botón de tema)
    
    def _on_btn_enter(self, event):
        """Efecto hover al entrar"""
        event.widget.config(bg='#f5f5f5')
    
    def _on_btn_leave(self, event):
        """Efecto hover al salir"""
        event.widget.config(bg='#ffffff')
    
    def actualizar_tema(self, tema_dict):
        """Actualizar colores según tema"""
        self.tema = tema_dict
        self.frame.config(bg=tema_dict['accent_primary'])
        for widget in self.frame.winfo_children():
            widget.config(bg=tema_dict['accent_primary'])
    
    def pack(self, **kwargs):
        fill_value = kwargs.pop('fill', tk.X)
        self.frame.pack(fill=fill_value, **kwargs)
    
    def grid(self, **kwargs):
        """Permitir uso de grid para posicionar la barra"""
        self.frame.grid(**kwargs)
    
    def update_button_text(self, texto):
        """Actualizar texto del botón de tema"""
        self.btn_tema.config(text=texto)


class PanelModerno(tk.Frame):
    """Frame con estilo card moderno, sombra simulada y mejor diseño"""
    
    def __init__(self, parent, titulo="", tema=None, with_shadow=True, **kwargs):
        super().__init__(parent, **kwargs)
        self.tema = tema or TEMA_CLARO
        self.titulo = titulo
        self.with_shadow = with_shadow
        
        # Configurar como card con sombra
        self.config(bg=self.tema['bg_principal'], relief=tk.FLAT, bd=0)
        self.crear_panel()
    
    def crear_panel(self):
        """Crear estructura del panel tipo card"""
        # Card principal - usar pack en lugar de place para mejor manejo del espacio
        self.card = tk.Frame(self, bg=self.tema.get('card_bg', self.tema['bg_secundario']), 
                            relief=tk.FLAT, bd=1, highlightthickness=1,
                            highlightbackground=self.tema.get('card_border', self.tema['border']))
        self.card.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        if self.titulo:
            # Header del card
            header_frame = tk.Frame(self.card, bg=self.tema.get('card_bg', self.tema['bg_secundario']))
            header_frame.pack(fill=tk.X, padx=0, pady=0)
            
            self.titulo_label = tk.Label(header_frame, text=self.titulo, font=FUENTES['subtitulo'],
                                   bg=self.tema.get('card_bg', self.tema['bg_secundario']), 
                                   fg=self.tema['accent_primary'])
            self.titulo_label.pack(anchor=tk.W, padx=ESPACIADO['lg'], pady=(ESPACIADO['lg'], ESPACIADO['md']))
            
            # Línea separadora más sutil
            sep = tk.Frame(header_frame, bg=self.tema.get('border', '#e0e0e0'), height=1)
            sep.pack(fill=tk.X, padx=ESPACIADO['lg'], pady=(0, ESPACIADO['md']))
        
        # Contenido del card con padding
        self.content_frame = tk.Frame(self.card, bg=self.tema.get('card_bg', self.tema['bg_secundario']))
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['lg'], pady=ESPACIADO['lg'])
    
    def actualizar_tema(self, tema_dict):
        """Actualizar tema del panel"""
        self.tema = tema_dict
        card_bg = tema_dict.get('card_bg', tema_dict['bg_secundario'])
        self.config(bg=tema_dict['bg_principal'])
        self.card.config(bg=card_bg, highlightbackground=tema_dict.get('card_border', tema_dict['border']))
        self.content_frame.config(bg=card_bg)


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
    """Botón moderno con hover effects y animaciones suaves"""
    
    def __init__(self, parent, texto, tema=None, tipo='primary', icono=None, **kwargs):
        self.tema = tema or TEMA_CLARO
        self.tipo = tipo
        
        # Mapa de colores según tipo con mejores combinaciones
        color_map = {
            'primary': (self.tema['accent_primary'], '#ffffff'),
            'success': (self.tema['success'], '#ffffff'),
            'error': (self.tema['error'], '#ffffff'),
            'warning': (self.tema['warning'], '#1e293b'),
            'secondary': (self.tema['border'], self.tema['fg_principal']),
            'ghost': (self.tema.get('card_bg', self.tema['bg_secundario']), self.tema['accent_primary']),
        }
        bg, fg = color_map.get(tipo, color_map['primary'])
        
        # Agregar icono al texto si se proporciona
        texto_final = f"{icono} {texto}" if icono else texto
        
        super().__init__(parent, text=texto_final, font=FUENTES['botones'],
                        bg=bg, fg=fg, relief=tk.FLAT, 
                        padx=ESPACIADO['lg'], pady=ESPACIADO['md'], 
                        cursor='hand2',
                        activebackground=oscurecer_color(bg, 0.1),
                        activeforeground=fg, 
                        borderwidth=0,
                        **kwargs)
        
        self.color_original = bg
        self.color_hover = oscurecer_color(bg, 0.08) if tipo != 'ghost' else aclarar_color(bg, 0.05)
        
        # Bindings para efectos hover
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
    
    def _on_enter(self, event):
        """Efecto al pasar el mouse"""
        self.config(bg=self.color_hover)
    
    def _on_leave(self, event):
        """Efecto al salir el mouse"""
        self.config(bg=self.color_original)
    
    @staticmethod
    def _oscurecer_color(color_hex):
        """DEPRECATED: usar oscurecer_color de tema_moderno"""
        return oscurecer_color(color_hex)
