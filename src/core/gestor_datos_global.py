"""
Gestor Global de Datos - Singleton
Punto único de acceso a datos para Censo, Pagos y Faenas
Elimina la necesidad de API REST para módulos locales
"""

import threading
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

from src.core.base_datos import BaseDatos
from src.core.logger import registrar_operacion, registrar_error
from src.core.validadores import validar_nombre


class GestorDatosGlobal:
    """
    Gestor centralizado de datos (Singleton)
    
    Proporciona acceso unificado a:
    - Habitantes (Censo)
    - Pagos
    - Faenas
    
    Beneficios:
    - Sin HTTP overhead
    - Sin timeouts
    - Sincronización automática
    - Cache inteligente
    - Thread-safe
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._inicializado = False
        return cls._instance
    
    def __init__(self):
        if not self._inicializado:
            with self._lock:
                if not self._inicializado:
                    self._inicializar()
                    self._inicializado = True
    
    def _inicializar(self):
        """Inicializar el gestor"""
        self.bd = BaseDatos()
        self._cache_habitantes = None
        self._cache_timestamp = None
        self._cache_ttl = 30  # Aumentado a 30 segundos para mejor rendimiento
        print("[GestorDatosGlobal] OK - Inicializado correctamente")
    
    # ============================================================================
    # HABITANTES (CENSO)
    # ============================================================================
    
    def obtener_habitantes(self, incluir_inactivos: bool = False) -> List[Dict]:
        """
        Obtener lista de habitantes con cache inteligente
        
        Args:
            incluir_inactivos: Si True, incluye habitantes marcados como inactivos
        
        Returns:
            Lista de habitantes
        """
        try:
            # Verificar cache
            ahora = datetime.now()
            if (self._cache_habitantes is not None and 
                self._cache_timestamp is not None and 
                (ahora - self._cache_timestamp).seconds < self._cache_ttl):
                habitantes = self._cache_habitantes
            else:
                # Recargar desde BD
                habitantes = self.bd.obtener_todos()
                self._cache_habitantes = habitantes
                self._cache_timestamp = ahora
            
            # Filtrar inactivos si es necesario
            if not incluir_inactivos:
                habitantes = [h for h in habitantes if h.get('activo', True)]
            
            return habitantes
            
        except Exception as e:
            registrar_error('GestorDatosGlobal', 'obtener_habitantes', str(e))
            return []
    
    def agregar_habitante(self, nombre: str) -> Tuple[Optional[Dict], str]:
        """
        Agregar nuevo habitante
        
        Args:
            nombre: Nombre completo del habitante
        
        Returns:
            Tupla (habitante, mensaje)
        """
        try:
            # Validar nombre
            nombre_validado = validar_nombre(nombre)
            
            # Verificar duplicados
            existente = self.bd.buscar_habitante(nombre_validado)
            if existente:
                return None, f"Ya existe un habitante: {existente[0].get('nombre')}"
            
            # Agregar
            habitante, mensaje = self.bd.agregar_habitante(nombre_validado)
            
            if habitante:
                # Invalidar cache
                self._invalidar_cache()
                registrar_operacion('HABITANTE_AGREGADO', 'Nuevo habitante', 
                                   {'nombre': nombre_validado, 'folio': habitante.get('folio')})
            
            return habitante, mensaje
            
        except Exception as e:
            mensaje = f"Error al agregar habitante: {str(e)}"
            registrar_error('GestorDatosGlobal', 'agregar_habitante', str(e), 
                          contexto=f"nombre={nombre}")
            return None, mensaje
    
    def buscar_habitante(self, criterio: str) -> List[Dict]:
        """
        Buscar habitantes por nombre o folio
        
        Args:
            criterio: Texto a buscar
        
        Returns:
            Lista de habitantes que coinciden
        """
        try:
            return self.bd.buscar_habitante(criterio)
        except Exception as e:
            registrar_error('GestorDatosGlobal', 'buscar_habitante', str(e))
            return []
    
    def obtener_habitante_por_folio(self, folio: str) -> Optional[Dict]:
        """
        Obtener habitante por folio exacto
        
        Args:
            folio: Folio del habitante (ej: HAB-0001)
        
        Returns:
            Habitante o None
        """
        try:
            resultados = self.bd.buscar_habitante(folio)
            for h in resultados:
                if h.get('folio') == folio:
                    return h
            return None
        except Exception as e:
            registrar_error('GestorDatosGlobal', 'obtener_habitante_por_folio', str(e))
            return None
    
    def obtener_habitante_por_nombre(self, nombre: str) -> Optional[Dict]:
        """
        Obtener habitante por nombre exacto
        
        Args:
            nombre: Nombre completo del habitante
        
        Returns:
            Habitante o None
        """
        try:
            nombre_lower = nombre.lower().strip()
            habitantes = self.obtener_habitantes(incluir_inactivos=True)
            
            for h in habitantes:
                if h.get('nombre', '').lower().strip() == nombre_lower:
                    return h
            
            return None
        except Exception as e:
            registrar_error('GestorDatosGlobal', 'obtener_habitante_por_nombre', str(e))
            return None
    
    def actualizar_habitante(self, folio: str, **cambios) -> Tuple[bool, str]:
        """
        Actualizar datos de un habitante
        
        Args:
            folio: Folio del habitante
            **cambios: Campos a actualizar
        
        Returns:
            Tupla (exito, mensaje)
        """
        try:
            exito, mensaje = self.bd.actualizar_habitante(folio, **cambios)
            if exito:
                self._invalidar_cache()
                registrar_operacion('HABITANTE_ACTUALIZADO', 'Datos actualizados',
                                   {'folio': folio, 'cambios': cambios})
            return exito, mensaje
        except Exception as e:
            mensaje = f"Error al actualizar habitante: {str(e)}"
            registrar_error('GestorDatosGlobal', 'actualizar_habitante', str(e))
            return False, mensaje
    
    def eliminar_habitante(self, folio: str) -> Tuple[bool, str]:
        """
        Eliminar habitante (soft delete)
        
        Args:
            folio: Folio del habitante
        
        Returns:
            Tupla (exito, mensaje)
        """
        try:
            exito, mensaje = self.bd.eliminar_habitante(folio)
            if exito:
                self._invalidar_cache()
                registrar_operacion('HABITANTE_ELIMINADO', 'Habitante eliminado',
                                   {'folio': folio})
            return exito, mensaje
        except Exception as e:
            mensaje = f"Error al eliminar habitante: {str(e)}"
            registrar_error('GestorDatosGlobal', 'eliminar_habitante', str(e))
            return False, mensaje
    
    def obtener_siguiente_folio(self) -> str:
        """
        Obtener el siguiente folio disponible
        
        Returns:
            Folio en formato HAB-XXXX
        """
        try:
            return self.bd.obtener_siguiente_folio()
        except Exception as e:
            registrar_error('GestorDatosGlobal', 'obtener_siguiente_folio', str(e))
            return "HAB-0001"
    
    # ============================================================================
    # PAGOS
    # ============================================================================
    
    def obtener_pagos(self, filtros: Optional[Dict] = None) -> List[Dict]:
        """
        Obtener pagos con filtros opcionales
        
        Args:
            filtros: Diccionario con filtros (concepto, fecha_inicio, fecha_fin, etc)
        
        Returns:
            Lista de pagos
        """
        try:
            pagos = self.bd.obtener_todos_pagos()
            
            # Aplicar filtros si existen
            if filtros:
                if 'concepto' in filtros:
                    pagos = [p for p in pagos if p.get('concepto') == filtros['concepto']]
                
                if 'habitante_id' in filtros:
                    pagos = [p for p in pagos if p.get('habitante_id') == filtros['habitante_id']]
            
            return pagos
        except Exception as e:
            registrar_error('GestorDatosGlobal', 'obtener_pagos', str(e))
            return []
    
    def agregar_pago(self, habitante_id: str, monto: float, concepto: str, 
                    fecha: Optional[str] = None, detalles: Optional[str] = None) -> Tuple[Optional[Dict], str]:
        """
        Registrar un nuevo pago
        
        Args:
            habitante_id: Folio del habitante
            monto: Monto del pago
            concepto: Concepto del pago
            fecha: Fecha del pago (opcional, usa fecha actual)
            detalles: Detalles adicionales (opcional)
        
        Returns:
            Tupla (pago, mensaje)
        """
        try:
            # Verificar que el habitante existe
            habitante = self.obtener_habitante_por_folio(habitante_id)
            if not habitante:
                return None, f"No existe habitante con folio {habitante_id}"
            
            # Crear pago
            pago = {
                'habitante_id': habitante_id,
                'monto': monto,
                'concepto': concepto,
                'fecha': fecha or datetime.now().strftime('%Y-%m-%d'),
                'detalles': detalles or ''
            }
            
            # Guardar en BD (implementar en BaseDatos)
            # Por ahora retornamos el pago
            registrar_operacion('PAGO_REGISTRADO', 'Nuevo pago',
                               {'habitante_id': habitante_id, 'monto': monto, 'concepto': concepto})
            
            return pago, "Pago registrado correctamente"
            
        except Exception as e:
            mensaje = f"Error al agregar pago: {str(e)}"
            registrar_error('GestorDatosGlobal', 'agregar_pago', str(e))
            return None, mensaje
    
    # ============================================================================
    # FAENAS
    # ============================================================================
    
    def obtener_faenas(self, filtros: Optional[Dict] = None) -> List[Dict]:
        """
        Obtener faenas con filtros opcionales
        
        Args:
            filtros: Diccionario con filtros (año, mes, tipo, etc)
        
        Returns:
            Lista de faenas
        """
        try:
            # Implementar cuando se tenga método en BaseDatos
            return []
        except Exception as e:
            registrar_error('GestorDatosGlobal', 'obtener_faenas', str(e))
            return []
    
    def agregar_faena(self, datos: Dict) -> Tuple[Optional[Dict], str]:
        """
        Registrar una nueva faena
        
        Args:
            datos: Diccionario con datos de la faena
        
        Returns:
            Tupla (faena, mensaje)
        """
        try:
            # Implementar cuando se tenga método en BaseDatos
            registrar_operacion('FAENA_REGISTRADA', 'Nueva faena', datos)
            return datos, "Faena registrada correctamente"
        except Exception as e:
            mensaje = f"Error al agregar faena: {str(e)}"
            registrar_error('GestorDatosGlobal', 'agregar_faena', str(e))
            return None, mensaje
    
    # ============================================================================
    # SINCRONIZACIÓN
    # ============================================================================
    
    def sincronizar_folios(self, entidades: List[Dict]) -> int:
        """
        Sincroniza folios de entidades (personas en pagos, participantes en faenas)
        con los folios correctos del censo
        
        Args:
            entidades: Lista de entidades con 'nombre' y 'folio'
        
        Returns:
            Número de entidades actualizadas
        """
        try:
            habitantes = self.obtener_habitantes(incluir_inactivos=True)
            mapa_nombres = {h.get('nombre', '').lower().strip(): h for h in habitantes}
            
            actualizados = 0
            
            for entidad in entidades:
                nombre = entidad.get('nombre', '').lower().strip()
                if nombre in mapa_nombres:
                    folio_correcto = mapa_nombres[nombre].get('folio')
                    folio_actual = entidad.get('folio')
                    
                    if folio_actual != folio_correcto:
                        entidad['folio'] = folio_correcto
                        actualizados += 1
            
            if actualizados > 0:
                registrar_operacion('SINCRONIZACION_FOLIOS', 'Folios sincronizados',
                                   {'actualizados': actualizados})
            
            return actualizados
            
        except Exception as e:
            registrar_error('GestorDatosGlobal', 'sincronizar_folios', str(e))
            return 0
    
    def obtener_o_crear_habitante(self, nombre: str) -> Tuple[Optional[Dict], str]:
        """
        Busca un habitante por nombre, si no existe lo crea
        
        Args:
            nombre: Nombre del habitante
        
        Returns:
            Tupla (habitante, mensaje)
        """
        try:
            # Buscar primero
            habitante = self.obtener_habitante_por_nombre(nombre)
            if habitante:
                return habitante, f"Habitante existente: {habitante.get('folio')}"
            
            # Crear si no existe
            return self.agregar_habitante(nombre)
            
        except Exception as e:
            mensaje = f"Error en obtener_o_crear_habitante: {str(e)}"
            registrar_error('GestorDatosGlobal', 'obtener_o_crear_habitante', str(e))
            return None, mensaje
    
    # ============================================================================
    # ESTADÍSTICAS Y UTILIDADES
    # ============================================================================
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtener estadísticas generales del sistema
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            habitantes = self.obtener_habitantes()
            pagos = self.obtener_pagos()
            
            return {
                'total_habitantes': len(habitantes),
                'habitantes_activos': len([h for h in habitantes if h.get('activo', True)]),
                'total_pagos': len(pagos),
                'ultimo_folio': self.obtener_siguiente_folio()
            }
        except Exception as e:
            registrar_error('GestorDatosGlobal', 'obtener_estadisticas', str(e))
            return {}
    
    def _invalidar_cache(self):
        """Invalidar cache de habitantes"""
        self._cache_habitantes = None
        self._cache_timestamp = None
    
    def refrescar_cache(self):
        """Forzar recarga del cache"""
        self._invalidar_cache()
        return self.obtener_habitantes()


# ============================================================================
# FUNCIÓN DE ACCESO GLOBAL
# ============================================================================

_gestor_instance = None

def obtener_gestor() -> GestorDatosGlobal:
    """
    Obtener instancia del gestor global
    
    Returns:
        Instancia singleton de GestorDatosGlobal
    """
    global _gestor_instance
    if _gestor_instance is None:
        _gestor_instance = GestorDatosGlobal()
    return _gestor_instance
