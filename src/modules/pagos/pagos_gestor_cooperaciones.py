"""
Módulo de gestión de cooperaciones
Responsable de: crear, editar, eliminar y gestionar cooperaciones
"""

import time
import json
from datetime import datetime
from tkinter import messagebox, ttk
import tkinter as tk

from src.core.logger import registrar_operacion, registrar_error
from src.modules.pagos.pagos_constantes import PATRONES, MENSAJES


class GestorCooperaciones:
    """Gestor centralizado de cooperaciones"""
    
    def __init__(self, archivo_datos, gestor_seguridad):
        self.cooperaciones = []
        self.coop_activa_id = None
        self.archivo_datos = archivo_datos
        self.gestor_seguridad = gestor_seguridad
    
    def cargar_cooperaciones(self, datos):
        """Cargar cooperaciones desde datos guardados"""
        self.cooperaciones = datos.get('cooperaciones', [])
        self.coop_activa_id = datos.get('cooperacion_activa')
        
        if not self.cooperaciones:
            self._crear_cooperacion_default()
    
    def _crear_cooperacion_default(self):
        """Crear cooperación por defecto si no existen"""
        nueva = self._generar_cooperacion(
            nombre='Cooperacion General',
            proyecto='Proyecto Comunitario 2026',
            monto=100.0
        )
        self.cooperaciones = [nueva]
        self.coop_activa_id = nueva['id']
    
    def obtener_cooperacion_activa(self):
        """Obtener la cooperación activa actual"""
        for coop in self.cooperaciones:
            if coop.get('id') == self.coop_activa_id:
                return coop
        return None
    
    def obtener_cooperacion_por_id(self, coop_id):
        """Obtener una cooperación por su ID"""
        return next((c for c in self.cooperaciones if c.get('id') == coop_id), None)
    
    def crear_cooperacion(self, nombre, proyecto, monto):
        """Crear una nueva cooperación"""
        if not nombre or not nombre.strip():
            raise ValueError("El nombre de la cooperación no puede estar vacío")
        
        if monto <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        
        nueva = self._generar_cooperacion(nombre, proyecto, monto)
        self.cooperaciones.append(nueva)
        self.coop_activa_id = nueva['id']
        
        registrar_operacion(
            'CREAR_COOP',
            f'Nueva cooperación creada: {nombre}',
            {'id': nueva['id'], 'monto': monto, 'proyecto': proyecto}
        )
        
        return nueva
    
    def editar_cooperacion(self, coop_id, nombre, proyecto, monto):
        """Editar una cooperación existente"""
        coop = self.obtener_cooperacion_por_id(coop_id)
        if not coop:
            raise ValueError(f"Cooperación con ID {coop_id} no encontrada")
        
        if not nombre or not nombre.strip():
            raise ValueError("El nombre de la cooperación no puede estar vacío")
        
        if monto <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        
        cambios = {
            'nombre_anterior': coop.get('nombre'),
            'proyecto_anterior': coop.get('proyecto'),
            'monto_anterior': coop.get('monto_cooperacion')
        }
        
        coop['nombre'] = nombre
        coop['proyecto'] = proyecto
        coop['monto_cooperacion'] = monto
        
        registrar_operacion(
            'EDITAR_COOP',
            f'Cooperación editada: {nombre}',
            {**cambios, 'nombre_nuevo': nombre, 'monto_nuevo': monto}
        )
    
    def eliminar_cooperacion(self, coop_id):
        """Eliminar una cooperación"""
        coop = self.obtener_cooperacion_por_id(coop_id)
        if not coop:
            raise ValueError(f"Cooperación con ID {coop_id} no encontrada")
        
        if len(self.cooperaciones) <= 1:
            raise ValueError("No se puede eliminar la última cooperación")
        
        self.cooperaciones = [c for c in self.cooperaciones if c.get('id') != coop_id]
        
        # Si se eliminó la activa, activar la primera
        if self.coop_activa_id == coop_id:
            self.coop_activa_id = self.cooperaciones[0].get('id') if self.cooperaciones else None
        
        registrar_operacion(
            'ELIMINAR_COOP',
            f'Cooperación eliminada: {coop.get("nombre")}',
            {'id': coop_id}
        )
    
    def activar_cooperacion(self, coop_id):
        """Activar una cooperación"""
        if self.obtener_cooperacion_por_id(coop_id):
            self.coop_activa_id = coop_id
            registrar_operacion('ACTIVAR_COOP', f'Cooperación activada', {'id': coop_id})
        else:
            raise ValueError(f"Cooperación con ID {coop_id} no encontrada")
    
    def obtener_listado_nombres(self):
        """Obtener lista de nombres de cooperaciones"""
        return [c.get('nombre', 'Sin nombre') for c in self.cooperaciones]
    
    def obtener_nombre_activa(self):
        """Obtener nombre de la cooperación activa"""
        coop = self.obtener_cooperacion_activa()
        return coop.get('nombre', 'Cooperacion') if coop else 'Ninguna'
    
    def sincronizar_personas(self, personas_nuevas, reemplazar=False):
        """
        Sincronizar personas con la cooperación activa
        
        Args:
            personas_nuevas: Lista de personas a sincronizar
            reemplazar: Si True, reemplaza todas las personas; si False, agrega nuevas
        
        Returns:
            dict con resultado de la sincronización
        """
        coop = self.obtener_cooperacion_activa()
        if not coop:
            return {'exito': False, 'mensaje': 'No hay cooperación activa'}
        
        personas_existentes = coop.get('personas', [])
        
        if reemplazar:
            agregadas = len(personas_nuevas)
            coop['personas'] = personas_nuevas
        else:
            folios_existentes = {p.get('folio') for p in personas_existentes}
            nuevas = [p for p in personas_nuevas if p.get('folio') not in folios_existentes]
            agregadas = len(nuevas)
            coop['personas'].extend(nuevas)
        
        return {
            'exito': True,
            'agregadas': agregadas,
            'total': len(coop['personas'])
        }
    
    def _generar_cooperacion(self, nombre, proyecto, monto):
        """Generar estructura de cooperación"""
        return {
            'id': f"coop-{int(time.time())}",
            'nombre': nombre,
            'proyecto': proyecto,
            'monto_cooperacion': monto,
            'personas': [],
            'fecha_creacion': datetime.now().strftime(PATRONES['datetime_formato']),
            'estado': 'activa'
        }
    
    def exportar_datos_guardado(self):
        """Exportar datos para guardado"""
        return {
            'cooperaciones': self.cooperaciones,
            'cooperacion_activa': self.coop_activa_id
        }
