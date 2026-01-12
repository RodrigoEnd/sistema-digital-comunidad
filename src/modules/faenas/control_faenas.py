"""
Sistema de Registro de Faenas Comunitarias
Refactorizado y modularizado - Controlador principal simplificado
"""

import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import sys
import os
from uuid import uuid4
from typing import Dict, List, Optional

# Configurar path para imports cuando se ejecuta directamente
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
from src.config import (
    API_URL, PASSWORD_CIFRADO, ARCHIVO_FAENAS, MODO_OFFLINE,
    DIAS_LIMITE_EDICION_FAENA, PESO_FAENA_MINIMO, PESO_FAENA_MAXIMO,
    PESO_SUSTITUCION_HABITANTE, PESO_SUSTITUCION_EXTERNO,
    PESO_TRABAJADOR_CONTRATADO
)

try:
    from src.core.base_datos import db
except Exception:
    db = None


class SistemaFaenas:
    """Controlador principal del sistema de registro de faenas"""

    def __init__(self, root, usuario, gestor_auth=None, default_year=None):
        self.root = root
        self.usuario_actual = usuario
        self.gestor_auth = gestor_auth
        self.root.title("Registro de Faenas Comunitarias")
        self.root.state('zoomed')

        # Datos y servicios
        self.faenas: List[Dict] = []
        self.faena_seleccionada: Optional[Dict] = None
        self.habitantes_cache: List[Dict] = []
        self.default_year = default_year

        self.gestor_historial = GestorHistorial(id_cooperacion='faenas')
        self.repo = FaenasRepositorio(ARCHIVO_FAENAS, PASSWORD_CIFRADO)
        self.servicio = FaenasServicio(api_url=API_URL)

        # Cargar datos iniciales
        self.cargar_datos()
        self._refrescar_habitantes()

        # Configurar UI
        self._configurar_ui()

        # Actualizar interfaz
        self.actualizar_listado_faenas()
        self.actualizar_resumen_anual()

    def _configurar_ui(self) -> None:
        """Configurar la interfaz de usuario"""
        callbacks = {
            'registrar_faena': self.registrar_faena,
            'refrescar_habitantes': self._refrescar_habitantes,
            'on_select_faena': self.on_select_faena,
            'actualizar_detalle_faena': self.actualizar_detalle_faena,
            'agregar_participantes': self.agregar_participantes_multiples,
            'registrar_pago': self.registrar_pago_en_lugar,
            'eliminar_participante': self.eliminar_participante,
            'actualizar_resumen': self.actualizar_resumen_anual,
            'toggle_resumen': self._toggle_panel_resumen
        }

        self.ui_manager = FaenasUIManager(self.root, self.usuario_actual, callbacks)
        self.ui_manager.configurar_interfaz()

    # =================================================================
    # GESTIÓN DE DATOS
    # =================================================================

    def cargar_datos(self) -> None:
        """Cargar faenas desde repositorio"""
        resultado = self.repo.cargar()
        if resultado.get('ok'):
            self.faenas = resultado.get('faenas', [])
        else:
            self.faenas = []

    def guardar_datos(self, mostrar_alerta: bool = False) -> None:
        """Guardar faenas en repositorio"""
        resultado = self.repo.guardar(self.faenas)
        if not resultado.get('ok'):
            if mostrar_alerta:
                error = resultado.get('error', 'Error desconocido')
                messagebox.showerror("Error", f"No se pudo guardar: {error}")
        elif mostrar_alerta:
            messagebox.showinfo("Listo", "Faenas guardadas")

    def _refrescar_habitantes(self) -> None:
        """Carga habitantes desde API o base local para sugerencias"""
        resultado = self.servicio.sincronizar_participantes_con_censo(self.faenas)
        if resultado.get('ok'):
            self.habitantes_cache = resultado.get('habitantes_cache', [])
            actualizados = resultado.get('actualizados', 0)
            if actualizados > 0:
                self.guardar_datos(mostrar_alerta=False)
        else:
            # Fallback local
            if db:
                try:
                    self.habitantes_cache = db.obtener_todos()
                except Exception:
                    self.habitantes_cache = []

    def _normalizar_faena(self, faena: Dict) -> None:
        """Asegura campos nuevos para faenas ya guardadas"""
        faena.setdefault('participantes', [])
        faena.setdefault('pagos_sustitutos', [])
        faena.setdefault('monto_pago_faena', None)
        faena.setdefault('hora_inicio', '')
        faena.setdefault('hora_fin', '')
        faena.setdefault('es_programada', False)

    # =================================================================
    # ACCIONES PRINCIPALES
    # =================================================================

    def registrar_faena(self) -> None:
        """Registrar una nueva faena"""
        print("[DEBUG] registrar_faena invoked")
        datos = self.ui_manager.obtener_datos_formulario()

        # Validaciones
        if not datos['nombre']:
            messagebox.showerror("Error", "El nombre de la faena es obligatorio")
            return

        try:
            fecha_dt = datetime.strptime(datos['fecha'], "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Error", "Fecha inválida. Usa DD/MM/AAAA")
            return

        peso = datos['peso']
        if peso < PESO_FAENA_MINIMO or peso > PESO_FAENA_MAXIMO:
            messagebox.showerror("Error", f"El peso debe estar entre {PESO_FAENA_MINIMO} y {PESO_FAENA_MAXIMO}")
            return

        fecha_iso = fecha_dt.strftime("%Y-%m-%d")
        if any(f['fecha'] == fecha_iso for f in self.faenas):
            messagebox.showerror("Error", "Ya existe una faena registrada para esa fecha")
            return

        # Verificar si es fecha futura
        hoy = datetime.now().date()
        es_futura = fecha_dt.date() > hoy

        # Crear faena
        faena = {
            'id': f"faena-{uuid4().hex[:8]}",
            'fecha': fecha_iso,
            'nombre': datos['nombre'],
            'peso': peso,
            'hora_inicio': datos['hora_inicio'],
            'hora_fin': datos['hora_fin'],
            'es_programada': es_futura,
            'participantes': [],
            'pagos_sustitutos': [],
            'monto_pago_faena': None,
            'creado_por': self.usuario_actual.get('nombre') if self.usuario_actual else 'Sistema'
        }

        self.faenas.append(faena)
        self.gestor_historial.registrar_creacion('FAENA', faena['id'], faena,
                                                  faena['creado_por'])
        registrar_operacion('FAENA_CREADA', 'Faena registrada',
                           {'fecha': fecha_iso, 'nombre': datos['nombre'],
                            'peso': peso, 'es_programada': es_futura})

        self.ui_manager.limpiar_formulario()
        self.actualizar_listado_faenas(seleccionar_id=faena['id'])
        self.actualizar_resumen_anual()
        self.guardar_datos()

        if es_futura:
            messagebox.showinfo("Faena programada",
                               f"Faena programada para {datos['fecha']}.\n"
                               "No se pueden agregar participantes hasta esa fecha.")
        else:
            messagebox.showinfo("Listo", "Faena registrada. Ahora agrega participantes del día.")

    def agregar_participantes_multiples(self) -> None:
        """Abrir diálogo para agregar múltiples participantes"""
        print("[DEBUG] agregar_participantes_multiples invoked")
        if not self.faena_seleccionada:
            messagebox.showwarning("Selecciona una faena",
                                   "Primero registra y selecciona la faena del día")
            return

        if self.faena_seleccionada.get('es_programada'):
            messagebox.showwarning("Faena programada",
                                   "No se pueden agregar participantes a faenas futuras.\n"
                                   "Espera a que llegue la fecha.")
            return

        if not self._puede_editar_faena():
            messagebox.showwarning("Faena expirada",
                                   f"Han pasado más de {DIAS_LIMITE_EDICION_FAENA} días desde la faena.\n"
                                   "Ya no se pueden modificar los registros.")
            return

        def callback_agregar(nuevos: List[Dict]):
            """Callback cuando se agregan participantes"""
            for participante in nuevos:
                self.faena_seleccionada['participantes'].append(participante)

            self.gestor_historial.registrar_cambio('AGREGAR', 'FAENA_PARTICIPANTE',
                                                    self.faena_seleccionada['id'],
                                                    {'participantes': nuevos},
                                                    self.usuario_actual.get('nombre', 'Sistema'))

            self.actualizar_detalle_faena()
            self.actualizar_listado_faenas(seleccionar_id=self.faena_seleccionada['id'])
            self.actualizar_resumen_anual()
            self.guardar_datos()

        DialogoAgregarParticipantes(
            self.root,
            self.faena_seleccionada,
            self.habitantes_cache,
            callback_agregar,
            self.ui_manager.tema
        )

    def eliminar_participante(self) -> None:
        """Eliminar participante seleccionado"""
        print("[DEBUG] eliminar_participante invoked")
        if not self.faena_seleccionada:
            return

        if not self._puede_editar_faena():
            messagebox.showwarning("Faena expirada",
                                   f"Han pasado más de {DIAS_LIMITE_EDICION_FAENA} días desde la faena.\n"
                                   "Ya no se pueden modificar los registros.")
            return

        seleccion = self.ui_manager.tree_participantes.selection()
        if not seleccion:
            return

        idx = self.ui_manager.tree_participantes.index(seleccion[0])
        try:
            participante = self.faena_seleccionada['participantes'].pop(idx)
            if participante.get('pago_monto'):
                messagebox.showwarning("No permitido",
                                       "No puedes remover a alguien que ya pagó en lugar de asistir")
                self.faena_seleccionada['participantes'].insert(idx, participante)
                return

            self.gestor_historial.registrar_cambio('ELIMINAR', 'FAENA_PARTICIPANTE',
                                                    self.faena_seleccionada['id'],
                                                    {'participante': participante},
                                                    self.usuario_actual.get('nombre', 'Sistema'))

            self.actualizar_detalle_faena()
            self.actualizar_listado_faenas(seleccionar_id=self.faena_seleccionada['id'])
            self.actualizar_resumen_anual()
            self.guardar_datos()
        except Exception as e:
            registrar_error('faenas', 'eliminar_participante', str(e))

    def registrar_pago_en_lugar(self) -> None:
        """Abrir diálogo para registrar sustitución de faena"""
        print("[DEBUG] registrar_pago_en_lugar invoked")
        if not self.faena_seleccionada:
            messagebox.showwarning("Selecciona una faena", "Primero elige la faena del día")
            return

        if self.faena_seleccionada.get('es_programada'):
            messagebox.showwarning("Faena programada",
                                   "No se pueden registrar sustituciones en faenas futuras.\n"
                                   "Espera a que llegue la fecha.")
            return

        if not self._puede_editar_faena():
            messagebox.showwarning("Faena expirada",
                                   f"Han pasado más de {DIAS_LIMITE_EDICION_FAENA} días desde la faena.\n"
                                   "Ya no se pueden modificar los registros.")
            return

        def callback_guardar(datos: Dict):
            """Callback cuando se guarda sustitución"""
            tipo = datos['tipo']
            folio_pagador = datos['folio_pagador']
            nombre_pagador = datos['nombre_pagador']

            if tipo == 'habitante':
                folio_trabajador = datos['folio_trabajador']
                nombre_trabajador = datos['nombre_trabajador']

                # Agregar al pagador con penalización
                participante_pagador = next((p for p in self.faena_seleccionada['participantes']
                                            if p.get('folio') == folio_pagador), None)
                if not participante_pagador:
                    participante_pagador = {
                        'folio': folio_pagador,
                        'nombre': nombre_pagador or folio_pagador,
                        'hora_registro': datetime.now().isoformat(),
                        'sustitucion_tipo': 'habitante',
                        'trabajador_folio': folio_trabajador,
                        'trabajador_nombre': nombre_trabajador,
                        'peso_aplicado': PESO_SUSTITUCION_HABITANTE
                    }
                    self.faena_seleccionada['participantes'].append(participante_pagador)
                else:
                    participante_pagador['sustitucion_tipo'] = 'habitante'
                    participante_pagador['trabajador_folio'] = folio_trabajador
                    participante_pagador['trabajador_nombre'] = nombre_trabajador
                    participante_pagador['peso_aplicado'] = PESO_SUSTITUCION_HABITANTE

                # Agregar al trabajador con peso completo
                participante_trabajador = next((p for p in self.faena_seleccionada['participantes']
                                               if p.get('folio') == folio_trabajador), None)
                if not participante_trabajador:
                    participante_trabajador = {
                        'folio': folio_trabajador,
                        'nombre': nombre_trabajador or folio_trabajador,
                        'hora_registro': datetime.now().isoformat(),
                        'peso_aplicado': PESO_TRABAJADOR_CONTRATADO
                    }
                    self.faena_seleccionada['participantes'].append(participante_trabajador)

                mensaje = f"{nombre_pagador} contrató a {nombre_trabajador} (habitante)"

            else:  # externo
                nombre_ext = datos['nombre_externo']

                participante_pagador = next((p for p in self.faena_seleccionada['participantes']
                                            if p.get('folio') == folio_pagador), None)
                if not participante_pagador:
                    participante_pagador = {
                        'folio': folio_pagador,
                        'nombre': nombre_pagador or folio_pagador,
                        'hora_registro': datetime.now().isoformat(),
                        'sustitucion_tipo': 'externo',
                        'trabajador_nombre': nombre_ext,
                        'peso_aplicado': PESO_SUSTITUCION_EXTERNO
                    }
                    self.faena_seleccionada['participantes'].append(participante_pagador)
                else:
                    participante_pagador['sustitucion_tipo'] = 'externo'
                    participante_pagador['trabajador_nombre'] = nombre_ext
                    participante_pagador['peso_aplicado'] = PESO_SUSTITUCION_EXTERNO

                mensaje = f"{nombre_pagador} contrató a {nombre_ext} (externo)"

            self.gestor_historial.registrar_cambio('SUSTITUCION_FAENA', 'FAENA',
                                                    self.faena_seleccionada['id'],
                                                    {'tipo': tipo, 'pagador': folio_pagador,
                                                     'descripcion': mensaje},
                                                    self.usuario_actual.get('nombre', 'Sistema'))

            registrar_operacion('FAENA_SUSTITUCION', 'Sustitución de faena registrada', {
                'faena': self.faena_seleccionada.get('nombre'),
                'fecha': self.faena_seleccionada.get('fecha'),
                'tipo': tipo,
                'pagador': folio_pagador
            })

            self.actualizar_detalle_faena()
            self.actualizar_listado_faenas(seleccionar_id=self.faena_seleccionada['id'])
            self.actualizar_resumen_anual()
            self.guardar_datos()

            messagebox.showinfo("Registro exitoso", mensaje)

        DialogoRegistroPagoEnLugar(
            self.root,
            self.faena_seleccionada,
            self.habitantes_cache,
            callback_guardar,
            self.ui_manager.tema
        )

    # =================================================================
    # ACTUALIZACIÓN DE UI
    # =================================================================

    def on_select_faena(self, _event=None) -> None:
        """Handler cuando se selecciona una faena"""
        seleccion = self.ui_manager.tree_faenas.selection()
        if not seleccion:
            self.faena_seleccionada = None
            self.ui_manager.lbl_faena_actual.config(text="Sin faena seleccionada")
            self.ui_manager.tree_participantes.delete(
                *self.ui_manager.tree_participantes.get_children())
            return

        iid = seleccion[0]
        faena = next((f for f in self.faenas if f['id'] == iid), None)
        self.faena_seleccionada = faena

        if faena:
            self._normalizar_faena(faena)

            # Actualizar estado programada
            fecha_dt = datetime.strptime(faena['fecha'], "%Y-%m-%d").date()
            hoy = datetime.now().date()
            faena['es_programada'] = fecha_dt > hoy

            texto = f"{faena['nombre']} ({self._formato_fecha(faena['fecha'])})"
            if faena.get('hora_inicio') or faena.get('hora_fin'):
                horario = f"{faena.get('hora_inicio', '')} - {faena.get('hora_fin', '')}".strip(' -')
                texto += f" [{horario}]"
            if faena.get('es_programada'):
                texto += " [PROGRAMADA]"

            self.ui_manager.lbl_faena_actual.config(text=texto)
            self.actualizar_detalle_faena()

    def actualizar_detalle_faena(self) -> None:
        """Actualizar lista de participantes de la faena seleccionada"""
        self.ui_manager.tree_participantes.delete(
            *self.ui_manager.tree_participantes.get_children())

        if not self.faena_seleccionada:
            return

        criterio = self.ui_manager.buscar_participante_var.get().lower().strip()

        for p in self.faena_seleccionada.get('participantes', []):
            folio = p.get('folio', '')
            nombre = p.get('nombre', '')

            # Filtrar por búsqueda
            if criterio and criterio not in folio.lower() and criterio not in nombre.lower():
                continue

            # Determinar estado
            estado = "Asistió"
            if p.get('sustitucion_tipo'):
                if p.get('sustitucion_tipo') == 'habitante':
                    trabajador = p.get('trabajador_nombre', '')
                    estado = f"Contrató a {trabajador} (hab.)"
                elif p.get('sustitucion_tipo') == 'externo':
                    trabajador = p.get('trabajador_nombre', '')
                    estado = f"Contrató a {trabajador} (ext.)"
            elif p.get('pago_monto'):
                estado = f"Pagó ${p['pago_monto']}"

            # Extraer hora de registro
            hora = ''
            if p.get('hora_registro'):
                try:
                    hora_dt = datetime.fromisoformat(p['hora_registro'])
                    hora = hora_dt.strftime('%H:%M')
                except Exception:
                    hora = ''
            elif p.get('pago_fecha'):
                try:
                    hora_dt = datetime.fromisoformat(p['pago_fecha'])
                    hora = hora_dt.strftime('%H:%M')
                except Exception:
                    hora = ''

            self.ui_manager.tree_participantes.insert('', tk.END,
                                                     values=(folio, nombre, estado, hora))

    def actualizar_listado_faenas(self, seleccionar_id: Optional[str] = None) -> None:
        """Actualizar lista de faenas registradas"""
        self.ui_manager.tree_faenas.delete(*self.ui_manager.tree_faenas.get_children())
        ordenadas = sorted(self.faenas, key=lambda f: f.get('fecha', ''), reverse=True)

        for faena in ordenadas:
            self._normalizar_faena(faena)
            iid = faena['id']
            self.ui_manager.tree_faenas.insert('', tk.END, iid=iid, values=(
                self._formato_fecha(faena.get('fecha', '')),
                faena.get('nombre', ''),
                faena.get('peso', 0),
                len(faena.get('participantes', []))
            ))

        if seleccionar_id:
            if self.ui_manager.tree_faenas.exists(seleccionar_id):
                self.ui_manager.tree_faenas.selection_set(seleccionar_id)
                self.ui_manager.tree_faenas.see(seleccionar_id)
                self.on_select_faena()

    def actualizar_resumen_anual(self) -> None:
        """Actualizar resumen anual de puntos"""
        if not hasattr(self.ui_manager, 'tree_resumen'):
            return

        self.ui_manager.tree_resumen.delete(*self.ui_manager.tree_resumen.get_children())

        try:
            anio = int(self.ui_manager.anio_var.get())
        except ValueError:
            anio = datetime.now().year

        años_disponibles = self.servicio.obtener_años_disponibles(self.faenas)
        if hasattr(self.ui_manager, 'anio_combo'):
            self.ui_manager.anio_combo['values'] = [str(a) for a in años_disponibles]
            if str(anio) not in self.ui_manager.anio_combo['values']:
                self.ui_manager.anio_var.set(str(datetime.now().year))
                anio = datetime.now().year

        resumen = self.servicio.calcular_resumen_anual(self.faenas, anio)
        puntos = resumen.get('puntos', {})
        max_puntos = resumen.get('max_puntos', 1)

        # Filtrar por búsqueda
        criterio = self.ui_manager.resumen_buscar_var.get().lower().strip()
        if criterio:
            puntos = self.servicio.filtrar_resumen_por_criterio(puntos, criterio)

        if not puntos:
            return

        # Configurar tags con colores
        for data in sorted(puntos.values(), key=lambda x: (-x['puntos'], x['nombre'])):
            color = self.servicio.calcular_color_por_puntaje(data['puntos'], max_puntos)
            tag = f"color-{data['folio']}"
            texto_color = '#ffffff' if data['puntos'] >= max_puntos * 0.7 else '#1f2937'
            self.ui_manager.tree_resumen.tag_configure(tag, background=color,
                                                       foreground=texto_color)
            self.ui_manager.tree_resumen.insert('', tk.END,
                                                values=(data['folio'], data['nombre'],
                                                       f"{data['puntos']:.1f}"),
                                                tags=(tag,))

    # =================================================================
    # HELPERS
    # =================================================================

    def _toggle_panel_resumen(self, panel) -> None:
        """Colapsa o expande el panel de resumen anual"""
        if panel.content_frame.winfo_ismapped():
            panel.content_frame.pack_forget()
            titulo_actual = panel.titulo_label.cget('text')
            nuevo_titulo = titulo_actual.replace('▼', '▶')
            panel.titulo_label.config(text=nuevo_titulo)
        else:
            from src.ui.tema_moderno import ESPACIADO
            panel.content_frame.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['lg'],
                                    pady=ESPACIADO['lg'])
            titulo_actual = panel.titulo_label.cget('text')
            nuevo_titulo = titulo_actual.replace('▶', '▼')
            panel.titulo_label.config(text=nuevo_titulo)
            self.actualizar_resumen_anual()

    def _puede_editar_faena(self) -> bool:
        """
        Valida si una faena puede ser editada.
        Retorna False si han pasado más de N días desde la fecha de la faena.
        """
        try:
            resultado = self.servicio.validar_puede_editar_faena(
                self.faena_seleccionada, dias_limite=DIAS_LIMITE_EDICION_FAENA)
            return resultado.get('puede_editar', False)
        except Exception as e:
            print(f"Error validando fecha: {e}")
            return True  # Por defecto permitir

    @staticmethod
    def _formato_fecha(fecha_iso: str) -> str:
        """Formatear fecha ISO a DD/MM/YYYY"""
        try:
            return datetime.strptime(fecha_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            return fecha_iso


def main():
    """Punto de entrada principal con autenticación"""
    from src.auth.login_window import VentanaLogin

    login_root = tk.Tk()

    def on_login(usuario, gestor_auth):
        """Callback cuando el login es exitoso"""
        login_root.destroy()

        root = tk.Tk()
        root.title(f"Registro de Faenas - {usuario['nombre']} ({usuario['rol']})")

        # Permitir pasar año por defecto via argumentos (--anio 2025)
        default_year = None
        try:
            args = sys.argv[1:]
            if '--anio' in args:
                idx = args.index('--anio')
                if idx + 1 < len(args):
                    default_year = int(args[idx + 1])
        except Exception:
            default_year = None

        app = SistemaFaenas(root, usuario, gestor_auth, default_year=default_year)
        root.mainloop()

    VentanaLogin(login_root, on_login)
    login_root.mainloop()


if __name__ == '__main__':
    main()
