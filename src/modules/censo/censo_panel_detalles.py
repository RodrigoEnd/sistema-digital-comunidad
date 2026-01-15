"""
Panel lateral de detalles del censo
Muestra información completa del habitante seleccionado
"""

import tkinter as tk
from tkinter import ttk


class CensoPanelDetalles:
    """Clase para gestionar el panel lateral de detalles"""
    
    def __init__(self, parent, gestor, callback_actualizar, 
                 callback_pagos, callback_faenas, callback_nota, callback_estado):
        """
        Inicializa el panel de detalles
        
        Args:
            parent: Frame contenedor
            gestor: Instancia de GestorDatosGlobal
            callback_actualizar: Función para actualizar la lista
            callback_pagos: Función para abrir control de pagos
            callback_faenas: Función para abrir registro de faenas
            callback_nota: Función para editar nota
            callback_estado: Función para cambiar estado
        """
        self.parent = parent
        self.gestor = gestor
        self.callback_actualizar = callback_actualizar
        self.callback_pagos = callback_pagos
        self.callback_faenas = callback_faenas
        self.callback_nota = callback_nota
        self.callback_estado = callback_estado
        
        self.habitante_actual = None
        
        # Crear panel inicial
        self.mostrar_mensaje_inicial()
    
    def mostrar_mensaje_inicial(self):
        """Muestra mensaje cuando no hay habitante seleccionado"""
        self.limpiar_panel()
        ttk.Label(self.parent, text="Selecciona un habitante\npara ver sus detalles",
                 font=('Arial', 10), foreground='#888', justify=tk.CENTER).pack(expand=True)
    
    def limpiar_panel(self):
        """Limpia todos los widgets del panel"""
        for widget in self.parent.winfo_children():
            widget.destroy()
    
    def mostrar_detalles(self, habitante):
        """
        Muestra los detalles del habitante en el panel
        
        Args:
            habitante: Diccionario con datos del habitante
        """
        self.habitante_actual = habitante
        self.limpiar_panel()
        
        # Título
        ttk.Label(self.parent, text="Información Completa", 
                 font=('Arial', 11, 'bold')).pack(pady=(0, 10), anchor=tk.W)
        
        # Datos del habitante
        datos_frame = ttk.Frame(self.parent)
        datos_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(datos_frame, text="Folio:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(datos_frame, text=habitante['folio'], font=('Arial', 9)).grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(datos_frame, text="Nombre:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=2)
        nombre_label = ttk.Label(datos_frame, text=habitante['nombre'], font=('Arial', 9), wraplength=180)
        nombre_label.grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(datos_frame, text="Fecha:", font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(datos_frame, text=habitante.get('fecha_registro', 'N/A'), 
                 font=('Arial', 9)).grid(row=2, column=1, sticky=tk.W, pady=2, padx=5)
        
        activo = habitante.get('activo', True)
        estado_texto = "● Activo" if activo else "● Inactivo"
        estado_color = '#4CAF50' if activo else '#F44336'
        
        ttk.Label(datos_frame, text="Estado:", font=('Arial', 9, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=2)
        estado_label = ttk.Label(datos_frame, text=estado_texto, font=('Arial', 9), foreground=estado_color)
        estado_label.grid(row=3, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Nota completa
        ttk.Separator(self.parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(self.parent, text="Nota:", font=('Arial', 9, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        nota_text = tk.Text(self.parent, height=5, width=25, font=('Arial', 9), 
                           wrap=tk.WORD, relief=tk.SOLID, borderwidth=1)
        nota_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        nota_text.insert('1.0', habitante.get('nota', 'Sin nota'))
        nota_text.config(state=tk.DISABLED)
        
        # Botones de acción
        ttk.Separator(self.parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        botones_frame = ttk.Frame(self.parent)
        botones_frame.pack(fill=tk.X)
        
        ttk.Button(botones_frame, text="Editar Nota", 
                  command=lambda: self.callback_nota(habitante)).pack(fill=tk.X, pady=2)
        ttk.Button(botones_frame, text="Ver Pagos", 
                  command=self.callback_pagos).pack(fill=tk.X, pady=2)
        ttk.Button(botones_frame, text="Ver Faenas", 
                  command=self.callback_faenas).pack(fill=tk.X, pady=2)
        
        # Mostrar botón de historial (importar aquí para evitar circular)
        from .censo_dialogos import mostrar_historial
        ttk.Button(botones_frame, text="Historial", 
                  command=lambda: mostrar_historial(self.parent.winfo_toplevel(), habitante)).pack(fill=tk.X, pady=2)
        
        if activo:
            ttk.Button(botones_frame, text="Marcar Inactivo", 
                      command=lambda: self.callback_estado(habitante['folio'], False)).pack(fill=tk.X, pady=2)
        else:
            ttk.Button(botones_frame, text="Marcar Activo", 
                      command=lambda: self.callback_estado(habitante['folio'], True)).pack(fill=tk.X, pady=2)
