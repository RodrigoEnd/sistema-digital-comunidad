"""
Base de Datos - SQLite Backend
Migración completa de JSON a SQLite
"""

import os
from datetime import datetime
from src.auth.seguridad import seguridad
from src.config import ARCHIVO_HABITANTES, PASSWORD_CIFRADO
from src.core.logger import registrar_operacion, registrar_error
from src.core.base_datos_sqlite import obtener_bd

class BaseDatos:
    """Wrapper de compatibilidad que usa SQLite como backend"""
    
    def __init__(self, archivo=ARCHIVO_HABITANTES):
        self.archivo = archivo
        self.password = PASSWORD_CIFRADO
        self.bd = obtener_bd()
        self.habitantes = []
        self.cargar_datos()
        
        print(f"Base de datos SQLite cargada: {len(self.habitantes)} habitantes")
        print(f"Ubicación segura: {seguridad.ruta_segura}")
    
    def generar_datos_prueba(self):
        """Base de datos vacía - sin datos de prueba"""
        self.habitantes = []
        print("Base de datos inicializada vacía - lista para usar")
    
    def cargar_datos(self):
        """Cargar todos los habitantes de SQLite"""
        try:
            self.habitantes = self.bd.obtener_todos_habitantes()
            if not self.habitantes:
                self.generar_datos_prueba()
        except Exception as e:
            registrar_error('BaseDatos', 'cargar_datos', str(e))
            self.habitantes = []
    
    def obtener_siguiente_folio(self):
        """Obtener el siguiente folio disponible"""
        if not self.habitantes:
            return "HAB-0001"
        
        folios_numericos = []
        for hab in self.habitantes:
            try:
                num = int(hab.get('folio', 'HAB-0000').split('-')[1])
                folios_numericos.append(num)
            except:
                pass
        
        if folios_numericos:
            siguiente = max(folios_numericos) + 1
        else:
            siguiente = 1
        
        return f"HAB-{siguiente:04d}"
    
    def agregar_habitante(self, nombre):
        """Agregar un nuevo habitante"""
        # Verificar si ya existe
        existente = self.bd.buscar_habitante(nombre)
        if existente:
            registrar_operacion('AGREGAR_HABITANTE', 'Intento duplicado', {'nombre': nombre})
            return None, "Ya existe un habitante con ese nombre"
        
        habitante, mensaje = self.bd.agregar_habitante(nombre)
        if habitante:
            self.cargar_datos()  # Recargar lista
        return habitante, mensaje
    
    def reordenar_y_asignar_folios(self):
        """Este método ya no es necesario en SQLite"""
        pass
    
    def buscar_habitante(self, criterio):
        """Buscar habitante por nombre o folio"""
        return self.bd.buscar_habitante(criterio)
    
    def obtener_habitante_por_nombre(self, nombre):
        """Obtener habitante por nombre exacto"""
        resultados = self.bd.buscar_habitante(nombre)
        return resultados[0] if resultados else None
    
    def obtener_todos(self):
        """Obtener todos los habitantes"""
        return self.habitantes
    
    def eliminar_habitante(self, folio):
        """Eliminar habitante por folio (soft delete)"""
        exito, mensaje = self.bd.eliminar_habitante(folio)
        if exito:
            self.cargar_datos()
        return exito, mensaje
    
    def actualizar_habitante(self, folio, cambios):
        """Actualizar habitante por folio"""
        exito, mensaje = self.bd.actualizar_habitante(folio, **cambios)
        if exito:
            self.cargar_datos()
        return exito, mensaje
    
    def guardar_datos(self):
        """En SQLite los datos se guardan automáticamente"""
        return True
    
    def obtener_habitante_por_folio(self, folio):
        """Obtener habitante por folio"""
        return self.bd.obtener_habitante_por_folio(folio)
    
    def eliminar_habitante(self, folio):
        """Eliminar habitante (soft delete)"""
        exito, mensaje = self.bd.eliminar_habitante(folio)
        if exito:
            self.cargar_datos()
        return exito, mensaje


# Instancia global de la base de datos
db = BaseDatos()
