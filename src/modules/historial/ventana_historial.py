"""
Ventana para ver el historial de cambios del sistema
"""
import tkinter as tk
from tkinter import ttk, messagebox
from src.modules.historial.historial import GestorHistorial
from datetime import datetime
from src.ui.tema_moderno import TEMA_CLARO, TEMA_OSCURO, FUENTES

class VentanaHistorial:
    """Ventana para visualizar el historial de cambios"""
    
    def __init__(self, parent, filtro_entidad=None, filtro_id=None):
        self.parent = parent
        self.filtro_entidad = filtro_entidad
        self.filtro_id = filtro_id
        self.gestor_historial = GestorHistorial()
        
        self.crear_ventana()
    
    def crear_ventana(self):
        """Crear interfaz de historial"""
        tema_visual = TEMA_OSCURO
        self.ventana = tk.Toplevel(self.parent)
        self.ventana.title("Historial de Cambios - Auditoría")
        self.ventana.geometry("1100x650")
        self.ventana.transient(self.parent)
        self.ventana.configure(bg=tema_visual['bg_principal'])

        estilo = ttk.Style()
        estilo.theme_use('clam')
        estilo.configure('TFrame', background=tema_visual['bg_principal'])
        estilo.configure('TLabelframe', background=tema_visual['bg_secundario'], foreground=tema_visual['fg_principal'], font=FUENTES['subtitulo'])
        estilo.configure('TLabelframe.Label', background=tema_visual['bg_secundario'], foreground=tema_visual['fg_principal'], font=FUENTES['subtitulo'])
        estilo.configure('TLabel', background=tema_visual['bg_principal'], foreground=tema_visual['fg_principal'], font=FUENTES['normal'])
        estilo.configure('TButton', background=tema_visual['accent_primary'], foreground='#ffffff', padding=8, borderwidth=0, font=FUENTES['botones'])
        estilo.map('TButton', background=[('active', tema_visual['accent_secondary'])])
        estilo.configure('TEntry', fieldbackground=tema_visual['input_bg'], borderwidth=1)
        estilo.configure('TCombobox', fieldbackground=tema_visual['input_bg'], background=tema_visual['input_bg'])
        estilo.configure('Treeview', background=tema_visual['table_row_even'], foreground=tema_visual['fg_principal'],
                        fieldbackground=tema_visual['table_row_even'], borderwidth=0, rowheight=26, font=FUENTES['normal'])
        estilo.map('Treeview', background=[('selected', tema_visual['table_selected'])], foreground=[('selected', tema_visual['fg_principal'])])
        estilo.configure('Treeview.Heading', background=tema_visual['table_header'], foreground=tema_visual['fg_principal'],
                        padding=8, font=FUENTES['subtitulo'], borderwidth=0)
        
        # Frame principal
        main_frame = ttk.Frame(self.ventana, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = "📜 Historial de Cambios y Auditoría"
        if self.filtro_entidad:
            titulo += f" - {self.filtro_entidad}"
        ttk.Label(main_frame, text=titulo, font=FUENTES['titulo']).pack(pady=(0, 10))
        
        # Frame de filtros
        filtros_frame = ttk.LabelFrame(main_frame, text="Filtros", padding="10")
        filtros_frame.pack(fill=tk.X, pady=(0, 10))
        
        row1 = ttk.Frame(filtros_frame)
        row1.pack(fill=tk.X, pady=5)
        
        ttk.Label(row1, text="Tipo:").pack(side=tk.LEFT, padx=5)
        self.tipo_var = tk.StringVar()
        tipo_combo = ttk.Combobox(row1, textvariable=self.tipo_var, 
                                  values=['Todos', 'CREAR', 'EDITAR', 'ELIMINAR', 'PAGO', 'SINCRONIZAR'],
                                  state='readonly', width=15)
        tipo_combo.set('Todos')
        tipo_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text="Entidad:").pack(side=tk.LEFT, padx=(20, 5))
        self.entidad_var = tk.StringVar()
        entidad_combo = ttk.Combobox(row1, textvariable=self.entidad_var,
                                     values=['Todas', 'HABITANTE', 'COOPERACION', 'PAGO', 'PERSONA'],
                                     state='readonly', width=15)
        entidad_combo.set('Todas')
        entidad_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text="Fecha:").pack(side=tk.LEFT, padx=(20, 5))
        self.fecha_var = tk.StringVar()
        fecha_entry = ttk.Entry(row1, textvariable=self.fecha_var, width=12)
        fecha_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(row1, text="(DD/MM/YYYY)", font=('Arial', 8, 'italic')).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(row1, text="🔍 Filtrar", command=self.aplicar_filtros, width=12).pack(side=tk.LEFT, padx=(20, 5))
        ttk.Button(row1, text="🔄 Limpiar", command=self.limpiar_filtros, width=12).pack(side=tk.LEFT, padx=5)
        
        # Label de info
        self.info_label = ttk.Label(main_frame, text="", font=FUENTES['pequeño'])
        self.info_label.pack(pady=5)
        
        # Frame de tabla
        tabla_frame = ttk.Frame(main_frame)
        tabla_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        scrollbar_y = ttk.Scrollbar(tabla_frame, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(tabla_frame, orient=tk.HORIZONTAL)
        
        # Treeview
        self.tree = ttk.Treeview(tabla_frame,
                                columns=('id', 'fecha', 'hora', 'tipo', 'entidad', 'usuario', 'resumen'),
                                show='headings',
                                yscrollcommand=scrollbar_y.set,
                                xscrollcommand=scrollbar_x.set)
        
        # Configurar columnas
        self.tree.heading('id', text='#')
        self.tree.heading('fecha', text='Fecha')
        self.tree.heading('hora', text='Hora')
        self.tree.heading('tipo', text='Tipo')
        self.tree.heading('entidad', text='Entidad')
        self.tree.heading('usuario', text='Usuario')
        self.tree.heading('resumen', text='Resumen')
        
        self.tree.column('id', width=60, anchor=tk.CENTER)
        self.tree.column('fecha', width=100, anchor=tk.CENTER)
        self.tree.column('hora', width=90, anchor=tk.CENTER)
        self.tree.column('tipo', width=100, anchor=tk.CENTER)
        self.tree.column('entidad', width=120, anchor=tk.CENTER)
        self.tree.column('usuario', width=120, anchor=tk.CENTER)
        self.tree.column('resumen', width=400, anchor=tk.W)
        
        # Posicionar elementos
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_x.grid(row=1, column=0, sticky=(tk.E, tk.W))
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        tabla_frame.columnconfigure(0, weight=1)
        tabla_frame.rowconfigure(0, weight=1)
        
        # Frame de detalles
        detalles_frame = ttk.LabelFrame(main_frame, text="Detalles del Cambio", padding="10")
        detalles_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.detalles_text = tk.Text(detalles_frame, height=6, wrap=tk.WORD, 
                         font=('Courier New', 10), state='disabled',
                         bg=tema_visual['bg_secundario'], fg=tema_visual['fg_principal'],
                         insertbackground=tema_visual['fg_principal'], relief=tk.FLAT, padx=10, pady=10)
        detalles_text_scroll = ttk.Scrollbar(detalles_frame, command=self.detalles_text.yview)
        self.detalles_text.config(yscrollcommand=detalles_text_scroll.set)
        self.detalles_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detalles_text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botones inferiores
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(bottom_frame, text="🔄 Actualizar", command=self.cargar_historial, 
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="📋 Exportar", command=self.exportar_historial, 
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="✕ Cerrar", command=self.ventana.destroy, 
                  width=12).pack(side=tk.RIGHT, padx=5)
        
        # Evento de selección
        self.tree.bind('<<TreeviewSelect>>', self.mostrar_detalles)
        
        # Cargar historial inicial
        self.cargar_historial()
    
    def cargar_historial(self):
        """Cargar historial desde el gestor"""
        # Obtener historial completo o filtrado
        if self.filtro_entidad and self.filtro_id:
            historial = self.gestor_historial.obtener_historial_entidad(
                self.filtro_entidad, self.filtro_id
            )
        else:
            historial = self.gestor_historial.historial
        
        # Aplicar filtros adicionales de la UI
        historial = self.filtrar_historial(historial)
        
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Agregar registros (más recientes primero)
        for registro in reversed(historial):
            # Crear resumen del cambio
            resumen = self.crear_resumen(registro)
            
            # Determinar color según tipo
            tipo = registro.get('tipo', '')
            if tipo == 'CREAR':
                tag = 'crear'
            elif tipo == 'EDITAR':
                tag = 'editar'
            elif tipo == 'ELIMINAR':
                tag = 'eliminar'
            elif tipo == 'PAGO':
                tag = 'pago'
            else:
                tag = 'otro'
            
            self.tree.insert('', tk.END, values=(
                registro.get('id', ''),
                registro.get('fecha', ''),
                registro.get('hora', ''),
                tipo,
                registro.get('entidad', ''),
                registro.get('usuario', ''),
                resumen
            ), tags=(tag,), iid=str(registro.get('id', '')))
        
        tema_visual = TEMA_OSCURO
        self.tree.tag_configure('crear', background=tema_visual['table_row_odd'], foreground=tema_visual['success'])
        self.tree.tag_configure('editar', background=tema_visual['table_row_odd'], foreground=tema_visual['warning'])
        self.tree.tag_configure('eliminar', background=tema_visual['table_row_odd'], foreground=tema_visual['error'])
        self.tree.tag_configure('pago', background=tema_visual['table_row_odd'], foreground=tema_visual['accent_primary'])
        self.tree.tag_configure('otro', background=tema_visual['table_row_even'], foreground=tema_visual['fg_principal'])
        
        # Actualizar label de info
        self.info_label.config(text=f"📊 Mostrando {len(historial)} registros")
    
    def filtrar_historial(self, historial):
        """Aplicar filtros de UI al historial"""
        resultado = historial.copy()
        
        # Filtrar por tipo
        if self.tipo_var.get() and self.tipo_var.get() != 'Todos':
            resultado = [r for r in resultado if r.get('tipo') == self.tipo_var.get()]
        
        # Filtrar por entidad
        if self.entidad_var.get() and self.entidad_var.get() != 'Todas':
            resultado = [r for r in resultado if r.get('entidad') == self.entidad_var.get()]
        
        # Filtrar por fecha
        if self.fecha_var.get():
            fecha_buscar = self.fecha_var.get()
            resultado = [r for r in resultado if r.get('fecha') == fecha_buscar]
        
        return resultado
    
    def crear_resumen(self, registro):
        """Crear resumen legible del cambio"""
        tipo = registro.get('tipo', '')
        entidad = registro.get('entidad', '')
        id_entidad = registro.get('id_entidad', '')
        cambios = registro.get('cambios', {})
        
        if tipo == 'CREAR':
            return f"Se creó {entidad.lower()} '{id_entidad}'"
        elif tipo == 'ELIMINAR':
            return f"Se eliminó {entidad.lower()} '{id_entidad}'"
        elif tipo == 'PAGO':
            monto = cambios.get('monto', 0)
            return f"Pago de ${monto:.2f} registrado para '{id_entidad}'"
        elif tipo == 'EDITAR':
            num_cambios = len(cambios)
            return f"Se editó {entidad.lower()} '{id_entidad}' ({num_cambios} cambio(s))"
        else:
            return f"{tipo} en {entidad.lower()} '{id_entidad}'"
    
    def mostrar_detalles(self, event=None):
        """Mostrar detalles del registro seleccionado"""
        seleccion = self.tree.selection()
        if not seleccion:
            return
        
        registro_id = seleccion[0]
        
        # Buscar registro completo
        registro = next((r for r in self.gestor_historial.historial 
                        if str(r.get('id', '')) == registro_id), None)
        
        if not registro:
            return
        
        # Formatear detalles
        detalles = f"""DETALLES DEL CAMBIO #{registro.get('id', '')}
{'=' * 80}
Fecha/Hora: {registro.get('fecha', '')} {registro.get('hora', '')}
Tipo: {registro.get('tipo', '')}
Entidad: {registro.get('entidad', '')}
ID Entidad: {registro.get('id_entidad', '')}
Usuario: {registro.get('usuario', '')}

CAMBIOS REALIZADOS:
"""
        
        cambios = registro.get('cambios', {})
        if isinstance(cambios, dict):
            for campo, info in cambios.items():
                if isinstance(info, dict) and 'anterior' in info and 'nuevo' in info:
                    detalles += f"\n  • {campo}:\n"
                    detalles += f"      Anterior: {info['anterior']}\n"
                    detalles += f"      Nuevo: {info['nuevo']}\n"
                else:
                    detalles += f"\n  • {campo}: {info}\n"
        else:
            detalles += f"\n{cambios}\n"
        
        # Actualizar texto
        self.detalles_text.config(state='normal')
        self.detalles_text.delete(1.0, tk.END)
        self.detalles_text.insert(1.0, detalles)
        self.detalles_text.config(state='disabled')
    
    def aplicar_filtros(self):
        """Aplicar filtros y recargar"""
        self.cargar_historial()
    
    def limpiar_filtros(self):
        """Limpiar filtros"""
        self.tipo_var.set('Todos')
        self.entidad_var.set('Todas')
        self.fecha_var.set('')
        self.cargar_historial()
    
    def exportar_historial(self):
        """Exportar historial a TXT o CSV"""
        try:
            from tkinter import filedialog
            ruta = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Texto", "*.txt"), ("CSV", "*.csv"), ("Todos", "*.*")],
                initialfile=f"historial_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            if not ruta:
                return

            if ruta.lower().endswith('.csv'):
                import csv
                with open(ruta, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID', 'Fecha', 'Hora', 'Tipo', 'Entidad', 'Usuario', 'Resumen'])
                    for item in self.tree.get_children():
                        valores = self.tree.item(item)['values']
                        writer.writerow(valores)
            else:
                with open(ruta, 'w', encoding='utf-8') as f:
                    f.write("HISTORIAL DE CAMBIOS - SISTEMA COMUNIDAD\n")
                    f.write(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                    f.write("=" * 100 + "\n\n")
                    for item in self.tree.get_children():
                        valores = self.tree.item(item)['values']
                        f.write(f"ID: {valores[0]} | Fecha: {valores[1]} {valores[2]} | ")
                        f.write(f"Tipo: {valores[3]} | Entidad: {valores[4]} | ")
                        f.write(f"Usuario: {valores[5]}\n")
                        f.write(f"  Resumen: {valores[6]}\n")
                        f.write("-" * 100 + "\n")

            messagebox.showinfo("Éxito", f"Historial exportado correctamente a:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
