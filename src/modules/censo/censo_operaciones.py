"""
Operaciones del módulo de censo
Funciones para filtrar, ordenar, buscar y actualizar habitantes
"""

import re
import unicodedata
from difflib import SequenceMatcher

from tkinter import messagebox

from src.config import CENSO_NOMBRES_SIMILARES_MAX_RESULTADOS
from src.core.logger import registrar_operacion, registrar_error


# Palabras que no aportan al comparar nombres (artículos/preposiciones comunes)
STOPWORDS_NOMBRE = {"de", "del", "la", "las", "los", "y"}


def _normalizar_nombre(nombre):
    """Normaliza nombre para comparación: minúsculas, sin acentos y espacios colapsados."""
    texto = unicodedata.normalize("NFD", nombre)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto.lower()).strip()


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
        elif columna == 'folio':
            # Para folio, ordenar por el número extraído (FOL-0001 -> 1)
            def extraer_numero_folio(habitante):
                folio = habitante.get('folio', 'FOL-9999')
                try:
                    # Extraer el número después de FOL-
                    if 'FOL-' in folio:
                        return int(folio.split('-')[1])
                    return 9999
                except:
                    return 9999
            
            lista_ordenada.sort(key=extraer_numero_folio, reverse=orden_reversa)
        else:
            # Para las demás, ordenar por string
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
    similares = []

    nombre_norm = _normalizar_nombre(nombre)
    tokens_nombre = [t for t in nombre_norm.split() if t not in STOPWORDS_NOMBRE]

    for hab in habitantes:
        nombre_hab = hab.get('nombre', '')
        nombre_hab_norm = _normalizar_nombre(nombre_hab)

        if not nombre_hab_norm:
            continue

        tokens_hab = [t for t in nombre_hab_norm.split() if t not in STOPWORDS_NOMBRE]

        # Coincidencia exacta ignorando acentos/espacios
        if nombre_hab_norm == nombre_norm:
            similares.append(hab)
            continue

        # Evitar falsos positivos por apellidos: exigir que el primer nombre coincida
        if not tokens_hab or not tokens_nombre or tokens_hab[0] != tokens_nombre[0]:
            continue

        # Aceptar variantes mínimas de ortografía (ej. acentos o letras invertidas)
        ratio_similitud = SequenceMatcher(None, nombre_hab_norm, nombre_norm).ratio()
        if ratio_similitud >= 0.9:
            similares.append(hab)

    return similares[:CENSO_NOMBRES_SIMILARES_MAX_RESULTADOS]


def actualizar_estado_habitante(folio, activo, gestor, callback_exito=None):
    """
    Actualiza el estado activo/inactivo de un habitante
    
    Args:
        folio: Folio del habitante
        activo: True para activo, False para inactivo
        gestor: Instancia de GestorDatosGlobal
        callback_exito: Función a llamar si la actualización es exitosa
    
    Returns:
        True si fue exitoso, False en caso contrario
    """
    try:
        exito, mensaje = gestor.actualizar_habitante(folio, activo=activo)
        if exito:
            estado_txt = "activo" if activo else "inactivo"
            registrar_operacion('CENSO_ESTADO', f"Estado actualizado a {estado_txt}", {'folio': folio})
            if callback_exito:
                callback_exito()
            return True
        else:
            messagebox.showerror("Error", f"No se pudo actualizar el estado: {mensaje}")
            return False
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo actualizar: {e}")
        registrar_error('censo_operaciones', 'actualizar_estado_habitante', str(e), contexto=f"folio={folio}")
        return False


def colocar_nota_habitante(folio, nota, gestor, callback_exito=None):
    """
    Actualiza la nota de un habitante
    
    Args:
        folio: Folio del habitante
        nota: Texto de la nota
        gestor: Instancia de GestorDatosGlobal
        callback_exito: Función a llamar si la actualización es exitosa
    
    Returns:
        True si fue exitoso, False en caso contrario
    """
    try:
        exito, mensaje = gestor.actualizar_habitante(folio, nota=nota)
        if exito:
            registrar_operacion('CENSO_NOTA', 'Nota actualizada', {'folio': folio})
            if callback_exito:
                callback_exito()
            return True
        else:
            messagebox.showerror("Error", f"No se pudo guardar la nota: {mensaje}")
            return False
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar: {e}")
        registrar_error('censo_operaciones', 'colocar_nota_habitante', str(e), contexto=f"folio={folio}")
        return False


def editar_nombre_habitante(folio, nuevo_nombre, gestor, callback_exito=None):
    """
    Actualiza el nombre de un habitante
    
    Args:
        folio: Folio del habitante
        nuevo_nombre: Nuevo nombre completo
        gestor: Instancia del gestor
        callback_exito: Función a ejecutar si es exitoso
    """
    try:
        if not nuevo_nombre or len(nuevo_nombre.strip()) < 3:
            messagebox.showerror("Error", "El nombre debe tener al menos 3 caracteres")
            return False
        
        exito, mensaje = gestor.actualizar_habitante(folio, nombre=nuevo_nombre.strip())
        
        if exito:
            registrar_operacion(
                'CENSO',
                'Nombre actualizado',
                {'folio': folio, 'nuevo_nombre': nuevo_nombre}
            )
            if callback_exito:
                callback_exito()
            return True
        else:
            messagebox.showerror("Error", mensaje)
            return False
    
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo actualizar el nombre: {str(e)}")
        registrar_error('censo_operaciones', 'editar_nombre_habitante', str(e), contexto=f"folio={folio}")
        return False
