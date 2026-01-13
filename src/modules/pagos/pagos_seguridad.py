"""
Módulo de gestión de seguridad y permisos para pagos
Responsable de: validar permisos, gestionar contraseñas, auditoría
"""

from src.auth.seguridad import seguridad
from src.core.logger import registrar_operacion, registrar_error


class GestorSeguridad:
    """Gestor de seguridad para el módulo de pagos"""
    
    def __init__(self, gestor_auth=None):
        self.gestor_auth = gestor_auth
        self.usuario_actual = None
        self.permisos_rol = {}
    
    def establecer_usuario(self, usuario, gestor_auth):
        """Establecer usuario autenticado actual"""
        self.usuario_actual = usuario
        self.gestor_auth = gestor_auth
        self.permisos_rol = gestor_auth.ROLES if gestor_auth else {}
        
        registrar_operacion(
            'USUARIO_ESTABLECIDO',
            f'Usuario {usuario["nombre"]} establecido en módulo de pagos',
            {'rol': usuario['rol']}
        )
    
    def tiene_permiso(self, permiso):
        """
        Verifica si el usuario actual tiene un permiso
        
        Args:
            permiso: nombre del permiso a verificar
        
        Returns:
            bool
        """
        if not self.usuario_actual:
            return False
        
        rol = self.usuario_actual.get('rol')
        if not rol or rol not in self.permisos_rol:
            return False
        
        permisos = self.permisos_rol[rol].get('permisos', [])
        
        # Permisos con comodín o específicos
        return '*' in permisos or permiso in permisos
    
    def obtener_rol_actual(self):
        """Obtener rol del usuario actual"""
        if self.usuario_actual:
            return self.usuario_actual.get('rol', 'desconocido')
        return None
    
    def obtener_usuario_actual(self):
        """Obtener usuario actual"""
        return self.usuario_actual
    
    def obtener_nombre_usuario(self):
        """Obtener nombre del usuario actual"""
        if self.usuario_actual:
            return self.usuario_actual.get('nombre', 'Desconocido')
        return 'No autenticado'
    
    def hash_password(self, password):
        """Crear hash seguro de contraseña"""
        return seguridad.hash_password(password).decode('utf-8')
    
    def verificar_password(self, password, password_hash):
        """Verificar contraseña contra hash"""
        try:
            return seguridad.verificar_password(password, password_hash.encode('utf-8'))
        except:
            return False
    
    def registrar_accion_usuario(self, accion, detalles=None):
        """Registrar una acción del usuario actual"""
        usuario_nombre = self.obtener_nombre_usuario()
        registrar_operacion(
            accion,
            f'Acción ejecutada por {usuario_nombre}',
            detalles or {},
            usuario_nombre
        )
    
    def obtener_permiso_descriptivo(self, permiso):
        """Obtener descripción legible de un permiso"""
        descriptivos = {
            'crear': 'Crear personas y cooperaciones',
            'editar': 'Editar datos existentes',
            'pagar': 'Registrar pagos',
            'eliminar': 'Eliminar personas',
            'exportar': 'Exportar datos',
            'visualizar': 'Ver datos',
        }
        return descriptivos.get(permiso, permiso)
    
    def obtener_permisos_usuario(self):
        """Obtener lista de permisos del usuario actual"""
        rol = self.obtener_rol_actual()
        if not rol or rol not in self.permisos_rol:
            return []
        
        permisos = self.permisos_rol[rol].get('permisos', [])
        
        if '*' in permisos:
            # Todos los permisos
            return [
                'crear', 'editar', 'pagar', 'eliminar',
                'exportar', 'visualizar'
            ]
        
        return permisos
    
    def validar_acceso_cooperacion(self, coop_id):
        """
        Validar que el usuario tenga acceso a una cooperación
        Por ahora, todos los usuarios ven todas las cooperaciones
        Puede extenderse para implementar restricciones
        
        Returns:
            bool
        """
        return self.usuario_actual is not None
    
    def obtener_nivel_seguridad(self):
        """
        Obtener nivel de seguridad del usuario
        
        Returns:
            str: 'admin', 'editor', 'viewer'
        """
        rol = self.obtener_rol_actual()
        
        if not rol:
            return 'viewer'
        
        permisos = self.obtener_permisos_usuario()
        
        if 'eliminar' in permisos and '*' in permisos:
            return 'admin'
        elif 'editar' in permisos:
            return 'editor'
        else:
            return 'viewer'
    
    def auditar_operacion_sensible(self, operacion, detalles, resultado):
        """Auditar operación sensible (eliminar, cambiar contraseña, etc)"""
        usuario = self.obtener_nombre_usuario()
        
        registrar_operacion(
            f'AUDITORIA_{operacion}',
            f'Operación sensible por {usuario}',
            {
                'usuario': usuario,
                'rol': self.obtener_rol_actual(),
                'operacion': operacion,
                'detalles': detalles,
                'resultado': resultado
            }
        )
