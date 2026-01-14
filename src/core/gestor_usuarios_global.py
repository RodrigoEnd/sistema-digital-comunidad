"""
Gestor Global de Usuarios y Autenticación
Proporciona credenciales globales para toda la aplicación
"""

import hashlib
from datetime import datetime
from src.core.base_datos_sqlite import obtener_bd
from src.core.logger import registrar_operacion, registrar_error


class GestorUsuariosGlobal:
    """Gestor centralizado de usuarios y autenticación global"""
    
    def __init__(self):
        self.bd = obtener_bd()
        self.usuario_actual = None
        self.rol_actual = None
        self.token_sesion = None
    
    def login(self, nombre_usuario, contraseña):
        """
        Autenticar usuario y crear sesión global
        
        Args:
            nombre_usuario: Nombre del usuario
            contraseña: Contraseña en texto plano
        
        Returns:
            dict con resultado de login y datos del usuario
        """
        try:
            usuario = self.bd.obtener_usuario(nombre_usuario)
            
            if not usuario:
                registrar_error('GestorUsuariosGlobal', 'login', f'Usuario no existe: {nombre_usuario}')
                return {'exito': False, 'error': 'Usuario o contraseña incorrectos'}
            
            if not usuario.get('activo'):
                registrar_error('GestorUsuariosGlobal', 'login', f'Usuario inactivo: {nombre_usuario}')
                return {'exito': False, 'error': 'Usuario inactivo'}
            
            # Verificar contraseña
            hash_ingresado = hashlib.sha256(contraseña.encode()).hexdigest()
            if hash_ingresado != usuario.get('contraseña'):
                registrar_error('GestorUsuariosGlobal', 'login', f'Contraseña incorrecta: {nombre_usuario}')
                return {'exito': False, 'error': 'Usuario o contraseña incorrectos'}
            
            # Crear sesión
            self.usuario_actual = nombre_usuario
            self.rol_actual = usuario.get('rol', 'delegado')
            self.token_sesion = hashlib.sha256(
                f"{nombre_usuario}{datetime.now().isoformat()}".encode()
            ).hexdigest()
            
            registrar_operacion(
                'LOGIN',
                f'Usuario logeado: {nombre_usuario}',
                {'usuario': nombre_usuario, 'rol': self.rol_actual}
            )
            
            return {
                'exito': True,
                'usuario': nombre_usuario,
                'rol': self.rol_actual,
                'email': usuario.get('email', ''),
                'token': self.token_sesion
            }
        
        except Exception as e:
            registrar_error('GestorUsuariosGlobal', 'login', str(e))
            return {'exito': False, 'error': str(e)}
    
    def logout(self):
        """Cerrar sesión actual"""
        usuario = self.usuario_actual
        self.usuario_actual = None
        self.rol_actual = None
        self.token_sesion = None
        
        if usuario:
            registrar_operacion('LOGOUT', f'Usuario cerró sesión: {usuario}', {'usuario': usuario})
    
    def obtener_usuario_actual(self):
        """Obtener nombre del usuario logeado"""
        return self.usuario_actual
    
    def obtener_rol_actual(self):
        """Obtener rol del usuario logeado"""
        return self.rol_actual
    
    def tiene_permiso(self, permiso):
        """
        Verificar si el usuario actual tiene un permiso específico
        
        Args:
            permiso: Nombre del permiso a verificar
        
        Returns:
            bool - True si tiene permiso, False si no
        """
        if not self.usuario_actual:
            return False
        
        # Admin tiene todos los permisos
        if self.rol_actual == 'admin':
            return True
        
        # Operador tiene permisos de edición
        if self.rol_actual == 'operador':
            return permiso in ['ver', 'crear', 'editar', 'pagar']
        
        # Lectura tiene solo permiso de ver
        if self.rol_actual == 'lectura':
            return permiso == 'ver'
        
        return False
    
    def puede_editar(self):
        """Verificar si usuario actual puede editar datos"""
        return self.tiene_permiso('editar')
    
    def puede_pagar(self):
        """Verificar si usuario actual puede registrar pagos"""
        return self.tiene_permiso('pagar')
    
    def puede_crear(self):
        """Verificar si usuario actual puede crear registros"""
        return self.tiene_permiso('crear')
    
    def puede_ver(self):
        """Verificar si usuario actual puede ver datos"""
        return self.tiene_permiso('ver')
    
    def crear_usuario(self, nombre_usuario, contraseña, email='', rol='operador'):
        """
        Crear nuevo usuario
        
        Args:
            nombre_usuario: Nombre único del usuario
            contraseña: Contraseña en texto plano
            email: Email del usuario
            rol: Rol del usuario (admin, operador, lectura, reportes)
        
        Returns:
            dict con resultado
        """
        # Solo admin puede crear usuarios
        if self.rol_actual != 'admin':
            return {'exito': False, 'error': 'No tienes permisos para crear usuarios'}
        
        exito, mensaje = self.bd.crear_usuario(nombre_usuario, contraseña, email, rol)
        
        if exito:
            registrar_operacion(
                'CREAR_USUARIO',
                f'Usuario creado: {nombre_usuario}',
                {'usuario': nombre_usuario, 'rol': rol}
            )
        
        return {'exito': exito, 'mensaje': mensaje}
    
    def obtener_usuarios(self):
        """Obtener lista de usuarios activos"""
        return self.bd.obtener_usuarios(activos_solo=True)
    
    def cambiar_contraseña(self, nombre_usuario, contraseña_actual, contraseña_nueva):
        """
        Cambiar contraseña de un usuario
        
        Args:
            nombre_usuario: Usuario cuya contraseña cambiar
            contraseña_actual: Contraseña actual para validación
            contraseña_nueva: Nueva contraseña
        
        Returns:
            dict con resultado
        """
        # Validar permisos
        if self.usuario_actual != nombre_usuario and self.rol_actual != 'admin':
            return {'exito': False, 'error': 'No tienes permisos para cambiar esta contraseña'}
        
        # Validar contraseña actual si no es admin
        if self.rol_actual != 'admin':
            usuario = self.bd.obtener_usuario(nombre_usuario)
            hash_actual = hashlib.sha256(contraseña_actual.encode()).hexdigest()
            if hash_actual != usuario.get('contraseña'):
                return {'exito': False, 'error': 'Contraseña actual incorrecta'}
        
        exito, mensaje = self.bd.actualizar_contraseña(nombre_usuario, contraseña_nueva)
        
        if exito:
            registrar_operacion(
                'CAMBIAR_CONTRASEÑA',
                f'Contraseña cambiada: {nombre_usuario}',
                {'usuario': nombre_usuario}
            )
        
        return {'exito': exito, 'mensaje': mensaje}
    
    def validar_sesion(self, token):
        """
        Validar que un token de sesión sea válido
        
        Args:
            token: Token de sesión a validar
        
        Returns:
            bool - True si es válido
        """
        return token == self.token_sesion and self.usuario_actual is not None


# Instancia global única
_instancia_global = None


def obtener_gestor_usuarios():
    """Obtener instancia global del gestor de usuarios"""
    global _instancia_global
    if _instancia_global is None:
        _instancia_global = GestorUsuariosGlobal()
    return _instancia_global
