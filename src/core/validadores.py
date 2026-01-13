"""
Modulo de validaciones centralizadas
Contiene todas las funciones de validacion del sistema
Proporciona validacion robusta para entrada de datos en todos los modulos
"""

import re
from datetime import datetime
from src.config import (
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
    Valida un monto de dinero de forma robusta
    
    BUG FIX #2: Ahora rechaza montos cero y negativos explícitamente
    
    Args:
        monto (float): Monto a validar
        
    Returns:
        float: Monto validado (redondeado a 2 decimales)
        
    Raises:
        ErrorValidacion: Si el monto no es valido
        
    Validaciones:
        ✓ Debe ser un número válido
        ✓ DEBE ser positivo (> 0)
        ✓ NO puede ser cero
        ✓ NO puede ser negativo
        ✓ Debe estar entre MONTO_MINIMO y MONTO_MAXIMO
        ✓ No puede tener más de 2 decimales
    """
    # 1. Validar que sea un número válido
    try:
        monto_float = float(monto)
    except (ValueError, TypeError):
        raise ErrorValidacion("El monto debe ser un número válido")
    
    # 2. VALIDACIÓN CRÍTICA: Rechazar números negativos
    if monto_float < 0:
        raise ErrorValidacion("El monto no puede ser negativo")
    
    # 3. VALIDACIÓN CRÍTICA: Rechazar cero
    if monto_float == 0:
        raise ErrorValidacion("El monto debe ser mayor a $0.00")
    
    # 4. Validar contra límite mínimo
    if monto_float < MONTO_MINIMO:
        raise ErrorValidacion(f"El monto debe ser mayor o igual a ${MONTO_MINIMO:.2f}")
    
    # 5. Validar contra límite máximo
    if monto_float > MONTO_MAXIMO:
        raise ErrorValidacion(f"El monto no puede exceder ${MONTO_MAXIMO:.2f}")
    
    # 6. Redondear a 2 decimales (evitar errores de precisión flotante)
    monto_float = round(monto_float, 2)
    
    # 7. Validar que tenga máximo 2 decimales
    if len(str(monto_float).split('.')[-1]) > 2:
        raise ErrorValidacion("El monto no puede tener más de 2 decimales")
    
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
    try:
        inicio = datetime.strptime(fecha_inicio, '%d/%m/%Y')
        fin = datetime.strptime(fecha_fin, '%d/%m/%Y')
    except ValueError:
        raise ErrorValidacion("Las fechas deben estar en formato DD/MM/YYYY")
    
    if inicio > fin:
        raise ErrorValidacion("La fecha de inicio no puede ser posterior a la de fin")
    
    return fecha_inicio, fecha_fin


# ============================================================================
# VALIDACIONES ADICIONALES ROBUSTAS - NUEVAS FUNCIONES
# ============================================================================

def validar_edad(edad):
    """
    Valida la edad de una persona con rango razonable
    
    Args:
        edad (int): Edad a validar
        
    Returns:
        int: Edad validada
        
    Raises:
        ErrorValidacion: Si la edad no es valida
    """
    try:
        edad_int = int(edad)
    except (ValueError, TypeError):
        raise ErrorValidacion("La edad debe ser un numero entero")
    
    if edad_int < 0:
        raise ErrorValidacion("La edad no puede ser negativa")
    
    if edad_int > 120:
        raise ErrorValidacion("La edad no puede exceder 120 anos")
    
    if edad_int < 1:
        raise ErrorValidacion("La edad debe ser mayor a 0")
    
    return edad_int


def validar_genero(genero):
    """
    Valida el genero de una persona
    
    Args:
        genero (str): Genero a validar (M, F, O, N/A)
        
    Returns:
        str: Genero validado en mayuscula
        
    Raises:
        ErrorValidacion: Si el genero no es valido
    """
    if not isinstance(genero, str):
        raise ErrorValidacion("El genero debe ser texto")
    
    genero = genero.strip().upper()
    
    generos_validos = ['M', 'F', 'O', 'N/A']
    
    if genero not in generos_validos:
        raise ErrorValidacion(f"Genero invalido. Valores permitidos: {', '.join(generos_validos)}")
    
    return genero


def validar_campo_obligatorio(valor, nombre_campo):
    """
    Valida que un campo obligatorio no este vacio
    
    Args:
        valor: Valor a validar
        nombre_campo (str): Nombre del campo para mensaje de error
        
    Returns:
        El valor si es valido
        
    Raises:
        ErrorValidacion: Si el valor esta vacio
    """
    if valor is None:
        raise ErrorValidacion(f"{nombre_campo} es obligatorio")
    
    if isinstance(valor, str) and not valor.strip():
        raise ErrorValidacion(f"{nombre_campo} es obligatorio")
    
    return valor


def validar_rango_numerico(valor, minimo, maximo, nombre_campo):
    """
    Valida que un numero este dentro de un rango
    
    Args:
        valor: Numero a validar
        minimo: Valor minimo permitido
        maximo: Valor maximo permitido
        nombre_campo (str): Nombre del campo para mensaje de error
        
    Returns:
        El valor validado
        
    Raises:
        ErrorValidacion: Si el valor esta fuera de rango
    """
    try:
        valor_num = float(valor)
    except (ValueError, TypeError):
        raise ErrorValidacion(f"{nombre_campo} debe ser un numero valido")
    
    if valor_num < minimo:
        raise ErrorValidacion(f"{nombre_campo} no puede ser menor a {minimo}")
    
    if valor_num > maximo:
        raise ErrorValidacion(f"{nombre_campo} no puede ser mayor a {maximo}")
    
    return valor_num


def validar_largo_string(valor, minimo, maximo, nombre_campo):
    """
    Valida que un string tenga una longitud dentro de rango
    
    Args:
        valor (str): String a validar
        minimo (int): Longitud minima permitida
        maximo (int): Longitud maxima permitida
        nombre_campo (str): Nombre del campo para mensaje de error
        
    Returns:
        str: El valor validado
        
    Raises:
        ErrorValidacion: Si la longitud esta fuera de rango
    """
    if not isinstance(valor, str):
        raise ErrorValidacion(f"{nombre_campo} debe ser texto")
    
    valor = valor.strip()
    largo = len(valor)
    
    if largo < minimo:
        raise ErrorValidacion(f"{nombre_campo} debe tener al menos {minimo} caracteres")
    
    if largo > maximo:
        raise ErrorValidacion(f"{nombre_campo} no puede exceder {maximo} caracteres")
    
    return valor


def validar_estado_pago(estado):
    """
    Valida el estado de un pago
    
    Args:
        estado (str): Estado a validar
        
    Returns:
        str: Estado validado en minuscula
        
    Raises:
        ErrorValidacion: Si el estado no es valido
    """
    if not isinstance(estado, str):
        raise ErrorValidacion("El estado debe ser texto")
    
    estado = estado.strip().lower()
    
    estados_validos = ['pendiente', 'parcial', 'completo', 'pagado']
    
    if estado not in estados_validos:
        raise ErrorValidacion(f"Estado invalido. Valores permitidos: {', '.join(estados_validos)}")
    
    return estado


def validar_fecha_formato(fecha):
    """
    Valida que una fecha este en formato DD/MM/YYYY
    
    Args:
        fecha (str): Fecha a validar
        
    Returns:
        str: Fecha validada
        
    Raises:
        ErrorValidacion: Si la fecha no es valida
    """
    if not isinstance(fecha, str):
        raise ErrorValidacion("La fecha debe ser texto")
    
    fecha = fecha.strip()
    
    try:
        datetime.strptime(fecha, '%d/%m/%Y')
    except ValueError:
        raise ErrorValidacion("La fecha debe estar en formato DD/MM/YYYY")
    
    return fecha


def validar_fecha_no_futura(fecha):
    """
    Valida que una fecha no sea posterior a hoy
    
    Args:
        fecha (str): Fecha en formato DD/MM/YYYY
        
    Returns:
        str: Fecha validada
        
    Raises:
        ErrorValidacion: Si la fecha es futura
    """
    fecha_validada = validar_fecha_formato(fecha)
    fecha_obj = datetime.strptime(fecha_validada, '%d/%m/%Y')
    
    if fecha_obj.date() > datetime.now().date():
        raise ErrorValidacion("La fecha no puede ser posterior a hoy")
    
    return fecha_validada


def validar_no_caracteres_especiales(valor, nombre_campo, excepciones=''):
    """
    Valida que un string no contenga caracteres especiales peligrosos
    
    Args:
        valor (str): String a validar
        nombre_campo (str): Nombre del campo para mensaje de error
        excepciones (str): Caracteres especiales permitidos (ej: '-.')
        
    Returns:
        str: El valor validado
        
    Raises:
        ErrorValidacion: Si contiene caracteres peligrosos
    """
    if not isinstance(valor, str):
        raise ErrorValidacion(f"{nombre_campo} debe ser texto")
    
    caracteres_peligrosos = r'[<>\"\'%;()&+]'
    if excepciones:
        excepciones_escape = re.escape(excepciones)
        caracteres_peligrosos = f'[<>\"\'%;()&+](?![{excepciones_escape}])'
    
    if re.search(caracteres_peligrosos, valor):
        raise ErrorValidacion(f"{nombre_campo} contiene caracteres no permitidos")
    
    return valor


def validar_entrada_dict(datos, campos_requeridos):
    """
    Valida que un diccionario tenga todos los campos requeridos
    
    Args:
        datos (dict): Diccionario a validar
        campos_requeridos (list): Lista de campos que deben estar presentes
        
    Returns:
        dict: El diccionario validado
        
    Raises:
        ErrorValidacion: Si faltan campos o el diccionario es invalido
    """
    if not isinstance(datos, dict):
        raise ErrorValidacion("Los datos deben ser un diccionario")
    
    campos_faltantes = []
    for campo in campos_requeridos:
        if campo not in datos or datos[campo] is None:
            campos_faltantes.append(campo)
        elif isinstance(datos[campo], str) and not datos[campo].strip():
            campos_faltantes.append(campo)
    
    if campos_faltantes:
        raise ErrorValidacion(f"Campos obligatorios faltantes: {', '.join(campos_faltantes)}")
    
    return datos


def sanitizar_entrada(valor):
    """
    Sanitiza una entrada de usuario quitando espacios excesivos y caracteres problematicos
    
    Args:
        valor (str): Valor a sanitizar
        
    Returns:
        str: Valor sanitizado
    """
    if not isinstance(valor, str):
        return valor
    
    # Remover espacios al inicio y final
    valor = valor.strip()
    
    # Reemplazar multiples espacios con un solo espacio
    valor = re.sub(r'\s+', ' ', valor)
    
    return valor
