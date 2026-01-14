import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Dict, Callable, Optional

from src.ui.estilos_globales import TEMA_GLOBAL
from src.ui.tema_moderno import FUENTES, ESPACIADO, ICONOS
from src.ui.ui_moderna import BarraSuperior, PanelModerno, BotonModerno
from src.config import (
    HORA_INICIO_DEFECTO, HORA_INICIO_AMPM_DEFECTO,
    HORA_FIN_DEFECTO, HORA_FIN_AMPM_DEFECTO,
    PESO_FAENA_DEFECTO
)
from src.modules.faenas.dashboard_faenas import DashboardFaenas
from src.modules.faenas.buscador_avanzado import BuscadorAvanzadoFaenas


class FaenasUIManager:
    """Gestor de componentes UI para el sistema de faenas"""

    def __init__(self, root, usuario: Dict, callbacks: Dict, tema: Dict = None):
        """
        Inicializar gestor de UI
        
        Args:
            root: Ventana raíz de Tkinter
            usuario: Diccionario con información del usuario actual
            callbacks: Diccionario con funciones callback para eventos
            tema: Tema visual a usar
        """
        self.root = root
        self.usuario = usuario
        self.callbacks = callbacks
        self.tema = tema or TEMA_GLOBAL

        # Variables de formulario
        self.fecha_var = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y"))
        self.nombre_var = tk.StringVar()
        self.peso_var = tk.IntVar(value=PESO_FAENA_DEFECTO)
        self.hora_inicio_var = tk.StringVar(value=HORA_INICIO_DEFECTO)
        self.hora_inicio_ampm_var = tk.StringVar(value=HORA_INICIO_AMPM_DEFECTO)
        self.hora_fin_var = tk.StringVar(value=HORA_FIN_DEFECTO)
        self.hora_fin_ampm_var = tk.StringVar(value=HORA_FIN_AMPM_DEFECTO)
        self.buscar_participante_var = tk.StringVar()
        self.anio_var = tk.StringVar(value=str(datetime.now().year))
        self.resumen_buscar_var = tk.StringVar()

        # Referencias a widgets
        self.barra: Optional[BarraSuperior] = None
        self.tree_faenas: Optional[ttk.Treeview] = None
        self.tree_participantes: Optional[ttk.Treeview] = None
        self.tree_resumen: Optional[ttk.Treeview] = None
        self.lbl_faena_actual: Optional[tk.Label] = None
        self.anio_combo: Optional[ttk.Combobox] = None
        self.panel_resumen: Optional[PanelModerno] = None

    def configurar_interfaz(self) -> None:
        """Configurar toda la interfaz de usuario"""
        self.root.configure(bg=self.tema['bg_principal'])

        # Barra superior
        self.barra = BarraSuperior(self.root, self.usuario, lambda: None)
        self.barra.pack(fill=tk.X)

        # Contenedor con scroll
        scroll_container = tk.Frame(self.root, bg=self.tema['bg_principal'])
        scroll_container.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['lg'], pady=ESPACIADO['lg'])
        scroll_container.columnconfigure(0, weight=1)
        scroll_container.rowconfigure(0, weight=1)

        canvas = tk.Canvas(scroll_container, bg=self.tema['bg_principal'], highlightthickness=0)
        canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar = ttk.Scrollbar(scroll_container, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        canvas.configure(yscrollcommand=scrollbar.set)

        main = tk.Frame(canvas, bg=self.tema['bg_principal'])
        window_id = canvas.create_window((0, 0), window=main, anchor='nw')

        # Ajustar región de scroll
        main.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(window_id, width=e.width))

        # Scroll del canvas
        def _on_canvas_scroll(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        canvas.bind('<MouseWheel>', _on_canvas_scroll)

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=0)
        main.rowconfigure(1, weight=0)
        main.rowconfigure(2, weight=1)
        main.rowconfigure(3, weight=1)

        dashboard = DashboardFaenas(main, self.callbacks.get('obtener_datos_dashboard', lambda: {}))
        dashboard.frame.grid(row=0, column=0, columnspan=2, sticky='nsew', pady=(0, ESPACIADO['lg']))
        
        buscador = BuscadorAvanzadoFaenas(main, self.callbacks.get('busqueda_avanzada', lambda x: None))
        buscador.frame.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=(0, ESPACIADO['lg']))
        
        self._crear_panel_formulario(main)
        self._crear_panel_listado(main)
        self._crear_panel_detalle(main)
        self._crear_panel_resumen(main)

    def _crear_panel_formulario(self, parent) -> None:
        """Crear panel de formulario para registrar faenas"""
        panel = PanelModerno(parent, titulo="Registrar faena del día", tema=self.tema)
        panel.grid(row=0, column=0, columnspan=2, sticky='nsew', pady=(0, ESPACIADO['lg']))

        frm = panel.content_frame
        frm.columnconfigure(1, weight=1)

        # Fecha
        tk.Label(frm, text="Fecha (DD/MM/AAAA)", font=FUENTES['subtitulo'],
                 bg=self.tema['bg_secundario'], fg=self.tema['fg_principal']).grid(
            row=0, column=0, sticky='w')
        tk.Entry(frm, textvariable=self.fecha_var, font=FUENTES['normal'],
                 bg=self.tema['input_bg'], fg=self.tema['fg_principal'],
                 relief=tk.SOLID, bd=1, width=14,
                 insertbackground=self.tema['accent_primary']).grid(row=0, column=1, sticky='w')

        # Nombre
        tk.Label(frm, text="Nombre de la faena", font=FUENTES['subtitulo'],
                 bg=self.tema['bg_secundario'], fg=self.tema['fg_principal']).grid(
            row=1, column=0, sticky='w', pady=(ESPACIADO['sm'], 0))
        tk.Entry(frm, textvariable=self.nombre_var, font=FUENTES['normal'],
                 bg=self.tema['input_bg'], fg=self.tema['fg_principal'],
                 relief=tk.SOLID, bd=1, width=38,
                 insertbackground=self.tema['accent_primary']).grid(row=1, column=1, sticky='w')

        # Horario
        tk.Label(frm, text="Horario", font=FUENTES['subtitulo'],
                 bg=self.tema['bg_secundario'], fg=self.tema['fg_principal']).grid(
            row=1, column=2, sticky='w', pady=(ESPACIADO['sm'], 0), padx=(ESPACIADO['lg'], 0))
        self._crear_selector_horario(frm)

        # Peso
        tk.Label(frm, text="Peso (1-10)", font=FUENTES['subtitulo'],
                 bg=self.tema['bg_secundario'], fg=self.tema['fg_principal']).grid(
            row=2, column=0, sticky='w', pady=(ESPACIADO['sm'], 0))
        self._crear_selector_peso(frm)

        # Botones de acción
        self._crear_botones_formulario(frm)

    def _crear_selector_horario(self, parent) -> None:
        """Crear selectores de horario"""
        horario_frame = tk.Frame(parent, bg=self.tema['bg_secundario'])
        horario_frame.grid(row=1, column=3, sticky='w')

        # Hora inicio
        ttk.Combobox(horario_frame, textvariable=self.hora_inicio_var,
                     values=[str(i) for i in range(1, 13)],
                     width=3, state='readonly').pack(side=tk.LEFT)
        ttk.Combobox(horario_frame, textvariable=self.hora_inicio_ampm_var,
                     values=['AM', 'PM'],
                     width=4, state='readonly').pack(side=tk.LEFT, padx=(2, 4))

        tk.Label(horario_frame, text="a", font=FUENTES['normal'],
                 bg=self.tema['bg_secundario'], fg=self.tema['fg_principal']).pack(
            side=tk.LEFT, padx=4)

        # Hora fin
        ttk.Combobox(horario_frame, textvariable=self.hora_fin_var,
                     values=[str(i) for i in range(1, 13)],
                     width=3, state='readonly').pack(side=tk.LEFT)
        ttk.Combobox(horario_frame, textvariable=self.hora_fin_ampm_var,
                     values=['AM', 'PM'],
                     width=4, state='readonly').pack(side=tk.LEFT, padx=(2, 0))

    def _crear_selector_peso(self, parent) -> None:
        """Crear selector de peso"""
        peso_row = tk.Frame(parent, bg=self.tema['bg_secundario'])
        peso_row.grid(row=2, column=1, sticky='we')
        peso_row.columnconfigure(0, weight=1)

        tk.Scale(peso_row, from_=1, to=10, orient=tk.HORIZONTAL, variable=self.peso_var,
                 length=200, showvalue=False,
                 bg=self.tema['bg_secundario'], fg=self.tema['fg_principal'],
                 troughcolor=self.tema['accent_light'], highlightthickness=0,
                 activebackground=self.tema['accent_primary']).grid(row=0, column=0, sticky='w')

        tk.Entry(peso_row, textvariable=self.peso_var, width=4, font=FUENTES['normal'],
                 bg=self.tema['input_bg'], fg=self.tema['fg_principal'],
                 relief=tk.SOLID, bd=1, justify='center',
                 insertbackground=self.tema['accent_primary']).grid(
            row=0, column=1, padx=(ESPACIADO['sm'], 0))

    def _crear_botones_formulario(self, parent) -> None:
        """Crear botones de acción del formulario"""
        acciones = tk.Frame(parent, bg=self.tema['bg_secundario'])
        acciones.grid(row=0, column=4, rowspan=3, padx=ESPACIADO['lg'])

        BotonModerno(acciones, texto="Registrar faena del día", tema=self.tema,
                     command=self.callbacks.get('registrar_faena')).pack(
            fill=tk.X, pady=(0, ESPACIADO['sm']))

        BotonModerno(acciones, texto="Refrescar habitantes", tema=self.tema,
                     tipo='secondary',
                     command=self.callbacks.get('refrescar_habitantes')).pack(fill=tk.X)

    def _crear_panel_listado(self, parent) -> None:
        panel = PanelModerno(parent, titulo="Faenas registradas", tema=self.tema)
        panel.grid(row=2, column=0, sticky='nsew', padx=(0, ESPACIADO['lg']))
        panel.content_frame.rowconfigure(1, weight=1)
        panel.content_frame.columnconfigure(0, weight=1)

        filtro_frame = tk.Frame(panel.content_frame, bg=self.tema['bg_secundario'])
        filtro_frame.grid(row=0, column=0, sticky='we', pady=(0, ESPACIADO['sm']))

        tk.Label(filtro_frame, text="Estado:", font=FUENTES['normal'],
                bg=self.tema['bg_secundario'], fg=self.tema['fg_principal']).pack(side=tk.LEFT, padx=5)
        ttk.Combobox(filtro_frame, values=['Todas', 'Completadas', 'Pagadas', 'Pendientes'],
                    width=15, state='readonly').pack(side=tk.LEFT, padx=5)

        columns = ('fecha', 'nombre', 'peso', 'participantes', 'estado')
        self.tree_faenas = ttk.Treeview(panel.content_frame, columns=columns,
                                        show='headings', height=14)
        self.tree_faenas.heading('fecha', text='Fecha')
        self.tree_faenas.heading('nombre', text='Faena')
        self.tree_faenas.heading('peso', text='Peso')
        self.tree_faenas.heading('participantes', text='Participantes')
        self.tree_faenas.heading('estado', text='Estado')

        self.tree_faenas.column('fecha', width=100, anchor='center')
        self.tree_faenas.column('nombre', width=220)
        self.tree_faenas.column('peso', width=60, anchor='center')
        self.tree_faenas.column('participantes', width=100, anchor='center')
        self.tree_faenas.column('estado', width=80, anchor='center')

        self.tree_faenas.tag_configure('completada', background='#d4edda')
        self.tree_faenas.tag_configure('pagada', background='#cce5ff')
        self.tree_faenas.tag_configure('pendiente', background='#fff3cd')

        scroll_y = ttk.Scrollbar(panel.content_frame, orient=tk.VERTICAL,
                                 command=self.tree_faenas.yview)
        self.tree_faenas.configure(yscrollcommand=scroll_y.set)

        self.tree_faenas.grid(row=1, column=0, sticky='nsew')
        scroll_y.grid(row=1, column=1, sticky='ns')

        self.tree_faenas.bind('<<TreeviewSelect>>',
                              self.callbacks.get('on_select_faena'))
        self.tree_faenas.bind('<Button-3>', self._mostrar_menu_contexto)

    def _crear_panel_detalle(self, parent) -> None:
        panel = PanelModerno(parent, titulo="Participantes de la faena", tema=self.tema)
        panel.grid(row=2, column=1, sticky='nsew')
        panel.content_frame.rowconfigure(2, weight=1)
        panel.content_frame.columnconfigure(0, weight=1)

        # Info faena actual
        info = tk.Frame(panel.content_frame, bg=self.tema['bg_secundario'])
        info.grid(row=0, column=0, sticky='we', pady=(0, ESPACIADO['sm']))
        self.lbl_faena_actual = tk.Label(info, text="Sin faena seleccionada",
                                         font=FUENTES['subtitulo'],
                                         bg=self.tema['bg_secundario'],
                                         fg=self.tema['fg_principal'])
        self.lbl_faena_actual.pack(side=tk.LEFT)

        # Búsqueda y botones
        self._crear_controles_participantes(panel.content_frame)

        # TreeView participantes
        self._crear_tree_participantes(panel.content_frame)

    def _crear_controles_participantes(self, parent) -> None:
        """Crear controles de búsqueda y botones de participantes"""
        busqueda_frame = tk.Frame(parent, bg=self.tema['bg_secundario'])
        busqueda_frame.grid(row=1, column=0, sticky='we', pady=(0, ESPACIADO['sm']))

        tk.Label(busqueda_frame, text="Buscar:", font=FUENTES['normal'],
                 bg=self.tema['bg_secundario'], fg=self.tema['fg_principal']).pack(
            side=tk.LEFT, padx=(0, ESPACIADO['sm']))

        self.buscar_participante_var.trace_add(
            'write', lambda *_: self.callbacks.get('actualizar_detalle_faena')())

        tk.Entry(busqueda_frame, textvariable=self.buscar_participante_var,
                 font=FUENTES['normal'], width=30,
                 bg=self.tema['input_bg'], fg=self.tema['fg_principal'],
                 relief=tk.SOLID, bd=1,
                 insertbackground=self.tema['accent_primary']).pack(side=tk.LEFT)

        # Botones
        botones = tk.Frame(busqueda_frame, bg=self.tema['bg_secundario'])
        botones.pack(side=tk.RIGHT)

        BotonModerno(botones, texto=f"{ICONOS['buscar']} Agregar", tema=self.tema,
                     tipo='primary',
                     command=self.callbacks.get('agregar_participantes')).pack(
            side=tk.LEFT, padx=(0, ESPACIADO['sm']))

        BotonModerno(botones, texto=f"{ICONOS['guardar']} Pago en lugar", tema=self.tema,
                     tipo='secondary',
                     command=self.callbacks.get('registrar_pago')).pack(
            side=tk.LEFT, padx=(0, ESPACIADO['sm']))

        BotonModerno(botones, texto=f"{ICONOS['eliminar']} Quitar", tema=self.tema,
                     tipo='error',
                     command=self.callbacks.get('eliminar_participante')).pack(side=tk.LEFT)

    def _crear_tree_participantes(self, parent) -> None:
        """Crear TreeView de participantes"""
        cols = ('folio', 'nombre', 'estado', 'hora')
        self.tree_participantes = ttk.Treeview(parent, columns=cols, show='headings', height=12)
        self.tree_participantes.heading('folio', text='Folio')
        self.tree_participantes.heading('nombre', text='Nombre')
        self.tree_participantes.heading('estado', text='Modo')
        self.tree_participantes.heading('hora', text='Hora')
        self.tree_participantes.column('folio', width=90, anchor='center')
        self.tree_participantes.column('nombre', width=200)
        self.tree_participantes.column('estado', width=110, anchor='center')
        self.tree_participantes.column('hora', width=80, anchor='center')

        scroll_y = ttk.Scrollbar(parent, orient=tk.VERTICAL,
                                 command=self.tree_participantes.yview)
        self.tree_participantes.configure(yscrollcommand=scroll_y.set)
        self.tree_participantes.grid(row=2, column=0, sticky='nsew')
        scroll_y.grid(row=2, column=1, sticky='ns')

    def _crear_panel_resumen(self, parent) -> None:
        self.panel_resumen = PanelModerno(parent, titulo="Resumen anual de puntos",
                                         tema=self.tema)
        self.panel_resumen.grid(row=3, column=0, columnspan=2, sticky='nsew',
                               pady=(ESPACIADO['lg'], 0))
        self.panel_resumen.content_frame.columnconfigure(0, weight=1)
        self.panel_resumen.content_frame.rowconfigure(1, weight=1)

        self._crear_filtros_resumen()
        self._crear_tree_resumen()

    def _crear_filtros_resumen(self) -> None:
        """Crear controles de filtros de resumen"""
        filtros = tk.Frame(self.panel_resumen.content_frame, bg=self.tema['bg_secundario'])
        filtros.grid(row=0, column=0, sticky='we', pady=(0, ESPACIADO['sm']))

        tk.Label(filtros, text="Año", font=FUENTES['subtitulo'],
                 bg=self.tema['bg_secundario'], fg=self.tema['fg_principal']).pack(side=tk.LEFT)

        self.anio_combo = ttk.Combobox(filtros, textvariable=self.anio_var,
                                       values=[], width=8, state='readonly')
        self.anio_combo.pack(side=tk.LEFT, padx=ESPACIADO['sm'])
        self.anio_combo.bind('<<ComboboxSelected>>',
                            lambda e: self.callbacks.get('actualizar_resumen')())

        # Búsqueda en resumen
        tk.Label(filtros, text="Buscar", font=FUENTES['subtitulo'],
                 bg=self.tema['bg_secundario'], fg=self.tema['fg_principal']).pack(
            side=tk.LEFT, padx=(ESPACIADO['md'], ESPACIADO['xs']))

        entry_resumen_buscar = ttk.Entry(filtros, textvariable=self.resumen_buscar_var, width=24)
        entry_resumen_buscar.pack(side=tk.LEFT)
        self.resumen_buscar_var.trace_add('write',
                                         lambda *args: self.callbacks.get('actualizar_resumen')())

    def _crear_tree_resumen(self) -> None:
        """Crear TreeView de resumen"""
        cols = ('folio', 'nombre', 'puntos')
        self.tree_resumen = ttk.Treeview(self.panel_resumen.content_frame, columns=cols,
                                        show='headings', height=8)
        self.tree_resumen.heading('folio', text='Folio')
        self.tree_resumen.heading('nombre', text='Nombre')
        self.tree_resumen.heading('puntos', text='Puntos')
        self.tree_resumen.column('folio', width=90, anchor='center')
        self.tree_resumen.column('nombre', width=260)
        self.tree_resumen.column('puntos', width=120, anchor='center')

        scroll_y = ttk.Scrollbar(self.panel_resumen.content_frame, orient=tk.VERTICAL,
                                 command=self.tree_resumen.yview)
        self.tree_resumen.configure(yscrollcommand=scroll_y.set)

        self.tree_resumen.grid(row=1, column=0, sticky='nsew')
        scroll_y.grid(row=1, column=1, sticky='ns')

    def limpiar_formulario(self) -> None:
        """Limpiar campos del formulario"""
        self.nombre_var.set('')
        self.peso_var.set(PESO_FAENA_DEFECTO)
        self.hora_inicio_var.set(HORA_INICIO_DEFECTO)
        self.hora_inicio_ampm_var.set(HORA_INICIO_AMPM_DEFECTO)
        self.hora_fin_var.set(HORA_FIN_DEFECTO)
        self.hora_fin_ampm_var.set(HORA_FIN_AMPM_DEFECTO)

    def obtener_datos_formulario(self) -> Dict:
        """Obtener datos del formulario"""
        return {
            'fecha': self.fecha_var.get().strip(),
            'nombre': self.nombre_var.get().strip(),
            'peso': int(self.peso_var.get()),
            'hora_inicio': f"{self.hora_inicio_var.get()} {self.hora_inicio_ampm_var.get()}" if self.hora_inicio_var.get() else '',
            'hora_fin': f"{self.hora_fin_var.get()} {self.hora_fin_ampm_var.get()}" if self.hora_fin_var.get() else ''
        }

    def _mostrar_menu_contexto(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label='Ver detalles', command=self.callbacks.get('ver_detalles'))
        menu.add_command(label='Editar', command=self.callbacks.get('editar_faena'))
        menu.add_separator()
        menu.add_command(label='Eliminar', command=self.callbacks.get('eliminar_faena'))
        menu.post(event.x_root, event.y_root)
