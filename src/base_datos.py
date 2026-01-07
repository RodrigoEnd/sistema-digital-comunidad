import json
import os
from datetime import datetime
from seguridad import seguridad

class BaseDatos:
    def __init__(self, archivo="base_datos_habitantes.json"):
        self.archivo = archivo
        self.password = "SistemaComunidad2026"  # Contraseña para cifrado de archivos
        self.habitantes = []
        self.cargar_datos()
        
        print(f"Base de datos cargada: {len(self.habitantes)} habitantes")
        print(f"Ubicación segura: {seguridad.ruta_segura}")
        
        # Crear datos de prueba si no existen
        if not self.habitantes:
            self.generar_datos_prueba()
    
    def generar_datos_prueba(self):
        """Generar 10 nombres de muestra para pruebas iniciales"""
        nombres_muestra = [
            "Juan Garcia Lopez",
            "Maria Rodriguez Martinez",
            "Pedro Hernandez Cruz",
            "Ana Gonzalez Flores",
            "Luis Martinez Gomez",
            "Carmen Lopez Sanchez",
            "Jose Perez Torres",
            "Rosa Ramirez Morales",
            "Miguel Diaz Rivera",
            "Isabel Fernandez Ruiz"
        ]
        
        habitantes_temp = []
        for i, nombre in enumerate(nombres_muestra, start=1):
            habitantes_temp.append({
                'nombre': nombre,
                'folio': f"HAB-{i:04d}",
                'fecha_registro': datetime.now().strftime("%d/%m/%Y"),
                'activo': True
            })
        
        self.habitantes = habitantes_temp
        self.guardar_datos()
        print(f"Base de datos creada con {len(self.habitantes)} habitantes de muestra")
    
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
            return None, "Ya existe un habitante con ese nombre"
        
        nuevo_habitante = {
            'nombre': nombre,
            'folio': '',
            'fecha_registro': datetime.now().strftime("%d/%m/%Y"),
            'activo': True
        }
        
        self.habitantes.append(nuevo_habitante)
        self.reordenar_y_asignar_folios()
        self.guardar_datos()
        
        # Obtener el folio asignado
        habitante = next((h for h in self.habitantes if h['nombre'] == nombre), None)
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
    
    def guardar_datos(self):
        """Guardar datos cifrados en ubicación segura"""
        try:
            datos = {
                'habitantes': self.habitantes,
                'total': len(self.habitantes),
                'fecha_actualizacion': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            
            return seguridad.cifrar_archivo(datos, self.archivo, self.password)
        except Exception as e:
            print(f"Error al guardar: {str(e)}")
            return False
    
    def cargar_datos(self):
        """Cargar datos descifrados desde ubicación segura"""
        try:
            if seguridad.archivo_existe(self.archivo):
                datos = seguridad.descifrar_archivo(self.archivo, self.password)
                if datos:
                    self.habitantes = datos.get('habitantes', [])
                else:
                    self.habitantes = []
            else:
                self.habitantes = []
        except Exception as e:
            print(f"Error al cargar: {str(e)}")
            self.habitantes = []

# Instancia global de la base de datos
db = BaseDatos()
