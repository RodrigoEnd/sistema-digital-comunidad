"""
Módulo de gestión de datos y persistencia
MIGRADO A SQLite - Usa base de datos en lugar de archivos JSON
"""

import json
import threading
from datetime import datetime
from src.auth.seguridad import seguridad
from src.core.logger import registrar_operacion, registrar_error
from src.modules.pagos.pagos_constantes import PATRONES, TIMERS
from src.core.base_datos_sqlite import obtener_bd


class GestorDatos:
    """Gestor centralizado de persistencia de datos - Backend SQLite"""
    
    def __init__(self, archivo_datos=None, password_cifrado=None):
        """Inicializar gestor de datos con SQLite"""
        self.bd = obtener_bd()
        self.archivo_datos = archivo_datos  # Para compatibilidad
        self.password_cifrado = password_cifrado  # Para compatibilidad
        self.password_hash = None
        self.guardado_pendiente = None
        self.lock_guardado = threading.Lock()
    
    def cargar_datos_archivo(self):
        """
        Cargar datos de cooperaciones desde SQLite
        
        Returns:
            dict con datos cargados o None si no existen
        """
        try:
            # Obtener todas las cooperaciones desde pagos
            pagos = self.bd.obtener_todos_pagos()
            
            # Obtener monto de cooperación desde preferencias
            prefs = self._obtener_preferencias()
            
            datos = {
                'cooperaciones': self._agrupar_pagos_por_cooperacion(pagos),
                'cooperacion_activa': prefs.get('cooperacion_activa_id', 1),
                'password_hash': self.password_hash,
                'monto_cooperacion': prefs.get('monto_cooperacion', 100.0)
            }
            
            return datos
        except Exception as e:
            registrar_error('GestorDatos', 'cargar_datos_archivo', str(e))
            return None
    
    def _agrupar_pagos_por_cooperacion(self, pagos):
        """Agrupar pagos en estructura de cooperaciones"""
        cooperaciones = []
        
        # Obtener todas las cooperaciones únicas por concepto/mes
        coops_dict = {}
        
        for pago in pagos:
            concepto = pago.get('concepto', 'Cooperación General')
            if concepto not in coops_dict:
                coops_dict[concepto] = {
                    'id': len(cooperaciones) + 1,
                    'nombre': concepto,
                    'fecha_inicio': pago.get('fecha_pago', ''),
                    'personas': []
                }
            
            # Obtener habitante
            habitante = self.bd.obtener_habitante_por_folio(pago.get('habitante_id', 0))
            if habitante:
                coops_dict[concepto]['personas'].append({
                    'folio': habitante.get('folio'),
                    'nombre': habitante.get('nombre'),
                    'monto_esperado': pago.get('monto', 0),
                    'pagado': pago.get('monto', 0) if pago.get('estado') == 'completado' else 0,
                    'pendiente': 0 if pago.get('estado') == 'completado' else pago.get('monto', 0),
                    'estado': pago.get('estado', 'pendiente')
                })
        
        return list(coops_dict.values())
    
    def _obtener_preferencias(self):
        """Obtener preferencias del usuario admin"""
        try:
            admin = self.bd.obtener_usuario('admin')
            if admin:
                return {
                    'cooperacion_activa_id': 1,
                    'monto_cooperacion': 100.0
                }
        except:
            pass
        return {}
    
    def guardar_datos(self, root, datos_completos, mostrar_alerta=True, inmediato=False):
        """
        Guardar datos con debounce
        
        Args:
            root: ventana tkinter para programar tareas
            datos_completos: dict con datos a guardar
            mostrar_alerta: si mostrar alerta de éxito
            inmediato: si True, guarda inmediatamente sin debounce
        """
        # Validar que datos_completos sea válido
        if not datos_completos or not isinstance(datos_completos, dict):
            registrar_error('GestorDatos', 'guardar_datos', 'Datos inválidos para guardar')
            return
        
        if inmediato:
            self._ejecutar_guardado(datos_completos, mostrar_alerta)
        else:
            # Cancelar guardado pendiente anterior para evitar conflictos
            if self.guardado_pendiente:
                try:
                    root.after_cancel(self.guardado_pendiente)
                except:
                    pass
            
            # Programar nuevo guardado con debounce
            delay = TIMERS.get('debounce_guardado', 1000)
            self.guardado_pendiente = root.after(
                delay,
                lambda: self._ejecutar_guardado(datos_completos.copy(), mostrar_alerta)
            )
    
    def _ejecutar_guardado(self, datos_completos, mostrar_alerta=True):
        """Ejecuta el guardado real de datos en SQLite"""
        with self.lock_guardado:
            try:
                self.guardado_pendiente = None
                
                # Guardar cooperaciones en SQLite
                cooperaciones = datos_completos.get('cooperaciones', [])
                
                for coop in cooperaciones:
                    for persona in coop.get('personas', []):
                        # Obtener ID del habitante por folio
                        habitante = self.bd.obtener_habitante_por_folio(persona.get('folio'))
                        if habitante:
                            # Registrar o actualizar pago
                            self.bd.registrar_pago(
                                habitante_id=habitante.get('id'),
                                monto=persona.get('monto_esperado', 0),
                                concepto=coop.get('nombre'),
                                observaciones=f"Actualizado: {persona.get('estado')}"
                            )
                
                # Guardar preferencias
                self._guardar_preferencias({
                    'cooperacion_activa_id': datos_completos.get('cooperacion_activa', 1),
                    'monto_cooperacion': datos_completos.get('monto_cooperacion', 100.0)
                })
                
                registrar_operacion(
                    'GestorDatos',
                    'Datos guardados en SQLite',
                    {'timestamp': datetime.now().strftime(PATRONES['datetime_formato'])}
                )
                
                return True
            
            except Exception as e:
                registrar_error('GestorDatos', '_ejecutar_guardado', str(e))
                return False
    
    def _guardar_preferencias(self, prefs):
        """Guardar preferencias en base de datos"""
        try:
            # En SQLite se guardarían en tabla de preferencias
            # Por ahora simplemente las almacenamos en memoria
            pass
        except Exception as e:
            registrar_error('GestorDatos', '_guardar_preferencias', str(e))
    
    def establecer_password_hash(self, password_hash):
        """Guardar hash de contraseña"""
        self.password_hash = password_hash
    
    def obtener_password_hash(self):
        """Obtener hash de contraseña almacenado"""
        return self.password_hash
    
    def crear_respaldo_temporal(self, datos_completos):
        """Crear un respaldo temporal en memoria antes de guardar"""
        return json.loads(json.dumps(datos_completos))
    
    def validar_estructura_datos(self, datos):
        """
        Validar que los datos tengan la estructura correcta
        
        Returns:
            (bool, str) - (es_válido, mensaje)
        """
        campos_requeridos = ['cooperaciones']
        
        for campo in campos_requeridos:
            if campo not in datos:
                return False, f"Falta campo requerido: {campo}"
        
        if not isinstance(datos.get('cooperaciones'), list):
            return False, "Las cooperaciones deben ser una lista"
        
        return True, "Estructura válida"
    
    def exportar_datos_guardado(self, cooperaciones, coop_activa_id, 
                               password_hash, tamaño_letra):
        """Preparar datos para guardado"""
        return {
            'cooperaciones': cooperaciones,
            'cooperacion_activa': coop_activa_id,
            'password_hash': password_hash,
            'tamaño': tamaño_letra,
            'fecha_guardado': datetime.now().strftime(PATRONES['datetime_formato'])
        }
    
    def limpiar_datos_sensibles(self, datos):
        """
        Crear copia de datos sin información sensible
        Útil para logs o auditoría
        
        Returns:
            dict con datos desensibilizados
        """
        datos_limpios = json.loads(json.dumps(datos))
        
        # No incluir hash de contraseña
        if 'password_hash' in datos_limpios:
            datos_limpios['password_hash'] = '***'
        
        return datos_limpios
