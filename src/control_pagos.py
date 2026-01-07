import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime
import hashlib
import requests
import subprocess
import sys
import time

class SistemaControlPagos:
    # Temas
    TEMAS = {
        'claro': {
            'bg': '#f0f0f0',
            'fg': '#000000',
            'frame_bg': '#ffffff',
            'button_bg': '#e0e0e0',
            'entrada_bg': '#ffffff',
            'titulo_fg': '#1a1a1a',
            'exito_fg': '#2e7d32',
            'alerta_fg': '#f57f17',
            'error_fg': '#c62828',
            'tablas_even': '#f5f5f5',
            'tablas_odd': '#ffffff'
        },
        'oscuro': {
            'bg': '#1e1e1e',
            'fg': '#e0e0e0',
            'frame_bg': '#2d2d2d',
            'button_bg': '#404040',
            'entrada_bg': '#3a3a3a',
            'titulo_fg': '#f0f0f0',
            'exito_fg': '#66bb6a',
            'alerta_fg': '#ffa726',
            'error_fg': '#ef5350',
            'tablas_even': '#252525',
            'tablas_odd': '#2d2d2d'
        }
    }
    
    TAMAÑOS_LETRA = {
        'pequeño': {'titulo': 10, 'normal': 8, 'grande': 9},
        'normal': {'titulo': 14, 'normal': 10, 'grande': 12},
        'grande': {'titulo': 18, 'normal': 12, 'grande': 16}
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Control de Pagos - Proyectos Comunitarios")
        self.root.state('zoomed')  # Pantalla completa en Windows
        
        # Tema y accesibilidad
        self.tema_actual = tk.StringVar(value='claro')
        self.tamaño_actual = tk.StringVar(value='normal')
        
        # Datos
        self.cooperaciones = []
        self.coop_activa_id = None
        self.personas = []
        self.monto_cooperacion = 100.0
        self.proyecto_actual = "Proyecto Comunitario 2026"
        self.mostrar_total = False
        self.archivo_datos = "datos_pagos.json"
        self.password_hash = None
        self.api_url = "http://127.0.0.1:5000/api"
        self.fila_animada = None
        
        # Cargar datos si existen (incluyendo tema y tamaño guardados)
        self.cargar_datos()
        self.aplicar_cooperacion_activa()
        
        # Aplicar tema y tamaño guardados
        if hasattr(self, 'tema_guardado'):
            self.tema_actual.set(self.tema_guardado)
        if hasattr(self, 'tamaño_guardado'):
            self.tamaño_actual.set(self.tamaño_guardado)
        
        # Ahora sí vincular los eventos de cambio
        self.tema_actual.trace('w', self.aplicar_tema)
        self.tamaño_actual.trace('w', self.aplicar_tamaño)
        
        # Verificar/iniciar API local
        if not self.asegurar_api_activa():
            messagebox.showerror("Error", "No se pudo iniciar ni conectar con la API local")
            return
        
        # Verificar/establecer contraseña primera vez
        if not self.verificar_password_inicial():
            return
        
        self.nombre_visible = tk.BooleanVar(value=True)
        self.folio_visible = tk.BooleanVar(value=True)
        
        # Configurar interfaz
        self.configurar_interfaz()
    
    def obtener_colores(self):
        """Obtener paleta de colores del tema actual"""
        return self.TEMAS[self.tema_actual.get()]
    
    def obtener_tamaños(self):
        """Obtener tamaños de letra"""
        return self.TAMAÑOS_LETRA[self.tamaño_actual.get()]
    
    def aplicar_tema(self, *args):
        """Aplicar cambios de tema a toda la interfaz"""
        self.guardar_datos(mostrar_alerta=False)
        messagebox.showinfo("Tema Actualizado", "El tema se aplicará al reiniciar el programa")
    
    def aplicar_tamaño(self, *args):
        """Aplicar cambios de tamaño de letra"""
        self.guardar_datos(mostrar_alerta=False)
        messagebox.showinfo("Tamaño Actualizado", "El tamaño de letra se aplicará al reiniciar el programa")

    
    def hash_password(self, password):
        """Crear hash de la contraseña"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verificar_password_inicial(self):
        """Verificar si existe contraseña, si no, crearla"""
        if self.password_hash is None:
            return self.establecer_password_inicial()
        return True
    
    def establecer_password_inicial(self):
        """Diálogo para establecer contraseña por primera vez"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Configuracion Inicial - Establecer Contraseña")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)  # No permitir cerrar
        
        ttk.Label(dialog, text="CONFIGURACION INICIAL", font=('Arial', 14, 'bold')).pack(pady=10)
        ttk.Label(dialog, text="Establezca una contraseña para proteger\nla modificacion del monto de cooperacion", 
                 font=('Arial', 10)).pack(pady=5)
        
        ttk.Label(dialog, text="Contraseña:", font=('Arial', 10, 'bold')).pack(pady=5)
        pass1_entry = ttk.Entry(dialog, show="*", width=30)
        pass1_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Confirmar Contraseña:", font=('Arial', 10, 'bold')).pack(pady=5)
        pass2_entry = ttk.Entry(dialog, show="*", width=30)
        pass2_entry.pack(pady=5)
        
        resultado = {'success': False}
        
        def guardar_password():
            pass1 = pass1_entry.get()
            pass2 = pass2_entry.get()
            
            if not pass1 or not pass2:
                messagebox.showerror("Error", "Debe llenar ambos campos")
                return
            
            if pass1 != pass2:
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                pass1_entry.delete(0, tk.END)
                pass2_entry.delete(0, tk.END)
                pass1_entry.focus()
                return
            
            if len(pass1) < 4:
                messagebox.showerror("Error", "La contraseña debe tener al menos 4 caracteres")
                return
            
            self.password_hash = self.hash_password(pass1)
            self.guardar_datos()
            messagebox.showinfo("Exito", "Contraseña establecida correctamente")
            resultado['success'] = True
            dialog.destroy()
        
        ttk.Button(dialog, text="Establecer Contraseña", command=guardar_password).pack(pady=15)
        pass1_entry.focus()
        
        dialog.wait_window()
        return resultado['success']
    
    def solicitar_password(self):
        """Solicitar contraseña para modificar monto"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Contraseña Requerida")
        dialog.geometry("350x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Ingrese la contraseña para modificar el monto:", 
                 font=('Arial', 10, 'bold')).pack(pady=10)
        
        pass_entry = ttk.Entry(dialog, show="*", width=30)
        pass_entry.pack(pady=10)
        
        resultado = {'success': False}
        
        def verificar():
            password = pass_entry.get()
            if self.hash_password(password) == self.password_hash:
                resultado['success'] = True
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Contraseña incorrecta")
                pass_entry.delete(0, tk.END)
                pass_entry.focus()
        
        ttk.Button(dialog, text="Verificar", command=verificar, width=18).pack(pady=5)
        ttk.Button(dialog, text="Cancelar", command=dialog.destroy, width=12).pack(pady=5)
        dialog.bind("<Return>", lambda event: verificar())
        pass_entry.focus()
        
        dialog.wait_window()
        return resultado['success']

    # ====== GESTION DE COOPERACIONES ======
    def obtener_cooperacion_activa(self):
        for coop in self.cooperaciones:
            if coop.get('id') == self.coop_activa_id:
                return coop
        return None

    def aplicar_cooperacion_activa(self):
        coop = self.obtener_cooperacion_activa()
        if coop is None and self.cooperaciones:
            self.coop_activa_id = self.cooperaciones[0].get('id')
            coop = self.cooperaciones[0]
        if coop is None:
            coop = {
                'id': f"coop-{int(time.time())}",
                'nombre': 'Cooperacion General',
                'proyecto': self.proyecto_actual,
                'monto_cooperacion': self.monto_cooperacion,
                'personas': []
            }
            self.cooperaciones = [coop]
            self.coop_activa_id = coop['id']
        self.personas = coop.setdefault('personas', [])
        self.monto_cooperacion = coop.get('monto_cooperacion', self.monto_cooperacion)
        self.proyecto_actual = coop.get('proyecto', self.proyecto_actual)

    def refrescar_selector_cooperacion(self, seleccionar_activa=True):
        nombres = [c.get('nombre', 'Sin nombre') for c in self.cooperaciones]
        self.coop_selector['values'] = nombres
        if seleccionar_activa:
            activa = self.obtener_cooperacion_activa()
            if activa and activa.get('nombre') in nombres:
                idx = nombres.index(activa['nombre'])
                self.coop_selector.current(idx)

    def on_cambio_cooperacion(self, event=None):
        nombre = self.coop_selector.get()
        destino = next((c for c in self.cooperaciones if c.get('nombre') == nombre), None)
        if not destino:
            return
        self.coop_activa_id = destino.get('id')
        self.aplicar_cooperacion_activa()
        self.refrescar_interfaz_cooperacion()
        self.sincronizar_coop_con_censo(mostrar_mensaje=False)
        self.actualizar_tabla()
        self.actualizar_totales()
        self.guardar_datos(mostrar_alerta=False)

    def nueva_cooperacion(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Nueva Cooperacion")
        dialog.geometry("500x320")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tamaños = self.obtener_tamaños()
        
        ttk.Label(dialog, text="Nombre de la cooperacion:", font=('Arial', tamaños['normal'], 'bold')).pack(pady=5, padx=20, anchor=tk.W)
        nombre_var = tk.StringVar(value="Cooperacion nueva")
        nombre_entry = ttk.Entry(dialog, textvariable=nombre_var, width=50)
        nombre_entry.pack(pady=5, padx=20)
        
        ttk.Label(dialog, text="Monto base por persona:", font=('Arial', tamaños['normal'], 'bold')).pack(pady=5, padx=20, anchor=tk.W)
        monto_var = tk.DoubleVar(value=self.monto_cooperacion)
        monto_entry = ttk.Entry(dialog, textvariable=monto_var, width=20)
        monto_entry.pack(pady=5, padx=20, anchor=tk.W)
        
        ttk.Label(dialog, text="Descripcion/Proyecto:", font=('Arial', tamaños['normal'], 'bold')).pack(pady=5, padx=20, anchor=tk.W)
        proyecto_var = tk.StringVar(value=self.proyecto_var.get())
        proyecto_entry = ttk.Entry(dialog, textvariable=proyecto_var, width=50)
        proyecto_entry.pack(pady=5, padx=20)
        
        def crear(event=None):
            nombre = nombre_var.get().strip()
            try:
                monto = float(monto_var.get())
            except:
                messagebox.showerror("Error", "Monto invalido")
                return
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
            if monto <= 0:
                messagebox.showerror("Error", "El monto debe ser mayor a 0")
                return
            if any(nombre.lower() == c.get('nombre', '').lower() for c in self.cooperaciones):
                messagebox.showerror("Error", "Ya existe una cooperacion con ese nombre")
                return
            nueva = {
                'id': f"coop-{int(time.time()*1000)}",
                'nombre': nombre,
                'proyecto': proyecto_var.get().strip() or nombre,
                'monto_cooperacion': monto,
                'personas': []
            }
            self.cooperaciones.append(nueva)
            self.coop_activa_id = nueva['id']
            self.proyecto_actual = nueva['proyecto']
            self.monto_cooperacion = monto
            self.aplicar_cooperacion_activa()
            self.refrescar_selector_cooperacion()
            self.refrescar_interfaz_cooperacion()
            self.sincronizar_coop_con_censo(mostrar_mensaje=False)
            self.actualizar_tabla()
            self.actualizar_totales()
            self.guardar_datos(mostrar_alerta=False)
            dialog.destroy()
            messagebox.showinfo("Exito", f"Cooperacion '{nombre}' creada y activada")
        
        botones = ttk.Frame(dialog)
        botones.pack(pady=20)
        ttk.Button(botones, text="Crear y activar", command=crear, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(botones, text="Cancelar", command=dialog.destroy, width=14).pack(side=tk.LEFT, padx=5)
        dialog.bind("<Return>", crear)
        nombre_entry.focus()

    def editar_cooperacion(self):
        coop = self.obtener_cooperacion_activa()
        if not coop:
            messagebox.showerror("Error", "No hay cooperacion activa")
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Cooperacion")
        dialog.geometry("500x320")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tamaños = self.obtener_tamaños()
        
        ttk.Label(dialog, text="Nombre de la cooperacion:", font=('Arial', tamaños['normal'], 'bold')).pack(pady=5, padx=20, anchor=tk.W)
        nombre_var = tk.StringVar(value=coop.get('nombre', ''))
        nombre_entry = ttk.Entry(dialog, textvariable=nombre_var, width=50)
        nombre_entry.pack(pady=5, padx=20)
        
        ttk.Label(dialog, text="Monto base por persona:", font=('Arial', tamaños['normal'], 'bold')).pack(pady=5, padx=20, anchor=tk.W)
        monto_var = tk.DoubleVar(value=coop.get('monto_cooperacion', self.monto_cooperacion))
        monto_entry = ttk.Entry(dialog, textvariable=monto_var, width=20)
        monto_entry.pack(pady=5, padx=20, anchor=tk.W)
        
        ttk.Label(dialog, text="Descripcion/Proyecto:", font=('Arial', tamaños['normal'], 'bold')).pack(pady=5, padx=20, anchor=tk.W)
        proyecto_var = tk.StringVar(value=coop.get('proyecto', self.proyecto_var.get()))
        proyecto_entry = ttk.Entry(dialog, textvariable=proyecto_var, width=50)
        proyecto_entry.pack(pady=5, padx=20)
        
        def guardar(event=None):
            nombre = nombre_var.get().strip()
            try:
                monto = float(monto_var.get())
            except:
                messagebox.showerror("Error", "Monto invalido")
                return
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
            if monto <= 0:
                messagebox.showerror("Error", "El monto debe ser mayor a 0")
                return
            if any(nombre.lower() == c.get('nombre', '').lower() and c.get('id') != coop.get('id') for c in self.cooperaciones):
                messagebox.showerror("Error", "Ya existe otra cooperacion con ese nombre")
                return
            coop['nombre'] = nombre
            coop['monto_cooperacion'] = monto
            coop['proyecto'] = proyecto_var.get().strip() or nombre
            self.monto_cooperacion = monto
            self.proyecto_actual = coop['proyecto']
            self.refrescar_selector_cooperacion()
            self.refrescar_interfaz_cooperacion()
            self.guardar_datos(mostrar_alerta=False)
            dialog.destroy()
            messagebox.showinfo("Exito", "Cooperacion actualizada")
        
        botones = ttk.Frame(dialog)
        botones.pack(pady=20)
        ttk.Button(botones, text="Guardar", command=guardar, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(botones, text="Cancelar", command=dialog.destroy, width=14).pack(side=tk.LEFT, padx=5)
        dialog.bind("<Return>", guardar)
        nombre_entry.focus()

    def sincronizar_coop_con_censo(self, mostrar_mensaje=True):
        coop = self.obtener_cooperacion_activa()
        if not coop:
            messagebox.showerror("Error", "No hay cooperacion activa")
            return
        agregados = 0
        try:
            response = requests.get(f"{self.api_url}/habitantes", timeout=6)
            if response.status_code != 200:
                if mostrar_mensaje:
                    messagebox.showerror("Error", "No se pudo obtener habitantes desde el censo")
                return
            data = response.json()
            habitantes = data.get('habitantes', [])
            
            print(f"DEBUG: API devolvió {len(habitantes)} habitantes")
            print(f"DEBUG: Total en respuesta: {data.get('total', 'N/A')}")
            
            existentes = {p.get('nombre', '').lower(): p for p in coop.get('personas', [])}
            for hab in habitantes:
                nombre = hab.get('nombre', '').strip()
                folio = hab.get('folio', 'SIN-FOLIO')
                if not nombre:
                    continue
                if nombre.lower() not in existentes:
                    nuevo = {
                        'nombre': nombre,
                        'folio': folio,
                        'monto_esperado': coop.get('monto_cooperacion', self.monto_cooperacion),
                        'pagos': [],
                        'notas': ''
                    }
                    coop['personas'].append(nuevo)
                    agregados += 1
            self.personas = coop['personas']
            self.actualizar_tabla()
            self.actualizar_totales()
            self.guardar_datos(mostrar_alerta=False)
            if mostrar_mensaje:
                if agregados:
                    messagebox.showinfo("Sincronizacion", f"Se agregaron {agregados} habitantes desde el censo\nTotal en cooperación: {len(self.personas)}")
                else:
                    messagebox.showinfo("Sincronizacion", "No habia nuevos habitantes para agregar")
        except Exception as e:
            if mostrar_mensaje:
                messagebox.showerror("Error", f"No se pudo sincronizar con el censo: {e}")

    def refrescar_interfaz_cooperacion(self):
        coop = self.obtener_cooperacion_activa()
        if not coop:
            print("DEBUG: No hay cooperación activa")
            return
        self.personas = coop.setdefault('personas', [])
        print(f"DEBUG refrescar_interfaz: Cargadas {len(self.personas)} personas de cooperación")
        self.monto_cooperacion = coop.get('monto_cooperacion', self.monto_cooperacion)
        self.proyecto_actual = coop.get('proyecto', self.proyecto_actual)
        if hasattr(self, 'monto_var'):
            self.monto_var.set(self.monto_cooperacion)
        if hasattr(self, 'proyecto_var'):
            self.proyecto_var.set(self.proyecto_actual)
        if hasattr(self, 'total_personas_label'):
            self.total_personas_label.config(text=str(len(self.personas)))
        
    def configurar_interfaz(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)  # Fila 4 es donde está la tabla
        
        tamaños = self.obtener_tamaños()
        colores = self.obtener_colores()
        
        # ===== ENCABEZADO CON CONTROLES DE TEMA =====
        header_frame = ttk.LabelFrame(main_frame, text="Informacion del Proyecto", padding="10")
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        header_frame.columnconfigure(2, weight=1)
        header_frame.columnconfigure(3, weight=1)
        header_frame.columnconfigure(4, weight=1)
        
        # Fila 0: Controles de accesibilidad
        ttk.Label(header_frame, text="Tema:", font=('Arial', tamaños['normal'])).grid(row=0, column=5, sticky=tk.E, padx=5)
        tema_combo = ttk.Combobox(header_frame, textvariable=self.tema_actual, state="readonly", width=10, values=['claro', 'oscuro'])
        tema_combo.grid(row=0, column=6, padx=5, sticky=tk.W)
        
        ttk.Label(header_frame, text="Tamaño Letra:", font=('Arial', tamaños['normal'])).grid(row=0, column=7, sticky=tk.E, padx=5)
        tamaño_combo = ttk.Combobox(header_frame, textvariable=self.tamaño_actual, state="readonly", width=10, values=['pequeño', 'normal', 'grande'])
        tamaño_combo.grid(row=0, column=8, padx=5, sticky=tk.W)
        
        # Fila 1 del encabezado
        ttk.Label(header_frame, text="Proyecto:", font=('Arial', tamaños['normal'], 'bold')).grid(row=1, column=0, sticky=tk.W, padx=5)
        self.proyecto_var = tk.StringVar(value="Proyecto Comunitario 2026")
        ttk.Entry(header_frame, textvariable=self.proyecto_var, width=40).grid(row=1, column=1, padx=5)
        
        ttk.Label(header_frame, text="Fecha:", font=('Arial', tamaños['normal'], 'bold')).grid(row=1, column=2, sticky=tk.W, padx=5)
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        ttk.Label(header_frame, text=fecha_actual, font=('Arial', tamaños['normal'])).grid(row=1, column=3, padx=5)
        
        # Fila 2 del encabezado
        ttk.Label(header_frame, text="Monto de Cooperacion:", font=('Arial', tamaños['normal'], 'bold')).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.monto_var = tk.DoubleVar(value=self.monto_cooperacion)
        monto_entry = ttk.Entry(header_frame, textvariable=self.monto_var, width=15)
        monto_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Button(header_frame, text="Actualizar Monto", command=self.actualizar_monto, width=16).grid(row=2, column=2, padx=5)
        
        ttk.Label(header_frame, text="Total Personas:", font=('Arial', tamaños['normal'], 'bold')).grid(row=2, column=3, sticky=tk.W, padx=5)
        self.total_personas_label = ttk.Label(header_frame, text=str(len(self.personas)), font=('Arial', tamaños['normal']))
        self.total_personas_label.grid(row=2, column=4, padx=5)

        ttk.Label(header_frame, text="Cooperacion:", font=('Arial', tamaños['normal'], 'bold')).grid(row=3, column=0, sticky=tk.W, padx=5, pady=(5,0))
        self.coop_selector = ttk.Combobox(header_frame, state="readonly", width=28)
        self.coop_selector.grid(row=3, column=1, padx=5, pady=(5,0), sticky=(tk.W, tk.E))
        self.coop_selector.bind("<<ComboboxSelected>>", self.on_cambio_cooperacion)
        ttk.Button(header_frame, text="Nueva Cooperacion", command=self.nueva_cooperacion, width=16).grid(row=3, column=2, padx=5, pady=(5,0))
        ttk.Button(header_frame, text="Editar Cooperacion", command=self.editar_cooperacion, width=16).grid(row=3, column=3, padx=5, pady=(5,0))
        
        # ===== BUSQUEDA =====
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(search_frame, text="Buscar:", font=('Arial', tamaños['normal'], 'bold')).pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.buscar_tiempo_real())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Limpiar", command=self.limpiar_busqueda, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(search_frame, text="Mostrar nombre", variable=self.nombre_visible,
                command=self.actualizar_visibilidad_columnas).pack(side=tk.RIGHT, padx=5)
        ttk.Checkbutton(search_frame, text="Mostrar folio", variable=self.folio_visible,
                command=self.actualizar_visibilidad_columnas).pack(side=tk.RIGHT, padx=5)
        
        # ===== BOTONES DE CONTROL =====
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(control_frame, text="Agregar Persona", command=self.agregar_persona, width=16).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Editar Seleccionado", command=self.editar_persona, width=16).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Eliminar Seleccionado", command=self.eliminar_persona, width=16).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Registrar Pago", command=self.registrar_pago, width=16).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Ver Historial", command=self.ver_historial, width=14).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Guardar Datos", command=self.guardar_datos, width=14).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Sincronizar con Censo", command=self.sincronizar_coop_con_censo, width=18).pack(side=tk.LEFT, padx=5)
        
        # Botón para mostrar/ocultar total
        self.btn_toggle_total = ttk.Button(control_frame, text="Mostrar Total Recaudado", command=self.toggle_total, width=20)
        self.btn_toggle_total.pack(side=tk.RIGHT, padx=5)
        
        # ===== PANEL DE TOTAL (OCULTO INICIALMENTE) =====
        self.total_frame = ttk.LabelFrame(main_frame, text="Resumen Financiero", padding="10")
        self.total_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.total_frame.grid_remove()  # Ocultar inicialmente
        
        self.total_pagado_label = ttk.Label(self.total_frame, text="Total Recaudado: $0.00", 
                                           font=('Arial', tamaños['titulo'], 'bold'), foreground=colores['exito_fg'])
        self.total_pagado_label.pack(side=tk.LEFT, padx=20)
        
        self.total_pendiente_label = ttk.Label(self.total_frame, text="Total Pendiente: $0.00", 
                                              font=('Arial', 14, 'bold'), foreground='red')
        self.total_pendiente_label.pack(side=tk.LEFT, padx=20)
        
        self.personas_pagadas_label = ttk.Label(self.total_frame, text="Personas que pagaron: 0", 
                                               font=('Arial', 12))
        self.personas_pagadas_label.pack(side=tk.LEFT, padx=20)
        
        # ===== TABLA =====
        table_frame = ttk.Frame(main_frame)
        table_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Scrollbars
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        
        # Treeview (tabla)
        self.tree = ttk.Treeview(table_frame, 
                                 columns=('folio', 'nombre', 'monto_esperado', 'pagado', 'pendiente', 'estado', 'ultimo_pago', 'notas'),
                                 show='headings',
                                 yscrollcommand=scrollbar_y.set,
                                 xscrollcommand=scrollbar_x.set)
        
        # Configurar columnas
        self.tree.heading('folio', text='Folio')
        self.tree.heading('nombre', text='Nombre Completo')
        self.tree.heading('monto_esperado', text='Monto Esperado')
        self.tree.heading('pagado', text='Pagado')
        self.tree.heading('pendiente', text='Pendiente')
        self.tree.heading('estado', text='Estado')
        self.tree.heading('ultimo_pago', text='Ultimo Pago')
        self.tree.heading('notas', text='Notas')
        
        self.tree.column('folio', width=90, anchor=tk.CENTER, stretch=False)
        self.tree.column('nombre', width=220, anchor=tk.W)
        self.tree.column('monto_esperado', width=120, anchor=tk.CENTER)
        self.tree.column('pagado', width=100, anchor=tk.CENTER)
        self.tree.column('pendiente', width=100, anchor=tk.CENTER)
        self.tree.column('estado', width=100, anchor=tk.CENTER)
        self.tree.column('ultimo_pago', width=150, anchor=tk.CENTER)
        self.tree.column('notas', width=200, anchor=tk.W)
        
        # Posicionar elementos
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        # Tags para colores
        self.tree.tag_configure('pagado', background='#c8e6c9', foreground='#1b5e20')
        self.tree.tag_configure('pendiente', background='#ffccbc', foreground='#bf360c')
        self.tree.tag_configure('parcial', background='#fff9c4', foreground='#f57f17')
        self.tree.tag_configure('pago_ok', background='#66bb6a', foreground='#fff')
        self.tree.tag_configure('pago_parcial', background='#ffa726', foreground='#fff')
        
        self.actualizar_visibilidad_columnas()
        self.refrescar_selector_cooperacion()
        self.refrescar_interfaz_cooperacion()
        self.sincronizar_coop_con_censo(mostrar_mensaje=False)
        
        # Cargar datos en la tabla
        self.actualizar_tabla()
        self.actualizar_totales()

    def actualizar_visibilidad_columnas(self):
        """Mostrar/ocultar columnas de nombre y folio"""
        if not self.nombre_visible.get() and not self.folio_visible.get():
            self.folio_visible.set(True)
        
        if self.folio_visible.get():
            self.tree.column('folio', width=90, minwidth=40, stretch=False)
            self.tree.heading('folio', text='Folio')
        else:
            self.tree.column('folio', width=0, minwidth=0, stretch=False)
            self.tree.heading('folio', text='')
        
        if self.nombre_visible.get():
            self.tree.column('nombre', width=220, minwidth=120, stretch=True)
            self.tree.heading('nombre', text='Nombre Completo')
        else:
            self.tree.column('nombre', width=0, minwidth=0, stretch=False)
            self.tree.heading('nombre', text='')
        
    def sincronizar_con_censo(self, nombre):
        """Sincronizar persona con la base de datos de censo - buscar folio permanente"""
        try:
            # Buscar por nombre exacto
            response = requests.get(f"{self.api_url}/habitantes/nombre/{nombre}",
                                    timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['success'] and data['habitante']:
                    return data['habitante']['folio']
        except:
            pass
        
        # Si no existe, intentar agregarlo al censo
        try:
            response = requests.post(f"{self.api_url}/habitantes",
                                    json={'nombre': nombre},
                                    timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['success'] and data['habitante']:
                    return data['habitante']['folio']
        except:
            pass
        
        # Si todo falla, no retornar nada - el usuario será avisado
        return None

    def asegurar_api_activa(self):
        """Comprueba la API y la levanta si no está activa"""
        if self.verificar_api():
            return True
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            api_path = os.path.join(script_dir, "api_local.py")
            subprocess.Popen([sys.executable, api_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for _ in range(10):
                time.sleep(0.5)
                if self.verificar_api():
                    return True
        except Exception as e:
            print(f"Error iniciando API: {e}")
        return False

    def verificar_api(self):
        try:
            response = requests.get(f"{self.api_url}/ping", timeout=1.5)
            return response.status_code == 200
        except:
            return False
    
    def actualizar_monto(self):
        # Solicitar contraseña
        if not self.solicitar_password():
            messagebox.showwarning("Cancelado", "Operacion cancelada")
            self.monto_var.set(self.monto_cooperacion)  # Restaurar valor anterior
            return
        
        try:
            nuevo_monto = self.monto_var.get()
            if nuevo_monto <= 0:
                messagebox.showerror("Error", "El monto debe ser mayor a 0")
                self.monto_var.set(self.monto_cooperacion)
                return
            self.monto_cooperacion = nuevo_monto
            coop = self.obtener_cooperacion_activa()
            if coop:
                coop['monto_cooperacion'] = nuevo_monto
            messagebox.showinfo("Exito", f"Monto actualizado a ${nuevo_monto:.2f}")
            self.actualizar_tabla()
            self.actualizar_totales()
        except:
            messagebox.showerror("Error", "Por favor ingrese un monto valido")
            self.monto_var.set(self.monto_cooperacion)
    
    def agregar_persona(self):
        # Ventana para agregar persona
        dialog = tk.Toplevel(self.root)
        dialog.title("Agregar Nueva Persona")
        dialog.geometry("520x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tamaños = self.obtener_tamaños()
        
        # Campos
        ttk.Label(dialog, text="Nombre Completo:", font=('Arial', tamaños['normal'], 'bold')).pack(pady=5, padx=20, anchor=tk.W)
        nombre_entry = ttk.Entry(dialog, width=50)
        nombre_entry.pack(pady=5, padx=20)
        
        ttk.Label(dialog, text=f"Monto de cooperacion: ${self.monto_cooperacion:.2f}", 
                 font=('Arial', tamaños['normal'], 'italic')).pack(pady=5, padx=20, anchor=tk.W)
        ttk.Label(dialog, text=f"Cooperacion activa: {self.coop_selector.get() or 'Actual'}", 
                 font=('Arial', tamaños['normal'], 'italic')).pack(pady=2, padx=20, anchor=tk.W)
        
        ttk.Label(dialog, text="Notas (opcional):", font=('Arial', tamaños['normal'], 'bold')).pack(pady=5, padx=20, anchor=tk.W)
        notas_entry = ttk.Entry(dialog, width=50)
        notas_entry.pack(pady=5, padx=20)
        
        def guardar(event=None):
            nombre = nombre_entry.get().strip()
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
            
            # Verificar que no exista el nombre
            if any(p['nombre'].lower() == nombre.lower() for p in self.personas):
                messagebox.showerror("Error", "Ya existe una persona con ese nombre")
                return
            
            # Sincronizar con API (verificar/agregar en censo)
            folio = self.sincronizar_con_censo(nombre)
            if not folio:
                messagebox.showerror("Error", "Error al sincronizar con el censo")
                return
            
            persona = {
                'nombre': nombre,
                'folio': folio,
                'monto_esperado': self.monto_cooperacion,
                'pagos': [],  # Lista de pagos parciales
                'notas': notas_entry.get().strip()
            }
            
            self.personas.append(persona)
            self.actualizar_tabla()
            self.actualizar_totales()
            self.guardar_datos(mostrar_alerta=False)
            dialog.destroy()
            messagebox.showinfo("Exito", f"Persona agregada correctamente\nFolio: {folio}")
        
        botones = ttk.Frame(dialog)
        botones.pack(pady=20)
        ttk.Button(botones, text="Confirmar", command=guardar, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(botones, text="Cancelar", command=dialog.destroy, width=14).pack(side=tk.LEFT, padx=5)
        dialog.bind("<Return>", guardar)
        nombre_entry.focus()
    
    def editar_persona(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Por favor seleccione una persona")
            return
        
        item = seleccion[0]
        index = self.tree.index(item)
        persona = self.personas[index]
        
        # Ventana para editar
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Persona")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Campos prellenados
        ttk.Label(dialog, text=f"Folio: {persona.get('folio', 'SIN-FOLIO')}", 
                 font=('Arial', 9, 'italic')).pack(pady=5)
        
        ttk.Label(dialog, text="Nombre Completo:", font=('Arial', 10, 'bold')).pack(pady=5)
        nombre_entry = ttk.Entry(dialog, width=40)
        nombre_entry.insert(0, persona['nombre'])
        nombre_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Notas:", font=('Arial', 10, 'bold')).pack(pady=5)
        notas_entry = ttk.Entry(dialog, width=40)
        notas_entry.insert(0, persona.get('notas', ''))
        notas_entry.pack(pady=5)
        
        def guardar():
            nombre = nombre_entry.get().strip()
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
            
            # Verificar que no exista otro con el mismo nombre
            if nombre.lower() != persona['nombre'].lower():
                if any(p['nombre'].lower() == nombre.lower() for p in self.personas):
                    messagebox.showerror("Error", "Ya existe una persona con ese nombre")
                    return
            
            self.personas[index]['nombre'] = nombre
            self.personas[index]['notas'] = notas_entry.get().strip()
            
            self.actualizar_tabla()
            self.actualizar_totales()
            dialog.destroy()
            messagebox.showinfo("Exito", "Persona actualizada correctamente")
        
        ttk.Button(dialog, text="Guardar Cambios", command=guardar).pack(pady=15)
    
    def eliminar_persona(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Por favor seleccione una persona")
            return
        
        item = seleccion[0]
        index = self.tree.index(item)
        persona = self.personas[index]
        
        if messagebox.askyesno("Confirmar", f"¿Esta seguro de eliminar a {persona['nombre']}?"):
            self.personas.pop(index)
            self.actualizar_tabla()
            self.actualizar_totales()
            messagebox.showinfo("Exito", "Persona eliminada correctamente")
    
    def registrar_pago(self):
        """Registrar un pago (puede ser parcial)"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Por favor seleccione una persona")
            return
        
        item = seleccion[0]
        index = self.tree.index(item)
        persona = self.personas[index]
        
        # Calcular cuánto falta
        total_pagado = sum(pago['monto'] for pago in persona.get('pagos', []))
        monto_esperado = persona.get('monto_esperado', persona.get('monto', 100))
        pendiente = monto_esperado - total_pagado
        
        if pendiente <= 0:
            messagebox.showinfo("Informacion", "Esta persona ya completo su pago")
            return
        
        # Diálogo para registrar pago
        dialog = tk.Toplevel(self.root)
        dialog.title("Registrar Pago")
        dialog.geometry("400x280")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tamaños = self.obtener_tamaños()
        colores = self.obtener_colores()
        
        ttk.Label(dialog, text=f"Persona: {persona['nombre']}", font=('Arial', tamaños['titulo'], 'bold')).pack(pady=5)
        ttk.Label(dialog, text=f"Folio: {persona.get('folio', 'SIN-FOLIO')}", font=('Arial', tamaños['normal'], 'italic')).pack(pady=2)
        ttk.Label(dialog, text=f"Total Esperado: ${monto_esperado:.2f}").pack(pady=2)
        ttk.Label(dialog, text=f"Ya Pagado: ${total_pagado:.2f}").pack(pady=2)
        ttk.Label(dialog, text=f"Pendiente: ${pendiente:.2f}", foreground=colores['error_fg']).pack(pady=2)
        
        ttk.Label(dialog, text="\nMonto de este pago:", font=('Arial', tamaños['normal'], 'bold')).pack(pady=5)
        monto_var = tk.DoubleVar(value=pendiente)
        monto_entry = ttk.Entry(dialog, textvariable=monto_var, width=20)
        monto_entry.pack(pady=5)
        
        def guardar_pago(event=None):
            try:
                monto_pago = monto_var.get()
                if monto_pago <= 0:
                    messagebox.showerror("Error", "El monto debe ser mayor a 0")
                    return
                
                if monto_pago > pendiente:
                    if not messagebox.askyesno("Confirmar", 
                        f"El monto (${monto_pago:.2f}) es mayor al pendiente (${pendiente:.2f}).\n¿Desea continuar?"):
                        return
                
                # Registrar el pago
                pago = {
                    'monto': monto_pago,
                    'fecha': datetime.now().strftime("%d/%m/%Y"),
                    'hora': datetime.now().strftime("%H:%M:%S")
                }
                
                if 'pagos' not in persona:
                    persona['pagos'] = []
                
                persona['pagos'].append(pago)
                
                self.actualizar_tabla()
                self.actualizar_totales()
                self.guardar_datos(mostrar_alerta=False)
                dialog.destroy()
                
                # Visual feedback: animar la fila
                nuevo_total = sum(p['monto'] for p in persona['pagos'])
                if nuevo_total >= monto_esperado:
                    self.animar_fila_pagada(item, "completado")
                else:
                    self.animar_fila_pagada(item, "parcial")
                
            except:
                messagebox.showerror("Error", "Monto invalido")
        
        botones = ttk.Frame(dialog)
        botones.pack(pady=15)
        ttk.Button(botones, text="Registrar", command=guardar_pago, width=18).pack(side=tk.LEFT, padx=5)
        ttk.Button(botones, text="Cancelar", command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=5)
        dialog.bind("<Return>", guardar_pago)
        monto_entry.focus()
        monto_entry.select_range(0, tk.END)
    
    def animar_fila_pagada(self, item, tipo='completado'):
        """Animar la fila con pulso de color"""
        colores = self.obtener_colores()
        colores_pulso = [
            colores['exito_fg'] if tipo == 'completado' else colores['alerta_fg'],
            colores['fg']
        ]
        
        def pulso(idx=0):
            if idx < 4:
                # Cambiar color de texto
                self.tree.item(item, tags=('pago_ok' if tipo == 'completado' else 'pago_parcial',))
                self.root.after(150, lambda: pulso(idx + 1))
            else:
                # Restaurar color normal
                persona = self.personas[self.tree.index(item)]
                total_pagado = sum(p['monto'] for p in persona.get('pagos', []))
                monto_esperado = persona.get('monto_esperado', 100)
                if total_pagado >= monto_esperado:
                    self.tree.item(item, tags=('pagado',))
                elif total_pagado > 0:
                    self.tree.item(item, tags=('parcial',))
                else:
                    self.tree.item(item, tags=('pendiente',))
        
        pulso()
    
    def ver_historial(self):
        """Ver historial de pagos de una persona"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Por favor seleccione una persona")
            return
        
        item = seleccion[0]
        index = self.tree.index(item)
        persona = self.personas[index]
        
        # Ventana de historial
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Historial de Pagos - {persona['nombre']}")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        
        ttk.Label(dialog, text=f"Historial de {persona['nombre']}", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        
        ttk.Label(dialog, text=f"Folio: {persona.get('folio', 'SIN-FOLIO')}", 
                 font=('Arial', 10, 'italic')).pack()
        
        monto_esperado = persona.get('monto_esperado', persona.get('monto', 100))
        total_pagado = sum(pago['monto'] for pago in persona.get('pagos', []))
        
        info_frame = ttk.Frame(dialog)
        info_frame.pack(pady=10, padx=20, fill=tk.X)
        
        ttk.Label(info_frame, text=f"Monto Esperado: ${monto_esperado:.2f}", 
                 font=('Arial', 11, 'bold')).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Total Pagado: ${total_pagado:.2f}", 
                 font=('Arial', 11, 'bold'), foreground='green').pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Pendiente: ${max(0, monto_esperado - total_pagado):.2f}", 
                 font=('Arial', 11, 'bold'), foreground='red').pack(anchor=tk.W)
        
        # Tabla de pagos
        frame = ttk.Frame(dialog)
        frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_hist = ttk.Treeview(frame, columns=('num', 'monto', 'fecha', 'hora'), 
                                 show='headings', yscrollcommand=scrollbar.set)
        
        tree_hist.heading('num', text='#')
        tree_hist.heading('monto', text='Monto')
        tree_hist.heading('fecha', text='Fecha')
        tree_hist.heading('hora', text='Hora')
        
        tree_hist.column('num', width=50, anchor=tk.CENTER)
        tree_hist.column('monto', width=100, anchor=tk.CENTER)
        tree_hist.column('fecha', width=100, anchor=tk.CENTER)
        tree_hist.column('hora', width=100, anchor=tk.CENTER)
        
        tree_hist.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=tree_hist.yview)
        
        # Llenar datos
        for i, pago in enumerate(persona.get('pagos', []), 1):
            tree_hist.insert('', tk.END, values=(
                i,
                f"${pago['monto']:.2f}",
                pago['fecha'],
                pago['hora']
            ))
        
        if not persona.get('pagos'):
            ttk.Label(dialog, text="No hay pagos registrados", 
                     font=('Arial', 10, 'italic')).pack(pady=10)
        
        ttk.Button(dialog, text="Cerrar", command=dialog.destroy).pack(pady=10)
    
    def toggle_total(self):
        self.mostrar_total = not self.mostrar_total
        
        if self.mostrar_total:
            self.total_frame.grid()
            self.btn_toggle_total.config(text="Ocultar Total Recaudado")
        else:
            self.total_frame.grid_remove()
            self.btn_toggle_total.config(text="Mostrar Total Recaudado")
        
        self.actualizar_totales()
    
    def buscar_tiempo_real(self):
        """Busqueda en tiempo real"""
        self.actualizar_tabla()
    
    def limpiar_busqueda(self):
        """Limpiar busqueda"""
        self.search_var.set('')
        self.actualizar_tabla()
    
    def actualizar_tabla(self):
        print(f"DEBUG actualizar_tabla: Actualizando con {len(self.personas)} personas")
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Filtrar personas si hay búsqueda activa
        personas_mostrar = self.personas
        criterio = self.search_var.get().strip().lower()
        
        print(f"DEBUG: Criterio de búsqueda: '{criterio}'")
        
        if criterio:
            personas_mostrar = [p for p in self.personas 
                               if criterio in p['nombre'].lower() or 
                               criterio in p.get('folio', '').lower()]
            print(f"DEBUG: Después de filtrar quedan {len(personas_mostrar)} personas")
        
        print(f"DEBUG: Insertando {len(personas_mostrar)} personas en la tabla")
        insertadas = 0
        # Agregar personas
        for persona in personas_mostrar:
            insertadas += 1
            # Migrar datos antiguos si es necesario
            if 'monto_esperado' not in persona:
                persona['monto_esperado'] = persona.get('monto', 100)
            if 'pagos' not in persona:
                persona['pagos'] = []
            if 'folio' not in persona:
                persona['folio'] = 'SIN-FOLIO'
            
            monto_esperado = persona['monto_esperado']
            total_pagado = sum(pago['monto'] for pago in persona['pagos'])
            pendiente = max(0, monto_esperado - total_pagado)
            
            # Determinar estado
            if total_pagado >= monto_esperado:
                estado = 'Pagado'
                tag = 'pagado'
            elif total_pagado > 0:
                estado = 'Parcial'
                tag = 'parcial'
            else:
                estado = 'Pendiente'
                tag = 'pendiente'
            
            # Obtener fecha del último pago
            ultimo_pago = ''
            if persona['pagos']:
                ultimo = persona['pagos'][-1]
                ultimo_pago = f"{ultimo['fecha']} {ultimo['hora']}"
            
            self.tree.insert('', tk.END, 
                           values=(persona.get('folio', 'SIN-FOLIO'),
                                  persona['nombre'],
                                  f"${monto_esperado:.2f}",
                                  f"${total_pagado:.2f}",
                                  f"${pendiente:.2f}",
                                  estado,
                                  ultimo_pago,
                                  persona.get('notas', '')),
                           tags=(tag,))
        
        print(f"DEBUG: Se insertaron {insertadas} filas en el tree")
        items_en_tree = len(self.tree.get_children())
        print(f"DEBUG: Items visibles en tree: {items_en_tree}")
        
        # Actualizar contador de personas
        total_mostradas = len(personas_mostrar)
        total_general = len(self.personas)
        if total_mostradas == total_general:
            self.total_personas_label.config(text=str(total_general))
        else:
            self.total_personas_label.config(text=f"{total_mostradas} de {total_general}")
    
    def actualizar_totales(self):
        total_pagado = 0
        total_pendiente = 0
        personas_pagadas = 0
        
        for persona in self.personas:
            monto_esperado = persona.get('monto_esperado', persona.get('monto', 100))
            pagado = sum(pago['monto'] for pago in persona.get('pagos', []))
            
            total_pagado += pagado
            pendiente = max(0, monto_esperado - pagado)
            total_pendiente += pendiente
            
            if pagado >= monto_esperado:
                personas_pagadas += 1
        
        self.total_pagado_label.config(text=f"Total Recaudado: ${total_pagado:.2f}")
        self.total_pendiente_label.config(text=f"Total Pendiente: ${total_pendiente:.2f}")
        self.personas_pagadas_label.config(text=f"Personas que pagaron completo: {personas_pagadas} de {len(self.personas)}")
    
    def guardar_datos(self, mostrar_alerta=True):
        try:
            coop = self.obtener_cooperacion_activa()
            if coop:
                coop['proyecto'] = self.proyecto_var.get()
                coop['monto_cooperacion'] = self.monto_cooperacion
                coop['personas'] = self.personas
            datos = {
                'cooperaciones': self.cooperaciones,
                'cooperacion_activa': self.coop_activa_id,
                'password_hash': self.password_hash,
                'tema': self.tema_actual.get(),
                'tamaño': self.tamaño_actual.get(),
                'fecha_guardado': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            with open(self.archivo_datos, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            if mostrar_alerta:
                messagebox.showinfo("Exito", "Datos guardados correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")

    def cargar_datos(self):
        try:
            if os.path.exists(self.archivo_datos):
                with open(self.archivo_datos, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                self.password_hash = datos.get('password_hash', self.password_hash)
                if 'cooperaciones' in datos:
                    self.cooperaciones = datos.get('cooperaciones', [])
                    self.coop_activa_id = datos.get('cooperacion_activa')
                    self.tema_guardado = datos.get('tema', 'claro')
                    self.tamaño_guardado = datos.get('tamaño', 'normal')
                    print(f"DEBUG cargar_datos: Cargadas {len(self.cooperaciones)} cooperaciones")
                    if self.cooperaciones:
                        for i, coop in enumerate(self.cooperaciones):
                            print(f"  Cooperación {i+1}: {coop['nombre']} - {len(coop.get('personas', []))} personas")
            if not self.cooperaciones:
                nueva = {
                    'id': f"coop-{int(time.time())}",
                    'nombre': 'Cooperacion General',
                    'proyecto': self.proyecto_actual,
                    'monto_cooperacion': self.monto_cooperacion,
                    'personas': []
                }
                self.cooperaciones = [nueva]
                self.coop_activa_id = nueva['id']
                print("DEBUG cargar_datos: Creada cooperación nueva vacía")
        except Exception as e:
            print(f"Error al cargar datos: {str(e)}")

def main():
    root = tk.Tk()
    app = SistemaControlPagos(root)
    
    # Cargar nombre de proyecto guardado si existe
    if hasattr(app, '_proyecto_guardado'):
        app.proyecto_var.set(app._proyecto_guardado)
    
    root.mainloop()

if __name__ == "__main__":
    main()
