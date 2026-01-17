"""
Utilidades comunes para el módulo de censo
Centraliza formato de estado y truncado de notas
"""

from typing import Tuple

from src.config import CENSO_NOTA_MAX_DISPLAY


def estado_texto_color_tag(activo: bool) -> Tuple[str, str, str]:
    """
    Devuelve (texto_estado, color_hex, tag_treeview) según el estado.
    """
    texto = "Activo" if activo else "Inactivo"
    color = "#4CAF50" if activo else "#F44336"
    tag = "activo" if activo else "inactivo"
    return texto, color, tag


def resumir_nota(nota: str) -> str:
    """Trunca la nota al máximo configurado, añadiendo '...' si aplica."""
    if not nota:
        return ""
    return nota[:CENSO_NOTA_MAX_DISPLAY] + "..." if len(nota) > CENSO_NOTA_MAX_DISPLAY else nota
