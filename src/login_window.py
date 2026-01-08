"""
Ventana de login para el sistema
"""
import tkinter as tk
from tkinter import ttk, messagebox
from autenticacion import GestorAutenticacion
from tema_moderno import TEMA_CLARO, TEMA_OSCURO, FUENTES, ESPACIADO

class VentanaLogin:
    """Ventana de autenticación para el sistema"""
    
    def __init__(self, root, callback_exito):
        self.root = root
        self.callback_exito = callback_exito
        self.gestor_auth = GestorAutenticacion()
        self.usuario_actual = None
        self.tema_actual = 'claro'
        
        self.crear_ventana()
    
    def crear_ventana(self):
        """Crear interfaz de login moderno"""
        self.root.title("Sistema Digital Comunidad - Iniciar Sesión")
        self.root.geometry("820x660")
        self.root.minsize(760, 620)
        self.root.resizable(True, True)
        
        tema = TEMA_CLARO
        
        # Fondo principal
        self.root.configure(bg=tema['bg_principal'])
        
        # Centrar ventana
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Canvas para fondo decorativo
        canvas = tk.Canvas(self.root, bg=tema['accent_light'], highlightthickness=0, height=110)
        canvas.pack(fill=tk.X, pady=(0, 24))
        canvas.create_text(410, 50, text="🏘️", font=('Arial', 52), fill=tema['accent_primary'])
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg=tema['bg_principal'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['lg'], pady=ESPACIADO['lg'])
        
        # Título
        title_label = tk.Label(main_frame, text="Sistema Digital Comunidad", 
                      font=FUENTES['titulo_grande'], 
                      bg=tema['bg_principal'], fg=tema['accent_primary'])
        title_label.pack(pady=(0, 5))
        
        subtitle_label = tk.Label(main_frame, text="Iniciar Sesión", 
                     font=FUENTES['subtitulo'], 
                     bg=tema['bg_principal'], fg=tema['fg_secundario'])
        subtitle_label.pack(pady=(0, ESPACIADO['lg']))
        
        # Frame del formulario con fondo
        form_frame = tk.Frame(main_frame, bg=tema['bg_secundario'], 
                 relief=tk.FLAT, bd=0)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['md'], pady=ESPACIADO['md'])
        form_frame.pack_propagate(False)
        
        # Padding interno
        inner_frame = tk.Frame(form_frame, bg=tema['bg_secundario'])
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['lg'], pady=ESPACIADO['lg'])
        
        # Usuario
        user_label = tk.Label(inner_frame, text="Usuario:", 
                             font=FUENTES['subtitulo'],
                             bg=tema['bg_secundario'], fg=tema['fg_principal'])
        user_label.pack(anchor=tk.W, pady=(0, ESPACIADO['sm']))
        
        self.usuario_entry = tk.Entry(inner_frame, font=FUENTES['normal'], width=40,
                                      bg=tema['input_bg'], fg=tema['fg_principal'],
                                      relief=tk.SOLID, bd=1, insertbackground=tema['accent_primary'])
        self.usuario_entry.pack(fill=tk.X, pady=(0, ESPACIADO['lg']))
        self.usuario_entry.bind('<FocusIn>', lambda e: self._on_entry_focus(e, True))
        self.usuario_entry.bind('<FocusOut>', lambda e: self._on_entry_focus(e, False))
        
        # Contraseña
        pass_label = tk.Label(inner_frame, text="Contraseña:", 
                             font=FUENTES['subtitulo'],
                             bg=tema['bg_secundario'], fg=tema['fg_principal'])
        pass_label.pack(anchor=tk.W, pady=(0, ESPACIADO['sm']))
        
        self.password_entry = tk.Entry(inner_frame, font=FUENTES['normal'], width=40, show='●',
                                       bg=tema['input_bg'], fg=tema['fg_principal'],
                                       relief=tk.SOLID, bd=1, insertbackground=tema['accent_primary'])
        self.password_entry.pack(fill=tk.X, pady=(0, ESPACIADO['xl']))
        self.password_entry.bind('<FocusIn>', lambda e: self._on_entry_focus(e, True))
        self.password_entry.bind('<FocusOut>', lambda e: self._on_entry_focus(e, False))
        
        # Botones
        btn_frame = tk.Frame(inner_frame, bg=tema['bg_secundario'])
        btn_frame.pack(fill=tk.X, pady=(ESPACIADO['lg'], 0))
        
        login_btn = tk.Button(btn_frame, text="✓ Iniciar Sesión", command=self.intentar_login,
                     font=FUENTES['botones'], bg=tema['accent_primary'],
                     fg='#ffffff', relief=tk.FLAT, padx=ESPACIADO['lg'], 
                     pady=ESPACIADO['md'], cursor='hand2',
                     activebackground=tema['accent_secondary'])
        login_btn.pack(side=tk.LEFT, padx=(0, ESPACIADO['md']), expand=True, fill=tk.X)
        
        exit_btn = tk.Button(btn_frame, text="✕ Salir", command=self.root.quit,
                    font=FUENTES['botones'], bg=tema['error'],
                    fg='#ffffff', relief=tk.FLAT, padx=ESPACIADO['lg'],
                    pady=ESPACIADO['md'], cursor='hand2',
                    activebackground='#bb2d3b')
        exit_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Info de demostración
        info_label = tk.Label(main_frame, text="Demo: usuario=admin, contraseña=admin123",
                     font=FUENTES['pequeño'], 
                     bg=tema['bg_principal'], fg=tema['fg_terciario'],
                     justify=tk.CENTER)
        info_label.pack(pady=ESPACIADO['lg'])
        
        # Bindings
        self.usuario_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.intentar_login())
        
        # Foco inicial
        self.usuario_entry.focus()
    
    def _on_entry_focus(self, event, is_focus):
        """Cambiar border color al hacer focus/blur"""
        tema = TEMA_CLARO
        if is_focus:
            event.widget.config(relief=tk.SOLID, bd=2)
        else:
            event.widget.config(relief=tk.SOLID, bd=1)
    
    def intentar_login(self):
        """Intentar iniciar sesión"""
        usuario = self.usuario_entry.get().strip()
        password = self.password_entry.get()
        
        if not usuario or not password:
            messagebox.showerror("Error de Validación", "Por favor complete todos los campos")
            return
        
        # Verificar credenciales
        resultado = self.gestor_auth.login(usuario, password)
        
        if resultado['exito']:
            self.usuario_actual = {
                'nombre': resultado.get('usuario', usuario),
                'nombre_completo': resultado.get('nombre_completo', ''),
                'rol': resultado.get('rol', 'operador')
            }
            messagebox.showinfo("Bienvenido", 
                f"Sesión iniciada correctamente\n"
                f"Usuario: {self.usuario_actual['nombre_completo'] or self.usuario_actual['nombre']}\n"
                f"Rol: {self.usuario_actual['rol'].upper()}")
            
            # Cerrar ventana de login y continuar con callback
            self.root.withdraw()
            self.callback_exito(self.usuario_actual, self.gestor_auth)
        else:
            error_msg = resultado.get('error', 'Error desconocido en la autenticación')
            messagebox.showerror("Error de Autenticación", error_msg)
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()

