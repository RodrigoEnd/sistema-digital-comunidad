import json
import os
from datetime import datetime
from src.auth.seguridad import seguridad
from src.config import ARCHIVO_HABITANTES, PASSWORD_CIFRADO
from src.core.logger import registrar_operacion, registrar_error

class BaseDatos:
    def __init__(self, archivo=ARCHIVO_HABITANTES):
        self.archivo = archivo
        self.password = PASSWORD_CIFRADO
        self.habitantes = []
        self.cargar_datos()
        
        print(f"Base de datos cargada: {len(self.habitantes)} habitantes")
        print(f"Ubicación segura: {seguridad.ruta_segura}")
        
        # Crear datos de prueba si no existen
        if not self.habitantes:
            self.generar_datos_prueba()
    
    def generar_datos_prueba(self):
        """Base de datos vacía - sin datos de prueba"""
        self.habitantes = []
        self.guardar_datos()
        print("Base de datos inicializada vacía - lista para usar")
    
    def obtener_siguiente_folio(self):
        """Obtener el siguiente folio disponible"""
        if not self.habitantes:
            return "HAB-0001"
        
        # Obtener el último folio
        folios_numericos = []
        for hab in self.habitantes:
            try:
                num = int(hab['folio'].split('-')[1])
                folios_numericos.append(num)
            except:
                pass
        
        if folios_numericos:
            siguiente = max(folios_numericos) + 1
        else:
            siguiente = 1
        
        return f"HAB-{siguiente:04d}"
    
    def agregar_habitante(self, nombre):
        """Agregar un nuevo habitante con asignación automática de folio"""
        # Verificar si ya existe
        if any(h['nombre'].lower() == nombre.lower() for h in self.habitantes):
            registrar_operacion('AGREGAR_HABITANTE', 'Intento duplicado', {'nombre': nombre})
            return None, "Ya existe un habitante con ese nombre"
        
        nuevo_habitante = {
            'nombre': nombre,
            'folio': '',
            'fecha_registro': datetime.now().strftime("%d/%m/%Y"),
            'activo': True,
            'nota': ''
        }
        
        self.habitantes.append(nuevo_habitante)
        self.reordenar_y_asignar_folios()
        self.guardar_datos()
        
        # Obtener el folio asignado
        habitante = next((h for h in self.habitantes if h['nombre'] == nombre), None)
        registrar_operacion('AGREGAR_HABITANTE', 'Habitante agregado', {'nombre': nombre, 'folio': habitante['folio'] if habitante else 'N/A'})
        return habitante, "Habitante agregado correctamente"
    
    def reordenar_y_asignar_folios(self):
        """Reordenar alfabéticamente y reasignar folios"""
        # Ordenar alfabéticamente
        self.habitantes.sort(key=lambda x: x['nombre'].lower())
        
        # Reasignar folios
        for idx, habitante in enumerate(self.habitantes, start=1):
            habitante['folio'] = f"HAB-{idx:04d}"
    
    def buscar_habitante(self, criterio):
        """Buscar habitante por nombre o folio"""
        resultados = []
        criterio_lower = criterio.lower()
        
        for hab in self.habitantes:
            if (criterio_lower in hab['nombre'].lower() or 
                criterio_lower in hab['folio'].lower()):
                resultados.append(hab)
        
        return resultados
    
    def obtener_habitante_por_nombre(self, nombre):
        """Obtener habitante por nombre exacto"""
        for hab in self.habitantes:
            if hab['nombre'].lower() == nombre.lower():
                return hab
        return None
    
    def obtener_todos(self):
        """Obtener todos los habitantes"""
        return self.habitantes

    def actualizar_habitante(self, folio, cambios):
        """Actualiza campos permitidos de un habitante por folio"""
        actualizado = None
        for hab in self.habitantes:
            if hab.get('folio') == folio:
                if 'activo' in cambios and cambios['activo'] is not None:
                    hab['activo'] = bool(cambios['activo'])
                if 'nota' in cambios and cambios['nota'] is not None:
                    hab['nota'] = str(cambios['nota'])
                actualizado = hab
                break
        if actualizado:
            self.guardar_datos()
        return actualizado
    
    def guardar_datos(self):
        """Guardar datos cifrados en ubicación segura"""
        try:
            datos = {
                'habitantes': self.habitantes,
                'total': len(self.habitantes),
                'fecha_actualizacion': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            
            resultado = seguridad.cifrar_archivo(datos, self.archivo, self.password)
            if resultado:
                registrar_operacion('GUARDAR_DATOS', 'Datos guardados', {'total_habitantes': len(self.habitantes)})
            return resultado
        except Exception as e:
            registrar_error('GUARDAR_DATOS', str(e))
            print(f"Error al guardar: {str(e)}")
            return False
    
    def cargar_datos(self):
        """Cargar datos descifrados desde ubicación segura"""
        try:
            if seguridad.archivo_existe(self.archivo):
                datos = seguridad.descifrar_archivo(self.archivo, self.password)
                if datos:
                    self.habitantes = datos.get('habitantes', [])
                    for hab in self.habitantes:
                        hab.setdefault('activo', True)
                        hab.setdefault('nota', '')
                else:
                    self.habitantes = []
            else:
                self.habitantes = []
        except Exception as e:
            print(f"Error al cargar: {str(e)}")
            self.habitantes = []

# Instancia global de la base de datos
db = BaseDatos()
