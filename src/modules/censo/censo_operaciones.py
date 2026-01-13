"""
Operaciones del módulo de censo
Funciones para filtrar, ordenar, buscar y actualizar habitantes
"""

import requests
from tkinter import messagebox

from src.config import API_URL, CENSO_NOMBRES_SIMILARES_MIN_PALABRAS, CENSO_NOMBRES_SIMILARES_MAX_RESULTADOS
from src.core.logger import registrar_operacion, registrar_error


def aplicar_filtros(habitantes, criterio="", filtro_estado="Todos"):
    """
    Aplica filtros de búsqueda y estado a la lista de habitantes
    
    Args:
        habitantes: Lista completa de habitantes
        criterio: Texto de búsqueda por nombre o folio
        filtro_estado: "Todos", "Solo Activos" o "Solo Inactivos"
    
    Returns:
        Lista filtrada de habitantes
    """
    resultados = habitantes.copy()
    
    # Filtro de búsqueda por texto
    if criterio:
        criterio = criterio.lower()
        resultados = [
            hab for hab in resultados
            if criterio in hab.get('nombre', '').lower()
            or criterio in hab.get('folio', '').lower()
        ]
    
    # Filtro de estado
    if filtro_estado == "Solo Activos":
        resultados = [hab for hab in resultados if hab.get('activo', True)]
    elif filtro_estado == "Solo Inactivos":
        resultados = [hab for hab in resultados if not hab.get('activo', True)]
    
    return resultados


def ordenar_columna(habitantes, columna, orden_reversa=False):
    """
    Ordena la lista de habitantes por una columna específica
    
    Args:
        habitantes: Lista de habitantes a ordenar
        columna: Nombre de la columna ('folio', 'nombre', etc.)
        orden_reversa: True para orden descendente
    
    Returns:
        Lista ordenada de habitantes
    """
    try:
        lista_ordenada = habitantes.copy()
        
        if columna == 'activo':
            # Para activo, ordenar por booleano
            lista_ordenada.sort(key=lambda h: h.get(columna, True), reverse=orden_reversa)
        else:
            # Para las demás, ordenar por string/número
            lista_ordenada.sort(key=lambda h: str(h.get(columna, '')).lower(), reverse=orden_reversa)
        
        return lista_ordenada
    except Exception as e:
        print(f"Error al ordenar: {e}")
        return habitantes


def buscar_nombres_similares(habitantes, nombre):
    """
    Busca habitantes con nombres similares para evitar duplicados
    
    Args:
        habitantes: Lista de habitantes existentes
        nombre: Nombre a buscar
    
    Returns:
        Lista de habitantes con nombres similares (máx 5)
    """
    nombre_lower = nombre.lower()
    similares = []
    
    # Dividir nombre en palabras
    palabras_busqueda = nombre_lower.split()
    
    for hab in habitantes:
        nombre_hab = hab.get('nombre', '').lower()
        
        # Coincidencia exacta
        if nombre_hab == nombre_lower:
            similares.append(hab)
            continue
        
        # Coincidencia por palabras (al menos N palabras en común)
        palabras_hab = nombre_hab.split()
        palabras_comunes = set(palabras_busqueda) & set(palabras_hab)
        
        if len(palabras_comunes) >= min(CENSO_NOMBRES_SIMILARES_MIN_PALABRAS, len(palabras_busqueda)):
            similares.append(hab)
    
    return similares[:CENSO_NOMBRES_SIMILARES_MAX_RESULTADOS]


def actualizar_estado_habitante(folio, activo, api_url, callback_exito=None):
    """
    Actualiza el estado activo/inactivo de un habitante
    
    Args:
        folio: Folio del habitante
        activo: True para activo, False para inactivo
        api_url: URL de la API
        callback_exito: Función a llamar si la actualización es exitosa
    
    Returns:
        True si fue exitoso, False en caso contrario
    """
    try:
        resp = requests.patch(f"{api_url}/habitantes/{folio}", json={'activo': activo}, timeout=5)
        if resp.status_code == 200:
            estado_txt = "activo" if activo else "inactivo"
            registrar_operacion('CENSO_ESTADO', f"Estado actualizado a {estado_txt}", {'folio': folio})
            if callback_exito:
                callback_exito()
            return True
        else:
            detalle = resp.text
            messagebox.showerror("Error", f"No se pudo actualizar el estado (HTTP {resp.status_code}): {detalle}")
            return False
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo actualizar: {e}")
        return False


def colocar_nota_habitante(folio, nota, api_url, callback_exito=None):
    """
    Actualiza la nota de un habitante
    
    Args:
        folio: Folio del habitante
        nota: Texto de la nota
        api_url: URL de la API
        callback_exito: Función a llamar si la actualización es exitosa
    
    Returns:
        True si fue exitoso, False en caso contrario
    """
    try:
        resp = requests.patch(f"{api_url}/habitantes/{folio}", json={'nota': nota}, timeout=5)
        if resp.status_code == 200:
            registrar_operacion('CENSO_NOTA', 'Nota actualizada', {'folio': folio})
            if callback_exito:
                callback_exito()
            return True
        else:
            detalle = resp.text
            messagebox.showerror("Error", f"No se pudo guardar la nota (HTTP {resp.status_code}): {detalle}")
            return False
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar: {e}")
        return False
