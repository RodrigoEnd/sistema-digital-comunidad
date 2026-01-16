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


# Control opcional de optimizaciones pesadas (evita bloqueos en arranque)
HABILITAR_OPTIMIZACION_SISTEMA = os.getenv("OPTIMIZAR_SISTEMA", "0") == "1"

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
        self.proceso_pagos = None
        self.proceso_faenas = None
        self.procesos_externos = []
        
        self.configurar_interfaz()
        
        # Aplicar optimizaciones de sistema de forma diferida y silenciosa
        if HABILITAR_OPTIMIZACION_SISTEMA:
            self.root.after(100, self._aplicar_optimizaciones_sistema)
        
        # Limpieza al cerrar
        self.root.protocol("WM_DELETE_WINDOW", self.salir)

    def _aplicar_optimizaciones_sistema(self):
        """Lanza optimizaciones sin bloquear la carga de la UI."""
        try:
            optimizar_rendimiento_sistema(silencioso=True, instalar_dependencias=False)
        except Exception:
            # Si falla, no bloquea la interfaz ni muestra diálogos
            pass
    
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
        
        # Wrapper ligero para no bloquear el hilo de UI
        def comando_no_bloqueante():
            comando()
        
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

    def _lanzar_proceso(self, script_path):
        """Lanza un script Python en ventana oculta en Windows."""
        if sys.platform == 'win32':
            pythonw_exe = sys.executable.replace("python.exe", "pythonw.exe")
            if os.path.exists(pythonw_exe):
                return subprocess.Popen([pythonw_exe, script_path])
            CREATE_NO_WINDOW = 0x08000000
            return subprocess.Popen([sys.executable, script_path], creationflags=CREATE_NO_WINDOW)
        return subprocess.Popen([sys.executable, script_path])

    def _abrir_modulo_externo(self, attr_nombre, script_relativo, titulo, mensaje_existente, nombre_modulo=None):
        """Controla apertura de módulos evitando instancias duplicadas."""
        nombre_modulo = nombre_modulo or titulo
        proceso = getattr(self, attr_nombre)
        if proceso is not None:
            if proceso.poll() is None:
                messagebox.showinfo(titulo, mensaje_existente)
                return
            setattr(self, attr_nombre, None)
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(script_dir, *script_relativo)
            nuevo_proceso = self._lanzar_proceso(script_path)
            setattr(self, attr_nombre, nuevo_proceso)
            self.procesos_externos.append(nuevo_proceso)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir {nombre_modulo}:\n{str(e)}")
    
    def abrir_censo(self):
        """Abrir sistema de censo"""
        self._abrir_modulo_externo(
            attr_nombre="proceso_censo",
            script_relativo=["src", "modules", "censo", "censo_habitantes.py"],
            titulo="Censo Abierto",
            mensaje_existente="El sistema de censo ya está abierto.\n\nBusca la ventana existente.",
            nombre_modulo="Censo"
        )
    
    def abrir_pagos(self):
        """Abrir control de pagos (con su propio login)"""
        self._abrir_modulo_externo(
            attr_nombre="proceso_pagos",
            script_relativo=["src", "modules", "pagos", "control_pagos.py"],
            titulo="Control de Pagos",
            mensaje_existente="El módulo de Pagos ya está abierto.",
            nombre_modulo="Control de Pagos"
        )
    
    def abrir_faenas(self):
        """Abrir registro de faenas (con su propio login)"""
        self._abrir_modulo_externo(
            attr_nombre="proceso_faenas",
            script_relativo=["src", "modules", "faenas", "control_faenas.py"],
            titulo="Registro de Faenas",
            mensaje_existente="El módulo de Faenas ya está abierto.",
            nombre_modulo="Registro de Faenas"
        )
    
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
