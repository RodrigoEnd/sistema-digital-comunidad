"""
Módulo de gestión de interfaz de usuario para control de pagos
Responsable de construir y gestionar todos los componentes visuales
"""

import tkinter as tk
from tkinter import ttk

from src.ui.tema_moderno import FUENTES, FUENTES_DISPLAY, ESPACIADO, ICONOS
from src.ui.ui_moderna import PanelModerno, BotonModerno


class PagosUIManager:
    """Gestor de construcción y mantenimiento de interfaz de usuario"""
    
    def __init__(self, parent, tema, callbacks):
        """
        Inicializa el gestor de UI
        
        Args:
            parent: Frame o ventana padre
            tema: Diccionario con configuración de tema visual
            callbacks: Dict con funciones callback para eventos
        """
        self.parent = parent
        self.tema = tema
        self.callbacks = callbacks
        
        # Referencias a componentes (se crean en construir_interfaz)
        self.info_panel = None
        self.actions_panel = None
        self.tree = None
        self.scrollbar_y = None
        self.scrollbar_x = None
        
        # Labels de estadísticas
        self.total_personas_label = None
        self.total_pagado_label = None
        self.total_pendiente_label = None
        self.personas_pagadas_label = None
        
    def construir_interfaz_completa(self):
        """
        Construye toda la interfaz y retorna componentes principales
        
        Returns:
            Dict con referencias a componentes clave
        """
        # Este método se implementará en futuras iteraciones
        # Por ahora solo retorna estructura básica
        componentes = {
            'tree': None,
            'info_panel': None,
            'actions_panel': None,
            'labels_estadisticas': {}
        }
        
        return componentes
    
    def crear_panel_estadisticas(self, parent):
        """
        Crea panel con estadísticas principales
        
        Args:
            parent: Frame contenedor
        """
        # Implementación futura
        pass
    
    def crear_tabla_principal(self, parent):
        """
        Crea el Treeview principal con columnas configuradas
        
        Args:
            parent: Frame contenedor
            
        Returns:
            Tupla (tree, scrollbar_y, scrollbar_x)
        """
        # Implementación futura
        pass
    
    def actualizar_labels_estadisticas(self, datos):
        """
        Actualiza los labels de estadísticas con nuevos datos
        
        Args:
            datos: Dict con valores de estadísticas
        """
        if self.total_personas_label:
            self.total_personas_label.config(text=str(datos.get('total_personas', 0)))
        
        if self.total_pagado_label:
            self.total_pagado_label.config(text=f"${datos.get('total_pagado', 0):.2f}")
        
        if self.total_pendiente_label:
            self.total_pendiente_label.config(text=f"${datos.get('total_pendiente', 0):.2f}")
        
        if self.personas_pagadas_label:
            total = datos.get('total_personas', 0)
            pagadas = datos.get('personas_pagadas', 0)
            self.personas_pagadas_label.config(text=f"{pagadas} de {total}")
