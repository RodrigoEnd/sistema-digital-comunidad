"""
Menú Principal - Sistema de Gestión Comunitaria
Interfaz gráfica para seleccionar módulos del sistema
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os

# Configurar rutas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import MODO_OFFLINE
import requests
import time

class MenuPrincipal:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión Comunitaria")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Colores
        self.bg_principal = "#f5f7fa"
        self.bg_header = "#2c3e50"
        self.bg_boton = "#3498db"
        self.bg_boton_hover = "#2980b9"
        self.fg_blanco = "#ffffff"
        self.border_color = "#bdc3c7"
        
        self.root.configure(bg=self.bg_principal)
        
        # Rastrear procesos abiertos
        self.proceso_censo = None
        
        self.configurar_interfaz()
        
        # Verificar API al iniciar
        if not MODO_OFFLINE:
            self.root.after(500, self.verificar_api)
    
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
        
        # Estado de API
        self.api_status = tk.Label(botones_frame, 
                                   text="● API: Verificando...",
                                   font=("Arial", 9),
                                   bg=self.bg_principal, fg="#95a5a6")
        self.api_status.pack(anchor=tk.W, pady=(0, 15))
        
        # Botones del menú
        opciones = [
            ("1. Censo de Habitantes", self.abrir_censo, "📋"),
            ("2. Control de Pagos", self.abrir_pagos, "💰"),
            ("3. Registro de Faenas", self.abrir_faenas, "🔨"),
            ("4. Salir", self.salir, "🚪")
        ]
        
        for texto, comando, icono in opciones:
            self.crear_boton(botones_frame, f"{icono}  {texto}", comando)
        
        # Footer
        footer = tk.Label(self.root, 
                         text="Versión 1.0 - 2026",
                         font=("Arial", 9),
                         bg=self.bg_principal, fg="#7f8c8d")
        footer.pack(side=tk.BOTTOM, pady=10)
    
    def crear_boton(self, parent, texto, comando):
        """Crea un botón estilizado cuadrado"""
        btn_frame = tk.Frame(parent, bg=self.bg_principal)
        btn_frame.pack(fill=tk.X, pady=8)
        
        btn = tk.Button(btn_frame,
                       text=texto,
                       command=comando,
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
    
    def verificar_api(self):
        """Verificar estado de la API"""
        try:
            response = requests.get("http://127.0.0.1:5000/api/ping", timeout=2)
            if response.status_code == 200:
                self.api_status.config(text="● API: Activa", fg="#27ae60")
                return True
        except:
            pass
        
        self.api_status.config(text="● API: Inactiva - Iniciando...", fg="#e67e22")
        self.iniciar_api()
        return False
    
    def iniciar_api(self):
        """Iniciar servidor API en segundo plano"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            api_path = os.path.join(script_dir, "src", "api", "api_local.py")
            
            subprocess.Popen(
                [sys.executable, api_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            # Verificar después de 3 segundos
            self.root.after(3000, self.verificar_api)
        except Exception as e:
            self.api_status.config(text=f"● API: Error - {str(e)[:20]}", fg="#e74c3c")
    
    def abrir_censo(self):
        """Abrir sistema de censo"""
        # Verificar si ya hay un proceso de censo corriendo
        if self.proceso_censo is not None:
            # Verificar si el proceso sigue vivo
            if self.proceso_censo.poll() is None:
                # El proceso sigue activo, traer ventana al frente (no hay forma directa en subprocess)
                messagebox.showinfo("Información", 
                                   "El sistema de Censo ya está abierto.\nBúscalo en la barra de tareas.")
                return
            else:
                # El proceso terminó, permitir abrir uno nuevo
                self.proceso_censo = None
        
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            censo_path = os.path.join(script_dir, "src", "modules", "censo", "censo_habitantes.py")
            self.proceso_censo = subprocess.Popen([sys.executable, censo_path])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Censo:\n{str(e)}")
    
    def abrir_pagos(self):
        """Abrir control de pagos con autenticación"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            os.chdir(script_dir)
            from src.modules.pagos.control_pagos import main as control_main
            self.root.withdraw()  # Ocultar menú
            control_main()
            self.root.deiconify()  # Mostrar menú de nuevo
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Control de Pagos:\n{str(e)}")
            self.root.deiconify()
    
    def abrir_faenas(self):
        """Abrir registro de faenas con autenticación"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            os.chdir(script_dir)
            from src.modules.faenas.control_faenas import main as faenas_main
            self.root.withdraw()
            faenas_main()
            self.root.deiconify()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Registro de Faenas:\n{str(e)}")
            self.root.deiconify()
    
    def salir(self):
        """Cerrar aplicación"""
        if messagebox.askyesno("Confirmar salida", "¿Desea salir del sistema?"):
            self.root.destroy()
            sys.exit(0)


def main():
    root = tk.Tk()
    app = MenuPrincipal(root)
    root.mainloop()


if __name__ == "__main__":
    main()
