"""
Sistema de Censo de Habitantes - Módulo Principal Modularizado
Versión refactorizada con responsabilidades separadas
Optimizado para manejar grandes volúmenes de datos (2000+ habitantes)
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import sys
import time
import os
from datetime import datetime
import threading
import queue

# Configurar path para imports cuando se ejecuta directamente
proyecto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if proyecto_raiz not in sys.path:
    sys.path.insert(0, proyecto_raiz)

from src.config import TEMAS, CENSO_DEBOUNCE_MS, CENSO_COLUMNAS, CENSO_COLUMNAS_ANCHOS, CENSO_NOTA_MAX_DISPLAY, UI_DEBOUNCE_SEARCH
from src.ui.estilos_globales import TEMA_GLOBAL
from src.ui.tema_moderno import FUENTES
from src.core.logger import registrar_operacion, registrar_error
from src.core.optimizador_ui import get_ui_optimizer
from src.core.gestor_datos_global import obtener_gestor
from src.modules.indicadores.indicadores_estado import calcular_estado_habitante

# Imports de módulos internos del censo
from src.modules.censo.censo_dialogos import agregar_habitante, dialogo_editar_nota, mostrar_estadisticas, mostrar_historial, busqueda_avanzada
from src.modules.censo.censo_panel_detalles import CensoPanelDetalles
from src.modules.censo.censo_operaciones import aplicar_filtros, ordenar_columna, actualizar_estado_habitante, colocar_nota_habitante, editar_nombre_habitante
from src.modules.censo.censo_exportacion import exportar_excel
from src.modules.censo.censo_preferencias import cargar_preferencias, guardar_preferencias, aplicar_preferencias
from src.modules.censo.censo_tooltips import configurar_tooltips, mostrar_tooltip_indicador, ocultar_tooltip_indicador
from src.modules.censo.censo_optimizaciones import cargar_habitantes_async, actualizar_tabla_incremental


class SistemaCensoHabitantes:
    def __init__(self, root):
        self.root = root
        self.root.title("📋 Sistema de Censo de Habitantes - Comunidad San Pablo")
        
        # Optimizaciones de rendimiento para la ventana
        self.root.resizable(True, True)
        
        # Configurar para mejor rendimiento
        try:
            # Habilitar aceleración por hardware en Windows
            self.root.wm_attributes('-alpha', 1.0)
            
            # Configurar prioridad de proceso (Windows)
            if sys.platform == 'win32':
                import ctypes
                import psutil
                
                # Obtener proceso actual
                process = psutil.Process()
                
                # Establecer prioridad alta (sin llegar a realtime que puede causar problemas)
                process.nice(psutil.HIGH_PRIORITY_CLASS)
                
                print("[Censo] Prioridad de proceso establecida a ALTA")
        except Exception as e:
            print(f"[Censo] No se pudo optimizar prioridad: {e}")
        
        # Tamaño y posición optimizados
        self.root.geometry("1400x800")
        
        # Centrar ventana en pantalla (sin update_idletasks para mejor rendimiento)
        x = (self.root.winfo_screenwidth() // 2) - (1400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f"1400x800+{x}+{y}")
        
        self.style = ttk.Style()
        
        # Usar gestor en vez de API
        self.gestor = obtener_gestor()
        self.habitantes = []
        self.habitantes_filtrados = []  # Cache de resultados filtrados
        self.nombre_visible = tk.BooleanVar(value=True)
        self.folio_visible = tk.BooleanVar(value=True)
        self.filtro_estado = tk.StringVar(value="Todos")
        self._search_job = None
        
        # Sistema de optimización UI
        self._optimizer = get_ui_optimizer()
        self._search_cache = {}
        self._last_search_key = None
        
        # Control de threading y operaciones asíncronas
        self._carga_en_progreso = False
        self._actualizacion_en_progreso = False
        self._cancelar_busqueda = False
        self._cola_tareas = queue.Queue()
        self._thread_worker = None
        
        # Variables para ordenamiento
        self.columna_orden = None
        self.orden_reversa = False
        
        # Preferencias de usuario
        self.config_usuario_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 
                                                'SistemaComunidad', 'config_censo_usuario.json')
        
        # Referencias para ventanas de procesos
        self.proceso_control_pagos = None
        self.proceso_control_faenas = None
        
        # Tooltip para indicadores
        self.tooltip_label = None
        
        self.configurar_estilos()
        self.configurar_interfaz()
        
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_con_cleanup)
        
        self._inicializar_datos()

    def obtener_colores(self):
        return TEMA_GLOBAL

    def configurar_estilos(self):
        colores = self.obtener_colores()
        self.style.theme_use('clam')
        
        # Configurar estilos de forma optimizada
        self.style.configure('TFrame', background=colores['bg_principal'])
        self.style.configure('TLabel', background=colores['bg_principal'], foreground=colores['fg_principal'])
        self.style.configure('TButton', background=colores['bg_secundario'], foreground=colores['fg_principal'], padding=6, borderwidth=1)
        self.style.map('TButton', background=[('active', colores['button_hover'])])
        self.style.configure('TEntry', fieldbackground=colores['input_bg'], borderwidth=1)
        
        # Optimizar configuración de Treeview para mejor rendimiento
        self.style.configure('Treeview', 
                           background=colores['table_row_even'], 
                           fieldbackground=colores['table_row_even'], 
                           foreground=colores['fg_principal'], 
                           borderwidth=0,
                           rowheight=25)  # Altura fija para mejor rendimiento
        self.style.map('Treeview', 
                      background=[('selected', colores['table_selected'])], 
                      foreground=[('selected', colores['fg_principal'])])
        self.style.configure('Treeview.Heading', 
                           background=colores['table_header'], 
                           foreground=colores['table_header_text'], 
                           relief='flat',  # Flat para mejor rendimiento
                           padding=6)

    def _inicializar_datos(self):
        """Inicializa datos directamente desde gestor (optimizado)"""
        try:
            print("[Censo] Cargando habitantes desde gestor...")
            
            # Cargar en segundo plano para no bloquear UI
            self.root.after_idle(self._cargar_datos_asincrono)
            
        except Exception as e:
            print(f"[Censo] Error en inicialización: {e}")
            messagebox.showerror("Error", f"Error durante inicialización: {str(e)}")
    
    def _cargar_datos_asincrono(self):
        """Carga datos sin bloquear la interfaz"""
        try:
            self.cargar_habitantes()
            
            # Cargar preferencias
            self._cargar_y_aplicar_preferencias()
            
            print("[Censo] ✓ Inicialización completa")
        except Exception as e:
            print(f"[Censo] Error cargando datos: {e}")
    
    def configurar_interfaz(self):
        """Configura la interfaz gráfica principal"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # ===== ENCABEZADO =====
        self._crear_encabezado(main_frame)
        
        # ===== CONTENEDOR PARA TABLA Y PANEL LATERAL =====
        contenedor_principal = ttk.Frame(main_frame)
        contenedor_principal.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        contenedor_principal.columnconfigure(0, weight=3)
        contenedor_principal.columnconfigure(1, weight=1)
        contenedor_principal.rowconfigure(0, weight=1)
        
        # ===== TABLA =====
        self._crear_tabla(contenedor_principal)
        
        # ===== PANEL LATERAL DE DETALLES =====
        panel_frame = ttk.LabelFrame(contenedor_principal, text="Detalles del Habitante", padding="10")
        panel_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.panel_detalles = CensoPanelDetalles(
            panel_frame,
            self.gestor,
            self.cargar_habitantes,
            self.abrir_control_pagos,
            self.abrir_registro_faenas,
            self._editar_nota_seleccionada,
            self._cambiar_estado_seleccionado
        )
        
        # ===== BARRA DE ESTADO INFERIOR =====
        self.status_label = ttk.Label(main_frame, text="Cargando...", 
                                      font=('Arial', 9), foreground='#555')
        self.status_label.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        self.status_label.config(relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2))
        
        # Configurar atajos de teclado
        self._configurar_atajos()
    
    def _crear_encabezado(self, parent):
        """Crea el frame de encabezado con título e indicadores"""
        header_frame = ttk.LabelFrame(parent, text="Censo de Habitantes", padding="10")
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.header_frame = header_frame
        
        ttk.Label(header_frame, text="San Pablo Atotonilco - Sistema de Registro de Habitantes", 
               font=FUENTES['titulo']).grid(row=0, column=0, columnspan=4, pady=5)
        
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        ttk.Label(header_frame, text=f"Fecha: {fecha_actual}").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Button(header_frame, text="Abrir Control de Pagos", command=self.abrir_control_pagos, width=22).grid(row=1, column=1, padx=5)
        ttk.Button(header_frame, text="📊 Estadísticas", command=self._mostrar_estadisticas, width=18).grid(row=1, column=2, padx=5)
        
        self.total_label = ttk.Label(header_frame, text="Total Habitantes: 0", font=('Arial', 11, 'bold'))
        self.total_label.grid(row=1, column=3, sticky=tk.E, padx=5)

        # Indicadores de estado
        indicadores_frame = tk.Frame(header_frame, bg='#f0f0f0')
        indicadores_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=4)
        
        ttk.Label(indicadores_frame, text="Estado de la Comunidad:", font=FUENTES['pequeño']).pack(side=tk.LEFT, padx=5)
        
        self.canvas_pagos = tk.Canvas(indicadores_frame, width=25, height=25, bg='#f0f0f0', 
                                       highlightthickness=0, cursor='hand2')
        self.canvas_pagos.pack(side=tk.LEFT, padx=2)
        self.canvas_pagos.bind('<Enter>', lambda e: self._mostrar_tooltip_pagos())
        self.canvas_pagos.bind('<Leave>', lambda e: self._ocultar_tooltip())
        
        self.label_pagos = ttk.Label(indicadores_frame, text="Pagos", font=FUENTES['pequeño'])
        self.label_pagos.pack(side=tk.LEFT, padx=(0, 10))
        
        self.canvas_faenas = tk.Canvas(indicadores_frame, width=25, height=25, bg='#f0f0f0', 
                                        highlightthickness=0, cursor='hand2')
        self.canvas_faenas.pack(side=tk.LEFT, padx=2)
        self.canvas_faenas.bind('<Enter>', lambda e: self._mostrar_tooltip_faenas())
        self.canvas_faenas.bind('<Leave>', lambda e: self._ocultar_tooltip())
        
        self.label_faenas = ttk.Label(indicadores_frame, text="Faenas", font=FUENTES['pequeño'])
        self.label_faenas.pack(side=tk.LEFT)
        
        ttk.Button(header_frame, text="Abrir Registro de Faenas",
                    command=self.abrir_registro_faenas, width=24).grid(row=2, column=2, columnspan=2, padx=5, pady=4, sticky=tk.E)
    
    def _crear_tabla(self, parent):
        """Crea el frame de la tabla con controles"""
        table_frame = ttk.LabelFrame(parent, text="Listado de Habitantes", padding="8")
        table_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(1, weight=1)

        # Toolbar
        toolbar = ttk.Frame(table_frame)
        toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        toolbar.columnconfigure(1, weight=1)

        # Búsqueda con debouncing optimizado
        ttk.Label(toolbar, text="Buscar por nombre o folio:").grid(row=0, column=0, sticky=tk.W, padx=(0,5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=35)
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        # Solo activar búsqueda después de 300ms de inactividad
        self.search_var.trace('w', lambda *args: self._buscar_tiempo_real())

        # Filtro de estado
        ttk.Label(toolbar, text="Filtrar:").grid(row=0, column=2, sticky=tk.W, padx=(10,5))
        filtro_combo = ttk.Combobox(toolbar, textvariable=self.filtro_estado, 
                                    values=["Todos", "Solo Activos", "Solo Inactivos"],
                                    state='readonly', width=15)
        filtro_combo.grid(row=0, column=3, sticky=tk.W, padx=(0,5))
        filtro_combo.bind('<<ComboboxSelected>>', lambda e: self._aplicar_filtros())

        # Botones de acción
        acciones = ttk.Frame(toolbar)
        acciones.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(8,0))
        ttk.Button(acciones, text="Limpiar", command=self._limpiar_busqueda).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(acciones, text="🔍 Búsqueda Avanzada", command=self._busqueda_avanzada).pack(side=tk.LEFT, padx=5)
        ttk.Button(acciones, text="Agregar Habitante", command=self._agregar_habitante).pack(side=tk.LEFT, padx=5)
        ttk.Button(acciones, text="Actualizar Lista", command=self.cargar_habitantes).pack(side=tk.LEFT, padx=5)
        ttk.Button(acciones, text="📊 Exportar a Excel", command=self._exportar_excel).pack(side=tk.LEFT, padx=5)

        # Controles de visibilidad
        controles = ttk.Frame(toolbar)
        controles.grid(row=2, column=0, columnspan=2, sticky=tk.E, pady=(6,0))
        ttk.Checkbutton(controles, text="Mostrar nombre", variable=self.nombre_visible,
                command=self._actualizar_visibilidad_columnas).pack(side=tk.RIGHT, padx=5)
        ttk.Checkbutton(controles, text="Mostrar folio", variable=self.folio_visible,
                command=self._actualizar_visibilidad_columnas).pack(side=tk.RIGHT, padx=5)
        ttk.Button(controles, text="Maximizar Lista", command=self._toggle_tamano_lista).pack(side=tk.RIGHT, padx=10)
        
        # Scrollbars
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        
        # Treeview (optimizado: sin columna de icono, con displaycolumns para mejor rendimiento)
        self.tree = ttk.Treeview(table_frame, 
                                 columns=CENSO_COLUMNAS,
                                 show='headings',  # Solo encabezados, sin columna de ícono
                                 displaycolumns=CENSO_COLUMNAS,  # Especificar explícitamente
                                 yscrollcommand=scrollbar_y.set,
                                 xscrollcommand=scrollbar_x.set,
                                 selectmode='browse',  # Modo de selección optimizado
                                 height=20)  # Altura fija para mejor rendimiento
        
        # Configurar encabezados
        self.tree.heading('folio', text='Folio', command=lambda: self._ordenar_columna('folio'))
        self.tree.heading('nombre', text='Nombre Completo', command=lambda: self._ordenar_columna('nombre'))
        self.tree.heading('fecha_registro', text='Fecha de Registro', command=lambda: self._ordenar_columna('fecha_registro'))
        self.tree.heading('activo', text='Estado', command=lambda: self._ordenar_columna('activo'))
        self.tree.heading('nota', text='Nota', command=lambda: self._ordenar_columna('nota'))
        
        # Configurar anchos
        for col, ancho in CENSO_COLUMNAS_ANCHOS.items():
            self.tree.column(col, width=ancho, anchor=tk.CENTER if col in ['folio', 'fecha_registro', 'activo'] else tk.W)
        
        self.tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_y.grid(row=1, column=1, sticky=(tk.N, tk.S))
        scrollbar_x.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        self.tree.tag_configure('activo', background='#c8e6c9')
        self.tree.tag_configure('inactivo', background='#ffccbc')

        # Menú contextual
        self.menu_contextual = tk.Menu(self.root, tearoff=0)
        self.menu_contextual.add_command(label="✏️  Editar Nombre", command=self._editar_nombre_seleccion)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label="Marcar como activo", command=lambda: self._actualizar_estado_seleccion(True))
        self.menu_contextual.add_command(label="Marcar como inactivo", command=lambda: self._actualizar_estado_seleccion(False))
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label="Colocar nota", command=self._colocar_nota_seleccion)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label="🗑️  Eliminar Habitante", command=self._eliminar_habitante_seleccion)
        self.tree.bind('<Button-3>', self._mostrar_menu_contextual)
        
        # Eventos
        self.tree.bind('<<TreeviewSelect>>', self._on_seleccionar_habitante)
        
        # Configurar tooltips
        self.tooltips = configurar_tooltips(self.tree, self.habitantes, self.root)
        
        # Ajustar visibilidad inicial
        self._actualizar_visibilidad_columnas()
        self.lista_maximizada = False
    
    def _configurar_atajos(self):
        """Configura atajos de teclado"""
        self.root.bind('<Control-f>', lambda e: self._enfocar_busqueda())
        self.root.bind('<Control-n>', lambda e: self._agregar_habitante())
        self.root.bind('<F5>', lambda e: self.cargar_habitantes())
        self.root.bind('<Delete>', lambda e: self._actualizar_estado_seleccion(False))
        self.root.bind('<Escape>', lambda e: self._limpiar_busqueda())
    
    def _enfocar_busqueda(self):
        """Coloca el foco en el campo de búsqueda"""
        for widget in self.root.winfo_children():
            if self.__buscar_entry_recursivo(widget):
                return
    
    def __buscar_entry_recursivo(self, widget):
        """Busca recursivamente el Entry de búsqueda"""
        if isinstance(widget, ttk.Entry):
            try:
                if widget.cget('textvariable') == str(self.search_var):
                    widget.focus_set()
                    widget.select_range(0, tk.END)
                    return True
            except:
                pass
        for child in widget.winfo_children():
            if self.__buscar_entry_recursivo(child):
                return True
        return False

    def cargar_habitantes(self):
        """Cargar todos los habitantes desde el gestor (optimizado)"""
        cargar_habitantes_async(self)
    
    def _actualizar_tabla(self, habitantes):
        """Actualizar tabla con lista de habitantes (optimizado)"""
        actualizar_tabla_incremental(self, habitantes)
    
    def _actualizar_indicadores_y_barra_async(self):
        """Actualiza indicadores y barra de estado de forma asíncrona para no bloquear"""
        if hasattr(self, '_actualizar_indicadores_estado'):
            self._actualizar_indicadores_estado()
        if hasattr(self, '_actualizar_barra_estado'):
            self._actualizar_barra_estado()
    
    def _actualizar_barra_estado(self):
        """Actualiza la barra de estado inferior"""
        try:
            if not hasattr(self, 'status_label'):
                return
            
            activos = sum(1 for hab in self.habitantes if hab.get('activo', True))
            inactivos = len(self.habitantes) - activos
            con_notas = sum(1 for hab in self.habitantes if hab.get('nota', ''))
            
            ultima_actualizacion = datetime.now().strftime("%H:%M:%S")
            
            texto_estado = f"📊 Total: {len(self.habitantes)} | ✓ Activos: {activos} | ✗ Inactivos: {inactivos} | 📝 Con notas: {con_notas} | Última actualización: {ultima_actualizacion}"
            
            self.status_label.config(text=texto_estado)
        except Exception as e:
            print(f"Error actualizando barra de estado: {e}")
    
    # ===== MÉTODOS DE FILTRADO Y BÚSQUEDA =====
    
    def _buscar_tiempo_real(self):
        """Búsqueda en tiempo real optimizada con debounce y caché"""
        # Usar el optimizador global
        criterio = self.search_var.get().strip().lower()
        filtro = self.filtro_estado.get()
        
        # Generar clave de búsqueda
        search_key = f"{criterio}_{filtro}"
        
        # Si es la misma búsqueda, no hacer nada
        if search_key == self._last_search_key:
            return
        
        self._last_search_key = search_key
        
        # Cancelar búsquedas anteriores
        self._optimizer.debounce.cancel(f"censo_search_{id(self)}")
        
        # Programar nueva búsqueda con debounce (300ms)
        self._optimizer.debounce.debounce(
            f"censo_search_{id(self)}",
            300,  # Reducido de 500ms a 300ms para mejor respuesta
            self._ejecutar_busqueda_async,
            criterio,
            filtro
        )
    
    def _ejecutar_busqueda_async(self, criterio: str, filtro: str):
        """Ejecutar búsqueda de forma asíncrona"""
        # Verificar caché primero
        cache_key = f"{criterio}_{filtro}"
        
        if cache_key in self._search_cache:
            # Usar resultado en caché
            self.root.after(0, lambda: self._finalizar_filtrado(
                self._search_cache[cache_key], criterio, filtro
            ))
            return
        
        # Ejecutar filtrado en background
        def _filtrar_task():
            try:
                if not criterio and filtro == 'Todos':
                    return self.habitantes.copy()
                else:
                    return aplicar_filtros(self.habitantes, criterio, filtro)
            except Exception as e:
                print(f"Error filtrando: {e}")
                return []
        
        def _on_complete(resultados):
            # Guardar en caché (limitar tamaño)
            if len(self._search_cache) > 50:
                # Eliminar entradas antiguas
                self._search_cache.clear()
            
            self._search_cache[cache_key] = resultados
            self._finalizar_filtrado(resultados, criterio, filtro)
        
        # Ejecutar en background
        self._optimizer.async_update(
            f"censo_filter_{id(self)}",
            _filtrar_task,
            _on_complete
        )
    
    def _aplicar_filtros_async(self):
        """Aplica filtros de forma asíncrona para no bloquear UI - VERSION OPTIMIZADA"""
        # Cancelar trabajos previos si existen
        if self._search_job:
            self.root.after_cancel(self._search_job)
            self._search_job = None
        
        # Prevenir actualizaciones concurrentes
        if hasattr(self, '_actualizacion_en_progreso') and self._actualizacion_en_progreso:
            return
        
        self._cancelar_busqueda = False
        self._actualizacion_en_progreso = True
        
        criterio = self.search_var.get().strip().lower()
        filtro = self.filtro_estado.get()
        
        def _filtrar_thread():
            try:
                # Filtrar en background
                if not criterio and filtro == 'Todos':
                    resultados = self.habitantes.copy()
                else:
                    resultados = aplicar_filtros(self.habitantes, criterio, filtro)
                
                # Si fue cancelada, no actualizar
                if not self._cancelar_busqueda:
                    self.root.after(0, lambda: self._finalizar_filtrado(resultados, criterio, filtro))
                else:
                    self._actualizacion_en_progreso = False
                    
            except Exception as e:
                print(f"Error filtrando: {e}")
                self._actualizacion_en_progreso = False
        
        # Ejecutar filtrado en thread
        thread = threading.Thread(target=_filtrar_thread, daemon=True)
        thread.start()
    
    def _finalizar_filtrado(self, resultados, criterio, filtro):
        """Finaliza el filtrado actualizando la UI"""
        try:
            if hasattr(self, 'habitantes_filtrados'):
                self.habitantes_filtrados = resultados
            self._actualizar_tabla(resultados)
            # NO guardar preferencias automáticamente - solo al cerrar ventana si el usuario lo desea
        finally:
            self._actualizacion_en_progreso = False
    
    def _aplicar_filtros(self):
        """Wrapper para compatibilidad"""
        self._aplicar_filtros_async()
    def _limpiar_busqueda(self):
        """Limpiar campo de busqueda y filtros"""
        self.search_var.set('')
        self.filtro_estado.set('Todos')
        self._actualizar_tabla(self.habitantes)
        # Limpiar preferencias guardadas
        try:
            guardar_preferencias(self.config_usuario_path, '', 'Todos')
        except:
            pass
    
    def _ordenar_columna(self, columna):
        """Ordena la tabla por la columna especificada"""
        if self.columna_orden == columna:
            self.orden_reversa = not self.orden_reversa
        else:
            self.columna_orden = columna
            self.orden_reversa = False
        
        # Obtener lista actual mostrada
        lista_actual = []
        for item_id in self.tree.get_children():
            valores = self.tree.item(item_id, 'values')
            folio = valores[0]
            habitante = next((h for h in self.habitantes if h['folio'] == folio), None)
            if habitante:
                lista_actual.append(habitante)
        
        # Ordenar
        lista_ordenada = ordenar_columna(lista_actual, columna, self.orden_reversa)
        self._actualizar_tabla(lista_ordenada)
        
        # Actualizar indicador visual en encabezado
        nombres_columnas = {
            'folio': 'Folio',
            'nombre': 'Nombre Completo',
            'fecha_registro': 'Fecha de Registro',
            'activo': 'Estado',
            'nota': 'Nota'
        }
        
        for col in CENSO_COLUMNAS:
            texto_base = nombres_columnas[col]
            if col == columna:
                indicador = ' ▼' if self.orden_reversa else ' ▲'
                self.tree.heading(col, text=texto_base + indicador)
            else:
                self.tree.heading(col, text=texto_base)
    
    # ===== MÉTODOS DE DIÁLOGOS =====
    
    def _agregar_habitante(self):
        """Abre diálogo para agregar habitante"""
        agregar_habitante(self.root, self.habitantes, self.cargar_habitantes)
    
    def _mostrar_estadisticas(self):
        """Muestra ventana de estadísticas"""
        mostrar_estadisticas(self.root, self.habitantes)
    
    def _busqueda_avanzada(self):
        """Abre diálogo de búsqueda avanzada"""
        busqueda_avanzada(self.root, self.habitantes, self._actualizar_tabla)
    
    def _exportar_excel(self):
        """Exporta a Excel"""
        exportar_excel(self.root, self.habitantes, self.tree)
    
    # ===== MÉTODOS DE PANEL LATERAL =====
    
    def _on_seleccionar_habitante(self, event=None):
        """Maneja la selección de un habitante"""
        folio = self.__folio_seleccionado()
        if not folio:
            return
        
        habitante = next((h for h in self.habitantes if h['folio'] == folio), None)
        if habitante:
            self.panel_detalles.mostrar_detalles(habitante)
    
    def _editar_nota_seleccionada(self, habitante):
        """Edita la nota del habitante seleccionado"""
        dialogo_editar_nota(self.root, habitante, self.gestor, self.cargar_habitantes)
    
    def _editar_nombre_seleccion(self):
        """Edita el nombre del habitante seleccionado"""
        folio = self.__folio_seleccionado()
        if not folio:
            messagebox.showwarning("Selección", "Selecciona un habitante primero")
            return
        
        habitante = next((h for h in self.habitantes if h['folio'] == folio), None)
        if habitante:
            from src.modules.censo.censo_dialogos import dialogo_editar_nombre
            dialogo_editar_nombre(self.root, habitante, self.gestor, self.cargar_habitantes)
    
    def _cambiar_estado_seleccionado(self, folio, activo):
        """Cambia el estado del habitante"""
        # Pedir confirmación solo al marcar como inactivo
        if not activo:
            habitante = next((h for h in self.habitantes if h['folio'] == folio), None)
            nombre = habitante['nombre'] if habitante else 'este habitante'
            respuesta = messagebox.askyesno(
                "Confirmar cambio", 
                f"¿Seguro que desea marcar como INACTIVO a {nombre}?\n\n"
                "Esta acción se puede revertir posteriormente.",
                icon='warning'
            )
            if not respuesta:
                return
        
        actualizar_estado_habitante(folio, activo, self.gestor, self.cargar_habitantes)
    
    # ===== MÉTODOS DE MENÚ CONTEXTUAL =====
    
    def _mostrar_menu_contextual(self, event):
        """Muestra menú contextual al hacer clic derecho"""
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            self.menu_contextual.post(event.x_root, event.y_root)
    
    def _actualizar_estado_seleccion(self, activo):
        """Marca habitante seleccionado como activo/inactivo"""
        folio = self.__folio_seleccionado()
        if not folio:
            messagebox.showwarning("Seleccion", "Selecciona un habitante primero")
            return
        
        self._cambiar_estado_seleccionado(folio, activo)
    
    def _colocar_nota_seleccion(self):
        """Permite agregar o editar nota del habitante seleccionado"""
        folio = self.__folio_seleccionado()
        if not folio:
            messagebox.showwarning("Seleccion", "Selecciona un habitante primero")
            return
        
        nota = simpledialog.askstring("Nota", "Ingrese nota para el habitante:")
        if nota is None:
            return
        
        colocar_nota_habitante(folio, nota, self.gestor, self.cargar_habitantes)
    
    def _eliminar_habitante_seleccion(self):
        """Elimina el habitante seleccionado con confirmación"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Selecciona un habitante primero")
            return
        
        # Obtener datos del habitante
        item_id = seleccion[0]
        valores = self.tree.item(item_id, 'values')
        if not valores or len(valores) < 2:
            messagebox.showerror("Error", "No se pudo obtener datos del habitante")
            return
        
        folio, nombre = valores[0], valores[1]
        
        # Confirmar eliminación
        if not messagebox.askyesno("Confirmar Eliminación", 
                                  f"¿Desea eliminar a {nombre} (Folio: {folio})?\n\nEsta acción NO se puede deshacer."):
            return
        
        # Ejecutar eliminación via gestor
        try:
            exito, mensaje = self.gestor.eliminar_habitante(folio)
            if exito:
                messagebox.showinfo("Éxito", f"Habitante {nombre} eliminado correctamente")
                self.cargar_habitantes()
            else:
                messagebox.showerror("Error", mensaje)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar: {str(e)}")
            registrar_error('censo_habitantes', '_eliminar_habitante_seleccion', str(e), contexto=f"folio={folio}")
    
    def __folio_seleccionado(self):
        """Obtiene el folio del habitante seleccionado"""
        seleccion = self.tree.selection()
        if not seleccion:
            return None
        valores = self.tree.item(seleccion[0], 'values')
        return valores[0] if valores else None
    
    # ===== MÉTODOS DE INDICADORES Y TOOLTIPS =====
    
    def _actualizar_indicadores_estado(self):
        """Actualiza los indicadores de estado de pagos y faenas con caché"""
        try:
            # Protección: verificar que existen los canvas
            if not hasattr(self, 'canvas_pagos') or not hasattr(self, 'canvas_faenas'):
                return
            
            # Si ya tenemos valores en caché y no han pasado más de 30 segundos, no recalcular
            if hasattr(self, '_indicadores_cache_time'):
                import time
                if time.time() - self._indicadores_cache_time < 30:
                    return
            
            total_pagos = 0.0
            total_faenas = 0.0
            count = len(self.habitantes)
            
            if count == 0:
                ratio_pagos_promedio = 0.5
                ratio_faenas_promedio = 0.5
            else:
                # Optimización: Calcular en lotes de 50 y permitir que UI responda
                for i, hab in enumerate(self.habitantes):
                    folio = hab.get('folio', '')
                    nombre = hab.get('nombre', '')
                    estado = calcular_estado_habitante(folio, nombre)
                    total_pagos += estado['pagos']['ratio']
                    total_faenas += estado['faenas']['ratio']
                    
                    # Cada 50 habitantes, permitir que UI responda
                    if i > 0 and i % 50 == 0:
                        self.root.update_idletasks()
                
                ratio_pagos_promedio = total_pagos / count
                ratio_faenas_promedio = total_faenas / count
            
            color_pagos = self.__color_por_ratio(ratio_pagos_promedio)
            color_faenas = self.__color_por_ratio(ratio_faenas_promedio)
            
            self.canvas_pagos.delete('all')
            self.canvas_pagos.create_rectangle(2, 2, 23, 23, fill=color_pagos, outline='#333', width=2)
            
            self.canvas_faenas.delete('all')
            self.canvas_faenas.create_rectangle(2, 2, 23, 23, fill=color_faenas, outline='#333', width=2)
            
            self.estado_pagos_promedio = ratio_pagos_promedio
            self.estado_faenas_promedio = ratio_faenas_promedio
            
            # Guardar timestamp del caché
            import time
            self._indicadores_cache_time = time.time()
        except Exception as e:
            print(f"Error actualizando indicadores: {e}")
    
    def __color_por_ratio(self, ratio):
        """Convierte ratio a color hexadecimal"""
        try:
            if ratio < 0.33:
                r, g = 255, int(255 * (ratio / 0.33))
            elif ratio < 0.66:
                r, g = int(255 * (1 - (ratio - 0.33) / 0.33)), 255
            else:
                r, g = 0, int(255 * (1 - (ratio - 0.66) / 0.34))
            return f'#{r:02x}{g:02x}00'
        except:
            return '#999999'
    
    def _mostrar_tooltip_pagos(self):
        """Muestra tooltip de pagos usando valores en caché"""
        if hasattr(self, 'estado_pagos_promedio'):
            texto = f"Estado de pagos: {self.estado_pagos_promedio*100:.1f}%"
            self.tooltip_label = mostrar_tooltip_indicador(self.root, texto, 100, 150)
    
    def _mostrar_tooltip_faenas(self):
        """Muestra tooltip de faenas usando valores en caché"""
        if hasattr(self, 'estado_faenas_promedio'):
            texto = f"Estado de faenas: {self.estado_faenas_promedio*100:.1f}%"
            self.tooltip_label = mostrar_tooltip_indicador(self.root, texto, 100, 150)
    
    def _ocultar_tooltip(self):
        """Oculta el tooltip"""
        if self.tooltip_label:
            ocultar_tooltip_indicador(self.tooltip_label)
            self.tooltip_label = None
    
    # ===== MÉTODOS DE PREFERENCIAS =====
    
    def _cargar_y_aplicar_preferencias(self):
        """NO cargar preferencias automáticamente - iniciar siempre con búsqueda limpia"""
        # Comentado para evitar que se guarde el historial de búsqueda
        # prefs = cargar_preferencias(self.config_usuario_path)
        # if prefs:
        #     self.root.after(100, lambda: aplicar_preferencias(prefs, self.search_var, self.filtro_estado))
        #     self.root.after(200, self._aplicar_filtros)
        pass
    
    # ===== MÉTODOS AUXILIARES =====
    
    def _toggle_tamano_lista(self):
        """Alterna entre vista normal y lista maximizada"""
        try:
            if not self.lista_maximizada:
                if hasattr(self, 'header_frame'):
                    self.header_frame.grid_remove()
                self.root.state('zoomed')
                self.lista_maximizada = True
            else:
                if hasattr(self, 'header_frame'):
                    self.header_frame.grid()
                self.lista_maximizada = False
        except Exception as e:
            print(f"Error al cambiar tamaño de lista: {e}")
    
    def _actualizar_visibilidad_columnas(self):
        """Mostrar/ocultar columnas de nombre y folio"""
        if not self.nombre_visible.get() and not self.folio_visible.get():
            self.folio_visible.set(True)
        
        if self.folio_visible.get():
            self.tree.column('folio', width=CENSO_COLUMNAS_ANCHOS['folio'], minwidth=40, stretch=False)
        else:
            self.tree.column('folio', width=0, minwidth=0, stretch=False)
        
        if self.nombre_visible.get():
            self.tree.column('nombre', width=CENSO_COLUMNAS_ANCHOS['nombre'], minwidth=100)
        else:
            self.tree.column('nombre', width=0, minwidth=0)
    
    def cleanup_procesos_hijos(self):
        """Termina procesos hijos de pagos y faenas al cerrar"""
        procesos = [
            ('pagos', self.proceso_control_pagos),
            ('faenas', self.proceso_control_faenas)
        ]
        
        for nombre, proceso in procesos:
            if proceso and proceso.poll() is None:
                try:
                    proceso.terminate()
                    try:
                        proceso.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        proceso.kill()
                        proceso.wait()
                except Exception as e:
                    print(f"Error terminando proceso {nombre}: {e}")
    
    def cerrar_con_cleanup(self):
        """Cierra ventana y limpia procesos hijos"""
        self.cleanup_procesos_hijos()
        self.root.destroy()
    
    def abrir_control_pagos(self):
        """Abre el módulo de control de pagos"""
        if self.proceso_control_pagos and self.proceso_control_pagos.poll() is None:
            messagebox.showinfo("Ventana abierta", "El módulo de pagos ya está abierto")
            return
        
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            proyecto_raiz = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
            pagos_script = os.path.join(proyecto_raiz, "src", "modules", "pagos", "control_pagos.py")
            
            if os.path.exists(pagos_script):
                if sys.platform == 'win32':
                    pythonw_exe = sys.executable.replace("python.exe", "pythonw.exe")
                    if os.path.exists(pythonw_exe):
                        self.proceso_control_pagos = subprocess.Popen([pythonw_exe, pagos_script])
                    else:
                        CREATE_NO_WINDOW = 0x08000000
                        self.proceso_control_pagos = subprocess.Popen([sys.executable, pagos_script],
                                                                     creationflags=CREATE_NO_WINDOW)
                else:
                    self.proceso_control_pagos = subprocess.Popen([sys.executable, pagos_script])
            else:
                messagebox.showerror("Error", f"No se encontró el módulo de pagos en: {pagos_script}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir control de pagos: {e}")
    
    def abrir_registro_faenas(self):
        """Abre el módulo de registro de faenas"""
        if self.proceso_control_faenas and self.proceso_control_faenas.poll() is None:
            messagebox.showinfo("Ventana abierta", "El módulo de faenas ya está abierto")
            return
        
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            proyecto_raiz = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
            faenas_script = os.path.join(proyecto_raiz, "src", "modules", "faenas", "control_faenas.py")
            
            if os.path.exists(faenas_script):
                if sys.platform == 'win32':
                    pythonw_exe = sys.executable.replace("python.exe", "pythonw.exe")
                    if os.path.exists(pythonw_exe):
                        self.proceso_control_faenas = subprocess.Popen([pythonw_exe, faenas_script])
                    else:
                        CREATE_NO_WINDOW = 0x08000000
                        self.proceso_control_faenas = subprocess.Popen([sys.executable, faenas_script],
                                                                      creationflags=CREATE_NO_WINDOW)
                else:
                    self.proceso_control_faenas = subprocess.Popen([sys.executable, faenas_script])
            else:
                messagebox.showerror("Error", f"No se encontró el módulo de faenas en: {faenas_script}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir registro de faenas: {e}")


def main():
    root = tk.Tk()
    app = SistemaCensoHabitantes(root)
    root.mainloop()

if __name__ == "__main__":
    main()
