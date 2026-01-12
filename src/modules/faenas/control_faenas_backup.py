import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sys
import os
from uuid import uuid4

# Configurar path para imports cuando se ejecuta directamente
if __name__ == "__main__":
    # Agregar la raíz del proyecto al path
    proyecto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    if proyecto_raiz not in sys.path:
        sys.path.insert(0, proyecto_raiz)

from src.ui.estilos_globales import TEMA_GLOBAL
from src.ui.tema_moderno import FUENTES, ESPACIADO, ICONOS
from src.ui.ui_moderna import BarraSuperior, PanelModerno, BotonModerno
from src.auth.seguridad import seguridad
from src.core.logger import registrar_operacion, registrar_error
from src.modules.historial.historial import GestorHistorial
from src.modules.faenas.faenas_servicio import FaenasServicio
from src.modules.faenas.faenas_repo import FaenasRepositorio
from src.config import API_URL, PASSWORD_CIFRADO, ARCHIVO_FAENAS, MODO_OFFLINE

try:
    from src.core.base_datos import db
except Exception:
    db = None


class SistemaFaenas:
    """Registro diario de faenas con ponderación anual."""

    def __init__(self, root, usuario, gestor_auth=None, default_year=None):
        self.root = root
        self.usuario_actual = usuario
        self.gestor_auth = gestor_auth
        self.root.title("Registro de Faenas Comunitarias")
        self.root.state('zoomed')

        self.tema_visual = TEMA_GLOBAL

        self.faenas = []
        self.faena_seleccionada = None
        self.habitantes_cache = []
        self.gestor_historial = GestorHistorial(id_cooperacion='faenas')  # Historial independiente para faenas
        self.default_year = default_year
        
        # Servicio y repositorio
        self.repo = FaenasRepositorio(ARCHIVO_FAENAS, PASSWORD_CIFRADO)
        self.servicio = FaenasServicio(api_url=API_URL)

        self.cargar_datos()
        self._refrescar_habitantes()

        self.configurar_interfaz()
        self.actualizar_listado_faenas()
        self.actualizar_resumen_anual()  # Llamar DESPUÉS de configurar_interfaz()

    # ------------------------------------------------------------------
    # Datos
    # ------------------------------------------------------------------
    def cargar_datos(self):
        resultado = self.repo.cargar()
        if resultado.get('ok'):
            self.faenas = resultado.get('faenas', [])
        else:
            self.faenas = []

    def guardar_datos(self, mostrar_alerta=False):
        resultado = self.repo.guardar(self.faenas)
        if not resultado.get('ok'):
            if mostrar_alerta:
                error = resultado.get('error', 'Error desconocido')
                messagebox.showerror("Error", f"No se pudo guardar: {error}")
        elif mostrar_alerta:
            messagebox.showinfo("Listo", "Faenas guardadas")

    def _refrescar_habitantes(self):
        """Carga habitantes desde API o base local para sugerencias."""
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
    
    def _normalizar_faena(self, faena):
        """Asegura campos nuevos para faenas ya guardadas."""
        faena.setdefault('participantes', [])
        faena.setdefault('pagos_sustitutos', [])
        faena.setdefault('monto_pago_faena', None)
        faena.setdefault('hora_inicio', '')
        faena.setdefault('hora_fin', '')
        faena.setdefault('es_programada', False)

    # ------------------------------------------------------------------
    # Interfaz
    # ------------------------------------------------------------------
    def configurar_interfaz(self):
        self.root.configure(bg=self.tema_visual['bg_principal'])

        self.barra = BarraSuperior(self.root, self.usuario_actual, lambda: None)
        self.barra.pack(fill=tk.X)

        # Contenedor con canvas para permitir scroll vertical de todo el layout
        scroll_container = tk.Frame(self.root, bg=self.tema_visual['bg_principal'])
        scroll_container.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['lg'], pady=ESPACIADO['lg'])
        scroll_container.columnconfigure(0, weight=1)
        scroll_container.rowconfigure(0, weight=1)

        canvas = tk.Canvas(scroll_container, bg=self.tema_visual['bg_principal'], highlightthickness=0)
        canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar = ttk.Scrollbar(scroll_container, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        canvas.configure(yscrollcommand=scrollbar.set)

        main = tk.Frame(canvas, bg=self.tema_visual['bg_principal'])
        window_id = canvas.create_window((0, 0), window=main, anchor='nw')

        # Ajustar región de scroll y ancho para evitar cortes laterales
        main.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(window_id, width=e.width))
        
        # Scroll del canvas solo cuando el cursor está sobre él
        def _on_canvas_scroll(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        canvas.bind('<MouseWheel>', _on_canvas_scroll)

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)
        main.rowconfigure(2, weight=1)

        self._crear_panel_formulario(main)
        self._crear_panel_listado(main)
        self._crear_panel_detalle(main)
        self._crear_panel_resumen(main)

    def _crear_panel_formulario(self, parent):
        panel = PanelModerno(parent, titulo="Registrar faena del día", tema=self.tema_visual)
        panel.grid(row=0, column=0, columnspan=2, sticky='nsew', pady=(0, ESPACIADO['lg']))

        frm = panel.content_frame
        frm.columnconfigure(1, weight=1)

        tk.Label(frm, text="Fecha (DD/MM/AAAA)", font=FUENTES['subtitulo'],
                 bg=self.tema_visual['bg_secundario'], fg=self.tema_visual['fg_principal']).grid(row=0, column=0, sticky='w')
        self.fecha_var = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y"))
        tk.Entry(frm, textvariable=self.fecha_var, font=FUENTES['normal'],
                 bg=self.tema_visual['input_bg'], fg=self.tema_visual['fg_principal'],
                 relief=tk.SOLID, bd=1, width=14, insertbackground=self.tema_visual['accent_primary']).grid(row=0, column=1, sticky='w')

        tk.Label(frm, text="Nombre de la faena", font=FUENTES['subtitulo'],
                 bg=self.tema_visual['bg_secundario'], fg=self.tema_visual['fg_principal']).grid(row=1, column=0, sticky='w', pady=(ESPACIADO['sm'], 0))
        self.nombre_var = tk.StringVar()
        tk.Entry(frm, textvariable=self.nombre_var, font=FUENTES['normal'],
                 bg=self.tema_visual['input_bg'], fg=self.tema_visual['fg_principal'],
                 relief=tk.SOLID, bd=1, width=38, insertbackground=self.tema_visual['accent_primary']).grid(row=1, column=1, sticky='w')

        tk.Label(frm, text="Horario", font=FUENTES['subtitulo'],
                 bg=self.tema_visual['bg_secundario'], fg=self.tema_visual['fg_principal']).grid(row=1, column=2, sticky='w', pady=(ESPACIADO['sm'], 0), padx=(ESPACIADO['lg'], 0))
        horario_frame = tk.Frame(frm, bg=self.tema_visual['bg_secundario'])
        horario_frame.grid(row=1, column=3, sticky='w')
        
        # Hora inicio
        self.hora_inicio_var = tk.StringVar(value='9')
        ttk.Combobox(horario_frame, textvariable=self.hora_inicio_var, values=[str(i) for i in range(1, 13)],
                     width=3, state='readonly').pack(side=tk.LEFT)
        self.hora_inicio_ampm_var = tk.StringVar(value='AM')
        ttk.Combobox(horario_frame, textvariable=self.hora_inicio_ampm_var, values=['AM', 'PM'],
                     width=4, state='readonly').pack(side=tk.LEFT, padx=(2, 4))
        
        tk.Label(horario_frame, text="a", font=FUENTES['normal'],
                 bg=self.tema_visual['bg_secundario'], fg=self.tema_visual['fg_principal']).pack(side=tk.LEFT, padx=4)
        
        # Hora fin
        self.hora_fin_var = tk.StringVar(value='1')
        ttk.Combobox(horario_frame, textvariable=self.hora_fin_var, values=[str(i) for i in range(1, 13)],
                     width=3, state='readonly').pack(side=tk.LEFT)
        self.hora_fin_ampm_var = tk.StringVar(value='PM')
        ttk.Combobox(horario_frame, textvariable=self.hora_fin_ampm_var, values=['AM', 'PM'],
                     width=4, state='readonly').pack(side=tk.LEFT, padx=(2, 0))

        tk.Label(frm, text="Peso (1-10)", font=FUENTES['subtitulo'],
             bg=self.tema_visual['bg_secundario'], fg=self.tema_visual['fg_principal']).grid(row=2, column=0, sticky='w', pady=(ESPACIADO['sm'], 0))
        self.peso_var = tk.IntVar(value=5)
        peso_row = tk.Frame(frm, bg=self.tema_visual['bg_secundario'])
        peso_row.grid(row=2, column=1, sticky='we')
        peso_row.columnconfigure(0, weight=1)
        tk.Scale(peso_row, from_=1, to=10, orient=tk.HORIZONTAL, variable=self.peso_var,
             length=200, showvalue=False,
             bg=self.tema_visual['bg_secundario'], fg=self.tema_visual['fg_principal'],
             troughcolor=self.tema_visual['accent_light'], highlightthickness=0,
             activebackground=self.tema_visual['accent_primary']).grid(row=0, column=0, sticky='w')
        tk.Entry(peso_row, textvariable=self.peso_var, width=4, font=FUENTES['normal'],
             bg=self.tema_visual['input_bg'], fg=self.tema_visual['fg_principal'],
             relief=tk.SOLID, bd=1, justify='center',
             insertbackground=self.tema_visual['accent_primary']).grid(row=0, column=1, padx=(ESPACIADO['sm'], 0))

        acciones = tk.Frame(frm, bg=self.tema_visual['bg_secundario'])
        acciones.grid(row=0, column=4, rowspan=3, padx=ESPACIADO['lg'])
        BotonModerno(acciones, texto="Registrar faena del día", tema=self.tema_visual,
                     command=self.registrar_faena).pack(fill=tk.X, pady=(0, ESPACIADO['sm']))
        BotonModerno(acciones, texto="Refrescar habitantes", tema=self.tema_visual,
                     tipo='secondary', command=self._refrescar_habitantes).pack(fill=tk.X)

    def _crear_panel_listado(self, parent):
        panel = PanelModerno(parent, titulo="Faenas registradas", tema=self.tema_visual)
        panel.grid(row=1, column=0, sticky='nsew', padx=(0, ESPACIADO['lg']))
        panel.content_frame.rowconfigure(0, weight=1)
        panel.content_frame.columnconfigure(0, weight=1)

        columns = ('fecha', 'nombre', 'peso', 'participantes')
        self.tree_faenas = ttk.Treeview(panel.content_frame, columns=columns, show='headings', height=14)
        self.tree_faenas.heading('fecha', text='Fecha')
        self.tree_faenas.heading('nombre', text='Faena')
        self.tree_faenas.heading('peso', text='Peso')
        self.tree_faenas.heading('participantes', text='Participantes')

        self.tree_faenas.column('fecha', width=120, anchor='center')
        self.tree_faenas.column('nombre', width=260)
        self.tree_faenas.column('peso', width=70, anchor='center')
        self.tree_faenas.column('participantes', width=110, anchor='center')

        scroll_y = ttk.Scrollbar(panel.content_frame, orient=tk.VERTICAL, command=self.tree_faenas.yview)
        self.tree_faenas.configure(yscrollcommand=scroll_y.set)

        self.tree_faenas.grid(row=0, column=0, sticky='nsew')
        scroll_y.grid(row=0, column=1, sticky='ns')
        self.tree_faenas.bind('<<TreeviewSelect>>', self.on_select_faena)

    def _crear_panel_detalle(self, parent):
        panel = PanelModerno(parent, titulo="Participantes de la faena", tema=self.tema_visual)
        panel.grid(row=1, column=1, sticky='nsew')
        panel.content_frame.rowconfigure(2, weight=1)
        panel.content_frame.columnconfigure(0, weight=1)

        info = tk.Frame(panel.content_frame, bg=self.tema_visual['bg_secundario'])
        info.grid(row=0, column=0, sticky='we', pady=(0, ESPACIADO['sm']))
        self.lbl_faena_actual = tk.Label(info, text="Sin faena seleccionada", font=FUENTES['subtitulo'],
                                         bg=self.tema_visual['bg_secundario'], fg=self.tema_visual['fg_principal'])
        self.lbl_faena_actual.pack(side=tk.LEFT)

        busqueda_frame = tk.Frame(panel.content_frame, bg=self.tema_visual['bg_secundario'])
        busqueda_frame.grid(row=1, column=0, sticky='we', pady=(0, ESPACIADO['sm']))
        tk.Label(busqueda_frame, text="Buscar:", font=FUENTES['normal'],
                 bg=self.tema_visual['bg_secundario'], fg=self.tema_visual['fg_principal']).pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        self.buscar_participante_var = tk.StringVar()
        self.buscar_participante_var.trace_add('write', lambda *_: self.actualizar_detalle_faena())
        tk.Entry(busqueda_frame, textvariable=self.buscar_participante_var, font=FUENTES['normal'], width=30,
                 bg=self.tema_visual['input_bg'], fg=self.tema_visual['fg_principal'],
                 relief=tk.SOLID, bd=1, insertbackground=self.tema_visual['accent_primary']).pack(side=tk.LEFT)

        botones = tk.Frame(busqueda_frame, bg=self.tema_visual['bg_secundario'])
        botones.pack(side=tk.RIGHT)
        BotonModerno(botones, texto=f"{ICONOS['buscar']} Agregar", tema=self.tema_visual,
                     tipo='primary', command=self.agregar_participantes_multiples).pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        BotonModerno(botones, texto=f"{ICONOS['guardar']} Pago en lugar", tema=self.tema_visual,
                     tipo='secondary', command=self.registrar_pago_en_lugar).pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        BotonModerno(botones, texto=f"{ICONOS['eliminar']} Quitar", tema=self.tema_visual,
                     tipo='error', command=self.eliminar_participante).pack(side=tk.LEFT)

        cols = ('folio', 'nombre', 'estado', 'hora')
        self.tree_participantes = ttk.Treeview(panel.content_frame, columns=cols, show='headings', height=12)
        self.tree_participantes.heading('folio', text='Folio')
        self.tree_participantes.heading('nombre', text='Nombre')
        self.tree_participantes.heading('estado', text='Modo')
        self.tree_participantes.heading('hora', text='Hora')
        self.tree_participantes.column('folio', width=90, anchor='center')
        self.tree_participantes.column('nombre', width=200)
        self.tree_participantes.column('estado', width=110, anchor='center')
        self.tree_participantes.column('hora', width=80, anchor='center')

        scroll_y = ttk.Scrollbar(panel.content_frame, orient=tk.VERTICAL, command=self.tree_participantes.yview)
        self.tree_participantes.configure(yscrollcommand=scroll_y.set)
        self.tree_participantes.grid(row=2, column=0, sticky='nsew')
        scroll_y.grid(row=2, column=1, sticky='ns')

    def _crear_panel_resumen(self, parent):
        self.panel_resumen = PanelModerno(parent, titulo="▼ 📊 Resumen anual de puntos", tema=self.tema_visual)
        self.panel_resumen.grid(row=2, column=0, columnspan=2, sticky='nsew', pady=(ESPACIADO['lg'], 0))
        self.panel_resumen.content_frame.columnconfigure(0, weight=1)
        self.panel_resumen.content_frame.rowconfigure(1, weight=1)
        
        # Hacer el título clickeable para colapsar/expandir
        self.panel_resumen.titulo_label.bind('<Button-1>', lambda e: self._toggle_panel_resumen(self.panel_resumen))
        self.panel_resumen.titulo_label.config(cursor='hand2')

        filtros = tk.Frame(self.panel_resumen.content_frame, bg=self.tema_visual['bg_secundario'])
        filtros.grid(row=0, column=0, sticky='we', pady=(0, ESPACIADO['sm']))

        tk.Label(filtros, text="Año", font=FUENTES['subtitulo'],
                 bg=self.tema_visual['bg_secundario'], fg=self.tema_visual['fg_principal']).pack(side=tk.LEFT)
        años_disponibles = self.servicio.obtener_años_disponibles(self.faenas)
        valores_anio = [str(a) for a in años_disponibles]
        valor_inicial = str(self.default_year) if (self.default_year and str(self.default_year) in valores_anio) else str(datetime.now().year)
        self.anio_var = tk.StringVar(value=valor_inicial)
        self.anio_combo = ttk.Combobox(filtros, textvariable=self.anio_var, values=valores_anio, width=8,
                 state='readonly')
        self.anio_combo.pack(side=tk.LEFT, padx=ESPACIADO['sm'])
        # Auto-actualizar al cambiar año
        self.anio_combo.bind('<<ComboboxSelected>>', lambda e: self.actualizar_resumen_anual())

        # Búsqueda inteligente en resumen
        tk.Label(filtros, text="Buscar", font=FUENTES['subtitulo'],
                 bg=self.tema_visual['bg_secundario'], fg=self.tema_visual['fg_principal']).pack(side=tk.LEFT, padx=(ESPACIADO['md'], ESPACIADO['xs']))
        self.resumen_buscar_var = tk.StringVar()
        entry_resumen_buscar = ttk.Entry(filtros, textvariable=self.resumen_buscar_var, width=24)
        entry_resumen_buscar.pack(side=tk.LEFT)
        self.resumen_buscar_var.trace_add('write', lambda *args: self.actualizar_resumen_anual())

        cols = ('folio', 'nombre', 'puntos')
        self.tree_resumen = ttk.Treeview(self.panel_resumen.content_frame, columns=cols, show='headings', height=8)
        self.tree_resumen.heading('folio', text='Folio')
        self.tree_resumen.heading('nombre', text='Nombre')
        self.tree_resumen.heading('puntos', text='Puntos')
        self.tree_resumen.column('folio', width=90, anchor='center')
        self.tree_resumen.column('nombre', width=260)
        self.tree_resumen.column('puntos', width=120, anchor='center')

        scroll_y = ttk.Scrollbar(self.panel_resumen.content_frame, orient=tk.VERTICAL, command=self.tree_resumen.yview)
        self.tree_resumen.configure(yscrollcommand=scroll_y.set)

        self.tree_resumen.grid(row=1, column=0, sticky='nsew')
        scroll_y.grid(row=1, column=1, sticky='ns')

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def registrar_faena(self):
        print("[DEBUG] registrar_faena invoked")
        nombre = self.nombre_var.get().strip()
        fecha_txt = self.fecha_var.get().strip()
        try:
            fecha_dt = datetime.strptime(fecha_txt, "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Error", "Fecha inválida. Usa DD/MM/AAAA")
            return
        peso = int(self.peso_var.get())
        # Construir horario en formato 12hr
        hora_inicio = f"{self.hora_inicio_var.get()} {self.hora_inicio_ampm_var.get()}" if self.hora_inicio_var.get() else ''
        hora_fin = f"{self.hora_fin_var.get()} {self.hora_fin_ampm_var.get()}" if self.hora_fin_var.get() else ''
        if not nombre:
            messagebox.showerror("Error", "El nombre de la faena es obligatorio")
            return
        if peso < 1 or peso > 10:
            messagebox.showerror("Error", "El peso debe estar entre 1 y 10")
            return
        fecha_iso = fecha_dt.strftime("%Y-%m-%d")
        if any(f['fecha'] == fecha_iso for f in self.faenas):
            messagebox.showerror("Error", "Ya existe una faena registrada para esa fecha")
            return

        # Verificar si es fecha futura
        hoy = datetime.now().date()
        es_futura = fecha_dt.date() > hoy

        faena = {
            'id': f"faena-{uuid4().hex[:8]}",
            'fecha': fecha_iso,
            'nombre': nombre,
            'peso': peso,
            'hora_inicio': hora_inicio,
            'hora_fin': hora_fin,
            'es_programada': es_futura,
            'participantes': [],
            'pagos_sustitutos': [],
            'monto_pago_faena': None,
            'creado_por': self.usuario_actual.get('nombre') if self.usuario_actual else 'Sistema'
        }
        self.faenas.append(faena)
        self.gestor_historial.registrar_creacion('FAENA', faena['id'], faena, faena['creado_por'])
        registrar_operacion('FAENA_CREADA', 'Faena registrada', {'fecha': fecha_iso, 'nombre': nombre, 'peso': peso, 'es_programada': es_futura})

        self.nombre_var.set('')
        self.peso_var.set(5)
        self.hora_inicio_var.set('9')
        self.hora_inicio_ampm_var.set('AM')
        self.hora_fin_var.set('1')
        self.hora_fin_ampm_var.set('PM')
        self.actualizar_listado_faenas(seleccionar_id=faena['id'])
        self.actualizar_resumen_anual()
        self.guardar_datos()
        if es_futura:
            messagebox.showinfo("Faena programada", f"Faena programada para {fecha_txt}.\nNo se pueden agregar participantes hasta esa fecha.")
        else:
            messagebox.showinfo("Listo", "Faena registrada. Ahora agrega participantes del día.")

    def on_select_faena(self, _event=None):
        seleccion = self.tree_faenas.selection()
        if not seleccion:
            self.faena_seleccionada = None
            self.lbl_faena_actual.config(text="Sin faena seleccionada")
            self.tree_participantes.delete(*self.tree_participantes.get_children())
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
            self.lbl_faena_actual.config(text=texto)
            self.actualizar_detalle_faena()

    def actualizar_detalle_faena(self):
        self.tree_participantes.delete(*self.tree_participantes.get_children())
        if not self.faena_seleccionada:
            return
        
        criterio = self.buscar_participante_var.get().lower().strip() if hasattr(self, 'buscar_participante_var') else ''
        
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
                # Mantener compatibilidad con sistema antiguo de pagos
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
            
            self.tree_participantes.insert('', tk.END, values=(folio, nombre, estado, hora))

    def agregar_participantes_multiples(self):
        print("[DEBUG] agregar_participantes_multiples invoked")
        if not self.faena_seleccionada:
            messagebox.showwarning("Selecciona una faena", "Primero registra y selecciona la faena del día")
            return
        
        # Validar que no sea una faena programada (futura)
        if self.faena_seleccionada.get('es_programada'):
            messagebox.showwarning("Faena programada", "No se pueden agregar participantes a faenas futuras.\nEspera a que llegue la fecha.")
            return
        
        # Validar que no hayan pasado más de 7 días desde la faena
        if not self._puede_editar_faena():
            messagebox.showwarning("Faena expirada", "Han pasado más de 7 días desde la faena.\nYa no se pueden modificar los registros.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Agregar participantes")
        dialog.geometry("520x560")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Buscar habitante", font=FUENTES['subtitulo']).pack(pady=ESPACIADO['sm'])
        filtro_var = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=filtro_var, font=FUENTES['normal'])
        entry.pack(fill=tk.X, padx=ESPACIADO['lg'])

        columns = ('check', 'folio', 'nombre')
        tree = ttk.Treeview(dialog, columns=columns, show='headings', selectmode='none')
        tree.heading('check', text='✔')
        tree.heading('folio', text='Folio')
        tree.heading('nombre', text='Nombre')
        tree.column('check', width=40, anchor='center')
        tree.column('folio', width=100, anchor='center')
        tree.column('nombre', width=320)
        tree.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['lg'], pady=ESPACIADO['sm'])

        def refrescar_lista(_evt=None):
            tree.delete(*tree.get_children())
            criterio = filtro_var.get().lower().strip()
            for h in self.habitantes_cache:
                folio = h.get('folio', '')
                nombre = h.get('nombre', '')
                texto = f"{folio} - {nombre}".strip()
                
                # No mostrar habitantes que ya están en la faena
                if any(p.get('folio') == folio and p.get('nombre') == nombre for p in self.faena_seleccionada['participantes']):
                    continue
                
                if criterio and criterio not in texto.lower():
                    continue
                
                tree.insert('', tk.END, values=('☐', folio, nombre))
        filtro_var.trace_add('write', refrescar_lista)
        refrescar_lista()

        def toggle_item(event):
            item = tree.identify_row(event.y)
            if not item:
                return
            vals = list(tree.item(item, 'values'))
            vals[0] = '☐' if vals[0] == '☑' else '☑'
            tree.item(item, values=vals)
        tree.bind('<Button-1>', toggle_item)

        def agregar_seleccion():
            nuevos = []
            for item in tree.get_children():
                vals = tree.item(item, 'values')
                if vals and vals[0] == '☑':
                    folio, nombre = vals[1], vals[2]
                    if any(p.get('folio') == folio and p.get('nombre') == nombre for p in self.faena_seleccionada['participantes']):
                        continue
                    participante = {
                        'folio': folio,
                        'nombre': nombre or folio,
                        'hora_registro': datetime.now().isoformat()
                    }
                    self.faena_seleccionada['participantes'].append(participante)
                    nuevos.append(participante)
            if nuevos:
                self.gestor_historial.registrar_cambio('AGREGAR', 'FAENA_PARTICIPANTE', self.faena_seleccionada['id'],
                    {'participantes': nuevos}, self.usuario_actual.get('nombre', 'Sistema'))
                self.actualizar_detalle_faena()
                self.actualizar_listado_faenas(seleccionar_id=self.faena_seleccionada['id'])
                self.actualizar_resumen_anual()
                self.guardar_datos()
            dialog.destroy()

        tk.Button(dialog, text="Agregar seleccionados", command=agregar_seleccion).pack(pady=ESPACIADO['sm'])
        entry.focus()

    def eliminar_participante(self):
        print("[DEBUG] eliminar_participante invoked")
        if not self.faena_seleccionada:
            return
        
        # Validar que no hayan pasado más de 7 días desde la faena
        if not self._puede_editar_faena():
            messagebox.showwarning("Faena expirada", "Han pasado más de 7 días desde la faena.\nYa no se pueden modificar los registros.")
            return
        
        seleccion = self.tree_participantes.selection()
        if not seleccion:
            return
        idx = self.tree_participantes.index(seleccion[0])
        try:
            participante = self.faena_seleccionada['participantes'].pop(idx)
            if participante.get('pago_monto'):
                messagebox.showwarning("No permitido", "No puedes remover a alguien que ya pagó en lugar de asistir")
                # Reinsertar en su posición original
                self.faena_seleccionada['participantes'].insert(idx, participante)
                return
            self.gestor_historial.registrar_cambio('ELIMINAR', 'FAENA_PARTICIPANTE', self.faena_seleccionada['id'],
                {'participante': participante}, self.usuario_actual.get('nombre', 'Sistema'))
            self.actualizar_detalle_faena()
            self.actualizar_listado_faenas(seleccionar_id=self.faena_seleccionada['id'])
            self.actualizar_resumen_anual()
            self.guardar_datos()
        except Exception as e:
            registrar_error('faenas', 'eliminar_participante', str(e))

    def registrar_pago_en_lugar(self):
        print("[DEBUG] registrar_pago_en_lugar invoked")
        if not self.faena_seleccionada:
            messagebox.showwarning("Selecciona una faena", "Primero elige la faena del día")
            return
        
        # Validar que no sea una faena programada (futura)
        if self.faena_seleccionada.get('es_programada'):
            messagebox.showwarning("Faena programada", "No se pueden registrar sustituciones en faenas futuras.\nEspera a que llegue la fecha.")
            return
        
        # Validar que no hayan pasado más de 7 días desde la faena
        if not self._puede_editar_faena():
            messagebox.showwarning("Faena expirada", "Han pasado más de 7 días desde la faena.\nYa no se pueden modificar los registros.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Registrar sustitución de faena")
        dialog.geometry("620x700")
        dialog.transient(self.root)
        dialog.grab_set()

        # Instrucciones
        instrucciones = tk.Label(dialog, 
            text="Selecciona quién pagó por la faena y especifica si contrató a un habitante o a alguien externo.\n"
                 "• Habitante del pueblo: 90% de peso para quien pagó + 100% para quien trabajó\n"
                 "• Externo (albañil, etc.): 100% de peso para quien pagó",
            font=FUENTES['pequeño'], justify=tk.LEFT, wraplength=560,
            bg=self.tema_visual['bg_principal'], fg=self.tema_visual['fg_secundario'])
        instrucciones.pack(pady=ESPACIADO['md'], padx=ESPACIADO['lg'], anchor='w')

        # Selección de quien pagó
        tk.Label(dialog, text="¿Quién pagó por la faena?", font=FUENTES['subtitulo']).pack(pady=(ESPACIADO['sm'], 2), padx=ESPACIADO['lg'], anchor='w')
        filtro_pagador_var = tk.StringVar()
        tk.Entry(dialog, textvariable=filtro_pagador_var, font=FUENTES['normal']).pack(fill=tk.X, padx=ESPACIADO['lg'])

        columns_pagador = ('check', 'folio', 'nombre')
        tree_pagador = ttk.Treeview(dialog, columns=columns_pagador, show='headings', selectmode='none', height=6)
        tree_pagador.heading('check', text='✔')
        tree_pagador.heading('folio', text='Folio')
        tree_pagador.heading('nombre', text='Nombre')
        tree_pagador.column('check', width=40, anchor='center')
        tree_pagador.column('folio', width=100, anchor='center')
        tree_pagador.column('nombre', width=420)
        tree_pagador.pack(fill=tk.X, padx=ESPACIADO['lg'], pady=(ESPACIADO['sm'], ESPACIADO['md']))

        def refrescar_lista_pagador(_evt=None):
            tree_pagador.delete(*tree_pagador.get_children())
            criterio = filtro_pagador_var.get().lower().strip()
            # Mostrar habitantes que NO están ya en la lista de participantes (ni asistieron ni pagaron)
            todos = self.habitantes_cache
            for h in todos:
                folio = h.get('folio', '')
                nombre = h.get('nombre', '')
                texto = f"{folio} - {nombre}".strip()
                if criterio and criterio not in texto.lower():
                    continue
                
                # Verificar si ya está en la faena
                participante_existente = next((p for p in self.faena_seleccionada['participantes'] 
                                              if p.get('folio') == folio), None)
                
                if not participante_existente:
                    tree_pagador.insert('', tk.END, values=('☐', folio, nombre))
        
        filtro_pagador_var.trace_add('write', refrescar_lista_pagador)
        refrescar_lista_pagador()

        def toggle_pagador(event):
            item = tree_pagador.identify_row(event.y)
            if not item:
                return
            vals = list(tree_pagador.item(item, 'values'))
            # Solo permitir una selección a la vez
            for child in tree_pagador.get_children():
                vals_child = list(tree_pagador.item(child, 'values'))
                vals_child[0] = '☐'
                tree_pagador.item(child, values=vals_child)
            vals[0] = '☑'
            tree_pagador.item(item, values=vals)
        
        tree_pagador.bind('<Button-1>', toggle_pagador)

        # Separador
        ttk.Separator(dialog, orient='horizontal').pack(fill=tk.X, pady=ESPACIADO['md'], padx=ESPACIADO['lg'])

        # Tipo de sustitución
        tk.Label(dialog, text="¿Quién realizó el trabajo?", font=FUENTES['subtitulo'],
                bg=self.tema_visual['bg_principal'], fg=self.tema_visual['fg_principal']).pack(pady=(ESPACIADO['sm'], 2), padx=ESPACIADO['lg'], anchor='w')
        
        tipo_sustitucion_var = tk.StringVar(value='habitante')
        frame_tipo = tk.Frame(dialog, bg=self.tema_visual['bg_principal'])
        frame_tipo.pack(fill=tk.X, padx=ESPACIADO['lg'], pady=ESPACIADO['sm'])
        
        rb_habitante = tk.Radiobutton(frame_tipo, text="Habitante del pueblo", variable=tipo_sustitucion_var, 
                                     value='habitante', font=FUENTES['normal'], 
                                     bg=self.tema_visual['bg_principal'], fg=self.tema_visual['fg_principal'])
        rb_habitante.pack(anchor='w')
        
        rb_externo = tk.Radiobutton(frame_tipo, text="Persona externa (albañil, etc.)", variable=tipo_sustitucion_var, 
                                   value='externo', font=FUENTES['normal'],
                                   bg=self.tema_visual['bg_principal'], fg=self.tema_visual['fg_principal'])
        rb_externo.pack(anchor='w', pady=(ESPACIADO['xs'], 0))

        # Frame condicional: habitante
        frame_habitante = tk.Frame(dialog, bg=self.tema_visual['bg_principal'])
        frame_habitante.pack(fill=tk.X, padx=ESPACIADO['lg'], pady=ESPACIADO['sm'])
        
        tk.Label(frame_habitante, text="Selecciona al habitante que realizó el trabajo:", font=FUENTES['pequeño'],
                bg=self.tema_visual['bg_principal'], fg=self.tema_visual['fg_principal']).pack(anchor='w')
        filtro_trabajador_var = tk.StringVar()
        tk.Entry(frame_habitante, textvariable=filtro_trabajador_var, font=FUENTES['normal']).pack(fill=tk.X, pady=(2, ESPACIADO['xs']))
        
        columns_trabajador = ('check', 'folio', 'nombre')
        tree_trabajador = ttk.Treeview(frame_habitante, columns=columns_trabajador, show='headings', selectmode='none', height=5)
        tree_trabajador.heading('check', text='✔')
        tree_trabajador.heading('folio', text='Folio')
        tree_trabajador.heading('nombre', text='Nombre')
        tree_trabajador.column('check', width=40, anchor='center')
        tree_trabajador.column('folio', width=100, anchor='center')
        tree_trabajador.column('nombre', width=390)
        tree_trabajador.pack(fill=tk.X)

        def refrescar_lista_trabajador(_evt=None):
            tree_trabajador.delete(*tree_trabajador.get_children())
            criterio = filtro_trabajador_var.get().lower().strip()
            todos = self.habitantes_cache
            for h in todos:
                folio = h.get('folio', '')
                nombre = h.get('nombre', '')
                texto = f"{folio} - {nombre}".strip()
                if criterio and criterio not in texto.lower():
                    continue
                tree_trabajador.insert('', tk.END, values=('☐', folio, nombre))
        
        filtro_trabajador_var.trace_add('write', refrescar_lista_trabajador)
        refrescar_lista_trabajador()

        def toggle_trabajador(event):
            item = tree_trabajador.identify_row(event.y)
            if not item:
                return
            vals = list(tree_trabajador.item(item, 'values'))
            # Solo permitir una selección
            for child in tree_trabajador.get_children():
                vals_child = list(tree_trabajador.item(child, 'values'))
                vals_child[0] = '☐'
                tree_trabajador.item(child, values=vals_child)
            vals[0] = '☑'
            tree_trabajador.item(item, values=vals)
        
        tree_trabajador.bind('<Button-1>', toggle_trabajador)

        # Frame condicional: externo
        frame_externo = tk.Frame(dialog, bg=self.tema_visual['bg_principal'])
        frame_externo.pack(fill=tk.X, padx=ESPACIADO['lg'], pady=ESPACIADO['sm'])
        
        tk.Label(frame_externo, text="Nombre de la persona externa:", font=FUENTES['pequeño'],
                bg=self.tema_visual['bg_principal'], fg=self.tema_visual['fg_principal']).pack(anchor='w')
        nombre_externo_var = tk.StringVar()
        tk.Entry(frame_externo, textvariable=nombre_externo_var, font=FUENTES['normal']).pack(fill=tk.X)

        def actualizar_visibilidad_frames(_a=None, _b=None, _c=None):
            if tipo_sustitucion_var.get() == 'habitante':
                frame_habitante.pack(fill=tk.X, padx=ESPACIADO['lg'], pady=ESPACIADO['sm'])
                frame_externo.pack_forget()
            else:
                frame_habitante.pack_forget()
                frame_externo.pack(fill=tk.X, padx=ESPACIADO['lg'], pady=ESPACIADO['sm'])
        
        tipo_sustitucion_var.trace_add('write', actualizar_visibilidad_frames)
        actualizar_visibilidad_frames()

        def guardar_sustitucion():
            # Obtener quien pagó
            pagador_seleccionado = None
            for item in tree_pagador.get_children():
                vals = tree_pagador.item(item, 'values')
                if vals and vals[0] == '☑':
                    pagador_seleccionado = (vals[1], vals[2])
                    break
            
            if not pagador_seleccionado:
                messagebox.showwarning("Selección incompleta", "Debes seleccionar quién pagó por la faena")
                return
            
            folio_pagador, nombre_pagador = pagador_seleccionado
            tipo = tipo_sustitucion_var.get()
            
            if tipo == 'habitante':
                # Obtener el trabajador seleccionado
                trabajador_seleccionado = None
                for item in tree_trabajador.get_children():
                    vals = tree_trabajador.item(item, 'values')
                    if vals and vals[0] == '☑':
                        trabajador_seleccionado = (vals[1], vals[2])
                        break
                
                if not trabajador_seleccionado:
                    messagebox.showwarning("Selección incompleta", "Debes seleccionar al habitante que realizó el trabajo")
                    return
                
                folio_trabajador, nombre_trabajador = trabajador_seleccionado
                
                if folio_pagador == folio_trabajador:
                    messagebox.showwarning("Error", "No puedes seleccionar a la misma persona como pagador y trabajador.\nSi asistió personalmente, agrégalo desde el botón 'Agregar participantes'.")
                    return
                
                # Agregar al pagador con penalización del 10%
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
                        'peso_aplicado': 0.9  # 90% del peso
                    }
                    self.faena_seleccionada['participantes'].append(participante_pagador)
                else:
                    # Actualizar si ya existía
                    participante_pagador['sustitucion_tipo'] = 'habitante'
                    participante_pagador['trabajador_folio'] = folio_trabajador
                    participante_pagador['trabajador_nombre'] = nombre_trabajador
                    participante_pagador['peso_aplicado'] = 0.9
                
                # Agregar al trabajador con peso completo
                participante_trabajador = next((p for p in self.faena_seleccionada['participantes'] 
                                              if p.get('folio') == folio_trabajador), None)
                if not participante_trabajador:
                    participante_trabajador = {
                        'folio': folio_trabajador,
                        'nombre': nombre_trabajador or folio_trabajador,
                        'hora_registro': datetime.now().isoformat(),
                        'peso_aplicado': 1.0  # 100% del peso
                    }
                    self.faena_seleccionada['participantes'].append(participante_trabajador)
                
                mensaje = f"{nombre_pagador} contrató a {nombre_trabajador} (habitante)"
                
            else:  # externo
                nombre_ext = nombre_externo_var.get().strip()
                if not nombre_ext:
                    messagebox.showwarning("Dato faltante", "Debes escribir el nombre de la persona externa")
                    return
                
                # Agregar solo al pagador con peso completo
                participante_pagador = next((p for p in self.faena_seleccionada['participantes'] 
                                           if p.get('folio') == folio_pagador), None)
                if not participante_pagador:
                    participante_pagador = {
                        'folio': folio_pagador,
                        'nombre': nombre_pagador or folio_pagador,
                        'hora_registro': datetime.now().isoformat(),
                        'sustitucion_tipo': 'externo',
                        'trabajador_nombre': nombre_ext,
                        'peso_aplicado': 1.0  # 100% del peso
                    }
                    self.faena_seleccionada['participantes'].append(participante_pagador)
                else:
                    participante_pagador['sustitucion_tipo'] = 'externo'
                    participante_pagador['trabajador_nombre'] = nombre_ext
                    participante_pagador['peso_aplicado'] = 1.0
                
                mensaje = f"{nombre_pagador} contrató a {nombre_ext} (externo)"

            # Registrar en historial
            self.gestor_historial.registrar_cambio('SUSTITUCION_FAENA', 'FAENA', self.faena_seleccionada['id'],
                {'tipo': tipo, 'pagador': folio_pagador, 'descripcion': mensaje}, 
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
            dialog.destroy()

        tk.Button(dialog, text="Registrar sustitución", command=guardar_sustitucion, 
                 font=FUENTES['normal'], bg=self.tema_visual['accent_primary'], 
                 fg='white', relief=tk.FLAT, cursor='hand2').pack(pady=ESPACIADO['md'])

    def actualizar_listado_faenas(self, seleccionar_id=None):
        self.tree_faenas.delete(*self.tree_faenas.get_children())
        ordenadas = sorted(self.faenas, key=lambda f: f.get('fecha', ''), reverse=True)
        for faena in ordenadas:
            self._normalizar_faena(faena)
            iid = faena['id']
            self.tree_faenas.insert('', tk.END, iid=iid, values=(
                self._formato_fecha(faena.get('fecha', '')),
                faena.get('nombre', ''),
                faena.get('peso', 0),
                len(faena.get('participantes', []))
            ))
        if seleccionar_id:
            if self.tree_faenas.exists(seleccionar_id):
                self.tree_faenas.selection_set(seleccionar_id)
                self.tree_faenas.see(seleccionar_id)
                self.on_select_faena()

    def actualizar_resumen_anual(self):
        if not hasattr(self, 'tree_resumen'):
            return  # El árbol aún no existe
            
        self.tree_resumen.delete(*self.tree_resumen.get_children())
        try:
            anio = int(self.anio_var.get()) if hasattr(self, 'anio_var') else datetime.now().year
        except ValueError:
            anio = datetime.now().year

        años_disponibles = self.servicio.obtener_años_disponibles(self.faenas)
        if hasattr(self, 'anio_combo'):
            self.anio_combo['values'] = [str(a) for a in años_disponibles]
            if str(anio) not in self.anio_combo['values']:
                self.anio_var.set(str(datetime.now().year))
                anio = datetime.now().year
        
        resumen = self.servicio.calcular_resumen_anual(self.faenas, anio)
        puntos = resumen.get('puntos', {})
        max_puntos = resumen.get('max_puntos', 1)
        
        # Filtrar por búsqueda inteligente
        criterio = self.resumen_buscar_var.get().lower().strip() if hasattr(self, 'resumen_buscar_var') else ''
        if criterio:
            puntos = self.servicio.filtrar_resumen_por_criterio(puntos, criterio)

        if not puntos:
            return
        
        # Configurar tags con colores antes de insertar
        for data in sorted(puntos.values(), key=lambda x: (-x['puntos'], x['nombre'])):
            color = self.servicio.calcular_color_por_puntaje(data['puntos'], max_puntos)
            tag = f"color-{data['folio']}"
            # Texto negro para fondos claros, blanco para fondos oscuros
            texto_color = '#ffffff' if data['puntos'] >= max_puntos * 0.7 else '#1f2937'
            self.tree_resumen.tag_configure(tag, background=color, foreground=texto_color)
            self.tree_resumen.insert('', tk.END, values=(data['folio'], data['nombre'], f"{data['puntos']:.1f}"), tags=(tag,))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _toggle_panel_resumen(self, panel):
        """Colapsa o expande el panel de resumen anual"""
        if panel.content_frame.winfo_ismapped():
            panel.content_frame.pack_forget()
            titulo_actual = panel.titulo_label.cget('text')
            nuevo_titulo = titulo_actual.replace('▼', '▶')
            panel.titulo_label.config(text=nuevo_titulo)
        else:
            panel.content_frame.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['lg'], pady=ESPACIADO['lg'])
            titulo_actual = panel.titulo_label.cget('text')
            nuevo_titulo = titulo_actual.replace('▶', '▼')
            panel.titulo_label.config(text=nuevo_titulo)
            # Actualizar resumen cuando se expande
            self.actualizar_resumen_anual()
    
    def _puede_editar_faena(self):
        """
        Valida si una faena puede ser editada.
        Retorna False si han pasado más de 7 días desde la fecha de la faena.
        """
        try:
            resultado = self.servicio.validar_puede_editar_faena(self.faena_seleccionada, dias_limite=7)
            return resultado.get('puede_editar', False)
        except Exception as e:
            print(f"Error validando fecha: {e}")
            return True  # Por defecto permitir
    
    @staticmethod
    def _formato_fecha(fecha_iso):
        try:
            return datetime.strptime(fecha_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            return fecha_iso

def main():
    """Punto de entrada principal con autenticación"""
    from src.auth.login_window import VentanaLogin

    # Crear ventana de login
    login_root = tk.Tk()

    def on_login(usuario, gestor_auth):
        """Callback cuando el login es exitoso"""
        # Cerrar ventana de login
        login_root.destroy()
        
        # Crear ventana principal
        root = tk.Tk()
        root.title(f"Registro de Faenas - {usuario['nombre']} ({usuario['rol']})")
        
        # Permitir pasar año por defecto via argumentos (--anio 2025)
        default_year = None
        try:
            args = sys.argv[1:]
            if '--anio' in args:
                idx = args.index('--anio')
                if idx + 1 < len(args):
                    default_year = int(args[idx+1])
        except Exception:
            default_year = None

        app = SistemaFaenas(root, usuario, gestor_auth, default_year=default_year)
        root.mainloop()

    VentanaLogin(login_root, on_login)
    login_root.mainloop()


if __name__ == '__main__':
    main()
