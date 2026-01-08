import os
import json
import bcrypt
import hmac
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SeguridadManager:
    """Gestor de seguridad para cifrado de archivos y protección de datos"""
    
    def __init__(self):
        self.ruta_segura = self._obtener_ruta_segura()
        self.archivo_clave = os.path.join(self.ruta_segura, '.key')
        self.salt = b'SistemaComunidad2026Salt'  # En producción, usar salt aleatorio por instalación
        
    def _obtener_ruta_segura(self):
        """Obtiene la ruta segura en AppData del usuario"""
        appdata = os.getenv('LOCALAPPDATA')
        ruta = os.path.join(appdata, 'SistemaComunidad')
        
        # Crear directorio si no existe
        if not os.path.exists(ruta):
            os.makedirs(ruta)
            # Ocultar carpeta en Windows
            try:
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                ctypes.windll.kernel32.SetFileAttributesW(ruta, FILE_ATTRIBUTE_HIDDEN)
            except:
                pass
        
        return ruta
    
    def generar_clave_desde_password(self, password):
        """Genera una clave de cifrado derivada de una contraseña"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        clave = kdf.derive(password.encode())
        return Fernet(self._codificar_clave(clave))
    
    def _codificar_clave(self, clave):
        """Codifica la clave en formato base64 válido para Fernet"""
        import base64
        return base64.urlsafe_b64encode(clave)
    
    def cifrar_archivo(self, datos, nombre_archivo, password):
        """Cifra y guarda un archivo JSON"""
        try:
            ruta_completa = os.path.join(self.ruta_segura, nombre_archivo)
            
            # Convertir datos a JSON
            json_data = json.dumps(datos, ensure_ascii=False, indent=2)
            
            # Generar Fernet con la contraseña
            fernet = self.generar_clave_desde_password(password)
            
            # Cifrar datos
            datos_cifrados = fernet.encrypt(json_data.encode('utf-8'))
            
            # Calcular HMAC para verificar integridad
            h = hmac.new(password.encode(), datos_cifrados, hashlib.sha256)
            hmac_digest = h.hexdigest()
            
            # Guardar: HMAC + datos cifrados
            with open(ruta_completa, 'wb') as f:
                f.write(hmac_digest.encode() + b'\n' + datos_cifrados)
            
            # Ocultar archivo
            try:
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                ctypes.windll.kernel32.SetFileAttributesW(ruta_completa, FILE_ATTRIBUTE_HIDDEN)
            except:
                pass
            
            return True
        except Exception as e:
            print(f"Error al cifrar archivo: {e}")
            return False
    
    def descifrar_archivo(self, nombre_archivo, password):
        """Descifra y carga un archivo JSON"""
        try:
            ruta_completa = os.path.join(self.ruta_segura, nombre_archivo)
            
            if not os.path.exists(ruta_completa):
                return None
            
            # Leer archivo
            with open(ruta_completa, 'rb') as f:
                contenido = f.read()
            
            # Separar HMAC y datos
            lineas = contenido.split(b'\n', 1)
            if len(lineas) != 2:
                return None
            
            hmac_guardado = lineas[0].decode()
            datos_cifrados = lineas[1]
            
            # Verificar HMAC
            h = hmac.new(password.encode(), datos_cifrados, hashlib.sha256)
            if h.hexdigest() != hmac_guardado:
                print("ADVERTENCIA: Archivo modificado externamente")
                return None
            
            # Descifrar
            fernet = self.generar_clave_desde_password(password)
            datos_descifrados = fernet.decrypt(datos_cifrados)
            
            # Convertir de JSON
            return json.loads(datos_descifrados.decode('utf-8'))
            
        except Exception as e:
            print(f"Error al descifrar archivo: {e}")
            return None
    
    def hash_password(self, password):
        """Crea un hash seguro de contraseña con bcrypt"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
    
    def verificar_password(self, password, hash_guardado):
        """Verifica una contraseña contra su hash"""
        if isinstance(hash_guardado, str):
            hash_guardado = hash_guardado.encode()
        return bcrypt.checkpw(password.encode(), hash_guardado)
    
    def obtener_ruta_archivo(self, nombre_archivo):
        """Obtiene la ruta completa de un archivo en la carpeta segura"""
        return os.path.join(self.ruta_segura, nombre_archivo)
    
    def archivo_existe(self, nombre_archivo):
        """Verifica si un archivo existe en la carpeta segura"""
        return os.path.exists(self.obtener_ruta_archivo(nombre_archivo))

# Instancia global
seguridad = SeguridadManager()
