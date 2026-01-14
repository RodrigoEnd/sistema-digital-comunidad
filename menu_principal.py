"""
Menú Principal - Sistema de Gestión Comunitaria
Interfaz gráfica para seleccionar módulos del sistema
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
import ctypes
import threading
import time

# Configurar rutas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import MODO_OFFLINE
import requests
from src.auth.gestor_perfiles import autenticar, agregar_delegado, listar_delegados, obtener_estadisticas

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
        self.proceso_api = None
        self.api_verificada = False
        self.verificando_api = False
        
        self.configurar_interfaz()
        
        # Verificar API en hilo separado (no bloquea UI)
        if not MODO_OFFLINE:
            threading.Thread(target=self._hilo_verificar_api, daemon=True).start()
    
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
            ("4. Administrar Usuarios", self.abrir_admin_usuarios, "👥"),
            ("5. Salir", self.salir, "🚪")
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
    
    def verificar_api(self):
        """Verificar estado de la API"""
        try:
            # URL CORRECTA: sin /api al final
            response = requests.get("http://127.0.0.1:5000/ping", timeout=2)
            if response.status_code == 200:
                self.root.after(0, lambda: self.api_status.config(text="● API: Activa", fg="#27ae60"))
                self.api_verificada = True
                return True
        except Exception as e:
            print(f"[API Check] Error: {e}")
            pass
        
        # API no responde - intentar iniciarla
        self.root.after(0, lambda: self.api_status.config(text="● API: Inactiva - Iniciando...", fg="#e67e22"))
        self.iniciar_api()
        return False
    
    def _hilo_verificar_api(self):
        """Hilo separado para verificar API sin bloquear UI"""
        time.sleep(0.5)  # Esperar a que UI esté lista
        
        for intento in range(5):
            if self.verificar_api():
                return
            time.sleep(1)  # Esperar 1 segundo entre intentos
        
        # Si después de 5 intentos no funciona, mostrar error
        self.root.after(0, lambda: self.api_status.config(
            text="● API: Error - No se pudo conectar", fg="#e74c3c"))
    
    def iniciar_api(self):
        """Iniciar servidor API en segundo plano - SIN MOSTRAR VENTANA"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            api_path = os.path.join(script_dir, "src", "api", "api_local.py")
            
            # Crear archivo de log para diagnóstico
            log_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 
                                    'SistemaComunidad', 'api_debug.log')
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            log_file = open(log_path, 'w')
            
            if sys.platform == 'win32':
                # Windows: usar STARTUPINFO para ocultar ventana COMPLETAMENTE
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                # CREATE_NEW_PROCESS_GROUP + CREATE_NO_WINDOW para ocultar completamente
                creation_flags = (
                    subprocess.CREATE_NEW_PROCESS_GROUP | 
                    0x08000000  # CREATE_NO_WINDOW
                )
                
                self.proceso_api = subprocess.Popen(
                    [sys.executable, api_path],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,  # Redirigir stderr a stdout
                    stdin=subprocess.DEVNULL,   # No leer entrada estándar
                    startupinfo=startupinfo,
                    creationflags=creation_flags,
                    close_fds=True              # Cerrar descriptores heredados
                )
            else:
                # Linux/Mac
                self.proceso_api = subprocess.Popen(
                    [sys.executable, api_path],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True
                )
            
            print(f"[API] Proceso iniciado con PID: {self.proceso_api.pid}")
            print(f"[API] Logs guardados en: {log_path}")
            
            # Verificar después de 3 segundos en hilo separado (más tiempo para iniciar)
            threading.Thread(target=self._esperar_y_verificar_api, daemon=True).start()
            
        except Exception as e:
            print(f"[API Error] {e}")
            self.root.after(0, lambda: self.api_status.config(
                text=f"● API: Error - {str(e)[:20]}", fg="#e74c3c"))
    
    def _esperar_y_verificar_api(self):
        """Espera a que API esté lista y verifica"""
        # Intentar 30 veces x 0.5s = 15 segundos máximo (más tiempo para iniciar)
        for intento in range(30):
            time.sleep(0.5)
            try:
                # Timeout corto para respuesta
                response = requests.get("http://127.0.0.1:5000/ping", timeout=0.5)
                if response.status_code == 200:
                    print("[API] Conectada exitosamente")
                    self.root.after(0, lambda: self.api_status.config(
                        text="● API: Activa", fg="#27ae60"))
                    self.api_verificada = True
                    return
            except requests.exceptions.Timeout:
                # Timeout - API aún cargando
                pass
            except requests.exceptions.ConnectionError as e:
                # Puerto no escucha - API fallando
                if intento == 29:  # Último intento
                    print(f"[API] Error de conexión: {e}")
                    # Mostrar contenido del log si existe
                    try:
                        log_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 
                                               'SistemaComunidad', 'api_debug.log')
                        with open(log_path, 'r') as f:
                            log_content = f.read()
                            if log_content:
                                print(f"[API Log]:\n{log_content[:500]}")
                    except:
                        pass
        
        print("[API] No se pudo conectar después de 15 segundos")
        self.root.after(0, lambda: self.api_status.config(
            text="● API: Error conectando - Ver logs", fg="#e74c3c"))
    
    def abrir_censo(self):
        """Abrir sistema de censo"""
        # Verificar si ya hay un proceso de censo corriendo
        if self.proceso_censo is not None:
            # Verificar si el proceso sigue vivo
            if self.proceso_censo.poll() is None:
                # El proceso sigue activo, intentar traer ventana al frente
                try:
                    # En Windows, intentar activar ventana por PID
                    if sys.platform == 'win32':
                        import win32gui
                        import win32con
                        
                        # Buscar ventana por título
                        hwnd = win32gui.FindWindow(None, "📋 Sistema de Censo de Habitantes - Comunidad San Pablo")
                        if hwnd:
                            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                            win32gui.SetForegroundWindow(hwnd)
                            return
                except:
                    pass
                
                messagebox.showinfo("Información", 
                                   "El sistema de Censo ya está abierto.\nVerifica la barra de tareas.")
                return
            else:
                # El proceso terminó, permitir abrir uno nuevo
                self.proceso_censo = None
        
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            censo_path = os.path.join(script_dir, "src", "modules", "censo", "censo_habitantes.py")
            self.proceso_censo = subprocess.Popen(
                [sys.executable, censo_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Censo:\n{str(e)}")
    
    def abrir_pagos(self):
        """Abrir control de pagos con autenticación"""
        # No bloquear UI mientras se carga
        self.root.config(cursor="wait")
        self.root.update()
        
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            os.chdir(script_dir)
            from src.modules.pagos.control_pagos import main as control_main
            
            # Ejecutar en hilo para no bloquear
            threading.Thread(
                target=self._ejecutar_pagos,
                args=(control_main,),
                daemon=False
            ).start()
            
        except Exception as e:
            self.root.config(cursor="arrow")
            messagebox.showerror("Error", f"No se pudo abrir Control de Pagos:\n{str(e)}")
    
    def _ejecutar_pagos(self, control_main):
        """Ejecutar control de pagos sin bloquear UI"""
        try:
            self.root.withdraw()  # Ocultar menú
            control_main()
            self.root.deiconify()  # Mostrar menú de nuevo
        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("Error", str(e))
        finally:
            self.root.config(cursor="arrow")
    
    def abrir_faenas(self):
        """Abrir registro de faenas con autenticación"""
        self.root.config(cursor="wait")
        self.root.update()
        
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            os.chdir(script_dir)
            from src.modules.faenas.control_faenas import main as faenas_main
            
            threading.Thread(
                target=self._ejecutar_faenas,
                args=(faenas_main,),
                daemon=False
            ).start()
            
        except Exception as e:
            self.root.config(cursor="arrow")
            messagebox.showerror("Error", f"No se pudo abrir Registro de Faenas:\n{str(e)}")
    
    def _ejecutar_faenas(self, faenas_main):
        """Ejecutar faenas sin bloquear UI"""
        try:
            self.root.withdraw()
            faenas_main()
            self.root.deiconify()
        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("Error", str(e))
        finally:
            self.root.config(cursor="arrow")
    
    def abrir_admin_usuarios(self):
        """Abrir administración de usuarios"""
        self.root.config(cursor="wait")
        self.root.update()
        
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            os.chdir(script_dir)
            from src.auth.ventana_admin_usuarios import VentanaAdminUsuarios
            
            ventana = tk.Toplevel(self.root)
            app = VentanaAdminUsuarios(ventana)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Administración de Usuarios:\n{str(e)}")
        finally:
            self.root.config(cursor="arrow")
    
    def salir(self):
        """Cerrar aplicación"""
        if messagebox.askyesno("Confirmar salida", "¿Desea salir del sistema?"):
            # Matar API si está corriendo
            if self.proceso_api is not None and self.proceso_api.poll() is None:
                try:
                    self.proceso_api.terminate()
                    self.proceso_api.wait(timeout=2)
                except:
                    pass
            
            # Matar Census si está corriendo
            if self.proceso_censo is not None and self.proceso_censo.poll() is None:
                try:
                    self.proceso_censo.terminate()
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
