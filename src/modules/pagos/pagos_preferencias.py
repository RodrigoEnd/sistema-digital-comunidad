"""
Sistema de preferencias de usuario para el módulo de pagos
Guarda y restaura configuraciones del usuario
"""

import json
import os
from src.config import RUTA_SEGURA
from src.core.logger import registrar_error


ARCHIVO_PREFERENCIAS = os.path.join(RUTA_SEGURA, 'preferencias_pagos.json')


def guardar_preferencias(cooperacion_activa=None, filtro_estado=None, tamaño_letra=None, 
                        paneles_colapsados=None, ultima_busqueda=None, orden_columna=None, 
                        orden_reversa=None):
    """
    Guarda las preferencias del usuario
    
    Args:
        cooperacion_activa: ID de la cooperación activa
        filtro_estado: Filtro de estado aplicado
        tamaño_letra: Tamaño de letra seleccionado
        paneles_colapsados: Dict con estado de paneles
        ultima_busqueda: Última búsqueda realizada
        orden_columna: Columna por la que se ordenó
        orden_reversa: Orden reverso o no
    """
    try:
        preferencias = cargar_preferencias()
        
        if cooperacion_activa is not None:
            preferencias['cooperacion_activa'] = cooperacion_activa
        if filtro_estado is not None:
            preferencias['filtro_estado'] = filtro_estado
        if tamaño_letra is not None:
            preferencias['tamaño_letra'] = tamaño_letra
        if paneles_colapsados is not None:
            preferencias['paneles_colapsados'] = paneles_colapsados
        if ultima_busqueda is not None:
            preferencias['ultima_busqueda'] = ultima_busqueda
        if orden_columna is not None:
            preferencias['orden_columna'] = orden_columna
        if orden_reversa is not None:
            preferencias['orden_reversa'] = orden_reversa
        
        with open(ARCHIVO_PREFERENCIAS, 'w', encoding='utf-8') as f:
            json.dump(preferencias, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        registrar_error('PREFERENCIAS_PAGOS', f'Error al guardar preferencias: {str(e)}')
        return False


def cargar_preferencias():
    """
    Carga las preferencias del usuario
    
    Returns:
        dict: Diccionario con las preferencias
    """
    try:
        if os.path.exists(ARCHIVO_PREFERENCIAS):
            with open(ARCHIVO_PREFERENCIAS, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        registrar_error('PREFERENCIAS_PAGOS', f'Error al cargar preferencias: {str(e)}')
        return {}


def aplicar_preferencias(sistema_pagos):
    """
    Aplica las preferencias guardadas al sistema de pagos
    
    Args:
        sistema_pagos: Instancia de SistemaControlPagos
    """
    try:
        preferencias = cargar_preferencias()
        
        # Aplicar cooperación activa
        if 'cooperacion_activa' in preferencias:
            coop_id = preferencias['cooperacion_activa']
            # Verificar que la cooperación existe
            if any(c['id'] == coop_id for c in sistema_pagos.cooperaciones):
                sistema_pagos.coop_activa_id = coop_id
                sistema_pagos.aplicar_cooperacion_activa()
        
        # Aplicar filtro de estado
        if 'filtro_estado' in preferencias and hasattr(sistema_pagos, 'filtro_estado_var'):
            sistema_pagos.filtro_estado_var.set(preferencias['filtro_estado'])
            sistema_pagos._aplicar_filtro_estado()
        
        # Aplicar tamaño de letra
        if 'tamaño_letra' in preferencias and hasattr(sistema_pagos, 'tamaño_actual'):
            sistema_pagos.tamaño_actual.set(preferencias['tamaño_letra'])
        
        # Aplicar orden de columna
        if 'orden_columna' in preferencias:
            sistema_pagos.columna_orden = preferencias['orden_columna']
            sistema_pagos.orden_reversa = preferencias.get('orden_reversa', False)
        
        # Aplicar última búsqueda (opcional, puede ser molesto)
        # if 'ultima_busqueda' in preferencias and hasattr(sistema_pagos, 'search_box'):
        #     sistema_pagos.search_box.set(preferencias['ultima_busqueda'])
        
        return True
    except Exception as e:
        registrar_error('PREFERENCIAS_PAGOS', f'Error al aplicar preferencias: {str(e)}')
        return False

