"""
Menú Principal - Sistema de Gestión Comunitaria
Interfaz gráfica para seleccionar módulos del sistema
SIN API - Arquitectura simplificada con Gestor Centralizado
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os

# Configurar rutas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.gestor_datos_global import obtener_gestor
from src.core.optimizacion_rendimiento import optimizar_rendimiento_sistema, configurar_tkinter_rendimiento

# Aplicar optimizaciones de rendimiento al inicio
print("\n🚀 Aplicando optimizaciones de rendimiento...")
optimizar_rendimiento_sistema()
print()

class MenuPrincipal:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión Comunitaria")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Aplicar optimizaciones de Tkinter
        configurar_tkinter_rendimiento(self.root)
        
        # Colores
        self.bg_principal = "#f5f7fa"
        self.bg_header = "#2c3e50"
        self.bg_boton = "#3498db"
        self.bg_boton_hover = "#2980b9"
        self.fg_blanco = "#ffffff"
        self.border_color = "#bdc3c7"
        
        self.root.configure(bg=self.bg_principal)
        
        # Inicializar gestor de datos
        self.gestor = obtener_gestor()
        
        # Rastrear procesos abiertos
        self.proceso_censo = None
        self.procesos_externos = []
        
        self.configurar_interfaz()
        
        # Limpieza al cerrar
        self.root.protocol("WM_DELETE_WINDOW", self.salir)
    
    def configurar_interfaz(self):
        # Header
        header_frame = tk.Frame(self.root, bg=self.bg_header, height=120)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, 
                text="════════════════════════════════════════",
                font=("Courier New", 10, "bold"),
                bg=self.bg_header, fg=self.fg_blanco).pack(pady=(15, 0))
        
        tk.Label(header_frame, 
                text="SISTEMA DE GESTIÓN COMUNITARIA",
                font=("Arial", 18, "bold"),
                bg=self.bg_header, fg=self.fg_blanco).pack(pady=5)
        
        tk.Label(header_frame, 
                text="San Pablo Atotonilco",
                font=("Arial", 12),
                bg=self.bg_header, fg="#ecf0f1").pack()
        
        tk.Label(header_frame, 
                text="════════════════════════════════════════",
                font=("Courier New", 10, "bold"),
                bg=self.bg_header, fg=self.fg_blanco).pack(pady=(0, 10))
        
        # Contenedor de botones
        botones_frame = tk.Frame(self.root, bg=self.bg_principal)
        botones_frame.pack(expand=True, fill=tk.BOTH, padx=40, pady=30)
        
        # Botones del menú
        opciones = [
            ("1. Censo de Habitantes", self.abrir_censo, "📋"),
            ("2. Control de Pagos", self.abrir_pagos, "💰"),
            ("3. Registro de Faenas", self.abrir_faenas, "🔨"),
            ("4. Administrar Usuarios", self.abrir_admin_usuarios, "👥"),
            ("5. Salir", self.salir, "🚪")
        ]
        
        for texto, comando, icono in opciones:
            self.crear_boton(botones_frame, f"{icono}  {texto}", comando)
        
        # Footer
        footer = tk.Label(self.root, 
                         text="Versión 2.0 - 2026 | Arquitectura Sin API",
                         font=("Arial", 9),
                         bg=self.bg_principal, fg="#7f8c8d")
        footer.pack(side=tk.BOTTOM, pady=10)
    
    def crear_boton(self, parent, texto, comando):
        """Crea un botón estilizado cuadrado"""
        btn_frame = tk.Frame(parent, bg=self.bg_principal)
        btn_frame.pack(fill=tk.X, pady=8)
        
        # Wrapper para ejecutar comandos de forma no bloqueante
        def comando_no_bloqueante():
            self.root.config(cursor="wait")
            self.root.update()
            try:
                comando()
            finally:
                self.root.config(cursor="arrow")
        
        btn = tk.Button(btn_frame,
                       text=texto,
                       command=comando_no_bloqueante,
                       font=("Arial", 12, "bold"),
                       bg=self.bg_boton,
                       fg=self.fg_blanco,
                       relief=tk.FLAT,
                       cursor="hand2",
                       height=2,
                       bd=0,
                       activebackground=self.bg_boton_hover,
                       activeforeground=self.fg_blanco)
        btn.pack(fill=tk.X, ipady=8)
        
        # Efectos hover
        btn.bind('<Enter>', lambda e: e.widget.config(bg=self.bg_boton_hover))
        btn.bind('<Leave>', lambda e: e.widget.config(bg=self.bg_boton))
        
        return btn
    
    def abrir_censo(self):
        """Abrir sistema de censo"""
        # Verificar si ya hay un proceso de censo corriendo
        if self.proceso_censo is not None:
            # Verificar si el proceso sigue vivo
            if self.proceso_censo.poll() is None:
                # El proceso sigue activo, mostrar mensaje
                messagebox.showinfo(
                    "Censo Abierto",
                    "El sistema de censo ya está abierto.\n\nBusca la ventana existente."
                )
                return
            else:
                # El proceso terminó, permitir abrir uno nuevo
                self.proceso_censo = None
        
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            censo_path = os.path.join(script_dir, "src", "modules", "censo", "censo_habitantes.py")
            
            # En Windows, usar pythonw.exe para evitar ventana de consola
            if sys.platform == 'win32':
                pythonw_exe = sys.executable.replace("python.exe", "pythonw.exe")
                if os.path.exists(pythonw_exe):
                    self.proceso_censo = subprocess.Popen([pythonw_exe, censo_path])
                else:
                    CREATE_NO_WINDOW = 0x08000000
                    self.proceso_censo = subprocess.Popen([sys.executable, censo_path], 
                                                         creationflags=CREATE_NO_WINDOW)
            else:
                self.proceso_censo = subprocess.Popen([sys.executable, censo_path])
            
            self.procesos_externos.append(self.proceso_censo)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Censo:\n{str(e)}")
    
    def abrir_pagos(self):
        """Abrir control de pagos (con su propio login)"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            pagos_path = os.path.join(script_dir, "src", "modules", "pagos", "control_pagos.py")
            
            # Abrir en proceso separado para que tenga su propio login
            if sys.platform == 'win32':
                pythonw_exe = sys.executable.replace("python.exe", "pythonw.exe")
                if os.path.exists(pythonw_exe):
                    subprocess.Popen([pythonw_exe, pagos_path])
                else:
                    CREATE_NO_WINDOW = 0x08000000
                    subprocess.Popen([sys.executable, pagos_path], creationflags=CREATE_NO_WINDOW)
            else:
                subprocess.Popen([sys.executable, pagos_path])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Control de Pagos:\n{str(e)}")
    
    def abrir_faenas(self):
        """Abrir registro de faenas (con su propio login)"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            faenas_path = os.path.join(script_dir, "src", "modules", "faenas", "control_faenas.py")
            
            # Abrir en proceso separado para que tenga su propio login
            if sys.platform == 'win32':
                pythonw_exe = sys.executable.replace("python.exe", "pythonw.exe")
                if os.path.exists(pythonw_exe):
                    subprocess.Popen([pythonw_exe, faenas_path])
                else:
                    CREATE_NO_WINDOW = 0x08000000
                    subprocess.Popen([sys.executable, faenas_path], creationflags=CREATE_NO_WINDOW)
            else:
                subprocess.Popen([sys.executable, faenas_path])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Registro de Faenas:\n{str(e)}")
    
    def abrir_admin_usuarios(self):
        """Abrir administración de usuarios"""
        try:
            from src.auth.ventana_admin_usuarios import VentanaAdminUsuarios
            ventana = tk.Toplevel(self.root)
            app = VentanaAdminUsuarios(ventana)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Administración de Usuarios:\n{str(e)}")
    
    def salir(self):
        """Cerrar aplicación y todos los procesos hijos"""
        if messagebox.askyesno("Confirmar salida", "¿Desea salir del sistema?"):
            # Terminar todos los procesos externos
            for proceso in self.procesos_externos:
                if proceso is not None and proceso.poll() is None:
                    try:
                        if sys.platform == 'win32':
                            os.system(f"taskkill /F /PID {proceso.pid} 2>nul")
                        else:
                            proceso.terminate()
                            proceso.wait(timeout=1)
                    except:
                        pass
            
            self.root.destroy()
            sys.exit(0)


def main():
    root = tk.Tk()
    app = MenuPrincipal(root)
    root.mainloop()


if __name__ == "__main__":
    main()
