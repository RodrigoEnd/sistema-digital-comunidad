"""
Ventana de Administración de Usuarios
Permite crear, editar y eliminar usuarios delegados
Solo el administrador puede acceder
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from src.auth.gestor_perfiles import (
    autenticar, agregar_delegado, listar_delegados, 
    obtener_estadisticas, eliminar_delegado, cambiar_contrasena_delegado
)
from src.core.logger import registrar_operacion


class VentanaAdminUsuarios:
    def __init__(self, root):
        self.root = root
        self.root.title("Administración de Usuarios")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        
        # Estilos
        self.bg_principal = "#f5f7fa"
        self.bg_header = "#2c3e50"
        self.bg_frame = "#ecf0f1"
        self.fg_texto = "#2c3e50"
        self.fg_blanco = "#ffffff"
        self.color_exito = "#27ae60"
        self.color_error = "#e74c3c"
        self.color_info = "#3498db"
        
        self.root.configure(bg=self.bg_principal)
        
        # Estado autenticación
        self.autenticado = False
        self.usuario_actual = None
        
        self.configurar_interfaz()
        
    def configurar_interfaz(self):
        """Configura la interfaz principal"""
        # Header
        header = tk.Frame(self.root, bg=self.bg_header, height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        titulo = tk.Label(header, text="👥 Administración de Usuarios",
                         font=("Arial", 16, "bold"), fg=self.fg_blanco,
                         bg=self.bg_header)
        titulo.pack(pady=15)
        
        # Frame de contenido
        self.frame_contenido = tk.Frame(self.root, bg=self.bg_principal)
        self.frame_contenido.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Mostrar pantalla de login primero
        self.mostrar_login()
    
    def mostrar_login(self):
        """Muestra la interfaz de login"""
        # Limpiar frame
        for widget in self.frame_contenido.winfo_children():
            widget.destroy()
        
        frame_login = tk.Frame(self.frame_contenido, bg=self.bg_frame, padx=20, pady=20)
        frame_login.pack(expand=True)
        
        # Título
        titulo = tk.Label(frame_login, text="Ingrese Credenciales",
                         font=("Arial", 14, "bold"), fg=self.fg_texto,
                         bg=self.bg_frame)
        titulo.pack(pady=10)
        
        # Descripción
        desc = tk.Label(frame_login, 
                   text="Solo administradores pueden gestionar usuarios.",
                   font=("Arial", 10), fg="#7f8c8d", bg=self.bg_frame)
        desc.pack(pady=5)
        
        # Usuario
        tk.Label(frame_login, text="Usuario:", font=("Arial", 10),
                fg=self.fg_texto, bg=self.bg_frame).pack(pady=5)
        
        self.entry_usuario = tk.Entry(frame_login, font=("Arial", 10), width=30)
        self.entry_usuario.pack(pady=5)
        self.entry_usuario.insert(0, "admin")
        
        # Contraseña
        tk.Label(frame_login, text="Contraseña:", font=("Arial", 10),
                fg=self.fg_texto, bg=self.bg_frame).pack(pady=5)
        
        self.entry_password = tk.Entry(frame_login, font=("Arial", 10), 
                                       width=30, show="*")
        self.entry_password.pack(pady=5)
        
        # Botón login
        btn_login = tk.Button(frame_login, text="Acceder",
                             command=self.realizar_login,
                             font=("Arial", 11, "bold"),
                             bg=self.color_info, fg=self.fg_blanco,
                             padx=20, pady=10, cursor="hand2")
        btn_login.pack(pady=15)
        
        # Enter activates login
        self.entry_password.bind("<Return>", lambda e: self.realizar_login())
    
    def realizar_login(self):
        """Realiza la autenticación del administrador"""
        usuario = self.entry_usuario.get().strip()
        password = self.entry_password.get()
        
        if not usuario or not password:
            messagebox.showerror("Error", "Ingrese usuario y contraseña")
            return
        
        try:
            # Autenticar contra el gestor de perfiles
            resultado = autenticar(usuario, password)
            
            if resultado["exito"]:
                self.autenticado = True
                self.usuario_actual = usuario
                registrar_operacion(
                    tipo="LOGIN_ADMIN",
                    accion="Administrador inició sesión",
                    detalles={"usuario": usuario},
                    usuario=usuario
                )
                self.mostrar_panel_admin()
            else:
                messagebox.showerror("Error", resultado["mensaje"])
                registrar_operacion(
                    tipo="LOGIN_FALLIDO",
                    accion="Intento fallido de login",
                    detalles={"usuario": usuario},
                    usuario=usuario
                )
        except Exception as e:
            messagebox.showerror("Error", f"Error en autenticación:\n{str(e)}")
    
    def mostrar_panel_admin(self):
        """Muestra el panel de administración"""
        # Limpiar frame
        for widget in self.frame_contenido.winfo_children():
            widget.destroy()
        
        # Frame principal
        frame_principal = tk.Frame(self.frame_contenido, bg=self.bg_principal)
        frame_principal.pack(fill=tk.BOTH, expand=True)
        
        # Subtítulo con usuario actual
        subtitulo = tk.Label(frame_principal, 
                            text=f"Conectado como: {self.usuario_actual} (Administrador)",
                            font=("Arial", 10, "bold"), fg=self.color_info,
                            bg=self.bg_principal)
        subtitulo.pack(pady=10)
        
        # Estadísticas
        self.mostrar_estadisticas(frame_principal)
        
        # Frame de botones
        frame_botones = tk.Frame(frame_principal, bg=self.bg_principal)
        frame_botones.pack(fill=tk.X, padx=10, pady=10)
        
        btn_agregar = tk.Button(frame_botones, text="➕ Agregar Delegado",
                               command=self.agregar_delegado_dialog,
                               font=("Arial", 10, "bold"),
                               bg=self.color_exito, fg=self.fg_blanco,
                               padx=15, pady=10, cursor="hand2")
        btn_agregar.pack(side=tk.LEFT, padx=5)
        
        btn_refrescar = tk.Button(frame_botones, text="🔄 Refrescar",
                                 command=self.refrescar_lista,
                                 font=("Arial", 10),
                                 bg=self.color_info, fg=self.fg_blanco,
                                 padx=15, pady=10, cursor="hand2")
        btn_refrescar.pack(side=tk.LEFT, padx=5)
        
        btn_cerrar = tk.Button(frame_botones, text="❌ Cerrar Sesión",
                              command=self.cerrar_sesion,
                              font=("Arial", 10),
                              bg=self.color_error, fg=self.fg_blanco,
                              padx=15, pady=10, cursor="hand2")
        btn_cerrar.pack(side=tk.RIGHT, padx=5)
        
        # Tabla de delegados
        frame_tabla = tk.Frame(frame_principal, bg=self.bg_principal)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_tabla)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        self.tabla_delegados = ttk.Treeview(frame_tabla, 
                           columns=("Usuario", "Cargo", "Creado", "Último Login"),
                                           height=12, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tabla_delegados.yview)
        
        self.tabla_delegados.column("#0", width=150)
        self.tabla_delegados.column("Usuario", width=140)
        self.tabla_delegados.column("Cargo", width=140)
        self.tabla_delegados.column("Creado", width=120)
        self.tabla_delegados.column("Último Login", width=150)
        
        self.tabla_delegados.heading("#0", text="Tipo")
        self.tabla_delegados.heading("Usuario", text="Usuario")
        self.tabla_delegados.heading("Cargo", text="Cargo")
        self.tabla_delegados.heading("Creado", text="Creado")
        self.tabla_delegados.heading("Último Login", text="Último Login")
        
        self.tabla_delegados.pack(fill=tk.BOTH, expand=True)
        
        # Opciones de clic derecho
        self.tabla_delegados.bind("<Button-3>", self.menu_contextual)
        
        # Llenar tabla
        self.refrescar_lista()
    
    def mostrar_estadisticas(self, parent):
        """Muestra las estadísticas de usuarios"""
        try:
            stats = obtener_estadisticas()
            
            frame_stats = tk.Frame(parent, bg=self.bg_frame, padx=15, pady=15)
            frame_stats.pack(fill=tk.X, padx=10, pady=10)
            
            info_text = f"Total Delegados: {stats['total_delegados']}/4 | "
            info_text += f"Espacios Disponibles: {stats['espacios_disponibles']} | "
            info_text += f"Admin Creado: {'Sí' if stats['admin_existe'] else 'No'}"
            
            label_stats = tk.Label(frame_stats, text=info_text,
                                  font=("Arial", 10), fg=self.fg_texto,
                                  bg=self.bg_frame)
            label_stats.pack()
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
    
    def refrescar_lista(self):
        """Refresca la lista de delegados"""
        try:
            # Limpiar tabla
            for item in self.tabla_delegados.get_children():
                self.tabla_delegados.delete(item)
            
            # Obtener delegados
            delegados = listar_delegados()
            
            for delegado in delegados:
                self.tabla_delegados.insert("", "end", 
                                           text="👤 Delegado",
                                           values=(delegado["usuario"],
                                                  delegado.get("cargo", "N/A"),
                                                  delegado.get("fecha_creacion", "N/A"),
                                                  delegado.get("ultimo_acceso", "Nunca")))
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al refrescar lista:\n{str(e)}")
    
    def agregar_delegado_dialog(self):
        """Abre diálogo para agregar delegado"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Agregar Nuevo Delegado")
        dialog.geometry("420x420")
        dialog.resizable(False, False)
        dialog.configure(bg=self.bg_principal)
        
        # Centrar en ventana padre
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Nombre completo
        tk.Label(dialog, text="Nombre completo:", font=("Arial", 10),
            fg=self.fg_texto, bg=self.bg_principal).pack(pady=5)
        entry_nombre = tk.Entry(dialog, font=("Arial", 10), width=35)
        entry_nombre.pack(pady=5)

        # Cargo
        tk.Label(dialog, text="Cargo:", font=("Arial", 10),
            fg=self.fg_texto, bg=self.bg_principal).pack(pady=5)
        entry_cargo = tk.Entry(dialog, font=("Arial", 10), width=35)
        entry_cargo.pack(pady=5)

        # Usuario
        tk.Label(dialog, text="Usuario:", font=("Arial", 10),
                fg=self.fg_texto, bg=self.bg_principal).pack(pady=5)
        entry_usuario = tk.Entry(dialog, font=("Arial", 10), width=30)
        entry_usuario.pack(pady=5)
        
        # Contraseña
        tk.Label(dialog, text="Contraseña:", font=("Arial", 10),
                fg=self.fg_texto, bg=self.bg_principal).pack(pady=5)
        entry_password = tk.Entry(dialog, font=("Arial", 10), width=30, show="*")
        entry_password.pack(pady=5)
        
        # Confirmación contraseña
        tk.Label(dialog, text="Confirmar Contraseña:", font=("Arial", 10),
                fg=self.fg_texto, bg=self.bg_principal).pack(pady=5)
        entry_confirm = tk.Entry(dialog, font=("Arial", 10), width=30, show="*")
        entry_confirm.pack(pady=5)
        
        def guardar():
            nombre = entry_nombre.get().strip()
            cargo = entry_cargo.get().strip()
            usuario = entry_usuario.get().strip()
            password = entry_password.get()
            confirm = entry_confirm.get()
            
            if not nombre or not cargo or not usuario or not password or not confirm:
                messagebox.showerror("Error", "Todos los campos son requeridos")
                return

            if usuario.lower() in nombre.lower().replace(" ", ""):
                messagebox.showerror("Error", "El nombre completo debe ser diferente al usuario")
                return
            
            if len(nombre) < 6:
                messagebox.showerror("Error", "Ingrese el nombre completo (mín 6 caracteres)")
                return

            if len(cargo) < 3:
                messagebox.showerror("Error", "Ingrese el cargo (mín 3 caracteres)")
                return
            
            if password != confirm:
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                return
            
            if len(password) < 6:
                messagebox.showerror("Error", "La contraseña debe tener al menos 6 caracteres")
                return
            
            try:
                resultado = agregar_delegado(usuario, password, nombre=nombre, cargo=cargo)
                if resultado["exito"]:
                    messagebox.showinfo("Éxito", f"Delegado '{usuario}' creado exitosamente")
                    registrar_operacion(
                        tipo="CREAR_DELEGADO",
                        accion="Delegado creado",
                        detalles={"delegado": usuario, "admin": self.usuario_actual},
                        usuario=self.usuario_actual
                    )
                    self.refrescar_lista()
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", resultado["mensaje"])
            except Exception as e:
                messagebox.showerror("Error", f"Error al crear delegado:\n{str(e)}")
        
        # Botones
        frame_botones = tk.Frame(dialog, bg=self.bg_principal)
        frame_botones.pack(pady=15)
        
        btn_guardar = tk.Button(frame_botones, text="Guardar",
                               command=guardar,
                               font=("Arial", 10, "bold"),
                               bg=self.color_exito, fg=self.fg_blanco,
                               padx=20, pady=8, cursor="hand2")
        btn_guardar.pack(side=tk.LEFT, padx=5)
        
        btn_cancelar = tk.Button(frame_botones, text="Cancelar",
                                command=dialog.destroy,
                                font=("Arial", 10),
                                bg="#95a5a6", fg=self.fg_blanco,
                                padx=20, pady=8, cursor="hand2")
        btn_cancelar.pack(side=tk.LEFT, padx=5)
    
    def menu_contextual(self, event):
        """Menú contextual para opciones de delegado"""
        seleccion = self.tabla_delegados.selection()
        if not seleccion:
            return
        
        item = seleccion[0]
        valores = self.tabla_delegados.item(item)["values"]
        usuario = valores[0] if valores else None
        
        if not usuario:
            return
        
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Cambiar Contraseña", 
                        command=lambda: self.cambiar_contrasena(usuario))
        menu.add_command(label="Eliminar Delegado",
                        command=lambda: self.eliminar_delegado_confirma(usuario))
        
        menu.post(event.x_root, event.y_root)
    
    def cambiar_contrasena(self, usuario):
        """Cambia la contraseña de un delegado"""
        nueva_pass = simpledialog.askstring("Cambiar Contraseña",
                                           f"Ingrese nueva contraseña para '{usuario}':",
                                           show="*")
        
        if nueva_pass is None:
            return
        
        if len(nueva_pass) < 6:
            messagebox.showerror("Error", "Contraseña muy corta (mín 6 caracteres)")
            return
        
        try:
            resultado = cambiar_contrasena_delegado(usuario, nueva_pass)
            if resultado["exito"]:
                messagebox.showinfo("Éxito", f"Contraseña actualizada para '{usuario}'")
                registrar_operacion(
                    tipo="CAMBIAR_PASSWORD",
                    accion="Contraseña de delegado actualizada",
                    detalles={"delegado": usuario, "admin": self.usuario_actual},
                    usuario=self.usuario_actual
                )
            else:
                messagebox.showerror("Error", resultado["mensaje"])
        except Exception as e:
            messagebox.showerror("Error", f"Error al cambiar contraseña:\n{str(e)}")
    
    def eliminar_delegado_confirma(self, usuario):
        """Solicita confirmación para eliminar delegado"""
        if messagebox.askyesno("Confirmar Eliminación",
                              f"¿Eliminar delegado '{usuario}'?\nEsta acción no se puede deshacer."):
            try:
                resultado = eliminar_delegado(usuario)
                if resultado["exito"]:
                    messagebox.showinfo("Éxito", f"Delegado '{usuario}' eliminado")
                    registrar_operacion(
                        tipo="ELIMINAR_DELEGADO",
                        accion="Delegado eliminado",
                        detalles={"delegado": usuario, "admin": self.usuario_actual},
                        usuario=self.usuario_actual
                    )
                    self.refrescar_lista()
                else:
                    messagebox.showerror("Error", resultado["mensaje"])
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar delegado:\n{str(e)}")
    
    def cerrar_sesion(self):
        """Cierra la sesión del administrador"""
        self.autenticado = False
        self.usuario_actual = None
        registrar_operacion(
            tipo="LOGOUT_ADMIN",
            accion="Administrador cerró sesión",
            detalles={},
            usuario="admin"
        )
        self.mostrar_login()
