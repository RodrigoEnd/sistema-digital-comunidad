"""
Sistema de historial de cambios y auditoria detallada
Registra todas las ediciones con timestamp, usuario y cambios
"""

import json
import os
from datetime import datetime
from pathlib import Path
from config import RUTA_SEGURA
from logger import registrar_operacion, registrar_error

class GestorHistorial:
    """Gestor de historial de cambios y auditoria"""
    
    def __init__(self):
        self.archivo_historial = os.path.join(RUTA_SEGURA, 'historial_cambios.json')
        self.historial = self._cargar_historial()
    
    def _cargar_historial(self):
        """Carga el historial desde archivo"""
        try:
            if os.path.exists(self.archivo_historial):
                with open(self.archivo_historial, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def _guardar_historial(self):
        """Guarda el historial en archivo"""
        try:
            # Mantener solo los ultimos 10000 registros para no agrandar demasiado el archivo
            historial_limitado = self.historial[-10000:]
            
            with open(self.archivo_historial, 'w', encoding='utf-8') as f:
                json.dump(historial_limitado, f, indent=2, ensure_ascii=False)
            
            # Ocultar archivo en Windows
            try:
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                ctypes.windll.kernel32.SetFileAttributesW(self.archivo_historial, FILE_ATTRIBUTE_HIDDEN)
            except:
                pass
        except Exception as e:
            registrar_error('historial', 'guardar_historial', str(e))
    
    def registrar_cambio(self, tipo, entidad, id_entidad, cambios, usuario='Sistema'):
        """
        Registra un cambio en el historial
        
        Args:
            tipo (str): CREAR, EDITAR, ELIMINAR, PAGO, etc
            entidad (str): Tipo de entidad (HABITANTE, COOPERACION, PAGO, etc)
            id_entidad (str): ID unico de la entidad
            cambios (dict): Diccionario con cambios {campo: {anterior: valor, nuevo: valor}}
            usuario (str): Usuario que realizo el cambio
        """
        try:
            registro = {
                'id': len(self.historial) + 1,
                'timestamp': datetime.now().isoformat(),
                'fecha': datetime.now().strftime('%d/%m/%Y'),
                'hora': datetime.now().strftime('%H:%M:%S'),
                'tipo': tipo,
                'entidad': entidad,
                'id_entidad': id_entidad,
                'usuario': usuario,
                'cambios': cambios
            }
            
            self.historial.append(registro)
            self._guardar_historial()
            
            # Registrar en logger tambien
            registrar_operacion(tipo, f'{entidad} {id_entidad}', cambios, usuario)
            
        except Exception as e:
            registrar_error('historial', 'registrar_cambio', str(e))
    
    def registrar_creacion(self, entidad, id_entidad, datos, usuario='Sistema'):
        """
        Registra la creacion de una entidad
        
        Args:
            entidad (str): Tipo de entidad
            id_entidad (str): ID unico
            datos (dict): Datos de la entidad creada
            usuario (str): Usuario que la creo
        """
        cambios = {campo: {'anterior': None, 'nuevo': valor} for campo, valor in datos.items()}
        self.registrar_cambio('CREAR', entidad, id_entidad, cambios, usuario)
    
    def registrar_edicion(self, entidad, id_entidad, datos_anterior, datos_nuevo, usuario='Sistema'):
        """
        Registra la edicion de una entidad
        
        Args:
            entidad (str): Tipo de entidad
            id_entidad (str): ID unico
            datos_anterior (dict): Datos antes de la edicion
            datos_nuevo (dict): Datos despues de la edicion
            usuario (str): Usuario que edito
        """
        cambios = {}
        
        # Encontrar campos que cambiaron
        todas_las_claves = set(datos_anterior.keys()) | set(datos_nuevo.keys())
        
        for clave in todas_las_claves:
            valor_anterior = datos_anterior.get(clave)
            valor_nuevo = datos_nuevo.get(clave)
            
            if valor_anterior != valor_nuevo:
                cambios[clave] = {'anterior': valor_anterior, 'nuevo': valor_nuevo}
        
        if cambios:
            self.registrar_cambio('EDITAR', entidad, id_entidad, cambios, usuario)
    
    def registrar_eliminacion(self, entidad, id_entidad, datos_eliminados, usuario='Sistema'):
        """
        Registra la eliminacion de una entidad
        
        Args:
            entidad (str): Tipo de entidad
            id_entidad (str): ID unico
            datos_eliminados (dict): Datos que fueron eliminados
            usuario (str): Usuario que elimino
        """
        cambios = {campo: {'anterior': valor, 'nuevo': None} for campo, valor in datos_eliminados.items()}
        self.registrar_cambio('ELIMINAR', entidad, id_entidad, cambios, usuario)
    
    def obtener_historial_entidad(self, entidad, id_entidad):
        """
        Obtiene el historial completo de una entidad
        
        Args:
            entidad (str): Tipo de entidad
            id_entidad (str): ID unico
            
        Returns:
            list: Lista de cambios para esa entidad
        """
        return [
            r for r in self.historial
            if r['entidad'] == entidad and r['id_entidad'] == id_entidad
        ]
    
    def obtener_historial_usuario(self, usuario):
        """
        Obtiene todos los cambios realizados por un usuario
        
        Args:
            usuario (str): Nombre del usuario
            
        Returns:
            list: Lista de cambios del usuario
        """
        return [r for r in self.historial if r['usuario'] == usuario]
    
    def obtener_historial_fecha(self, fecha_inicio, fecha_fin):
        """
        Obtiene cambios en un rango de fechas
        
        Args:
            fecha_inicio (str): Fecha en formato DD/MM/YYYY
            fecha_fin (str): Fecha en formato DD/MM/YYYY
            
        Returns:
            list: Lista de cambios en el rango
        """
        from datetime import datetime
        
        inicio = datetime.strptime(fecha_inicio, '%d/%m/%Y')
        fin = datetime.strptime(fecha_fin, '%d/%m/%Y')
        
        registros = []
        for r in self.historial:
            fecha_registro = datetime.strptime(r['fecha'], '%d/%m/%Y')
            if inicio <= fecha_registro <= fin:
                registros.append(r)
        
        return registros
    
    def obtener_historial_tipo(self, tipo):
        """
        Obtiene cambios de un tipo especifico
        
        Args:
            tipo (str): CREAR, EDITAR, ELIMINAR, etc
            
        Returns:
            list: Lista de cambios del tipo
        """
        return [r for r in self.historial if r['tipo'] == tipo]
    
    def obtener_ultimos_cambios(self, cantidad=50):
        """
        Obtiene los ultimos N cambios registrados
        
        Args:
            cantidad (int): Cantidad de registros
            
        Returns:
            list: Ultimos registros
        """
        return self.historial[-cantidad:]
    
    def obtener_estadisticas(self):
        """
        Obtiene estadisticas del historial
        
        Returns:
            dict: Estadisticas
        """
        if not self.historial:
            return {'total_cambios': 0}
        
        tipos = {}
        entidades = {}
        usuarios = {}
        
        for registro in self.historial:
            # Contar por tipo
            tipo = registro.get('tipo', 'DESCONOCIDO')
            tipos[tipo] = tipos.get(tipo, 0) + 1
            
            # Contar por entidad
            entidad = registro.get('entidad', 'DESCONOCIDA')
            entidades[entidad] = entidades.get(entidad, 0) + 1
            
            # Contar por usuario
            usuario = registro.get('usuario', 'DESCONOCIDO')
            usuarios[usuario] = usuarios.get(usuario, 0) + 1
        
        return {
            'total_cambios': len(self.historial),
            'por_tipo': tipos,
            'por_entidad': entidades,
            'por_usuario': usuarios,
            'primer_registro': self.historial[0]['timestamp'] if self.historial else None,
            'ultimo_registro': self.historial[-1]['timestamp'] if self.historial else None
        }
    
    def exportar_auditoria(self, archivo_salida):
        """
        Exporta el historial a archivo JSON
        
        Args:
            archivo_salida (str): Ruta del archivo de salida
            
        Returns:
            bool: Exito de la operacion
        """
        try:
            with open(archivo_salida, 'w', encoding='utf-8') as f:
                json.dump(self.historial, f, indent=2, ensure_ascii=False)
            registrar_operacion('EXPORTACION', 'Exportar auditoria', {'archivo': archivo_salida})
            return True
        except Exception as e:
            registrar_error('historial', 'exportar_auditoria', str(e))
            return False

# Instancia global
gestor_historial = GestorHistorial()
