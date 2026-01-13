"""
Módulo de Estadísticas Avanzadas para Control de Pagos
Proporciona análisis detallados, métricas y visualizaciones
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import calendar

from src.ui.tema_moderno import FUENTES, ESPACIADO, ICONOS
from src.ui.estilos_globales import TEMA_GLOBAL
from src.ui.ui_moderna import PanelModerno, BotonModerno


class VentanaEstadisticas:
    """Ventana con estadísticas avanzadas del sistema de pagos"""
    
    def __init__(self, parent, personas, cooperacion, monto_cooperacion):
        self.parent = parent
        self.personas = personas
        self.cooperacion = cooperacion
        self.monto_cooperacion = monto_cooperacion
        self.tema = TEMA_GLOBAL
        
        # Calcular estadísticas
        self.calcular_estadisticas()
        
        # Crear ventana
        self.ventana = tk.Toplevel(parent)
        self.ventana.title(f"📊 Estadísticas - {cooperacion}")
        self.ventana.geometry("1000x700")
        self.ventana.transient(parent)
        self.ventana.configure(bg=self.tema['bg_principal'])
        
        # Configurar grid
        self.ventana.grid_rowconfigure(0, weight=1)
        self.ventana.grid_columnconfigure(0, weight=1)
        
        self.crear_interfaz()
        
    def calcular_estadisticas(self):
        """Calcular todas las estadísticas necesarias"""
        personas_activas = [p for p in self.personas if p.get('activo', True)]
        
        # Estadísticas básicas
        self.total_personas = len(personas_activas)
        self.total_esperado = self.total_personas * self.monto_cooperacion
        
        # Estados de pago
        self.personas_pagado = []
        self.personas_parcial = []
        self.personas_pendiente = []
        self.personas_excedente = []
        self.total_recaudado = 0
        
        # Análisis de pagos
        self.pagos_por_persona = []
        self.montos_pagados = []
        self.fechas_pagos = []
        
        for persona in personas_activas:
            total_pagado = persona.get('total_pagado', 0)
            self.total_recaudado += total_pagado
            self.montos_pagados.append(total_pagado)
            
            porcentaje = (total_pagado / self.monto_cooperacion * 100) if self.monto_cooperacion > 0 else 0
            
            # Clasificar por estado
            if total_pagado >= self.monto_cooperacion:
                if total_pagado > self.monto_cooperacion:
                    self.personas_excedente.append(persona)
                else:
                    self.personas_pagado.append(persona)
            elif total_pagado > 0:
                self.personas_parcial.append(persona)
            else:
                self.personas_pendiente.append(persona)
            
            # Analizar pagos individuales
            pagos = persona.get('pagos', [])
            self.pagos_por_persona.append(len(pagos))
            
            for pago in pagos:
                try:
                    fecha_str = pago.get('fecha', '')
                    if fecha_str:
                        fecha = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
                        self.fechas_pagos.append(fecha)
                except:
                    pass
        
        # Calcular métricas
        self.porcentaje_recaudacion = (self.total_recaudado / self.total_esperado * 100) if self.total_esperado > 0 else 0
        self.promedio_pagado = sum(self.montos_pagados) / len(self.montos_pagados) if self.montos_pagados else 0
        self.mediana_pagado = self._calcular_mediana(self.montos_pagados)
        self.promedio_pagos_persona = sum(self.pagos_por_persona) / len(self.pagos_por_persona) if self.pagos_por_persona else 0
        
        # Top 10
        personas_ordenadas = sorted(personas_activas, key=lambda p: p.get('total_pagado', 0), reverse=True)
        self.top_pagadores = personas_ordenadas[:10]
        
        personas_con_atrasos = [p for p in personas_activas if 0 < p.get('total_pagado', 0) < self.monto_cooperacion]
        personas_con_atrasos.sort(key=lambda p: self.monto_cooperacion - p.get('total_pagado', 0), reverse=True)
        self.top_atrasados = personas_con_atrasos[:10]
        
        # Análisis temporal
        self.analizar_temporal()
        
    def _calcular_mediana(self, valores):
        """Calcular mediana de una lista de valores"""
        if not valores:
            return 0
        valores_ordenados = sorted(valores)
        n = len(valores_ordenados)
        if n % 2 == 0:
            return (valores_ordenados[n//2 - 1] + valores_ordenados[n//2]) / 2
        else:
            return valores_ordenados[n//2]
    
    def analizar_temporal(self):
        """Analizar patrones temporales de pagos"""
        if not self.fechas_pagos:
            self.pagos_por_mes = {}
            self.pagos_por_dia_semana = {}
            self.ultimo_pago = None
            return
        
        # Pagos por mes
        self.pagos_por_mes = defaultdict(int)
        for fecha in self.fechas_pagos:
            mes_año = fecha.strftime('%Y-%m')
            self.pagos_por_mes[mes_año] += 1
        
        # Pagos por día de la semana
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        self.pagos_por_dia_semana = {dia: 0 for dia in dias_semana}
        for fecha in self.fechas_pagos:
            dia = dias_semana[fecha.weekday()]
            self.pagos_por_dia_semana[dia] += 1
        
        # Último pago
        self.ultimo_pago = max(self.fechas_pagos) if self.fechas_pagos else None
        
    def crear_interfaz(self):
        """Crear la interfaz de estadísticas"""
        # Notebook para diferentes secciones
        notebook = ttk.Notebook(self.ventana)
        notebook.grid(row=0, column=0, sticky='nsew', padx=ESPACIADO['md'], pady=ESPACIADO['md'])
        
        # Pestañas
        self.crear_tab_resumen(notebook)
        self.crear_tab_metricas(notebook)
        self.crear_tab_top(notebook)
        self.crear_tab_temporal(notebook)
        
        # Botón cerrar
        btn_frame = tk.Frame(self.ventana, bg=self.tema['bg_principal'])
        btn_frame.grid(row=1, column=0, sticky='ew', padx=ESPACIADO['md'], pady=(0, ESPACIADO['md']))
        
        BotonModerno(btn_frame, f"{ICONOS['cerrar']} Cerrar", tema=self.tema, tipo='ghost',
                    command=self.ventana.destroy).pack(side=tk.RIGHT)
        
    def crear_tab_resumen(self, notebook):
        """Crear pestaña de resumen general"""
        frame = tk.Frame(notebook, bg=self.tema['bg_secundario'])
        notebook.add(frame, text='📊 Resumen General')
        
        # Scroll
        canvas = tk.Canvas(frame, bg=self.tema['bg_secundario'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.tema['bg_secundario'])
        
        scrollable.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=scrollable, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=ESPACIADO['md'], pady=ESPACIADO['md'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Título
        titulo = tk.Label(scrollable, text=f"📊 ESTADÍSTICAS GENERALES - {self.cooperacion}",
                         font=FUENTES['titulo'], bg=self.tema['bg_secundario'], fg=self.tema['texto_primario'])
        titulo.pack(pady=(0, ESPACIADO['lg']))
        
        # Panel de información general
        info_panel = PanelModerno(scrollable, titulo="📈 Información General", tema=self.tema, collapsible=False)
        info_panel.pack(fill=tk.X, pady=(0, ESPACIADO['md']))
        
        info_text = (
            f"Total de personas: {self.total_personas}\n"
            f"Total esperado: ${self.total_esperado:,.2f}\n"
            f"Total recaudado: ${self.total_recaudado:,.2f}\n"
            f"Porcentaje de recaudación: {self.porcentaje_recaudacion:.1f}%\n"
            f"Faltante: ${self.total_esperado - self.total_recaudado:,.2f}"
        )
        
        label_info = tk.Label(info_panel.content, text=info_text, font=FUENTES['normal'],
                             bg=self.tema['card_bg'], fg=self.tema['texto_primario'], justify=tk.LEFT)
        label_info.pack(anchor='w', padx=ESPACIADO['md'], pady=ESPACIADO['md'])
        
        # Barra de progreso visual
        self.crear_barra_progreso(info_panel.content, self.porcentaje_recaudacion)
        
        # Panel de distribución por estado
        dist_panel = PanelModerno(scrollable, titulo="📊 Distribución por Estado", tema=self.tema, collapsible=False)
        dist_panel.pack(fill=tk.X, pady=(0, ESPACIADO['md']))
        
        estados_frame = tk.Frame(dist_panel.content, bg=self.tema['card_bg'])
        estados_frame.pack(fill=tk.X, padx=ESPACIADO['md'], pady=ESPACIADO['md'])
        
        estados = [
            ('🟢 Al corriente', len(self.personas_pagado), '#4CAF50'),
            ('🟡 Atrasados', len(self.personas_parcial), '#FFC107'),
            ('🔴 Sin pagar', len(self.personas_pendiente), '#F44336'),
            ('⭐ Excedente', len(self.personas_excedente), '#2196F3')
        ]
        
        for estado, cantidad, color in estados:
            porcentaje = (cantidad / self.total_personas * 100) if self.total_personas > 0 else 0
            
            estado_frame = tk.Frame(estados_frame, bg=self.tema['card_bg'])
            estado_frame.pack(fill=tk.X, pady=ESPACIADO['xs'])
            
            label = tk.Label(estado_frame, text=f"{estado}: {cantidad} ({porcentaje:.1f}%)",
                           font=FUENTES['normal'], bg=self.tema['card_bg'], fg=self.tema['texto_primario'])
            label.pack(side=tk.LEFT, anchor='w')
            
            # Barra de porcentaje
            barra_frame = tk.Frame(estado_frame, bg=self.tema['bg_secundario'], height=20)
            barra_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(ESPACIADO['md'], 0))
            
            barra = tk.Frame(barra_frame, bg=color, height=20)
            barra.place(relwidth=porcentaje/100, relheight=1)
        
        # Gráfico ASCII de distribución
        self.crear_grafico_ascii_barras(scrollable, estados, "Distribución de Personas por Estado")
        
    def crear_tab_metricas(self, notebook):
        """Crear pestaña de métricas avanzadas"""
        frame = tk.Frame(notebook, bg=self.tema['bg_secundario'])
        notebook.add(frame, text='📈 Métricas Avanzadas')
        
        # Scroll
        canvas = tk.Canvas(frame, bg=self.tema['bg_secundario'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.tema['bg_secundario'])
        
        scrollable.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=scrollable, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=ESPACIADO['md'], pady=ESPACIADO['md'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Métricas de pagos
        metricas_panel = PanelModerno(scrollable, titulo="💰 Métricas de Pagos", tema=self.tema, collapsible=False)
        metricas_panel.pack(fill=tk.X, pady=(0, ESPACIADO['md']))
        
        metricas_text = (
            f"Promedio pagado por persona: ${self.promedio_pagado:,.2f}\n"
            f"Mediana de pagos: ${self.mediana_pagado:,.2f}\n"
            f"Promedio de pagos por persona: {self.promedio_pagos_persona:.1f}\n"
            f"Total de pagos registrados: {sum(self.pagos_por_persona)}\n"
            f"Tasa de cumplimiento: {(len(self.personas_pagado) + len(self.personas_excedente)) / self.total_personas * 100:.1f}%"
        )
        
        label_metricas = tk.Label(metricas_panel.content, text=metricas_text, font=FUENTES['normal'],
                                 bg=self.tema['card_bg'], fg=self.tema['texto_primario'], justify=tk.LEFT)
        label_metricas.pack(anchor='w', padx=ESPACIADO['md'], pady=ESPACIADO['md'])
        
        # Proyecciones
        proyeccion_panel = PanelModerno(scrollable, titulo="📊 Proyecciones", tema=self.tema, collapsible=False)
        proyeccion_panel.pack(fill=tk.X, pady=(0, ESPACIADO['md']))
        
        # Calcular proyección
        if len(self.personas_parcial) > 0:
            promedio_parcial = sum(p.get('total_pagado', 0) for p in self.personas_parcial) / len(self.personas_parcial)
            proyeccion = self.total_recaudado + (promedio_parcial * len(self.personas_pendiente))
        else:
            proyeccion = self.total_recaudado
        
        proyeccion_text = (
            f"Si todos pagaran completamente: ${self.total_esperado:,.2f}\n"
            f"Proyección basada en promedios: ${proyeccion:,.2f}\n"
            f"Diferencia vs esperado: ${proyeccion - self.total_esperado:,.2f}\n"
        )
        
        label_proyeccion = tk.Label(proyeccion_panel.content, text=proyeccion_text, font=FUENTES['normal'],
                                   bg=self.tema['card_bg'], fg=self.tema['texto_primario'], justify=tk.LEFT)
        label_proyeccion.pack(anchor='w', padx=ESPACIADO['md'], pady=ESPACIADO['md'])
        
        # Análisis de tendencia
        if len(self.fechas_pagos) >= 2:
            tendencia_panel = PanelModerno(scrollable, titulo="📉 Tendencia", tema=self.tema, collapsible=False)
            tendencia_panel.pack(fill=tk.X, pady=(0, ESPACIADO['md']))
            
            fechas_ordenadas = sorted(self.fechas_pagos)
            dias_transcurridos = (fechas_ordenadas[-1] - fechas_ordenadas[0]).days
            
            if dias_transcurridos > 0:
                pagos_por_dia = len(self.fechas_pagos) / dias_transcurridos
                tendencia_text = (
                    f"Período analizado: {dias_transcurridos} días\n"
                    f"Promedio de pagos por día: {pagos_por_dia:.2f}\n"
                    f"Último pago: {self.ultimo_pago.strftime('%d/%m/%Y %H:%M') if self.ultimo_pago else 'N/A'}\n"
                )
            else:
                tendencia_text = "Todos los pagos fueron realizados el mismo día"
            
            label_tendencia = tk.Label(tendencia_panel.content, text=tendencia_text, font=FUENTES['normal'],
                                      bg=self.tema['card_bg'], fg=self.tema['texto_primario'], justify=tk.LEFT)
            label_tendencia.pack(anchor='w', padx=ESPACIADO['md'], pady=ESPACIADO['md'])
    
    def crear_tab_top(self, notebook):
        """Crear pestaña de top pagadores y atrasados"""
        frame = tk.Frame(notebook, bg=self.tema['bg_secundario'])
        notebook.add(frame, text='👥 Top 10')
        
        # Dividir en dos columnas
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        
        # Top pagadores
        top_panel = PanelModerno(frame, titulo="🏆 Top 10 Mejores Pagadores", tema=self.tema, collapsible=False)
        top_panel.grid(row=0, column=0, sticky='nsew', padx=(ESPACIADO['md'], ESPACIADO['xs']), 
                      pady=ESPACIADO['md'])
        
        # Crear treeview para top pagadores
        tree_top = ttk.Treeview(top_panel.content, columns=('folio', 'nombre', 'pagado'), 
                               show='headings', height=12)
        tree_top.heading('folio', text='Folio')
        tree_top.heading('nombre', text='Nombre')
        tree_top.heading('pagado', text='Pagado')
        
        tree_top.column('folio', width=100, anchor='center')
        tree_top.column('nombre', width=200)
        tree_top.column('pagado', width=100, anchor='e')
        
        for i, persona in enumerate(self.top_pagadores, 1):
            valores = (
                persona.get('folio', 'N/A'),
                persona.get('nombre', 'Sin nombre'),
                f"${persona.get('total_pagado', 0):,.2f}"
            )
            tree_top.insert('', 'end', values=valores, tags=(f'rank{i}',))
        
        # Colorear los primeros 3
        tree_top.tag_configure('rank1', background='#FFD700')  # Oro
        tree_top.tag_configure('rank2', background='#C0C0C0')  # Plata
        tree_top.tag_configure('rank3', background='#CD7F32')  # Bronce
        
        tree_top.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['sm'], pady=ESPACIADO['sm'])
        
        # Scrollbar para top
        scroll_top = ttk.Scrollbar(top_panel.content, orient='vertical', command=tree_top.yview)
        tree_top.configure(yscrollcommand=scroll_top.set)
        scroll_top.pack(side=tk.RIGHT, fill=tk.Y, before=tree_top)
        
        # Top atrasados
        atraso_panel = PanelModerno(frame, titulo="⚠️ Top 10 Mayores Atrasos", tema=self.tema, collapsible=False)
        atraso_panel.grid(row=0, column=1, sticky='nsew', padx=(ESPACIADO['xs'], ESPACIADO['md']), 
                         pady=ESPACIADO['md'])
        
        # Crear treeview para atrasados
        tree_atraso = ttk.Treeview(atraso_panel.content, columns=('folio', 'nombre', 'falta'), 
                                  show='headings', height=12)
        tree_atraso.heading('folio', text='Folio')
        tree_atraso.heading('nombre', text='Nombre')
        tree_atraso.heading('falta', text='Falta')
        
        tree_atraso.column('folio', width=100, anchor='center')
        tree_atraso.column('nombre', width=200)
        tree_atraso.column('falta', width=100, anchor='e')
        
        for persona in self.top_atrasados:
            faltante = self.monto_cooperacion - persona.get('total_pagado', 0)
            valores = (
                persona.get('folio', 'N/A'),
                persona.get('nombre', 'Sin nombre'),
                f"${faltante:,.2f}"
            )
            tree_atraso.insert('', 'end', values=valores, tags=('atraso',))
        
        tree_atraso.tag_configure('atraso', background='#FFEBEE')
        
        tree_atraso.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['sm'], pady=ESPACIADO['sm'])
        
        # Scrollbar para atrasados
        scroll_atraso = ttk.Scrollbar(atraso_panel.content, orient='vertical', command=tree_atraso.yview)
        tree_atraso.configure(yscrollcommand=scroll_atraso.set)
        scroll_atraso.pack(side=tk.RIGHT, fill=tk.Y, before=tree_atraso)
    
    def crear_tab_temporal(self, notebook):
        """Crear pestaña de análisis temporal"""
        frame = tk.Frame(notebook, bg=self.tema['bg_secundario'])
        notebook.add(frame, text='📅 Análisis Temporal')
        
        # Scroll
        canvas = tk.Canvas(frame, bg=self.tema['bg_secundario'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.tema['bg_secundario'])
        
        scrollable.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=scrollable, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=ESPACIADO['md'], pady=ESPACIADO['md'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        if not self.fechas_pagos:
            no_data = tk.Label(scrollable, text="No hay datos de pagos para analizar",
                             font=FUENTES['titulo'], bg=self.tema['bg_secundario'], 
                             fg=self.tema['texto_secundario'])
            no_data.pack(pady=50)
            return
        
        # Pagos por mes
        mes_panel = PanelModerno(scrollable, titulo="📊 Pagos por Mes", tema=self.tema, collapsible=False)
        mes_panel.pack(fill=tk.X, pady=(0, ESPACIADO['md']))
        
        meses_ordenados = sorted(self.pagos_por_mes.items())
        mes_data = [(mes, cantidad) for mes, cantidad in meses_ordenados]
        
        self.crear_grafico_ascii_linea(mes_panel.content, mes_data, "Mes")
        
        # Pagos por día de la semana
        dia_panel = PanelModerno(scrollable, titulo="📊 Pagos por Día de la Semana", tema=self.tema, collapsible=False)
        dia_panel.pack(fill=tk.X, pady=(0, ESPACIADO['md']))
        
        dias_data = [(dia, self.pagos_por_dia_semana[dia]) for dia in 
                     ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']]
        
        self.crear_grafico_ascii_barras_horizontal(dia_panel.content, dias_data, "Día de la Semana")
    
    def crear_barra_progreso(self, parent, porcentaje):
        """Crear una barra de progreso visual"""
        frame = tk.Frame(parent, bg=self.tema['card_bg'], height=40)
        frame.pack(fill=tk.X, padx=ESPACIADO['md'], pady=(0, ESPACIADO['md']))
        
        # Contenedor de la barra
        barra_container = tk.Frame(frame, bg=self.tema['bg_secundario'], height=30, relief=tk.SUNKEN, bd=1)
        barra_container.pack(fill=tk.X, padx=ESPACIADO['sm'], pady=ESPACIADO['sm'])
        
        # Barra de progreso
        if porcentaje >= 100:
            color = '#4CAF50'  # Verde
        elif porcentaje >= 50:
            color = '#FFC107'  # Amarillo
        else:
            color = '#F44336'  # Rojo
        
        barra = tk.Frame(barra_container, bg=color, height=28)
        barra.place(relwidth=min(porcentaje/100, 1), relheight=1)
        
        # Texto del porcentaje
        texto = tk.Label(barra_container, text=f"{porcentaje:.1f}%", 
                        font=FUENTES['subtitulo'], bg=self.tema['bg_secundario'], 
                        fg=self.tema['texto_primario'])
        texto.place(relx=0.5, rely=0.5, anchor='center')
    
    def crear_grafico_ascii_barras(self, parent, datos, titulo):
        """Crear un gráfico de barras ASCII"""
        panel = PanelModerno(parent, titulo=titulo, tema=self.tema, collapsible=False)
        panel.pack(fill=tk.X, pady=(0, ESPACIADO['md']))
        
        text_widget = tk.Text(panel.content, height=10, font=('Courier New', 10),
                             bg=self.tema['card_bg'], fg=self.tema['texto_primario'],
                             relief=tk.FLAT, padx=ESPACIADO['md'], pady=ESPACIADO['md'])
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Encontrar el máximo para escalar
        max_val = max(cantidad for _, cantidad, _ in datos) if datos else 1
        ancho_maximo = 40
        
        for etiqueta, cantidad, _ in datos:
            if max_val > 0:
                ancho = int((cantidad / max_val) * ancho_maximo)
            else:
                ancho = 0
            barra = '█' * ancho
            text_widget.insert('end', f"{etiqueta:20s} │{barra} {cantidad}\n")
        
        text_widget.config(state='disabled')
    
    def crear_grafico_ascii_linea(self, parent, datos, label_x):
        """Crear un gráfico de línea ASCII simple"""
        if not datos:
            return
        
        text_widget = tk.Text(parent, height=10, font=('Courier New', 9),
                             bg=self.tema['card_bg'], fg=self.tema['texto_primario'],
                             relief=tk.FLAT, padx=ESPACIADO['md'], pady=ESPACIADO['md'])
        text_widget.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['sm'], pady=ESPACIADO['sm'])
        
        max_val = max(cantidad for _, cantidad in datos) if datos else 1
        altura = 8
        
        # Construir gráfico
        for etiqueta, cantidad in datos:
            nivel = int((cantidad / max_val) * altura) if max_val > 0 else 0
            barra = '│' + '█' * nivel
            # Convertir formato YYYY-MM a mes/año legible
            try:
                año, mes = etiqueta.split('-')
                mes_nombre = calendar.month_abbr[int(mes)]
                etiqueta_corta = f"{mes_nombre} {año[2:]}"
            except:
                etiqueta_corta = etiqueta[:8]
            
            text_widget.insert('end', f"{etiqueta_corta:10s} {barra} ({cantidad})\n")
        
        text_widget.config(state='disabled')
    
    def crear_grafico_ascii_barras_horizontal(self, parent, datos, titulo):
        """Crear gráfico de barras horizontal"""
        text_widget = tk.Text(parent, height=10, font=('Courier New', 10),
                             bg=self.tema['card_bg'], fg=self.tema['texto_primario'],
                             relief=tk.FLAT, padx=ESPACIADO['md'], pady=ESPACIADO['md'])
        text_widget.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['sm'], pady=ESPACIADO['sm'])
        
        max_val = max(cantidad for _, cantidad in datos) if datos else 1
        ancho_maximo = 30
        
        for etiqueta, cantidad in datos:
            if max_val > 0:
                ancho = int((cantidad / max_val) * ancho_maximo)
            else:
                ancho = 0
            barra = '█' * ancho
            text_widget.insert('end', f"{etiqueta:12s} │{barra} {cantidad}\n")
        
        text_widget.config(state='disabled')
