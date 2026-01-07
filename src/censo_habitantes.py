import tkinter as tk
from tkinter import ttk, messagebox
import requests
import subprocess
import sys
import time
import os
from datetime import datetime

class SistemaCensoHabitantes:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Censo de Habitantes del Pueblo")
        self.root.state('zoomed')
        
        self.api_url = "http://127.0.0.1:5000/api"
        self.habitantes = []
        self.nombre_visible = tk.BooleanVar(value=True)
        self.folio_visible = tk.BooleanVar(value=True)
        
        # Verificar/iniciar API local
        if not self.asegurar_api_activa():
            messagebox.showerror("Error", "No se pudo iniciar ni conectar con la API local")
            return
        
        self.configurar_interfaz()
        self.cargar_habitantes()

    def asegurar_api_activa(self):
        """Comprueba la API y la levanta si no está activa"""
        if self.verificar_api():
            return True
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            api_path = os.path.join(script_dir, "api_local.py")
            # Lanzar la API en segundo plano
            subprocess.Popen([sys.executable, api_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Esperar hasta 5 segundos a que responda
            for _ in range(10):
                time.sleep(0.5)
                if self.verificar_api():
                    return True
        except Exception as e:
            print(f"Error iniciando API: {e}")
        return False
    
    def verificar_api(self):
        """Verificar que la API está funcionando"""
        try:
            response = requests.get(f"{self.api_url}/ping", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def configurar_interfaz(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # ===== ENCABEZADO =====
        header_frame = ttk.LabelFrame(main_frame, text="Censo de Habitantes", padding="10")
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(header_frame, text="Sistema de Registro de Habitantes del Pueblo", 
                 font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=3, pady=5)
        
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        ttk.Label(header_frame, text=f"Fecha: {fecha_actual}").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Button(header_frame, text="Abrir Control de Pagos", command=self.abrir_control_pagos, width=22).grid(row=1, column=1, padx=5)
        
        self.total_label = ttk.Label(header_frame, text="Total Habitantes: 0", font=('Arial', 11, 'bold'))
        self.total_label.grid(row=1, column=2, sticky=tk.E, padx=5)
        
        # ===== BUSQUEDA =====
        search_frame = ttk.LabelFrame(main_frame, text="Busqueda", padding="10")
        search_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(search_frame, text="Buscar por nombre o folio:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.buscar_tiempo_real())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=50)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(search_frame, text="Limpiar", command=self.limpiar_busqueda).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Agregar Habitante", command=self.agregar_habitante).pack(side=tk.LEFT, padx=20)
        ttk.Button(search_frame, text="Actualizar Lista", command=self.cargar_habitantes).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(search_frame, text="Mostrar nombre", variable=self.nombre_visible,
                command=self.actualizar_visibilidad_columnas).pack(side=tk.RIGHT, padx=5)
        ttk.Checkbutton(search_frame, text="Mostrar folio", variable=self.folio_visible,
                command=self.actualizar_visibilidad_columnas).pack(side=tk.RIGHT, padx=5)
        
        # ===== TABLA =====
        table_frame = ttk.Frame(main_frame)
        table_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Scrollbars
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        
        # Treeview
        self.tree = ttk.Treeview(table_frame, 
                                 columns=('folio', 'nombre', 'fecha_registro', 'activo'),
                                 show='headings',
                                 yscrollcommand=scrollbar_y.set,
                                 xscrollcommand=scrollbar_x.set)
        
        self.tree.heading('folio', text='Folio')
        self.tree.heading('nombre', text='Nombre Completo')
        self.tree.heading('fecha_registro', text='Fecha de Registro')
        self.tree.heading('activo', text='Estado')
        
        self.tree.column('folio', width=80, anchor=tk.CENTER, stretch=False)
        self.tree.column('nombre', width=320, anchor=tk.W)
        self.tree.column('fecha_registro', width=120, anchor=tk.CENTER)
        self.tree.column('activo', width=100, anchor=tk.CENTER)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        self.tree.tag_configure('activo', background='#c8e6c9')
        self.tree.tag_configure('inactivo', background='#ffccbc')
        
        # Ajustar visibilidad inicial
        self.actualizar_visibilidad_columnas()
    
    def cargar_habitantes(self):
        """Cargar todos los habitantes desde la API"""
        try:
            response = requests.get(f"{self.api_url}/habitantes", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.habitantes = data['habitantes']
                self.actualizar_tabla(self.habitantes)
            else:
                messagebox.showerror("Error", "No se pudieron cargar los habitantes")
        except Exception as e:
            messagebox.showerror("Error", f"Error de conexion: {str(e)}")
    
    def actualizar_tabla(self, habitantes):
        """Actualizar tabla con lista de habitantes"""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Agregar habitantes
        for hab in habitantes:
            estado = "Activo" if hab.get('activo', True) else "Inactivo"
            tag = 'activo' if hab.get('activo', True) else 'inactivo'
            
            self.tree.insert('', tk.END,
                           values=(hab['folio'],
                                  hab['nombre'],
                                  hab.get('fecha_registro', ''),
                                  estado),
                           tags=(tag,))
        
        self.total_label.config(text=f"Total Habitantes: {len(habitantes)}")

    def actualizar_visibilidad_columnas(self):
        """Mostrar/ocultar columnas de nombre y folio"""
        # Evitar que ambas queden ocultas
        if not self.nombre_visible.get() and not self.folio_visible.get():
            self.folio_visible.set(True)
        
        if self.folio_visible.get():
            self.tree.column('folio', width=80, minwidth=40, stretch=False)
            self.tree.heading('folio', text='Folio')
        else:
            self.tree.column('folio', width=0, minwidth=0, stretch=False)
            self.tree.heading('folio', text='')
        
        if self.nombre_visible.get():
            self.tree.column('nombre', width=320, minwidth=120, stretch=True)
            self.tree.heading('nombre', text='Nombre Completo')
        else:
            self.tree.column('nombre', width=0, minwidth=0, stretch=False)
            self.tree.heading('nombre', text='')
    
    def buscar_tiempo_real(self):
        """Busqueda en tiempo real mientras se escribe"""
        criterio = self.search_var.get().strip()
        
        if not criterio:
            self.actualizar_tabla(self.habitantes)
            return
        
        try:
            response = requests.get(f"{self.api_url}/habitantes/buscar", 
                                   params={'q': criterio}, 
                                   timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.actualizar_tabla(data['resultados'])
        except:
            pass
    
    def limpiar_busqueda(self):
        """Limpiar campo de busqueda"""
        self.search_var.set('')
        self.actualizar_tabla(self.habitantes)
    
    def agregar_habitante(self):
        """Agregar nuevo habitante"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Agregar Nuevo Habitante")
        dialog.geometry("450x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Nombre Completo del Habitante:", 
                 font=('Arial', 10, 'bold')).pack(pady=10)
        nombre_entry = ttk.Entry(dialog, width=50)
        nombre_entry.pack(pady=10)
        
        def guardar(event=None):
            nombre = nombre_entry.get().strip()
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
            
            try:
                response = requests.post(f"{self.api_url}/habitantes",
                                        json={'nombre': nombre},
                                        timeout=5)
                data = response.json()
                
                if data['success']:
                    messagebox.showinfo("Exito", 
                        f"Habitante agregado correctamente\n"
                        f"Folio asignado: {data['habitante']['folio']}")
                    dialog.destroy()
                    self.cargar_habitantes()
                else:
                    messagebox.showerror("Error", data['mensaje'])
            except Exception as e:
                messagebox.showerror("Error", f"Error al agregar: {str(e)}")
        
        botones = ttk.Frame(dialog)
        botones.pack(pady=10)
        ttk.Button(botones, text="Confirmar", command=guardar, width=18).pack(side=tk.LEFT, padx=5)
        ttk.Button(botones, text="Cancelar", command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=5)
        dialog.bind("<Return>", guardar)
        nombre_entry.focus()

    def abrir_control_pagos(self):
        """Lanza la app de control de pagos"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            pagos_path = os.path.join(script_dir, "control_pagos.py")
            
            if not os.path.exists(pagos_path):
                messagebox.showerror("Error", f"No se encontró el archivo:\n{pagos_path}")
                return
            
            # Abrir el sistema de control de pagos
            subprocess.Popen([sys.executable, pagos_path])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Control de Pagos:\n{str(e)}")

def main():
    root = tk.Tk()
    app = SistemaCensoHabitantes(root)
    root.mainloop()

if __name__ == "__main__":
    main()
