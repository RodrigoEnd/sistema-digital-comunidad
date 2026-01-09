"""
Módulo de UI - Interfaz de Usuario
Contiene componentes visuales, temas y ventanas
"""
from .tema_moderno import TEMA_CLARO, TEMA_OSCURO, FUENTES, ESPACIADO, ICONOS
from .ui_moderna import BarraSuperior, PanelModerno, BotonModerno, CampoEntrada
from .ui_componentes_extra import SearchBox, CardEstadistica, Separator
from .ventana_busqueda import VentanaBusquedaAvanzada
from .buscador import BuscadorAvanzado

__all__ = ['TEMA_CLARO', 'TEMA_OSCURO', 'FUENTES', 'ESPACIADO', 'ICONOS',
           'BarraSuperior', 'PanelModerno', 'BotonModerno', 'CampoEntrada',
           'SearchBox', 'CardEstadistica', 'Separator',
           'VentanaBusquedaAvanzada', 'BuscadorAvanzado']
