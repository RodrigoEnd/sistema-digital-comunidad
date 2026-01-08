"""
Modulo de validaciones centralizadas
Contiene todas las funciones de validacion del sistema
"""

from config import (
    LONGITUD_MINIMA_NOMBRE,
    LONGITUD_MAXIMA_NOMBRE,
    MONTO_MINIMO,
    MONTO_MAXIMO
)

class ErrorValidacion(Exception):
    """Excepcion para errores de validacion"""
    pass

def validar_nombre(nombre):
    """
    Valida un nombre de habitante o cooperacion
    
    Args:
        nombre (str): Nombre a validar
        
    Returns:
        str: Nombre validado y limpio
        
    Raises:
        ErrorValidacion: Si el nombre no es valido
    """
    if not isinstance(nombre, str):
        raise ErrorValidacion("El nombre debe ser texto")
    
    nombre = nombre.strip()
    
    if not nombre:
        raise ErrorValidacion("El nombre no puede estar vacio")
    
    if len(nombre) < LONGITUD_MINIMA_NOMBRE:
        raise ErrorValidacion(f"El nombre debe tener al menos {LONGITUD_MINIMA_NOMBRE} caracteres")
    
    if len(nombre) > LONGITUD_MAXIMA_NOMBRE:
        raise ErrorValidacion(f"El nombre no puede exceder {LONGITUD_MAXIMA_NOMBRE} caracteres")
    
    # Validar caracteres permitidos (letras, números, espacios, guiones, acentos)
    caracteres_validos = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -áéíóúñü')
    if not all(c in caracteres_validos for c in nombre):
        raise ErrorValidacion("El nombre contiene caracteres no permitidos")
    
    return nombre

def validar_monto(monto):
    """
    Valida un monto de dinero
    
    Args:
        monto (float): Monto a validar
        
    Returns:
        float: Monto validado
        
    Raises:
        ErrorValidacion: Si el monto no es valido
    """
    try:
        monto_float = float(monto)
    except (ValueError, TypeError):
        raise ErrorValidacion("El monto debe ser un numero valido")
    
    if monto_float < MONTO_MINIMO:
        raise ErrorValidacion(f"El monto debe ser mayor a {MONTO_MINIMO}")
    
    if monto_float > MONTO_MAXIMO:
        raise ErrorValidacion(f"El monto no puede exceder {MONTO_MAXIMO}")
    
    # Validar que no tenga más de 2 decimales
    if round(monto_float, 2) != monto_float:
        monto_float = round(monto_float, 2)
    
    return monto_float

def validar_folio(folio):
    """
    Valida un folio de habitante
    
    Args:
        folio (str): Folio a validar
        
    Returns:
        str: Folio validado
        
    Raises:
        ErrorValidacion: Si el folio no es valido
    """
    if not isinstance(folio, str):
        raise ErrorValidacion("El folio debe ser texto")
    
    folio = folio.strip().upper()
    
    if not folio:
        raise ErrorValidacion("El folio no puede estar vacio")
    
    # El folio debe tener formato HAB-XXXX
    if not folio.startswith('HAB-') or len(folio) != 8:
        raise ErrorValidacion("El folio debe tener formato HAB-XXXX")
    
    return folio

def validar_email(email):
    """
    Valida un email
    
    Args:
        email (str): Email a validar
        
    Returns:
        str: Email validado
        
    Raises:
        ErrorValidacion: Si el email no es valido
    """
    email = email.strip().lower()
    
    if not email:
        return email  # Email opcional
    
    # Validacion basica de email
    if '@' not in email or '.' not in email.split('@')[1]:
        raise ErrorValidacion("Email invalido")
    
    if len(email) > 100:
        raise ErrorValidacion("Email demasiado largo")
    
    return email

def validar_telefono(telefono):
    """
    Valida un numero de telefono
    
    Args:
        telefono (str): Telefono a validar
        
    Returns:
        str: Telefono validado
        
    Raises:
        ErrorValidacion: Si el telefono no es valido
    """
    telefono = telefono.strip()
    
    if not telefono:
        return telefono  # Telefono opcional
    
    # Solo debe contener numeros y caracteres de formato
    if not all(c.isdigit() or c in '()- ' for c in telefono):
        raise ErrorValidacion("Telefono invalido")
    
    # Remover espacios y caracteres de formato para contar digitos
    digitos = ''.join(c for c in telefono if c.isdigit())
    
    if len(digitos) < 7:
        raise ErrorValidacion("Telefono debe tener al menos 7 digitos")
    
    if len(digitos) > 15:
        raise ErrorValidacion("Telefono demasiado largo")
    
    return telefono

def validar_url(url):
    """
    Valida una URL
    
    Args:
        url (str): URL a validar
        
    Returns:
        str: URL validada
        
    Raises:
        ErrorValidacion: Si la URL no es valida
    """
    url = url.strip()
    
    if not url:
        return url  # URL opcional
    
    if not (url.startswith('http://') or url.startswith('https://')):
        raise ErrorValidacion("URL debe comenzar con http:// o https://")
    
    if len(url) > 500:
        raise ErrorValidacion("URL demasiado larga")
    
    return url

def validar_fechas(fecha_inicio, fecha_fin):
    """
    Valida que fecha_inicio sea anterior a fecha_fin
    
    Args:
        fecha_inicio (str): Fecha en formato DD/MM/YYYY
        fecha_fin (str): Fecha en formato DD/MM/YYYY
        
    Returns:
        tuple: Tupla con ambas fechas validadas
        
    Raises:
        ErrorValidacion: Si las fechas no son validas
    """
    from datetime import datetime
    
    try:
        inicio = datetime.strptime(fecha_inicio, '%d/%m/%Y')
        fin = datetime.strptime(fecha_fin, '%d/%m/%Y')
    except ValueError:
        raise ErrorValidacion("Las fechas deben estar en formato DD/MM/YYYY")
    
    if inicio > fin:
        raise ErrorValidacion("La fecha de inicio no puede ser posterior a la de fin")
    
    return fecha_inicio, fecha_fin
