"""
Ventana de login para el sistema con diseño moderno y atractivo
"""
import tkinter as tk
from tkinter import ttk, messagebox
from src.auth.autenticacion import GestorAutenticacion
from src.ui.tema_moderno import TEMA_CLARO, TEMA_OSCURO, FUENTES, FUENTES_DISPLAY, ESPACIADO, ICONOS, aclarar_color

class VentanaLogin:
    """Ventana de autenticación para el sistema"""
    
    def __init__(self, root, callback_exito):
        self.root = root
        self.callback_exito = callback_exito
        self.gestor_auth = GestorAutenticacion()
        self.usuario_actual = None
        
        self.crear_ventana()
    
    def crear_ventana(self):
        """Crear interfaz de login moderno tipo card flotante"""
        self.root.title("Sistema Digital Comunidad - Iniciar Sesión")
        self.root.geometry("900x700")
        self.root.minsize(800, 650)
        self.root.resizable(True, True)
        
        tema = TEMA_CLARO
        
        # Fondo principal con gradiente simulado
        self.root.configure(bg=tema['bg_principal'])
        
        # Centrar ventana
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Canvas de fondo con efecto degradado superior
        header_canvas = tk.Canvas(self.root, bg=tema['accent_primary'], 
                                 highlightthickness=0, height=180)
        header_canvas.pack(fill=tk.X, pady=(0, 0))
        
        # Degradado simulado con rectángulos
        gradient_start = tema['accent_primary']
        gradient_end = aclarar_color(tema['accent_primary'], 0.2)
        
        # Iconos decorativos en el header
        header_canvas.create_text(450, 65, text=ICONOS['casa'], 
                                 font=('Arial', 64), fill='#ffffff')
        
        header_canvas.create_text(450, 140, text="Sistema Digital Comunidad",
                                 font=FUENTES['titulo_grande'], fill='#ffffff')
        
        # Frame principal centrado
        main_container = tk.Frame(self.root, bg=tema['bg_principal'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['xxxl'], 
                          pady=ESPACIADO['xl'])
        
        # Card flotante con sombra simulada
        shadow_frame = tk.Frame(main_container, bg='#d0d0d0')
        shadow_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, 
                          width=520, height=440, x=4, y=4)
        
        card_frame = tk.Frame(main_container, bg=tema.get('card_bg', '#ffffff'),
                             relief=tk.FLAT, bd=1, highlightthickness=1,
                             highlightbackground=tema.get('card_border', tema['border']))
        card_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=520, height=440)
        
        # Padding interno del card
        inner_frame = tk.Frame(card_frame, bg=tema.get('card_bg', '#ffffff'))
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['xxxl'], 
                        pady=ESPACIADO['xl'])
        
        # Título del card
        title_frame = tk.Frame(inner_frame, bg=tema.get('card_bg', '#ffffff'))
        title_frame.pack(pady=(0, ESPACIADO['xl']))
        
        tk.Label(title_frame, text="Bienvenido", 
                font=FUENTES['titulo'], 
                bg=tema.get('card_bg', '#ffffff'), 
                fg=tema['fg_principal']).pack()
        
        tk.Label(title_frame, text="Inicia sesión para continuar", 
                font=FUENTES['normal'], 
                bg=tema.get('card_bg', '#ffffff'), 
                fg=tema['fg_secundario']).pack()
        
        # Formulario
        form_container = tk.Frame(inner_frame, bg=tema.get('card_bg', '#ffffff'))
        form_container.pack(fill=tk.BOTH, expand=True)
        
        # Usuario
        user_label = tk.Label(form_container, text="Usuario", 
                             font=FUENTES['normal'],
                             bg=tema.get('card_bg', '#ffffff'), 
                             fg=tema['fg_principal'])
        user_label.pack(anchor=tk.W, pady=(0, ESPACIADO['xs']))
        
        user_field_container = tk.Frame(form_container, bg=tema['input_bg'],
                                       relief=tk.FLAT, bd=1, highlightthickness=1,
                                       highlightbackground=tema['border'])
        user_field_container.pack(fill=tk.X, pady=(0, ESPACIADO['lg']))
        
        user_inner = tk.Frame(user_field_container, bg=tema['input_bg'])
        user_inner.pack(fill=tk.X, padx=ESPACIADO['md'], pady=ESPACIADO['sm'])
        
        tk.Label(user_inner, text=ICONOS['usuario'], font=('Arial', 14),
                bg=tema['input_bg'], fg=tema['fg_terciario']).pack(side=tk.LEFT, 
                                                                   padx=(0, ESPACIADO['sm']))
        
        self.usuario_entry = tk.Entry(user_inner, font=FUENTES['normal'],
                                      bg=tema['input_bg'], fg=tema['fg_principal'],
                                      relief=tk.FLAT, bd=0, 
                                      insertbackground=tema['accent_primary'])
        self.usuario_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.user_field_container = user_field_container
        self.usuario_entry.bind('<FocusIn>', lambda e: self._on_entry_focus(self.user_field_container, True))
        self.usuario_entry.bind('<FocusOut>', lambda e: self._on_entry_focus(self.user_field_container, False))
        
        # Contraseña
        pass_label = tk.Label(form_container, text="Contraseña", 
                             font=FUENTES['normal'],
                             bg=tema.get('card_bg', '#ffffff'), 
                             fg=tema['fg_principal'])
        pass_label.pack(anchor=tk.W, pady=(0, ESPACIADO['xs']))
        
        pass_field_container = tk.Frame(form_container, bg=tema['input_bg'],
                                       relief=tk.FLAT, bd=1, highlightthickness=1,
                                       highlightbackground=tema['border'])
        pass_field_container.pack(fill=tk.X, pady=(0, ESPACIADO['xl']))
        
        pass_inner = tk.Frame(pass_field_container, bg=tema['input_bg'])
        pass_inner.pack(fill=tk.X, padx=ESPACIADO['md'], pady=ESPACIADO['sm'])
        
        tk.Label(pass_inner, text="🔒", font=('Arial', 14),
                bg=tema['input_bg'], fg=tema['fg_terciario']).pack(side=tk.LEFT,
                                                                   padx=(0, ESPACIADO['sm']))
        
        self.password_entry = tk.Entry(pass_inner, font=FUENTES['normal'], show='●',
                                       bg=tema['input_bg'], fg=tema['fg_principal'],
                                       relief=tk.FLAT, bd=0,
                                       insertbackground=tema['accent_primary'])
        self.password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.pass_field_container = pass_field_container
        self.password_entry.bind('<FocusIn>', lambda e: self._on_entry_focus(self.pass_field_container, True))
        self.password_entry.bind('<FocusOut>', lambda e: self._on_entry_focus(self.pass_field_container, False))
        
        # Botones con mejor diseño
        btn_frame = tk.Frame(form_container, bg=tema.get('card_bg', '#ffffff'))
        btn_frame.pack(fill=tk.X, pady=(ESPACIADO['lg'], 0))
        
        # Botón login principal (más grande y destacado)
        login_btn = tk.Button(btn_frame, text=f"{ICONOS['exito']} Iniciar Sesión", 
                     command=self.intentar_login,
                     font=FUENTES['botones'], bg=tema['accent_primary'],
                     fg='#ffffff', relief=tk.FLAT, 
                     padx=ESPACIADO['xl'], pady=ESPACIADO['md'],
                     cursor='hand2', bd=0,
                     activebackground=tema['accent_secondary'])
        login_btn.pack(fill=tk.X, pady=(0, ESPACIADO['md']))
        login_btn.bind('<Enter>', lambda e: e.widget.config(bg=tema['accent_secondary']))
        login_btn.bind('<Leave>', lambda e: e.widget.config(bg=tema['accent_primary']))
        
        # Botón salir secundario
        exit_btn = tk.Button(btn_frame, text=f"{ICONOS['cerrar']} Cancelar", 
                    command=self.root.quit,
                    font=FUENTES['normal'], bg=tema['bg_tertiary'],
                    fg=tema['fg_secundario'], relief=tk.FLAT,
                    padx=ESPACIADO['lg'], pady=ESPACIADO['sm'],
                    cursor='hand2', bd=0,
                    activebackground=tema['border'])
        exit_btn.pack(fill=tk.X)
        exit_btn.bind('<Enter>', lambda e: e.widget.config(bg=tema['border']))
        exit_btn.bind('<Leave>', lambda e: e.widget.config(bg=tema['bg_tertiary']))
        
        # Info de demostración en el footer
        footer_frame = tk.Frame(self.root, bg=tema['bg_principal'])
        footer_frame.pack(side=tk.BOTTOM, pady=ESPACIADO['lg'])
        
        info_card = tk.Frame(footer_frame, bg=tema['info_light'], 
                           relief=tk.FLAT, bd=1, highlightthickness=1,
                           highlightbackground=tema['info'])
        info_card.pack(padx=ESPACIADO['xl'])
        
        info_inner = tk.Frame(info_card, bg=tema['info_light'])
        info_inner.pack(padx=ESPACIADO['lg'], pady=ESPACIADO['md'])
        
        tk.Label(info_inner, text=f"{ICONOS['info']} Demo", 
                font=FUENTES['badge'],
                bg=tema['info_light'], fg=tema['info']).pack(anchor=tk.W)
        
        tk.Label(info_inner, text="Usuario: admin  |  Contraseña: admin123",
                font=FUENTES['pequeño'], 
                bg=tema['info_light'], fg=tema['info']).pack()
        
        # Bindings
        self.usuario_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.intentar_login())
        
        # Foco inicial
        self.usuario_entry.focus()
    
    def _on_entry_focus(self, container, is_focus):
        """Cambiar border color al hacer focus/blur"""
        tema = TEMA_CLARO
        if is_focus:
            container.config(highlightbackground=tema['accent_primary'], highlightthickness=2)
        else:
            container.config(highlightbackground=tema['border'], highlightthickness=1)
    
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
            # Cerrar ventana de login y continuar con callback
            self.callback_exito(self.usuario_actual, self.gestor_auth)
        else:
            error_msg = resultado.get('error', 'Error desconocido en la autenticación')
            messagebox.showerror("Error de Autenticación", error_msg)
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()

