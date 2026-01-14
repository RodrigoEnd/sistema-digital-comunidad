"""
Decoradores de Autenticación y Autorización
Protege métodos que requieren permisos específicos
"""

from functools import wraps
from src.core.logger import registrar_error, registrar_operacion
from src.core.gestor_usuarios_global import obtener_gestor_usuarios


def requiere_autenticacion(func):
    """
    Decorador que requiere que el usuario esté logeado
    
    Ejemplo de uso:
        @requiere_autenticacion
        def editar_monto(self, monto):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        gestor = obtener_gestor_usuarios()
        
        if not gestor.obtener_usuario_actual():
            registrar_error(
                'PROTECCIÓN',
                'requiere_autenticacion',
                f'Intento de acceso sin autenticación a {func.__name__}'
            )
            raise PermissionError("Debes estar logeado para realizar esta acción")
        
        return func(*args, **kwargs)
    
    return wrapper


def requiere_edicion(func):
    """
    Decorador que requiere permiso de edición
    
    Ejemplo de uso:
        @requiere_edicion
        def cambiar_monto(self, nuevo_monto):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        gestor = obtener_gestor_usuarios()
        
        if not gestor.puede_editar():
            usuario = gestor.obtener_usuario_actual()
            registrar_error(
                'PROTECCIÓN',
                'requiere_edicion',
                f'Usuario {usuario} intentó editar sin permisos'
            )
            raise PermissionError(
                f"No tienes permisos para editar. Tu rol es: {gestor.obtener_rol_actual()}"
            )
        
        usuario = gestor.obtener_usuario_actual()
        registrar_operacion(
            'EDICIÓN_AUTORIZADA',
            f'Edición realizada por {usuario}',
            {'funcion': func.__name__}
        )
        
        return func(*args, **kwargs)
    
    return wrapper


def requiere_pago(func):
    """Decorador que requiere permiso para registrar pagos"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        gestor = obtener_gestor_usuarios()
        
        if not gestor.puede_pagar():
            usuario = gestor.obtener_usuario_actual()
            registrar_error(
                'PROTECCIÓN',
                'requiere_pago',
                f'Usuario {usuario} intentó registrar pago sin permisos'
            )
            raise PermissionError(
                f"No tienes permisos para registrar pagos. Tu rol es: {gestor.obtener_rol_actual()}"
            )
        
        usuario = gestor.obtener_usuario_actual()
        registrar_operacion(
            'PAGO_AUTORIZADO',
            f'Pago registrado por {usuario}',
            {'funcion': func.__name__}
        )
        
        return func(*args, **kwargs)
    
    return wrapper


def requiere_admin(func):
    """Decorador que requiere rol de administrador"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        gestor = obtener_gestor_usuarios()
        
        if gestor.obtener_rol_actual() != 'admin':
            usuario = gestor.obtener_usuario_actual()
            registrar_error(
                'PROTECCIÓN',
                'requiere_admin',
                f'Usuario {usuario} intentó acceso admin sin permisos'
            )
            raise PermissionError("Requiere rol de administrador")
        
        usuario = gestor.obtener_usuario_actual()
        registrar_operacion(
            'ACCIÓN_ADMIN',
            f'Acción administrativa realizada por {usuario}',
            {'funcion': func.__name__}
        )
        
        return func(*args, **kwargs)
    
    return wrapper


def requiere_lectura(func):
    """Decorador que requiere al menos permiso de lectura"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        gestor = obtener_gestor_usuarios()
        
        if not gestor.puede_ver():
            usuario = gestor.obtener_usuario_actual()
            registrar_error(
                'PROTECCIÓN',
                'requiere_lectura',
                f'Usuario {usuario} intentó leer sin permisos'
            )
            raise PermissionError("No tienes permisos de lectura")
        
        return func(*args, **kwargs)
    
    return wrapper


def auditoria(accion):
    """
    Decorador que registra todas las acciones en auditoría
    
    Ejemplo de uso:
        @auditoria('CAMBIO_MONTO_COOPERACION')
        def cambiar_monto(self, nuevo_monto):
            ...
    """
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            gestor = obtener_gestor_usuarios()
            usuario = gestor.obtener_usuario_actual()
            
            try:
                resultado = func(*args, **kwargs)
                registrar_operacion(
                    accion,
                    f'Acción realizada: {func.__name__}',
                    {
                        'usuario': usuario,
                        'rol': gestor.obtener_rol_actual(),
                        'funcion': func.__name__
                    }
                )
                return resultado
            except Exception as e:
                registrar_error(
                    accion,
                    f'Error en {func.__name__}: {str(e)}',
                    {'usuario': usuario}
                )
                raise
        
        return wrapper
    return decorador
