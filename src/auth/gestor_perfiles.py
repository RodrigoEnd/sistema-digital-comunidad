"""
Gestor de Perfiles y Usuarios
Maneja la administración de usuarios con máximo 4 delegados + 1 admin
Datos cifrados y persistentes para futura app de escritorio
"""

import os
import json
import bcrypt
from datetime import datetime
from src.auth.seguridad import seguridad
from src.config import RUTA_SEGURA
from src.core.logger import registrar_operacion


class GestorPerfiles:
    """Gestiona perfiles de usuarios del sistema"""
    
    ARCHIVO_PERFILES = os.path.join(RUTA_SEGURA, 'perfiles.json')
    MAX_DELEGADOS = 4
    ADMIN_DEFAULT_PASSWORD = "admin3112"
    ADMIN_USER = "admin"
    
    def __init__(self):
        """Inicializar gestor de perfiles"""
        self._crear_archivo_perfiles_si_no_existe()
        self.perfiles = self._cargar_perfiles()
    
    def _crear_archivo_perfiles_si_no_existe(self):
        """Crear archivo de perfiles con admin por defecto"""
        if not os.path.exists(self.ARCHIVO_PERFILES):
            # Crear estructura inicial con admin
            perfiles_iniciales = {
                "admin": {
                    "nombre": "Administrador",
                    "rol": "admin",
                    "password_hash": self._hash_password(self.ADMIN_DEFAULT_PASSWORD),
                    "activo": True,
                    "fecha_creacion": datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    "ultimo_acceso": None
                }
            }
            
            # Cifrar archivo
            seguridad.cifrar_archivo(perfiles_iniciales, 'perfiles.json', self.ADMIN_DEFAULT_PASSWORD)
            
            registrar_operacion(
                tipo='SISTEMA',
                accion='Sistema inicializado con admin',
                detalles={'usuario': self.ADMIN_USER},
                usuario='sistema'
            )
    
    def _hash_password(self, password):
        """Hash seguro de contraseña con bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
    
    def _verify_password(self, password, hash_password):
        """Verificar contraseña contra hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hash_password.encode('utf-8'))
        except:
            return False
    
    def _cargar_perfiles(self):
        """Cargar perfiles desde archivo cifrado"""
        try:
            if not os.path.exists(self.ARCHIVO_PERFILES):
                return {}
            
            datos = seguridad.descifrar_archivo('perfiles.json', self.ADMIN_DEFAULT_PASSWORD)
            return datos or {}
        except Exception as e:
            print(f"Error al cargar perfiles: {e}")
            return {}
    
    def _guardar_perfiles(self):
        """Guardar perfiles cifrados"""
        try:
            seguridad.cifrar_archivo(self.perfiles, 'perfiles.json', self.ADMIN_DEFAULT_PASSWORD)
            return True
        except Exception as e:
            print(f"Error al guardar perfiles: {e}")
            return False
    
    def autenticar(self, usuario, password):
        """
        Autenticar usuario
        
        Args:
            usuario (str): Nombre de usuario
            password (str): Contraseña
            
        Returns:
            tuple: (exito, mensaje, perfil)
        """
        if usuario not in self.perfiles:
            registrar_operacion(
                tipo='ACCESO_FALLIDO',
                accion=f'Intento de acceso con usuario inexistente: {usuario}',
                detalles={'usuario': usuario},
                usuario='sistema'
            )
            return False, "Usuario no encontrado", None
        
        perfil = self.perfiles[usuario]
        
        if not perfil.get('activo'):
            registrar_operacion(
                tipo='ACCESO_FALLIDO',
                accion=f'Intento de acceso con usuario inactivo: {usuario}',
                detalles={'usuario': usuario},
                usuario=usuario
            )
            return False, "Usuario inactivo", None
        
        if not self._verify_password(password, perfil.get('password_hash', '')):
            registrar_operacion(
                tipo='ACCESO_FALLIDO',
                accion=f'Contraseña incorrecta para usuario: {usuario}',
                detalles={'usuario': usuario},
                usuario=usuario
            )
            return False, "Contraseña incorrecta", None
        
        # Actualizar último acceso
        perfil['ultimo_acceso'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        self._guardar_perfiles()
        
        registrar_operacion(
            tipo='ACCESO_EXITOSO',
            accion=f'Login exitoso: {usuario}',
            detalles={'usuario': usuario, 'rol': perfil.get('rol')},
            usuario=usuario
        )
        
        return True, "Autenticación exitosa", perfil
    
    def agregar_delegado(self, username, password, nombre=None, cargo=None, admin_password=None):
        """Agregar nuevo delegado (máx 4)"""
        # Si se proporciona contraseña admin, verificarla
        if admin_password is not None:
            if not self._verify_password(admin_password or '', self.perfiles.get('admin', {}).get('password_hash', '')):
                return False, "Contraseña de admin incorrecta"
        # Si no se proporciona, se asume que ya se validó en la UI de administrador
        nombre = (nombre or username).strip()
        cargo = (cargo or '').strip()
        
        # Verificar límite de delegados
        delegados = [p for p in self.perfiles.values() if p.get('rol') == 'delegado']
        if len(delegados) >= self.MAX_DELEGADOS:
            return False, f"Límite de {self.MAX_DELEGADOS} delegados alcanzado"
        
        # Verificar que username no exista
        if username in self.perfiles:
            return False, f"Usuario {username} ya existe"
        
        # Validaciones
        if not nombre or len(nombre) < 6 or username.lower() in nombre.lower().replace(' ', ''):
            return False, "Ingrese un nombre completo diferente al usuario"
        
        if not username or len(username.strip()) < 3:
            return False, "Username debe tener al menos 3 caracteres"
        
        if not password or len(password) < 6:
            return False, "Contraseña debe tener al menos 6 caracteres"

        if not cargo or len(cargo) < 3:
            return False, "Cargo es obligatorio"
        
        # Agregar delegado
        self.perfiles[username] = {
            "nombre": nombre,
            "cargo": cargo,
            "rol": "delegado",
            "password_hash": self._hash_password(password),
            "activo": True,
            "fecha_creacion": datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            "ultimo_acceso": None
        }
        
        self._guardar_perfiles()
        
        registrar_operacion(
            tipo='NUEVO_DELEGADO',
            accion=f'Delegado creado: {username}',
            detalles={'nombre': nombre, 'username': username},
            usuario='admin'
        )
        
        return True, f"Delegado {nombre} agregado exitosamente"
    
    def cambiar_password(self, usuario, password_antigua, password_nueva):
        """
        Cambiar contraseña de usuario
        
        Args:
            usuario (str): Username
            password_antigua (str): Contraseña actual
            password_nueva (str): Nueva contraseña
            
        Returns:
            tuple: (exito, mensaje)
        """
        if usuario not in self.perfiles:
            return False, "Usuario no encontrado"
        
        # Verificar contraseña antigua
        if not self._verify_password(password_antigua, self.perfiles[usuario].get('password_hash', '')):
            return False, "Contraseña actual incorrecta"
        
        # Validar nueva contraseña
        if not password_nueva or len(password_nueva) < 6:
            return False, "Nueva contraseña debe tener al menos 6 caracteres"
        
        # Cambiar contraseña
        self.perfiles[usuario]['password_hash'] = self._hash_password(password_nueva)
        self._guardar_perfiles()
        
        registrar_operacion(
            tipo='CAMBIO_PASSWORD',
            accion=f'Contraseña cambiada',
            detalles={'usuario': usuario},
            usuario=usuario
        )
        
        return True, "Contraseña cambiada exitosamente"
    
    def listar_delegados(self):
        """Obtener lista de delegados"""
        delegados = []
        for username, perfil in self.perfiles.items():
            if username != 'admin':
                delegados.append({
                    'usuario': username,
                    'username': username,
                    'nombre': perfil.get('nombre'),
                    'cargo': perfil.get('cargo'),
                    'activo': perfil.get('activo'),
                    'fecha_creacion': perfil.get('fecha_creacion'),
                    'ultimo_acceso': perfil.get('ultimo_acceso')
                })
        return delegados
    
    def desactivar_delegado(self, username, admin_password):
        """
        Desactivar delegado
        
        Args:
            username (str): Username del delegado
            admin_password (str): Contraseña admin
            
        Returns:
            tuple: (exito, mensaje)
        """
        # Verificar contraseña admin
        if not self._verify_password(admin_password, self.perfiles.get('admin', {}).get('password_hash', '')):
            return False, "Contraseña de admin incorrecta"
        
        if username == 'admin':
            return False, "No se puede desactivar el admin"
        
        if username not in self.perfiles:
            return False, "Usuario no encontrado"
        
        self.perfiles[username]['activo'] = False
        self._guardar_perfiles()
        
        registrar_operacion(
            tipo='DESACTIVAR_USUARIO',
            accion=f'Usuario desactivado: {username}',
            detalles={'username': username},
            usuario='admin'
        )
        
        return True, f"Usuario {username} desactivado"

    def eliminar_delegado(self, username, admin_password=None):
        """Elimina un delegado y persiste cambios"""
        if username == 'admin':
            return False, "No se puede eliminar el admin"
        if username not in self.perfiles:
            return False, "Usuario no encontrado"

        if admin_password is not None:
            if not self._verify_password(admin_password or '', self.perfiles.get('admin', {}).get('password_hash', '')):
                return False, "Contraseña de admin incorrecta"

        self.perfiles.pop(username, None)
        self._guardar_perfiles()

        registrar_operacion(
            tipo='ELIMINAR_USUARIO',
            accion=f'Usuario eliminado: {username}',
            detalles={'username': username},
            usuario='admin'
        )

        return True, f"Usuario {username} eliminado"

    def cambiar_contrasena_delegado(self, username, nueva_contrasena, admin_password=None):
        """Actualiza contraseña de un delegado"""
        if username not in self.perfiles:
            return False, "Usuario no encontrado"

        if username == 'admin':
            return False, "Use el módulo de seguridad para el admin"

        if len(nueva_contrasena or '') < 6:
            return False, "Contraseña muy corta (mínimo 6 caracteres)"

        if admin_password is not None:
            if not self._verify_password(admin_password or '', self.perfiles.get('admin', {}).get('password_hash', '')):
                return False, "Contraseña de admin incorrecta"

        self.perfiles[username]['password_hash'] = self._hash_password(nueva_contrasena)
        self._guardar_perfiles()

        registrar_operacion(
            tipo='CAMBIO_PASSWORD',
            accion=f'Contraseña actualizada para {username}',
            detalles={'username': username},
            usuario='admin'
        )

        return True, f"Contraseña actualizada para {username}"
    
    def obtener_estadisticas(self):
        """Obtener estadísticas de usuarios"""
        delegados = [p for p in self.perfiles.values() if p.get('rol') == 'delegado']
        total_delegados = len(delegados)
        admin_existe = 'admin' in self.perfiles
        espacios_disponibles = max(self.MAX_DELEGADOS - total_delegados, 0)
        
        return {
            'total_delegados': total_delegados,
            'espacios_disponibles': espacios_disponibles,
            'admin_existe': admin_existe
        }


# Instancia global
_gestor = GestorPerfiles()


def autenticar(usuario, password):
    """Autenticar usuario"""
    exito, mensaje, perfil = _gestor.autenticar(usuario, password)
    return {"exito": exito, "mensaje": mensaje, "perfil": perfil}


def agregar_delegado(username, password, nombre=None, cargo=None, admin_password=None):
    """Agregar delegado"""
    exito, mensaje = _gestor.agregar_delegado(username=username, password=password, nombre=nombre, cargo=cargo, admin_password=admin_password)
    return {"exito": exito, "mensaje": mensaje}


def listar_delegados():
    """Listar delegados"""
    return _gestor.listar_delegados()


def obtener_estadisticas():
    """Obtener estadísticas"""
    return _gestor.obtener_estadisticas()


def eliminar_delegado(username, admin_password=None):
    """Eliminar delegado"""
    exito, mensaje = _gestor.eliminar_delegado(username, admin_password)
    return {"exito": exito, "mensaje": mensaje}


def cambiar_contrasena_delegado(username, nueva_contrasena, admin_password=None):
    """Cambiar contraseña de delegado"""
    exito, mensaje = _gestor.cambiar_contrasena_delegado(username, nueva_contrasena, admin_password)
    return {"exito": exito, "mensaje": mensaje}
