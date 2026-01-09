"""
Módulo Core - Funcionalidades Centrales
Contiene base de datos, logging, validación y utilidades
"""
from .logger import registrar_operacion, registrar_error, registrar_transaccion
from .validadores import validar_nombre, validar_monto, ErrorValidacion
from .utilidades import *

__all__ = ['registrar_operacion', 'registrar_error', 'registrar_transaccion',
           'validar_nombre', 'validar_monto', 'ErrorValidacion']
