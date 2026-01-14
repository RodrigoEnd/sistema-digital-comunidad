import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import sys
import os
from uuid import uuid4
from typing import Dict, List, Optional

if __name__ == "__main__":
    proyecto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    if proyecto_raiz not in sys.path:
        sys.path.insert(0, proyecto_raiz)

from src.core.logger import registrar_operacion, registrar_error
from src.modules.historial.historial import GestorHistorial
from src.modules.faenas.faenas_servicio import FaenasServicio
from src.modules.faenas.faenas_repo import FaenasRepositorio
from src.modules.faenas.faenas_ui_manager import FaenasUIManager
from src.modules.faenas.dialogos_faenas import (
    DialogoAgregarParticipantes,
    DialogoRegistroPagoEnLugar
)
from src.modules.faenas.dashboard_faenas import DashboardFaenas
from src.modules.faenas.sistema_cuotas import SistemaCuotas, PanelCuotasUI
from src.modules.faenas.buscador_avanzado import BuscadorAvanzadoFaenas
from src.modules.faenas.formulario_moderno import FormularioFaenaModerno
from src.modules.faenas.generador_reportes_faenas import GeneradorReportesFaenas, PanelReportesFaenas
from src.modules.faenas.gestor_atajos import GestorAtajosRapidos
from src.ui.sistema_notificaciones import SistemaNotificaciones
from src.config import (
    API_URL, PASSWORD_CIFRADO, ARCHIVO_FAENAS, MODO_OFFLINE,
    DIAS_LIMITE_EDICION_FAENA, PESO_FAENA_MINIMO, PESO_FAENA_MAXIMO
)

try:
    from src.core.base_datos import db
except Exception:
    db = None


class SistemaFaenas:
    def __init__(self, root, usuario, gestor_auth=None, default_year=None):
        self.root = root
        self.usuario_actual = usuario
        self.gestor_auth = gestor_auth
        self.root.title("Registro de Faenas Comunitarias")
        
        self.geometry_width = 1400
        self.geometry_height = 800
        self.root.geometry(f"{self.geometry_width}x{self.geometry_height}")
        
        pantalla_ancho = self.root.winfo_screenwidth()
        pantalla_alto = self.root.winfo_screenheight()
        x = (pantalla_ancho - self.geometry_width) // 2
        y = (pantalla_alto - self.geometry_height) // 2
        self.root.geometry(f"+{x}+{y}")

        self.faenas: List[Dict] = []
        self.faena_seleccionada: Optional[Dict] = None
        self.habitantes_cache: List[Dict] = []
        self.default_year = default_year

        self.gestor_historial = GestorHistorial(id_cooperacion='faenas')
        self.repo = FaenasRepositorio(ARCHIVO_FAENAS, PASSWORD_CIFRADO)
        self.servicio = FaenasServicio(api_url=API_URL)
        
        self.sistema_cuotas = SistemaCuotas(db) if db else None
        self.generador_reportes = GeneradorReportesFaenas(db) if db else None
        self.notificaciones = SistemaNotificaciones(self.root)

        self.cargar_datos()
        self._refrescar_habitantes()

        callbacks = {
            'registrar_faena': self.registrar_faena,
            'refrescar_habitantes': self._refrescar_habitantes,
            'on_select_faena': self.on_select_faena,
            'actualizar_detalle_faena': self.actualizar_detalle_faena,
            'agregar_participantes': self.agregar_participantes_multiples,
            'eliminar_participante': self.eliminar_participante,
            'registrar_pago': self.registrar_pago_en_lugar,
            'obtener_datos_dashboard': self._obtener_datos_dashboard,
            'busqueda_avanzada': self._filtrar_por_busqueda,
            'ver_detalles': self.ver_detalles_faena,
            'editar_faena': self.editar_faena,
            'eliminar_faena': self.eliminar_faena
        }

        self.ui = FaenasUIManager(self.root, usuario, callbacks)
        self.ui.configurar_interfaz()
        
        atajos = {
            'nueva_faena': self.registrar_faena,
            'guardar': self._guardar_cambios,
            'buscar': self._activar_busqueda,
            'exportar': self._exportar_datos,
            'cancelar': self._limpiar_formulario,
            'actualizar': self.actualizar_listado_faenas,
            'ayuda': self._mostrar_ayuda
        }
        self.gestor_atajos = GestorAtajosRapidos(self.root, atajos)

        self.actualizar_listado_faenas()
        self.actualizar_resumen_anual()

    def cargar_datos(self):
        try:
            self.faenas = self.repo.cargar_faenas()
        except Exception as e:
            registrar_error('SistemaFaenas', 'cargar_datos', str(e))
            self.faenas = []

    def _refrescar_habitantes(self):
        try:
            if db:
                self.habitantes_cache = db.obtener_todos()
            else:
                self.habitantes_cache = []
        except Exception as e:
            registrar_error('SistemaFaenas', '_refrescar_habitantes', str(e))

    def registrar_faena(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("Registrar nueva faena")
        ventana.geometry("600x700")
        
        def guardar_faena(datos):
            try:
                faena_id = str(uuid4())
                faena = {
                    'id': faena_id,
                    'nombre': datos['nombre'],
                    'fecha': datos['fecha'],
                    'peso': float(datos['peso']),
                    'descripcion': datos['descripcion'],
                    'hora_inicio': datos['hora_inicio'],
                    'hora_fin': datos['hora_fin'],
                    'participantes': datos.get('participantes', []),
                    'estado': 'registrada',
                    'usuario_id': self.usuario_actual.get('id'),
                    'fecha_creacion': datetime.now().strftime('%d/%m/%Y %H:%M'),
                    'observaciones': datos['notas']
                }
                
                self.faenas.append(faena)
                self.repo.guardar_faenas(self.faenas)
                registrar_operacion('SistemaFaenas', 'registrar_faena', str(faena))
                
                self.notificaciones.mostrar('Exito', f"Faena '{faena['nombre']}' registrada correctamente", 'exito')
                self.actualizar_listado_faenas()
                ventana.destroy()
            except Exception as e:
                self.notificaciones.mostrar('Error', str(e), 'error')
                registrar_error('SistemaFaenas', 'guardar_faena', str(e))
        
        formulario = FormularioFaenaModerno(ventana, guardar_faena, ventana.destroy)
        formulario.pack(fill=tk.BOTH, expand=True)

    def actualizar_listado_faenas(self):
        if self.ui.tree_faenas:
            for item in self.ui.tree_faenas.get_children():
                self.ui.tree_faenas.delete(item)
            
            for faena in self.faenas:
                estado = faena.get('estado', 'registrada')
                tag = estado.lower()
                
                self.ui.tree_faenas.insert('', 'end', values=(
                    faena.get('fecha', ''),
                    faena.get('nombre', ''),
                    f"{faena.get('peso', 0):.1f}",
                    len(faena.get('participantes', [])),
                    estado.capitalize()
                ), tags=(tag,))

    def actualizar_resumen_anual(self):
        pass

    def on_select_faena(self, event=None):
        seleccion = self.ui.tree_faenas.selection()
        if seleccion:
            indice = self.ui.tree_faenas.index(seleccion[0])
            self.faena_seleccionada = self.faenas[indice]
            self.actualizar_detalle_faena()

    def actualizar_detalle_faena(self):
        if not self.faena_seleccionada:
            return
        
        nombre = self.faena_seleccionada.get('nombre', '')
        fecha = self.faena_seleccionada.get('fecha', '')
        self.ui.lbl_faena_actual.config(text=f"{nombre} - {fecha}")

    def agregar_participantes_multiples(self):
        if not self.faena_seleccionada:
            messagebox.showwarning("Advertencia", "Debe seleccionar una faena primero")
            return
        
        dialogo = DialogoAgregarParticipantes(self.root, self.habitantes_cache,
                                             self._agregar_participantes_a_faena)
        self.root.wait_window(dialogo)

    def _agregar_participantes_a_faena(self, participantes: List[str]):
        if self.faena_seleccionada:
            for part in participantes:
                self.faena_seleccionada['participantes'].append({
                    'nombre': part,
                    'hora_entrada': datetime.now().strftime('%H:%M'),
                    'hora_salida': '',
                    'horas_trabajadas': 0
                })
            self.repo.guardar_faenas(self.faenas)
            self.actualizar_detalle_faena()

    def eliminar_participante(self):
        messagebox.showinfo("Informacion", "Seleccione un participante para eliminar")

    def registrar_pago_en_lugar(self):
        if not self.faena_seleccionada:
            messagebox.showwarning("Advertencia", "Debe seleccionar una faena primero")
            return
        
        dialogo = DialogoRegistroPagoEnLugar(self.root)
        self.root.wait_window(dialogo)

    def _obtener_datos_dashboard(self) -> Dict:
        from datetime import datetime
        ahora = datetime.now()
        
        faenas_mes = [f for f in self.faenas if self._es_mismo_mes(f.get('fecha'), ahora.month, ahora.year)]
        horas_mes = sum([sum([p.get('horas_trabajadas', 0) for p in f.get('participantes', [])]) 
                        for f in faenas_mes])
        
        participantes = set()
        for faena in faenas_mes:
            for part in faena.get('participantes', []):
                participantes.add(part.get('nombre'))
        
        pendiente = sum([f.get('peso', 0) for f in faenas_mes if f.get('estado') != 'pagada'])
        completadas = len([f for f in faenas_mes if f.get('estado') != 'registrada'])
        promedio_horas = horas_mes / len(faenas_mes) if faenas_mes else 0
        
        return {
            'faenas_mes': len(faenas_mes),
            'horas_mes': horas_mes,
            'participantes': len(participantes),
            'pendiente_pago': pendiente * 50,
            'completadas': completadas,
            'promedio_horas': promedio_horas
        }

    def _filtrar_por_busqueda(self, filtros: Dict):
        pass

    def _guardar_cambios(self):
        try:
            self.repo.guardar_faenas(self.faenas)
            self.notificaciones.mostrar('Exito', 'Cambios guardados correctamente', 'exito')
        except Exception as e:
            self.notificaciones.mostrar('Error', str(e), 'error')

    def _limpiar_formulario(self):
        self.ui.nombre_var.set('')
        self.ui.peso_var.set(5)

    def _activar_busqueda(self):
        pass

    def _exportar_datos(self):
        try:
            from src.tools.exportador import Exportador
            exportador = Exportador()
            ruta = exportador.exportar_faenas(self.faenas)
            self.notificaciones.mostrar('Exito', f'Archivo exportado a: {ruta}', 'exito')
        except Exception as e:
            self.notificaciones.mostrar('Error', f'Error al exportar: {str(e)}', 'error')

    def _mostrar_ayuda(self):
        atajos = self.gestor_atajos.obtener_atajos_disponibles()
        texto = "Atajos disponibles:\n\n"
        for tecla, accion in atajos.items():
            texto += f"{tecla}: {accion}\n"
        messagebox.showinfo("Ayuda", texto)

    def ver_detalles_faena(self):
        if self.faena_seleccionada:
            detalles = f"Faena: {self.faena_seleccionada.get('nombre')}\n"
            detalles += f"Fecha: {self.faena_seleccionada.get('fecha')}\n"
            detalles += f"Peso: {self.faena_seleccionada.get('peso')}\n"
            detalles += f"Participantes: {len(self.faena_seleccionada.get('participantes', []))}"
            messagebox.showinfo("Detalles de faena", detalles)

    def editar_faena(self):
        messagebox.showinfo("Editar", "Edicion de faena (en desarrollo)")

    def eliminar_faena(self):
        if self.faena_seleccionada:
            if messagebox.askyesno("Confirmar", "Desea eliminar esta faena?"):
                self.faenas.remove(self.faena_seleccionada)
                self.repo.guardar_faenas(self.faenas)
                self.actualizar_listado_faenas()
                self.notificaciones.mostrar('Exito', 'Faena eliminada', 'exito')

    def _es_mismo_mes(self, fecha_str: str, mes: int, anio: int) -> bool:
        if not fecha_str:
            return False
        try:
            partes = fecha_str.split('/')
            return int(partes[1]) == mes and int(partes[2]) == anio
        except:
            return False


def main(root=None, usuario=None, gestor_auth=None):
    if root is None:
        root = tk.Tk()
    if usuario is None:
        usuario = {'id': '1', 'nombre': 'Admin', 'rol': 'admin'}
    
    app = SistemaFaenas(root, usuario, gestor_auth)
    return app


if __name__ == '__main__':
    root = tk.Tk()
    main(root)
    root.mainloop()
