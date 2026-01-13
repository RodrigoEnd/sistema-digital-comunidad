"""
Módulo de gestión de datos y persistencia
Responsable de: cargar, guardar, cifrar datos con debounce
"""

import json
import threading
from datetime import datetime
from src.auth.seguridad import seguridad
from src.core.logger import registrar_operacion, registrar_error
from src.modules.pagos.pagos_constantes import PATRONES, TIMERS


class GestorDatos:
    """Gestor centralizado de persistencia de datos"""
    
    def __init__(self, archivo_datos, password_cifrado):
        self.archivo_datos = archivo_datos
        self.password_cifrado = password_cifrado
        self.password_hash = None
        self.guardado_pendiente = None
        self.lock_guardado = threading.Lock()
    
    def cargar_datos_archivo(self):
        """
        Cargar datos del archivo cifrado
        
        Returns:
            dict con datos cargados o None si no existen
        """
        try:
            if seguridad.archivo_existe(self.archivo_datos):
                datos = seguridad.descifrar_archivo(self.archivo_datos, self.password_cifrado)
                if datos:
                    self.password_hash = datos.get('password_hash')
                    return datos
        except Exception as e:
            registrar_error('CARGAR_DATOS', str(e))
        
        return None
    
    def guardar_datos(self, root, datos_completos, mostrar_alerta=True, inmediato=False):
        """
        Guardar datos con debounce para evitar conflictos
        
        BUG FIX #7: Mejorada sincronización - valida datos antes de guardar
        
        Args:
            root: ventana tkinter para programar tareas
            datos_completos: dict con todos los datos a guardar
            mostrar_alerta: si mostrar alerta de éxito
            inmediato: si True, guarda inmediatamente sin debounce
        """
        # Validar que datos_completos sea válido (BUG FIX #7)
        if not datos_completos or not isinstance(datos_completos, dict):
            registrar_error('GUARDAR_DATOS', 'Datos inválidos para guardar')
            return
        
        if inmediato:
            self._ejecutar_guardado(datos_completos, mostrar_alerta)
        else:
            # Cancelar guardado pendiente ANTERIOR para evitar conflictos
            if self.guardado_pendiente:
                root.after_cancel(self.guardado_pendiente)
            
            # Programar nuevo guardado con debounce
            delay = TIMERS['debounce_guardado']
            self.guardado_pendiente = root.after(
                delay,
                lambda: self._ejecutar_guardado(datos_completos.copy(), mostrar_alerta)
            )
    
    def _ejecutar_guardado(self, datos_completos, mostrar_alerta=True):
        """Ejecuta el guardado real de datos"""
        with self.lock_guardado:
            try:
                self.guardado_pendiente = None
                
                # Agregar timestamp
                datos_completos['fecha_guardado'] = datetime.now().strftime(
                    PATRONES['datetime_formato']
                )
                
                # Guardar cifrado
                if seguridad.cifrar_archivo(datos_completos, self.archivo_datos, self.password_cifrado):
                    registrar_operacion(
                        'GUARDAR_DATOS',
                        'Datos guardados correctamente',
                        {'timestamp': datos_completos['fecha_guardado']}
                    )
                    return True
                else:
                    if mostrar_alerta:
                        registrar_error('GUARDAR_DATOS', 'No se pudo cifrar el archivo')
                    return False
            
            except Exception as e:
                registrar_error('GUARDAR_DATOS', str(e))
                return False
    
    def establecer_password_hash(self, password_hash):
        """Guardar hash de contraseña"""
        self.password_hash = password_hash
    
    def obtener_password_hash(self):
        """Obtener hash de contraseña almacenado"""
        return self.password_hash
    
    def crear_respaldo_temporal(self, datos_completos):
        """
        Crear un respaldo temporal en memoria antes de guardar
        
        Returns:
            dict con copia de los datos
        """
        return json.loads(json.dumps(datos_completos))
    
    def validar_estructura_datos(self, datos):
        """
        Validar que los datos tengan la estructura correcta
        
        Returns:
            (bool, str) - (es_válido, mensaje)
        """
        campos_requeridos = ['cooperaciones', 'cooperacion_activa', 'password_hash']
        
        for campo in campos_requeridos:
            if campo not in datos:
                return False, f"Falta campo requerido: {campo}"
        
        if not isinstance(datos.get('cooperaciones'), list):
            return False, "Las cooperaciones deben ser una lista"
        
        # Validar estructura de cooperaciones
        for coop in datos['cooperaciones']:
            if not isinstance(coop.get('personas'), list):
                return False, "Las personas de cada cooperación deben ser una lista"
        
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
        datos_limpios['password_hash'] = '***'
        
        return datos_limpios
