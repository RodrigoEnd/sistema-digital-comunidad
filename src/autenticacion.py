"""
Sistema de autenticacion y manejo de usuarios
Gestiona login, sesiones y control de acceso
"""

import json
import os
from datetime import datetime, timedelta
import bcrypt
from config import RUTA_SEGURA
from logger import registrar_acceso, registrar_operacion, registrar_error

class GestorAutenticacion:
    """Gestor de autenticacion de usuarios"""
    
    # Roles disponibles del sistema
    ROLES = {
        'admin': {'nombre': 'Administrador', 'permisos': ['*']},  # Todos los permisos
        'operador': {'nombre': 'Operador', 'permisos': ['ver', 'crear', 'editar', 'pagar']},
        'lectura': {'nombre': 'Solo Lectura', 'permisos': ['ver']},
        'reportes': {'nombre': 'Reportes', 'permisos': ['ver', 'exportar']}
    }
    
    def __init__(self):
        self.archivo_usuarios = os.path.join(RUTA_SEGURA, 'usuarios.json')
        self.archivo_sesiones = os.path.join(RUTA_SEGURA, 'sesiones.json')
        self.usuarios = self._cargar_usuarios()
        self.sesiones = self._cargar_sesiones()
        
        # Crear usuario admin por defecto si no existen usuarios
        if not self.usuarios:
            self._crear_usuario_predeterminado()
    
    def _cargar_usuarios(self):
        """Carga usuarios desde archivo"""
        try:
            if os.path.exists(self.archivo_usuarios):
                with open(self.archivo_usuarios, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            registrar_error('autenticacion', 'cargar_usuarios', str(e))
        return {}
    
    def _guardar_usuarios(self):
        """Guarda usuarios en archivo"""
        try:
            with open(self.archivo_usuarios, 'w', encoding='utf-8') as f:
                json.dump(self.usuarios, f, indent=2, ensure_ascii=False)
            
            # Ocultar archivo
            try:
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                ctypes.windll.kernel32.SetFileAttributesW(self.archivo_usuarios, FILE_ATTRIBUTE_HIDDEN)
            except:
                pass
        except Exception as e:
            registrar_error('autenticacion', 'guardar_usuarios', str(e))
    
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
        """Crea usuario admin predeterminado en primera instalacion"""
        usuario = 'admin'
        contraseña = 'admin123'
        
        hash_contraseña = bcrypt.hashpw(contraseña.encode(), bcrypt.gensalt(rounds=12))
        
        self.usuarios[usuario] = {
            'nombre_completo': 'Administrador del Sistema',
            'contraseña_hash': hash_contraseña.decode(),
            'rol': 'admin',
            'email': 'admin@sistemacomunidad.local',
            'activo': True,
            'fecha_creacion': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'ultimo_acceso': None
        }
        
        self._guardar_usuarios()
        registrar_operacion('CREACION_USUARIO', 'Usuario admin creado automáticamente', {'usuario': usuario})
    
    def crear_usuario(self, usuario, contraseña, nombre_completo, rol='operador', email=''):
        """
        Crea un nuevo usuario
        
        Args:
            usuario (str): Nombre de usuario unico
            contraseña (str): Contraseña en texto plano
            nombre_completo (str): Nombre completo del usuario
            rol (str): Rol del usuario (admin, operador, lectura, reportes)
            email (str): Email del usuario
            
        Returns:
            dict: Resultado de la creacion
        """
        try:
            # Validaciones
            if usuario in self.usuarios:
                return {'exito': False, 'error': 'El usuario ya existe'}
            
            if len(usuario) < 3:
                return {'exito': False, 'error': 'El usuario debe tener al menos 3 caracteres'}
            
            if len(contraseña) < 6:
                return {'exito': False, 'error': 'La contraseña debe tener al menos 6 caracteres'}
            
            if rol not in self.ROLES:
                return {'exito': False, 'error': f'Rol invalido: {rol}'}
            
            # Crear usuario
            hash_contraseña = bcrypt.hashpw(contraseña.encode(), bcrypt.gensalt(rounds=12))
            
            self.usuarios[usuario] = {
                'nombre_completo': nombre_completo,
                'contraseña_hash': hash_contraseña.decode(),
                'rol': rol,
                'email': email,
                'activo': True,
                'fecha_creacion': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'ultimo_acceso': None
            }
            
            self._guardar_usuarios()
            registrar_operacion('CREAR_USUARIO', f'Usuario {usuario} creado', {'usuario': usuario, 'rol': rol})
            
            return {'exito': True, 'mensaje': f'Usuario {usuario} creado correctamente'}
            
        except Exception as e:
            registrar_error('autenticacion', 'crear_usuario', str(e), f'usuario: {usuario}')
            return {'exito': False, 'error': str(e)}
    
    def login(self, usuario, contraseña):
        """
        Intenta hacer login con usuario y contraseña
        
        Args:
            usuario (str): Nombre de usuario
            contraseña (str): Contraseña
            
        Returns:
            dict: Token de sesion o error
        """
        try:
            if usuario not in self.usuarios:
                registrar_acceso(usuario, 'FALLIDO - Usuario no existe')
                return {'exito': False, 'error': 'Usuario o contraseña incorrectos'}
            
            user_data = self.usuarios[usuario]
            
            if not user_data.get('activo'):
                registrar_acceso(usuario, 'FALLIDO - Usuario inactivo')
                return {'exito': False, 'error': 'Usuario inactivo'}
            
            # Verificar contraseña
            hash_almacenado = user_data['contraseña_hash'].encode()
            if not bcrypt.checkpw(contraseña.encode(), hash_almacenado):
                registrar_acceso(usuario, 'FALLIDO - Contraseña incorrecta')
                return {'exito': False, 'error': 'Usuario o contraseña incorrectos'}
            
            # Crear sesion
            token = self._generar_token()
            expiracion = (datetime.now() + timedelta(hours=8)).isoformat()
            
            self.sesiones[token] = {
                'usuario': usuario,
                'rol': user_data['rol'],
                'inicio': datetime.now().isoformat(),
                'expiracion': expiracion
            }
            
            # Actualizar ultimo acceso
            self.usuarios[usuario]['ultimo_acceso'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            
            self._guardar_usuarios()
            self._guardar_sesiones()
            
            registrar_acceso(usuario, 'EXITOSO')
            
            return {
                'exito': True,
                'token': token,
                'usuario': usuario,
                'rol': user_data['rol'],
                'nombre_completo': user_data['nombre_completo']
            }
            
        except Exception as e:
            registrar_error('autenticacion', 'login', str(e), f'usuario: {usuario}')
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
