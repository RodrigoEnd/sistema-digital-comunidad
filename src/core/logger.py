"""
Sistema de logging y auditoria del sistema
Registra todas las operaciones importantes para debugging y auditoria
Incluye contexto de usuario, IP, y trazabilidad completa
"""

import logging
import os
import socket
from logging.handlers import RotatingFileHandler
from datetime import datetime
from src.config import (
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


# ============================================================================
# FUNCIONES DE UTILIDAD PARA LOGGING MEJORADO
# ============================================================================

def obtener_ip_local():
    """
    Obtiene la IP local de la maquina
    
    Returns:
        str: IP local o "127.0.0.1" si no puede obtenerla
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def obtener_nombre_usuario_sistema():
    """
    Obtiene el nombre del usuario del sistema operativo
    
    Returns:
        str: Nombre del usuario
    """
    try:
        return os.getenv('USERNAME', 'Unknown')
    except:
        return "Unknown"


def formatear_contexto(usuario=None, ip=None, operacion=None):
    """
    Formatea contexto enriquecido para logs
    
    Args:
        usuario (str): Nombre del usuario
        ip (str): IP del usuario
        operacion (str): Tipo de operacion
        
    Returns:
        str: String formateado con contexto
    """
    contexto = []
    
    if usuario:
        contexto.append(f"USUARIO: {usuario}")
    
    if ip:
        contexto.append(f"IP: {ip}")
    
    if operacion:
        contexto.append(f"OPERACION: {operacion}")
    
    return " | ".join(contexto) if contexto else ""


def registrar_operacion(tipo, accion, detalles, usuario="Sistema", ip=None):
    """
    Registra una operacion del sistema con auditoria mejorada
    
    Incluye: timestamp, usuario, IP, tipo de operacion, detalles
    
    Args:
        tipo (str): Tipo de operacion (AGREGAR, EDITAR, ELIMINAR, PAGO, etc)
        accion (str): Descripcion de la accion
        detalles (dict): Detalles adicionales de la operacion
        usuario (str): Usuario que realizo la operacion
        ip (str): IP del usuario (si aplica)
    """
    try:
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        # Obtener IP si no se proporciona
        if ip is None:
            ip = obtener_ip_local()
        
        # Formatear detalles si es diccionario
        if isinstance(detalles, dict):
            detalles_str = " | ".join([f"{k}: {v}" for k, v in detalles.items()])
        else:
            detalles_str = str(detalles)
        
        # Mensaje enriquecido
        contexto = formatear_contexto(usuario, ip, tipo)
        mensaje = f"[AUDITORIA] {contexto} | ACCION: {accion} | DETALLES: {detalles_str}"
        
        logger.info(mensaje)
    except Exception as e:
        logger.error(f"Error al registrar operacion: {e}")

def registrar_error(modulo, funcion, error, contexto="", usuario="Sistema"):
    """
    Registra un error del sistema con contexto enriquecido
    
    Args:
        modulo (str): Modulo donde ocurrio el error
        funcion (str): Funcion donde ocurrio el error
        error (str): Descripcion del error
        contexto (str): Contexto adicional
        usuario (str): Usuario cuando ocurrio el error
    """
    try:
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        ip = obtener_ip_local()
        
        mensaje = f"[ERROR] MODULO: {modulo} | FUNCION: {funcion} | USUARIO: {usuario} | IP: {ip} | ERROR: {error}"
        if contexto:
            mensaje += f" | CONTEXTO: {contexto}"
        
        logger.error(mensaje)
    except Exception as e:
        logger.error(f"Error al registrar error: {e}")

def registrar_transaccion(id_transaccion, tipo_transaccion, monto, estado, usuario="Sistema", detalles="", ip=None):
    """
    Registra una transaccion de dinero con auditoria completa
    
    Incluye: ID transaccion, tipo, monto, estado, usuario, IP, timestamp
    
    Args:
        id_transaccion (str): ID unico de transaccion
        tipo_transaccion (str): Tipo (PAGO, COOPERACION, REFUND, etc)
        monto (float): Monto de la transaccion
        estado (str): Estado (COMPLETADA, PENDIENTE, CANCELADA)
        usuario (str): Usuario que realizo la transaccion
        detalles (str): Detalles adicionales
        ip (str): IP del usuario
    """
    try:
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        # Obtener IP si no se proporciona
        if ip is None:
            ip = obtener_ip_local()
        
        contexto = formatear_contexto(usuario, ip, tipo_transaccion)
        
        mensaje = f"[TRANSACCION] {contexto} | ID: {id_transaccion} | MONTO: ${monto:.2f} | ESTADO: {estado}"
        if detalles:
            mensaje += f" | DETALLES: {detalles}"
        
        logger.info(mensaje)
    except Exception as e:
        logger.error(f"Error al registrar transaccion: {e}")

def registrar_acceso(usuario, resultado, ip=None, detalles=""):
    """
    Registra intentos de acceso al sistema con contexto completo
    
    Args:
        usuario (str): Usuario que intento acceder
        resultado (str): EXITOSO o FALLIDO
        ip (str): IP del usuario
        detalles (str): Detalles del intento
    """
    try:
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        # Obtener IP si no se proporciona
        if ip is None:
            ip = obtener_ip_local()
        
        contexto = formatear_contexto(usuario, ip)
        
        mensaje = f"[ACCESO] {contexto} | RESULTADO: {resultado}"
        if detalles:
            mensaje += f" | DETALLES: {detalles}"
        
        logger.info(mensaje)
    except Exception as e:
        logger.error(f"Error al registrar acceso: {e}")

def registrar_backup(nombre_archivo, tipo, estado, usuario="Sistema", ip=None):
    """
    Registra operaciones de backup con contexto completo
    
    Args:
        nombre_archivo (str): Nombre del archivo
        tipo (str): INICIO, COMPLETADO, FALLIDO
        estado (str): Detalles del estado
        usuario (str): Usuario que inició el backup
        ip (str): IP del usuario
    """
    try:
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        # Obtener IP si no se proporciona
        if ip is None:
            ip = obtener_ip_local()
        
        contexto = formatear_contexto(usuario, ip, "BACKUP")
        
        mensaje = f"[BACKUP] {contexto} | ARCHIVO: {nombre_archivo} | TIPO: {tipo} | ESTADO: {estado}"
        
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


# ============================================================================
# NUEVAS FUNCIONES DE LOGGING MEJORADO
# ============================================================================

def registrar_cambio_datos(tabla, operacion, id_registro, datos_antes=None, datos_despues=None, usuario="Sistema", ip=None):
    """
    Registra cambios en datos con historial antes/despues
    
    Util para auditoria de modificaciones
    
    Args:
        tabla (str): Tabla/modulo afectado (HABITANTES, PAGOS, FAENAS, etc)
        operacion (str): CREATE, UPDATE, DELETE
        id_registro (str): ID del registro afectado
        datos_antes (dict): Datos anteriores
        datos_despues (dict): Datos nuevos
        usuario (str): Usuario que hizo el cambio
        ip (str): IP del usuario
    """
    try:
        if ip is None:
            ip = obtener_ip_local()
        
        contexto = formatear_contexto(usuario, ip, operacion)
        
        mensaje = f"[CAMBIO_DATOS] {contexto} | TABLA: {tabla} | ID: {id_registro}"
        
        if datos_antes:
            datos_antes_str = " | ".join([f"{k}: {v}" for k, v in datos_antes.items()])
            mensaje += f" | ANTES: [{datos_antes_str}]"
        
        if datos_despues:
            datos_despues_str = " | ".join([f"{k}: {v}" for k, v in datos_despues.items()])
            mensaje += f" | DESPUES: [{datos_despues_str}]"
        
        logger.info(mensaje)
    except Exception as e:
        logger.error(f"Error al registrar cambio de datos: {e}")


def registrar_advertencia(titulo, descripcion, usuario="Sistema", ip=None):
    """
    Registra advertencias del sistema
    
    Args:
        titulo (str): Titulo de la advertencia
        descripcion (str): Descripcion detallada
        usuario (str): Usuario relacionado
        ip (str): IP del usuario
    """
    try:
        if ip is None:
            ip = obtener_ip_local()
        
        contexto = formatear_contexto(usuario, ip)
        
        mensaje = f"[ADVERTENCIA] {contexto} | TITULO: {titulo} | DESCRIPCION: {descripcion}"
        
        logger.warning(mensaje)
    except Exception as e:
        logger.error(f"Error al registrar advertencia: {e}")


def registrar_exportacion(tipo_exportacion, cantidad_registros, usuario="Sistema", ip=None, detalles=""):
    """
    Registra exportaciones de datos (Excel, PDF, etc)
    
    Args:
        tipo_exportacion (str): EXCEL, PDF, JSON, CSV, etc
        cantidad_registros (int): Cuantos registros fueron exportados
        usuario (str): Usuario que realizo la exportacion
        ip (str): IP del usuario
        detalles (str): Detalles adicionales
    """
    try:
        if ip is None:
            ip = obtener_ip_local()
        
        contexto = formatear_contexto(usuario, ip, f"EXPORTAR_{tipo_exportacion}")
        
        mensaje = f"[EXPORTACION] {contexto} | REGISTROS: {cantidad_registros}"
        if detalles:
            mensaje += f" | DETALLES: {detalles}"
        
        logger.info(mensaje)
    except Exception as e:
        logger.error(f"Error al registrar exportacion: {e}")


def registrar_validacion(tipo_validacion, resultado, detalles, usuario="Sistema"):
    """
    Registra intentos de validacion de datos
    
    Args:
        tipo_validacion (str): Tipo de validacion (EMAIL, MONTO, FECHA, etc)
        resultado (str): VALIDO o INVALIDO
        detalles (str): Detalles de la validacion
        usuario (str): Usuario que realizo la validacion
    """
    try:
        mensaje = f"[VALIDACION] TIPO: {tipo_validacion} | RESULTADO: {resultado} | DETALLES: {detalles} | USUARIO: {usuario}"
        logger.info(mensaje)
    except Exception as e:
        logger.error(f"Error al registrar validacion: {e}")


def obtener_estadisticas_logs():
    """
    Obtiene estadisticas de los logs
    
    Returns:
        dict: Estadisticas del archivo de log
    """
    try:
        if not os.path.exists(ARCHIVO_LOG):
            return {
                'archivo': ARCHIVO_LOG,
                'existe': False,
                'total_lineas': 0,
                'tamaño_kb': 0
            }
        
        tamaño = os.path.getsize(ARCHIVO_LOG) / 1024  # Convertir a KB
        
        with open(ARCHIVO_LOG, 'r', encoding='utf-8') as f:
            lineas = len(f.readlines())
        
        return {
            'archivo': ARCHIVO_LOG,
            'existe': True,
            'total_lineas': lineas,
            'tamaño_kb': round(tamaño, 2),
            'ultima_actualizacion': datetime.fromtimestamp(os.path.getmtime(ARCHIVO_LOG)).strftime('%d/%m/%Y %H:%M:%S')
        }
    except Exception as e:
        logger.error(f"Error al obtener estadisticas de logs: {e}")
        return {'error': str(e)}
