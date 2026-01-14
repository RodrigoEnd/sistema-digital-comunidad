import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from typing import Dict, List, Optional, Callable

from src.modules.faenas.dashboard_faenas import DashboardFaenas
from src.modules.faenas.sistema_cuotas import SistemaCuotas, PanelCuotasUI
from src.modules.faenas.buscador_avanzado import BuscadorAvanzadoFaenas
from src.modules.faenas.formulario_moderno import FormularioFaenaModerno, ValidadorFormularioFaena
from src.modules.faenas.generador_reportes_faenas import GeneradorReportesFaenas, PanelReportesFaenas
from src.modules.faenas.gestor_atajos import GestorAtajosRapidos
from src.ui.sistema_notificaciones import SistemaNotificaciones


class FaenasIntegracion:
    def __init__(self, parent_frame, callbacks: Dict[str, Callable], db=None):
        self.parent = parent_frame
        self.callbacks = callbacks
        self.db = db
        self.faenas = []
        self.faena_seleccionada = None
        
        self.notificaciones = SistemaNotificaciones(parent_frame)
        self.sistema_cuotas = SistemaCuotas(db) if db else None
        self.generador_reportes = GeneradorReportesFaenas(db) if db else None
        self.validador = ValidadorFormularioFaena()
        
        self.widgets = {}
    
    def crear_panel_dashboard(self, parent) -> DashboardFaenas:
        datos = self._obtener_datos_dashboard()
        dashboard = DashboardFaenas(parent, lambda: self._obtener_datos_dashboard())
        return dashboard
    
    def crear_panel_buscador(self, parent) -> BuscadorAvanzadoFaenas:
        buscador = BuscadorAvanzadoFaenas(parent, self._ejecutar_busqueda)
        return buscador
    
    def crear_panel_formulario(self, parent) -> FormularioFaenaModerno:
        def guardar_faena(datos):
            validacion = self.validador.validar(datos)
            if not validacion['valido']:
                self.notificaciones.mostrar('Error', validacion['errores'][0], 'error')
                return
            
            self.callbacks['registrar_faena'](datos)
            self.notificaciones.mostrar('Exito', 'Faena registrada correctamente', 'exito')
        
        formulario = FormularioFaenaModerno(parent, guardar_faena, lambda: None)
        return formulario
    
    def crear_panel_cuotas(self, parent) -> PanelCuotasUI:
        if not self.sistema_cuotas:
            return None
        
        cuotas_ui = PanelCuotasUI(parent, self.sistema_cuotas)
        return cuotas_ui
    
    def crear_panel_reportes(self, parent) -> PanelReportesFaenas:
        if not self.generador_reportes:
            return None
        
        reportes_ui = PanelReportesFaenas(parent, self.generador_reportes)
        return reportes_ui
    
    def crear_gestor_atajos(self, root) -> GestorAtajosRapidos:
        atajos = {
            'nueva_faena': lambda: self.callbacks.get('registrar_faena')(),
            'guardar': lambda: self._guardar_cambios(),
            'buscar': lambda: self._activar_busqueda(),
            'actualizar': lambda: self.callbacks.get('refrescar')(),
            'exportar': lambda: self._exportar_datos(),
        }
        
        gestor = GestorAtajosRapidos(root, atajos)
        return gestor
    
    def _obtener_datos_dashboard(self) -> Dict:
        ahora = datetime.now()
        mes_actual = ahora.month
        anio_actual = ahora.year
        
        faenas_mes = [f for f in self.faenas 
                     if self._pertenece_al_mes(f.get('fecha', ''), mes_actual, anio_actual)]
        
        horas_totales = sum([sum([p.get('horas_trabajadas', 0) 
                                 for p in f.get('participantes', [])]) 
                            for f in faenas_mes])
        
        participantes_unicos = set()
        for faena in faenas_mes:
            for part in faena.get('participantes', []):
                participantes_unicos.add(part.get('nombre'))
        
        pagos_pendientes = sum([f.get('peso', 0) * 50 
                               for f in faenas_mes 
                               if f.get('estado') != 'pagada'])
        
        completadas = len([f for f in faenas_mes if f.get('estado') != 'registrada'])
        
        promedio = horas_totales / len(faenas_mes) if faenas_mes else 0
        
        return {
            'faenas_mes': len(faenas_mes),
            'horas_mes': horas_totales,
            'participantes': len(participantes_unicos),
            'pendiente_pago': pagos_pendientes,
            'completadas': completadas,
            'promedio_horas': promedio
        }
    
    def _pertenece_al_mes(self, fecha_str: str, mes: int, anio: int) -> bool:
        if not fecha_str:
            return False
        try:
            partes = fecha_str.split('/')
            return int(partes[1]) == mes and int(partes[2]) == anio
        except:
            return False
    
    def _ejecutar_busqueda(self, filtros: Dict):
        resultados = []
        
        for faena in self.faenas:
            cumple = True
            
            if 'fecha' in filtros:
                if faena.get('fecha') != filtros['fecha']:
                    cumple = False
            
            if 'nombre' in filtros:
                if filtros['nombre'].lower() not in faena.get('nombre', '').lower():
                    cumple = False
            
            if 'participante' in filtros:
                participantes = [p.get('nombre') for p in faena.get('participantes', [])]
                if not any(filtros['participante'].lower() in p.lower() for p in participantes):
                    cumple = False
            
            if 'peso_min' in filtros:
                if faena.get('peso', 0) < filtros['peso_min']:
                    cumple = False
            
            if 'estado' in filtros:
                if faena.get('estado') != filtros['estado']:
                    cumple = False
            
            if cumple:
                resultados.append(faena)
        
        self.callbacks.get('actualizar_listado', lambda x: None)(resultados)
    
    def _guardar_cambios(self):
        if self.callbacks.get('guardar'):
            self.callbacks['guardar']()
            self.notificaciones.mostrar('Exito', 'Cambios guardados', 'exito')
    
    def _activar_busqueda(self):
        if self.callbacks.get('activar_busqueda'):
            self.callbacks['activar_busqueda']()
    
    def _exportar_datos(self):
        try:
            from src.tools.exportador import Exportador
            exportador = Exportador()
            ruta = exportador.exportar_faenas(self.faenas)
            self.notificaciones.mostrar('Exito', f'Archivo exportado a: {ruta}', 'exito')
        except Exception as e:
            self.notificaciones.mostrar('Error', f'Error al exportar: {str(e)}', 'error')
    
    def actualizar_faenas(self, faenas: List[Dict]):
        self.faenas = faenas
    
    def obtener_cuotas_participante(self, nombre: str) -> Dict:
        if not self.sistema_cuotas:
            return {}
        
        faenas_participante = []
        for faena in self.faenas:
            if any(p.get('nombre') == nombre for p in faena.get('participantes', [])):
                faenas_participante.append(faena)
        
        return self.sistema_cuotas.calcular_cuota(nombre, faenas_participante)
    
    def generar_reporte_mensual(self, mes: int, anio: int) -> Dict:
        if not self.generador_reportes:
            return {}
        
        faenas_mes = [f for f in self.faenas 
                     if self._pertenece_al_mes(f.get('fecha', ''), mes, anio)]
        
        return self.generador_reportes.generar_resumen_mensual(faenas_mes)
    
    def obtener_estadisticas_participantes(self) -> List[Dict]:
        if not self.generador_reportes:
            return []
        
        return self.generador_reportes.obtener_top_participantes(self.faenas, 10)
    
    def obtener_distribucion_actividades(self, mes: int, anio: int) -> Dict:
        if not self.generador_reportes:
            return {}
        
        faenas_mes = [f for f in self.faenas 
                     if self._pertenece_al_mes(f.get('fecha', ''), mes, anio)]
        
        return self.generador_reportes.obtener_distribucion(faenas_mes)
