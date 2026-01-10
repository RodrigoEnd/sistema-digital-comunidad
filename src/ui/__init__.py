"""
Módulo de UI - Interfaz de Usuario
Contiene componentes visuales, temas y ventanas
Importa del módulo centralizado de estilos globales
"""
from .estilos_globales import (TEMA_GLOBAL, TEMA_CLARO, TEMA_OSCURO, 
                               FUENTES, FUENTES_DISPLAY, ESPACIADO, 
                               RADIOS_BORDE, ICONOS, SOMBRAS, TRANSICIONES,
                               obtener_color_estado, interpolar_color, 
                               aclarar_color, oscurecer_color)
from .ui_moderna import BarraSuperior, PanelModerno, BotonModerno, CampoEntrada
from .ui_componentes_extra import SearchBox, CardEstadistica, Separator, Badge
from .ventana_busqueda import VentanaBusquedaAvanzada
from .buscador import BuscadorAvanzado

__all__ = ['TEMA_GLOBAL', 'TEMA_CLARO', 'TEMA_OSCURO', 'FUENTES', 'FUENTES_DISPLAY',
           'ESPACIADO', 'RADIOS_BORDE', 'ICONOS', 'SOMBRAS', 'TRANSICIONES',
           'obtener_color_estado', 'interpolar_color', 'aclarar_color', 'oscurecer_color',
           'BarraSuperior', 'PanelModerno', 'BotonModerno', 'CampoEntrada',
           'SearchBox', 'CardEstadistica', 'Separator', 'Badge',
           'VentanaBusquedaAvanzada', 'BuscadorAvanzado']
