"""
Ventana de búsqueda avanzada con filtros
"""
import tkinter as tk
from tkinter import ttk, messagebox
from buscador import BuscadorAvanzado

class VentanaBusquedaAvanzada:
    """Ventana para búsqueda avanzada con múltiples filtros"""
    
    def __init__(self, parent, personas, callback_seleccion):
        self.parent = parent
        self.personas = personas
        self.callback_seleccion = callback_seleccion
        self.buscador = BuscadorAvanzado()
        self.resultados = []
        
        self.crear_ventana()
    
    def crear_ventana(self):
        """Crear interfaz de búsqueda"""
        self.ventana = tk.Toplevel(self.parent)
        self.ventana.title("Búsqueda Avanzada")
        self.ventana.geometry("900x700")
        self.ventana.transient(self.parent)
        self.ventana.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(self.ventana, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="🔍 Búsqueda Avanzada de Personas", 
                 font=('Arial', 14, 'bold')).pack(pady=(0, 10))
        
        # Frame de filtros
        filtros_frame = ttk.LabelFrame(main_frame, text="Filtros de Búsqueda", padding="15")
        filtros_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Nombre
        row1 = ttk.Frame(filtros_frame)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="Nombre:", width=15).pack(side=tk.LEFT, padx=5)
        self.nombre_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.nombre_var, width=40).pack(side=tk.LEFT, padx=5)
        
        # Folio
        ttk.Label(row1, text="Folio:", width=10).pack(side=tk.LEFT, padx=5)
        self.folio_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.folio_var, width=20).pack(side=tk.LEFT, padx=5)
        
        # Estado de pago
        row2 = ttk.Frame(filtros_frame)
        row2.pack(fill=tk.X, pady=5)
        ttk.Label(row2, text="Estado:", width=15).pack(side=tk.LEFT, padx=5)
        self.estado_var = tk.StringVar()
        estado_combo = ttk.Combobox(row2, textvariable=self.estado_var, 
                                    values=['Todos', 'PAGADO', 'PENDIENTE', 'PARCIAL'],
                                    state='readonly', width=15)
        estado_combo.set('Todos')
        estado_combo.pack(side=tk.LEFT, padx=5)
        
        # Rango de montos
        ttk.Label(row2, text="Monto Pagado:", width=15).pack(side=tk.LEFT, padx=(20, 5))
        ttk.Label(row2, text="Min:").pack(side=tk.LEFT, padx=5)
        self.monto_min_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.monto_min_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(row2, text="Max:").pack(side=tk.LEFT, padx=5)
        self.monto_max_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.monto_max_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Botones de acción
        btn_frame = ttk.Frame(filtros_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="🔍 Buscar", command=self.realizar_busqueda, 
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Limpiar Filtros", command=self.limpiar_filtros, 
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📊 Estadísticas", command=self.mostrar_estadisticas, 
                  width=15).pack(side=tk.LEFT, padx=5)
        
        # Label de resultados
        self.resultado_label = ttk.Label(main_frame, text="", font=('Arial', 10, 'italic'))
        self.resultado_label.pack(pady=5)
        
        # Frame de tabla
        tabla_frame = ttk.Frame(main_frame)
        tabla_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        scrollbar_y = ttk.Scrollbar(tabla_frame, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(tabla_frame, orient=tk.HORIZONTAL)
        
        # Treeview
        self.tree = ttk.Treeview(tabla_frame,
                                columns=('folio', 'nombre', 'esperado', 'pagado', 'pendiente', 'estado'),
                                show='headings',
                                yscrollcommand=scrollbar_y.set,
                                xscrollcommand=scrollbar_x.set)
        
        # Configurar columnas
        self.tree.heading('folio', text='Folio')
        self.tree.heading('nombre', text='Nombre')
        self.tree.heading('esperado', text='Esperado')
        self.tree.heading('pagado', text='Pagado')
        self.tree.heading('pendiente', text='Pendiente')
        self.tree.heading('estado', text='Estado')
        
        self.tree.column('folio', width=100, anchor=tk.CENTER)
        self.tree.column('nombre', width=250, anchor=tk.W)
        self.tree.column('esperado', width=100, anchor=tk.CENTER)
        self.tree.column('pagado', width=100, anchor=tk.CENTER)
        self.tree.column('pendiente', width=100, anchor=tk.CENTER)
        self.tree.column('estado', width=100, anchor=tk.CENTER)
        
        # Posicionar elementos
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_x.grid(row=1, column=0, sticky=(tk.E, tk.W))
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        tabla_frame.columnconfigure(0, weight=1)
        tabla_frame.rowconfigure(0, weight=1)
        
        # Botones inferiores
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(bottom_frame, text="✓ Seleccionar", command=self.seleccionar_persona, 
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="✕ Cerrar", command=self.ventana.destroy, 
                  width=12).pack(side=tk.RIGHT, padx=5)
        
        # Doble clic para seleccionar
        self.tree.bind('<Double-1>', lambda e: self.seleccionar_persona())
        
        # Realizar búsqueda inicial
        self.realizar_busqueda()
    
    def realizar_busqueda(self):
        """Realizar búsqueda con los filtros actuales"""
        # Construir criterios
        criterios = {}
        
        if self.nombre_var.get():
            criterios['nombre'] = self.nombre_var.get()
        
        if self.folio_var.get():
            criterios['folio'] = self.folio_var.get()
        
        if self.estado_var.get() and self.estado_var.get() != 'Todos':
            criterios['estado_pago'] = self.estado_var.get()
        
        if self.monto_min_var.get():
            try:
                criterios['monto_minimo'] = float(self.monto_min_var.get())
            except ValueError:
                pass
        
        if self.monto_max_var.get():
            try:
                criterios['monto_maximo'] = float(self.monto_max_var.get())
            except ValueError:
                pass
        
        # Realizar búsqueda
        self.resultados = self.buscador.buscar_personas(self.personas, criterios)
        
        # Actualizar tabla
        self.actualizar_tabla()
        
        # Actualizar label de resultados
        self.resultado_label.config(
            text=f"✓ Encontrados {len(self.resultados)} resultado(s) de {len(self.personas)} personas"
        )
    
    def actualizar_tabla(self):
        """Actualizar tabla con resultados"""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Agregar resultados
        for persona in self.resultados:
            folio = persona.get('folio', 'SIN-FOLIO')
            nombre = persona.get('nombre', '')
            esperado = persona.get('monto_esperado', 0)
            pagos = persona.get('pagos', [])
            pagado = sum(p.get('monto', 0) for p in pagos)
            pendiente = max(0, esperado - pagado)
            
            if pendiente == 0:
                estado = 'PAGADO'
                tag = 'pagado'
            elif pagado == 0:
                estado = 'PENDIENTE'
                tag = 'pendiente'
            else:
                estado = 'PARCIAL'
                tag = 'parcial'
            
            self.tree.insert('', tk.END, values=(
                folio,
                nombre,
                f'${esperado:.2f}',
                f'${pagado:.2f}',
                f'${pendiente:.2f}',
                estado
            ), tags=(tag,))
        
        # Configurar colores
        self.tree.tag_configure('pagado', background='#c8e6c9')
        self.tree.tag_configure('pendiente', background='#ffccbc')
        self.tree.tag_configure('parcial', background='#fff9c4')
    
    def limpiar_filtros(self):
        """Limpiar todos los filtros"""
        self.nombre_var.set('')
        self.folio_var.set('')
        self.estado_var.set('Todos')
        self.monto_min_var.set('')
        self.monto_max_var.set('')
        self.realizar_busqueda()
    
    def mostrar_estadisticas(self):
        """Mostrar estadísticas de los resultados actuales"""
        if not self.resultados:
            messagebox.showinfo("Estadísticas", "No hay resultados para mostrar estadísticas")
            return
        
        stats = self.buscador.obtener_estadisticas(self.resultados)
        
        mensaje = f"""📊 ESTADÍSTICAS DE BÚSQUEDA

Total de Personas: {stats['total_personas']}

Estados de Pago:
  • Pagado Completo: {stats['pagado_completo']} personas
  • Pago Parcial: {stats['pago_parcial']} personas
  • Sin Pagar: {stats['sin_pagar']} personas

Montos:
  • Total Esperado: ${stats['total_esperado']:.2f}
  • Total Recaudado: ${stats['total_recaudado']:.2f}
  • Total Pendiente: ${stats['total_pendiente']:.2f}

Promedios:
  • Promedio Esperado: ${stats['promedio_esperado']:.2f}
  • Promedio Pagado: ${stats['promedio_pagado']:.2f}

Porcentaje de Recaudación: {stats['porcentaje_recaudacion']:.1f}%
"""
        
        messagebox.showinfo("Estadísticas de Búsqueda", mensaje)
    
    def seleccionar_persona(self):
        """Seleccionar persona y cerrar ventana"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Por favor seleccione una persona")
            return
        
        index = self.tree.index(seleccion[0])
        persona_seleccionada = self.resultados[index]
        
        self.callback_seleccion(persona_seleccionada)
        self.ventana.destroy()
