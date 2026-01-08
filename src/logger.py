"""
Sistema de logging y auditoria del sistema
Registra todas las operaciones importantes para debugging y auditoria
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from config import (
    CARPETA_LOGS,
    ARCHIVO_LOG,
    FORMATO_LOG,
    FORMATO_FECHA_LOG,
    LIMITE_LOG_MB,
    CANTIDAD_BACKUPS_LOG
)

# Crear carpeta de logs si no existe
if not os.path.exists(CARPETA_LOGS):
    os.makedirs(CARPETA_LOGS)
    # Ocultar carpeta en Windows
    try:
        import ctypes
        FILE_ATTRIBUTE_HIDDEN = 0x02
        ctypes.windll.kernel32.SetFileAttributesW(CARPETA_LOGS, FILE_ATTRIBUTE_HIDDEN)
    except:
        pass

# Crear logger principal
logger = logging.getLogger('SistemaComunidad')
logger.setLevel(logging.DEBUG)

# Formato de logs
formatter = logging.Formatter(FORMATO_LOG, datefmt=FORMATO_FECHA_LOG)

# Handler para archivo con rotacion
try:
    file_handler = RotatingFileHandler(
        ARCHIVO_LOG,
        maxBytes=LIMITE_LOG_MB * 1024 * 1024,  # Convertir MB a bytes
        backupCount=CANTIDAD_BACKUPS_LOG
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Ocultar archivo de log
    try:
        import ctypes
        FILE_ATTRIBUTE_HIDDEN = 0x02
        ctypes.windll.kernel32.SetFileAttributesW(ARCHIVO_LOG, FILE_ATTRIBUTE_HIDDEN)
    except:
        pass
except Exception as e:
    print(f"Error al configurar logging: {e}")

# Handler para consola (solo en desarrollo)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
# logger.addHandler(console_handler)  # Descomenta para ver logs en consola

def registrar_operacion(tipo, accion, detalles, usuario="Sistema"):
    """
    Registra una operacion del sistema con auditoria
    
    Args:
        tipo (str): Tipo de operacion (AGREGAR, EDITAR, ELIMINAR, PAGO, etc)
        accion (str): Descripcion de la accion
        detalles (dict): Detalles adicionales de la operacion
        usuario (str): Usuario que realizo la operacion
    """
    try:
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        mensaje = f"[AUDITORIA] {tipo} | Usuario: {usuario} | Accion: {accion} | Detalles: {detalles} | {timestamp}"
        logger.info(mensaje)
    except Exception as e:
        logger.error(f"Error al registrar operacion: {e}")

def registrar_error(modulo, funcion, error, contexto=""):
    """
    Registra un error del sistema
    
    Args:
        modulo (str): Modulo donde ocurrio el error
        funcion (str): Funcion donde ocurrio el error
        error (str): Descripcion del error
        contexto (str): Contexto adicional
    """
    try:
        mensaje = f"[ERROR] {modulo}.{funcion} | Error: {error} | Contexto: {contexto}"
        logger.error(mensaje)
    except Exception as e:
        logger.error(f"Error al registrar error: {e}")

def registrar_transaccion(id_transaccion, tipo_transaccion, monto, estado, detalles=""):
    """
    Registra una transaccion de dinero
    
    Args:
        id_transaccion (str): ID unico de transaccion
        tipo_transaccion (str): Tipo (PAGO, COOPERACION, REFUND, etc)
        monto (float): Monto de la transaccion
        estado (str): Estado (COMPLETADA, PENDIENTE, CANCELADA)
        detalles (str): Detalles adicionales
    """
    try:
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        mensaje = f"[TRANSACCION] ID: {id_transaccion} | Tipo: {tipo_transaccion} | Monto: ${monto:.2f} | Estado: {estado} | Detalles: {detalles} | {timestamp}"
        logger.info(mensaje)
    except Exception as e:
        logger.error(f"Error al registrar transaccion: {e}")

def registrar_acceso(usuario, resultado):
    """
    Registra intentos de acceso al sistema
    
    Args:
        usuario (str): Usuario que intento acceder
        resultado (str): EXITOSO o FALLIDO
    """
    try:
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        mensaje = f"[ACCESO] Usuario: {usuario} | Resultado: {resultado} | {timestamp}"
        logger.info(mensaje)
    except Exception as e:
        logger.error(f"Error al registrar acceso: {e}")

def registrar_backup(nombre_archivo, tipo, estado):
    """
    Registra operaciones de backup
    
    Args:
        nombre_archivo (str): Nombre del archivo
        tipo (str): INICIO, COMPLETADO, FALLIDO
        estado (str): Detalles del estado
    """
    try:
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        mensaje = f"[BACKUP] Archivo: {nombre_archivo} | Tipo: {tipo} | Estado: {estado} | {timestamp}"
        logger.info(mensaje)
    except Exception as e:
        logger.error(f"Error al registrar backup: {e}")

def obtener_historial_logs(cantidad=100):
    """
    Obtiene los ultimos registros del log
    
    Args:
        cantidad (int): Cantidad de registros a obtener
        
    Returns:
        list: Lista de ultimos registros
    """
    try:
        with open(ARCHIVO_LOG, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            return lineas[-cantidad:]
    except Exception as e:
        logger.error(f"Error al obtener historial: {e}")
        return []

def limpiar_logs_antiguos(dias=30):
    """
    Limpia logs anteriores a X dias (implementar si es necesario)
    
    Args:
        dias (int): Dias a mantener
    """
    try:
        from datetime import datetime, timedelta
        fecha_limite = datetime.now() - timedelta(days=dias)
        # Implementar logica de limpieza
        logger.info(f"Limpieza de logs anterior a {fecha_limite.strftime('%d/%m/%Y')}")
    except Exception as e:
        logger.error(f"Error al limpiar logs: {e}")
