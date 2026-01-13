"""
Gestión de preferencias de usuario del censo
Guarda y carga filtros, búsquedas, etc.
"""

import json
import os


def cargar_preferencias(config_path):
    """
    Carga las preferencias del usuario desde archivo JSON
    
    Args:
        config_path: Ruta al archivo de configuración
    
    Returns:
        Diccionario con preferencias o None si no existe
    """
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error cargando preferencias: {e}")
    return None


def guardar_preferencias(config_path, search_text, filtro_estado):
    """
    Guarda las preferencias del usuario
    
    Args:
        config_path: Ruta al archivo de configuración
        search_text: Texto de búsqueda actual
        filtro_estado: Filtro de estado actual
    
    Returns:
        True si fue exitoso
    """
    try:
        prefs = {
            'ultima_busqueda': search_text,
            'filtro_estado': filtro_estado
        }
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(prefs, f, indent=2)
        return True
    except Exception as e:
        print(f"Error guardando preferencias: {e}")
        return False


def aplicar_preferencias(prefs, search_var, filtro_estado_var):
    """
    Aplica las preferencias cargadas a las variables de tkinter
    
    Args:
        prefs: Diccionario con preferencias
        search_var: StringVar de búsqueda
        filtro_estado_var: StringVar de filtro de estado
    """
    try:
        if not prefs:
            return
        
        # Restaurar búsqueda
        if 'ultima_busqueda' in prefs:
            search_var.set(prefs['ultima_busqueda'])
        
        # Restaurar filtro de estado
        if 'filtro_estado' in prefs:
            filtro_estado_var.set(prefs['filtro_estado'])
    except Exception as e:
        print(f"Error aplicando preferencias: {e}")
