"""
Sistema de respaldos automaticos y recuperacion de datos
Crea backups encriptados de la base de datos
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from src.config import CARPETA_BACKUPS, RUTA_SEGURA, ARCHIVO_HABITANTES, ARCHIVO_PAGOS
from src.auth.seguridad import seguridad
from src.core.logger import registrar_backup, registrar_error

# Crear carpeta de backups si no existe
if not os.path.exists(CARPETA_BACKUPS):
    os.makedirs(CARPETA_BACKUPS)
    # Ocultar en Windows
    try:
        import ctypes
        FILE_ATTRIBUTE_HIDDEN = 0x02
        ctypes.windll.kernel32.SetFileAttributesW(CARPETA_BACKUPS, FILE_ATTRIBUTE_HIDDEN)
    except:
        pass

class GestorBackups:
    """Gestor de respaldos y recuperacion de datos"""
    
    def __init__(self):
        self.password_backup = "BackupSistemaComunidad2026"
        self.carpeta_backups = CARPETA_BACKUPS
    
    def crear_backup_completo(self):
        """
        Crea un backup completo del sistema (habitantes y pagos)
        
        Returns:
            dict: Informacion del backup creado
        """
        try:
            registrar_backup('sistema_completo', 'INICIO', 'Iniciando backup completo')
            
            timestamp = datetime.now().strftime('%d_%m_%Y_%H%M%S')
            nombre_carpeta_backup = f'backup_{timestamp}'
            ruta_backup = os.path.join(self.carpeta_backups, nombre_carpeta_backup)
            
            # Crear carpeta temporal
            os.makedirs(ruta_backup, exist_ok=True)
            
            # Archivos a respaldar
            archivos_backup = [
                (os.path.join(RUTA_SEGURA, ARCHIVO_HABITANTES), 'habitantes'),
                (os.path.join(RUTA_SEGURA, ARCHIVO_PAGOS), 'pagos')
            ]
            
            archivos_copiados = []
            
            for ruta_origen, tipo in archivos_backup:
                if os.path.exists(ruta_origen):
                    nombre_archivo = f'{tipo}_{timestamp}.bak'
                    ruta_destino = os.path.join(ruta_backup, nombre_archivo)
                    shutil.copy2(ruta_origen, ruta_destino)
                    archivos_copiados.append(nombre_archivo)
                    
                    registrar_backup(tipo, 'COMPLETADO', f'Archivo respaldado: {nombre_archivo}')
            
            # Crear archivo de metadatos
            metadatos = {
                'fecha_backup': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'archivos': archivos_copiados,
                'cantidad_archivos': len(archivos_copiados),
                'tamaño_carpeta': self._obtener_tamaño_carpeta(ruta_backup)
            }
            
            archivo_metadatos = os.path.join(ruta_backup, 'metadatos.json')
            with open(archivo_metadatos, 'w', encoding='utf-8') as f:
                json.dump(metadatos, f, indent=2, ensure_ascii=False)
            
            # Ocultar carpeta backup en Windows
            try:
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                ctypes.windll.kernel32.SetFileAttributesW(ruta_backup, FILE_ATTRIBUTE_HIDDEN)
            except:
                pass
            
            registrar_backup('sistema_completo', 'COMPLETADO', f'Backup completado: {nombre_carpeta_backup}')
            
            return {
                'exito': True,
                'nombre_carpeta': nombre_carpeta_backup,
                'ruta': ruta_backup,
                'archivos': archivos_copiados,
                'fecha': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'tamaño': metadatos['tamaño_carpeta']
            }
            
        except Exception as e:
            registrar_error('backup', 'crear_backup_completo', str(e))
            return {'exito': False, 'error': str(e)}
    
    def crear_backup_archivo(self, archivo, nombre_especifico=None):
        """
        Crea backup de un archivo especifico
        
        Args:
            archivo (str): Ruta del archivo
            nombre_especifico (str): Nombre personalizado (opcional)
            
        Returns:
            dict: Informacion del backup
        """
        try:
            if not os.path.exists(archivo):
                return {'exito': False, 'error': f'Archivo no encontrado: {archivo}'}
            
            timestamp = datetime.now().strftime('%d_%m_%Y_%H%M%S')
            nombre_archivo = nombre_especifico if nombre_especifico else f'{Path(archivo).stem}_{timestamp}.bak'
            ruta_backup = os.path.join(self.carpeta_backups, nombre_archivo)
            
            shutil.copy2(archivo, ruta_backup)
            
            # Ocultar archivo en Windows
            try:
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                ctypes.windll.kernel32.SetFileAttributesW(ruta_backup, FILE_ATTRIBUTE_HIDDEN)
            except:
                pass
            
            registrar_backup(Path(archivo).name, 'COMPLETADO', f'Backup individual creado')
            
            return {
                'exito': True,
                'archivo_backup': nombre_archivo,
                'ruta': ruta_backup,
                'fecha': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'tamaño': os.path.getsize(ruta_backup)
            }
            
        except Exception as e:
            registrar_error('backup', 'crear_backup_archivo', str(e), f'archivo: {archivo}')
            return {'exito': False, 'error': str(e)}
    
    def listar_backups(self):
        """
        Lista todos los backups disponibles
        
        Returns:
            list: Lista de carpetas de backup
        """
        try:
            backups = []
            if os.path.exists(self.carpeta_backups):
                for item in sorted(os.listdir(self.carpeta_backups), reverse=True):
                    ruta_item = os.path.join(self.carpeta_backups, item)
                    if os.path.isdir(ruta_item):
                        metadatos_file = os.path.join(ruta_item, 'metadatos.json')
                        metadatos = None
                        if os.path.exists(metadatos_file):
                            try:
                                with open(metadatos_file, 'r', encoding='utf-8') as f:
                                    metadatos = json.load(f)
                            except:
                                pass
                        
                        backups.append({
                            'nombre': item,
                            'ruta': ruta_item,
                            'metadatos': metadatos,
                            'tamaño': self._obtener_tamaño_carpeta(ruta_item)
                        })
            return backups
        except Exception as e:
            registrar_error('backup', 'listar_backups', str(e))
            return []
    
    def restaurar_backup(self, nombre_backup):
        """
        Restaura un backup completo
        
        Args:
            nombre_backup (str): Nombre de la carpeta del backup
            
        Returns:
            dict: Resultado de la restauracion
        """
        try:
            registrar_backup(nombre_backup, 'INICIO', 'Iniciando restauracion')
            
            ruta_backup = os.path.join(self.carpeta_backups, nombre_backup)
            
            if not os.path.exists(ruta_backup):
                return {'exito': False, 'error': f'Backup no encontrado: {nombre_backup}'}
            
            archivos_restaurados = []
            
            # Mapeo de archivos backup a nombres originales
            archivos_mapeo = {
                'habitantes': ARCHIVO_HABITANTES,
                'pagos': ARCHIVO_PAGOS
            }
            
            # Restaurar archivos
            for archivo_bak in os.listdir(ruta_backup):
                if archivo_bak.endswith('.bak'):
                    ruta_archivo_bak = os.path.join(ruta_backup, archivo_bak)
                    
                    # Determinar archivo destino
                    archivo_destino = None
                    for key, valor in archivos_mapeo.items():
                        if key in archivo_bak:
                            archivo_destino = valor
                            break
                    
                    if archivo_destino:
                        ruta_destino = os.path.join(RUTA_SEGURA, archivo_destino)
                        
                        # Crear backup del archivo actual antes de restaurar
                        if os.path.exists(ruta_destino):
                            ruta_respaldo_actual = ruta_destino + '.anterior'
                            shutil.copy2(ruta_destino, ruta_respaldo_actual)
                        
                        # Restaurar
                        shutil.copy2(ruta_archivo_bak, ruta_destino)
                        archivos_restaurados.append(archivo_destino)
            
            registrar_backup(nombre_backup, 'COMPLETADO', f'Restauracion exitosa: {len(archivos_restaurados)} archivos')
            
            return {
                'exito': True,
                'archivos_restaurados': archivos_restaurados,
                'fecha': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            }
            
        except Exception as e:
            registrar_error('backup', 'restaurar_backup', str(e), f'backup: {nombre_backup}')
            return {'exito': False, 'error': str(e)}
    
    def eliminar_backup(self, nombre_backup):
        """
        Elimina un backup
        
        Args:
            nombre_backup (str): Nombre de la carpeta del backup
            
        Returns:
            dict: Resultado de la eliminacion
        """
        try:
            ruta_backup = os.path.join(self.carpeta_backups, nombre_backup)
            
            if not os.path.exists(ruta_backup):
                return {'exito': False, 'error': f'Backup no encontrado: {nombre_backup}'}
            
            shutil.rmtree(ruta_backup)
            registrar_backup(nombre_backup, 'ELIMINADO', 'Backup eliminado')
            
            return {'exito': True, 'mensaje': f'Backup {nombre_backup} eliminado'}
            
        except Exception as e:
            registrar_error('backup', 'eliminar_backup', str(e), f'backup: {nombre_backup}')
            return {'exito': False, 'error': str(e)}
    
    def _obtener_tamaño_carpeta(self, ruta):
        """Obtiene el tamaño total de una carpeta en MB"""
        try:
            tamaño_bytes = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(ruta)
                for filename in filenames
            )
            return f'{tamaño_bytes / (1024*1024):.2f} MB'
        except:
            return 'Desconocido'
    
    def limpiar_backups_antiguos(self, dias=30):
        """
        Elimina backups anteriores a X dias
        
        Args:
            dias (int): Dias a mantener
            
        Returns:
            dict: Resultado de la limpieza
        """
        try:
            from datetime import datetime, timedelta
            
            fecha_limite = datetime.now() - timedelta(days=dias)
            backups_eliminados = []
            
            if not os.path.exists(self.carpeta_backups):
                return {'exito': True, 'eliminados': 0}
            
            for item in os.listdir(self.carpeta_backups):
                ruta_item = os.path.join(self.carpeta_backups, item)
                if os.path.isdir(ruta_item):
                    tiempo_modificacion = os.path.getmtime(ruta_item)
                    fecha_modificacion = datetime.fromtimestamp(tiempo_modificacion)
                    
                    if fecha_modificacion < fecha_limite:
                        shutil.rmtree(ruta_item)
                        backups_eliminados.append(item)
            
            registrar_backup('sistema_completo', 'LIMPIEZA', f'Se eliminaron {len(backups_eliminados)} backups antiguos')
            
            return {
                'exito': True,
                'eliminados': len(backups_eliminados),
                'backups': backups_eliminados
            }
            
        except Exception as e:
            registrar_error('backup', 'limpiar_backups_antiguos', str(e))
            return {'exito': False, 'error': str(e)}

# Instancia global
gestor_backups = GestorBackups()
