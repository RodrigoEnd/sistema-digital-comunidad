"""
Sistema de autenticacion y manejo de usuarios
Gestiona login, sesiones y control de acceso - Usa SQLite
"""

import json
import os
from datetime import datetime, timedelta
import bcrypt
from src.config import RUTA_SEGURA
from src.core.logger import registrar_acceso, registrar_operacion, registrar_error
from src.core.base_datos_sqlite import obtener_bd

class GestorAutenticacion:
    """Gestor de autenticacion de usuarios con SQLite"""
    
    # Roles disponibles del sistema
    ROLES = {
        'admin': {'nombre': 'Administrador', 'permisos': ['*']},  # Todos los permisos
        'operador': {'nombre': 'Operador', 'permisos': ['ver', 'crear', 'editar', 'pagar']},
        'lectura': {'nombre': 'Solo Lectura', 'permisos': ['ver']},
        'reportes': {'nombre': 'Reportes', 'permisos': ['ver', 'exportar']}
    }
    
    def __init__(self):
        self.bd = obtener_bd()
        self.archivo_sesiones = os.path.join(RUTA_SEGURA, 'sesiones.json')
        self.sesiones = self._cargar_sesiones()
    
    def _cargar_usuarios(self):
        """Carga usuarios de SQLite"""
        return self.bd.obtener_usuarios()
    
    @property
    def usuarios(self):
        """Propiedad para obtener usuarios actuales"""
        return self._cargar_usuarios()
    
    def _cargar_usuarios(self):
        """Carga usuarios de SQLite"""
        return self.bd.obtener_usuarios()
    
    def _guardar_usuarios(self):
        """En SQLite los usuarios se guardan automáticamente"""
        pass
    
    def _cargar_sesiones(self):
        """Carga sesiones desde archivo"""
        try:
            if os.path.exists(self.archivo_sesiones):
                with open(self.archivo_sesiones, 'r', encoding='utf-8') as f:
                    sesiones = json.load(f)
                    # Limpiar sesiones expiradas
                    self._limpiar_sesiones_expiradas(sesiones)
                    return sesiones
        except Exception as e:
            registrar_error('autenticacion', 'cargar_sesiones', str(e))
        return {}
    
    def _guardar_sesiones(self):
        """Guarda sesiones en archivo"""
        try:
            with open(self.archivo_sesiones, 'w', encoding='utf-8') as f:
                json.dump(self.sesiones, f, indent=2, ensure_ascii=False)
            
            # Ocultar archivo
            try:
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                ctypes.windll.kernel32.SetFileAttributesW(self.archivo_sesiones, FILE_ATTRIBUTE_HIDDEN)
            except:
                pass
        except Exception as e:
            registrar_error('autenticacion', 'guardar_sesiones', str(e))
    
    def _limpiar_sesiones_expiradas(self, sesiones):
        """Elimina sesiones expiradas"""
        sesiones_a_eliminar = []
        for token, sesion in sesiones.items():
            try:
                expiracion = datetime.fromisoformat(sesion.get('expiracion'))
                if datetime.now() > expiracion:
                    sesiones_a_eliminar.append(token)
            except:
                sesiones_a_eliminar.append(token)
        
        for token in sesiones_a_eliminar:
            del sesiones[token]
    
    def _crear_usuario_predeterminado(self):
        """Crea usuario admin predeterminado en primera instalación"""
        pass  # SQLite ya lo crea automáticamente
    
    def crear_usuario(self, usuario, contraseña, nombre_completo="", rol='operador', email=''):
        """Crea un nuevo usuario en SQLite"""
        try:
            # Validaciones
            if len(usuario) < 3:
                return {'exito': False, 'error': 'El usuario debe tener al menos 3 caracteres'}
            
            if len(contraseña) < 6:
                return {'exito': False, 'error': 'La contraseña debe tener al menos 6 caracteres'}
            
            if rol not in self.ROLES:
                return {'exito': False, 'error': f'Rol inválido: {rol}'}
            
            # Crear usuario en SQLite
            exito, mensaje = self.bd.crear_usuario(usuario, contraseña, email, rol)
            
            if exito:
                registrar_operacion('CREAR_USUARIO', f'Usuario {usuario} creado', {'usuario': usuario, 'rol': rol})
                return {'exito': True, 'mensaje': f'Usuario {usuario} creado correctamente'}
            else:
                return {'exito': False, 'error': mensaje}
            
        except Exception as e:
            registrar_error('autenticacion', 'crear_usuario', str(e))
            return {'exito': False, 'error': str(e)}
    
    def login(self, usuario, contraseña):
        """Intenta hacer login contra SQLite"""
        try:
            usuario_datos = self.bd.obtener_usuario(usuario)
            
            if not usuario_datos:
                registrar_acceso(usuario, 'FALLIDO - Usuario no existe')
                return {'exito': False, 'error': 'Usuario o contraseña incorrectos'}
            
            if not usuario_datos.get('activo'):
                registrar_acceso(usuario, 'FALLIDO - Usuario inactivo')
                return {'exito': False, 'error': 'Usuario inactivo'}
            
            # Verificar contraseña (usando SHA256)
            import hashlib
            hash_ingresado = hashlib.sha256(contraseña.encode()).hexdigest()
            
            if hash_ingresado != usuario_datos['contraseña']:
                registrar_acceso(usuario, 'FALLIDO - Contraseña incorrecta')
                return {'exito': False, 'error': 'Usuario o contraseña incorrectos'}
            
            # Crear sesion
            token = self._generar_token()
            expiracion = (datetime.now() + timedelta(hours=8)).isoformat()
            
            self.sesiones[token] = {
                'usuario': usuario,
                'rol': usuario_datos['rol'],
                'inicio': datetime.now().isoformat(),
                'expiracion': expiracion
            }
            
            self._guardar_sesiones()
            
            registrar_acceso(usuario, 'EXITOSO')
            
            return {
                'exito': True,
                'token': token,
                'usuario': usuario,
                'rol': usuario_datos['rol']
            }
            
        except Exception as e:
            registrar_error('autenticacion', 'login', str(e))
            return {'exito': False, 'error': str(e)}
    
    def verificar_sesion(self, token):
        """
        Verifica si un token de sesion es valido
        
        Args:
            token (str): Token de sesion
            
        Returns:
            dict: Informacion de sesion si es valida
        """
        if token not in self.sesiones:
            return None
        
        sesion = self.sesiones[token]
        
        try:
            expiracion = datetime.fromisoformat(sesion['expiracion'])
            if datetime.now() > expiracion:
                del self.sesiones[token]
                self._guardar_sesiones()
                return None
        except:
            return None
        
        return sesion
    
    def cerrar_sesion(self, token):
        """Cierra una sesion"""
        if token in self.sesiones:
            usuario = self.sesiones[token]['usuario']
            del self.sesiones[token]
            self._guardar_sesiones()
            registrar_operacion('CERRAR_SESION', f'Sesion cerrada para {usuario}', {})
            return True
        return False
    
    def cambiar_contraseña(self, usuario, contraseña_actual, contraseña_nueva):
        """
        Cambia la contraseña de un usuario
        
        Args:
            usuario (str): Nombre de usuario
            contraseña_actual (str): Contraseña actual
            contraseña_nueva (str): Nueva contraseña
            
        Returns:
            dict: Resultado del cambio
        """
        try:
            if usuario not in self.usuarios:
                return {'exito': False, 'error': 'Usuario no existe'}
            
            user_data = self.usuarios[usuario]
            
            # Verificar contraseña actual
            hash_almacenado = user_data['contraseña_hash'].encode()
            if not bcrypt.checkpw(contraseña_actual.encode(), hash_almacenado):
                return {'exito': False, 'error': 'Contraseña actual incorrecta'}
            
            # Validar nueva contraseña
            if len(contraseña_nueva) < 6:
                return {'exito': False, 'error': 'La nueva contraseña debe tener al menos 6 caracteres'}
            
            # Actualizar contraseña
            nuevo_hash = bcrypt.hashpw(contraseña_nueva.encode(), bcrypt.gensalt(rounds=12))
            self.usuarios[usuario]['contraseña_hash'] = nuevo_hash.decode()
            
            self._guardar_usuarios()
            registrar_operacion('CAMBIO_CONTRASEÑA', f'Contraseña cambiada para {usuario}', {})
            
            return {'exito': True, 'mensaje': 'Contraseña actualizada correctamente'}
            
        except Exception as e:
            registrar_error('autenticacion', 'cambiar_contraseña', str(e), f'usuario: {usuario}')
            return {'exito': False, 'error': str(e)}
    
    def _generar_token(self):
        """Genera un token de sesion aleatorio"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def verificar_permiso(self, token, permiso):
        """
        Verifica si una sesion tiene un permiso especifico
        
        Args:
            token (str): Token de sesion
            permiso (str): Permiso a verificar
            
        Returns:
            bool: True si tiene permiso
        """
        sesion = self.verificar_sesion(token)
        if not sesion:
            return False
        
        rol = sesion.get('rol')
        if rol not in self.ROLES:
            return False
        
        permisos = self.ROLES[rol]['permisos']
        return '*' in permisos or permiso in permisos

# Instancia global
gestor_auth = GestorAutenticacion()
