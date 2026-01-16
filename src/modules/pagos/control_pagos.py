import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from datetime import datetime
import subprocess
import sys
import time
import threading

# Configurar path para imports cuando se ejecuta directamente
if __name__ == "__main__":
    # Agregar la raíz del proyecto al path
    proyecto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    if proyecto_raiz not in sys.path:
        sys.path.insert(0, proyecto_raiz)

from src.core.logger import registrar_operacion, registrar_error, registrar_transaccion
from src.config import TEMAS, TAMAÑOS_LETRA
from src.core.validadores import validar_nombre, validar_monto, ErrorValidacion
from src.tools.exportador import ExportadorExcel
from src.tools.backups import GestorBackups
from src.modules.historial.historial import GestorHistorial
from src.ui.tema_moderno import FUENTES, FUENTES_DISPLAY, ESPACIADO, ICONOS
from src.ui.estilos_globales import TEMA_GLOBAL
from src.ui.ui_moderna import BarraSuperior, PanelModerno, BotonModerno
from src.ui.buscador import BuscadorAvanzado
from src.modules.pagos.pagos_seguridad import GestorSeguridad
from src.core.gestor_datos_global import obtener_gestor
from src.modules.pagos.pagos_dialogos import (
    DialogoRegistrarPago, 
    DialogoAgregarPersona, 
    DialogoEditarPersona,
    DialogoNuevaCooperacion,
    DialogoEditarCooperacion,
    DialogoVerHistorial
)
from src.modules.pagos.pagos_barra_estado import BarraEstadoModerna
from src.modules.pagos.pagos_tooltips import TooltipModerno
from src.modules.pagos.pagos_confirmaciones import ConfirmacionMejorada

class SistemaControlPagos:
    # Los temas y tamaños ahora vienen de config.py

    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Control de Pagos - Proyectos Comunitarios")
        # No usar 'zoomed' - cambiado a tamaño fijo
        self.root.geometry("1400x800")
        # Centrar ventana
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f"1400x800+{x}+{y}")

        # Configuración visual proveniente de config.py y tema moderno
        self.TEMAS = TEMAS
        self.TAMAÑOS_LETRA = TAMAÑOS_LETRA
        self.tema_global = TEMA_GLOBAL
        self.style = ttk.Style()
        # Accesibilidad
        self.tamaño_actual = tk.StringVar(value='normal')
        
        # Datos - inicializar ANTES de gestores
        self.cooperaciones = []
        self.coop_activa_id = None
        self.cooperacion_actual = None
        self.personas = []
        self.monto_cooperacion = 100.0
        self.proyecto_actual = "Cooperación General"
        self.cooperacion_actual = "Cooperación General"
        self.coop_activa_id = None
        self.mostrar_total = False
        self.password_hash = None
        self.fila_animada = None
        self.guardado_pendiente = None
        self.usuario_actual = None
        self.gestor_auth = None
        self.tree_persona_map = {}
        self.permisos_rol = {}
        self.barra_superior = None
        # BUGFIX: Inicializar variables UI temprano para evitar AttributeError
        self.monto_var = tk.DoubleVar(value=300.0)
        self.proyecto_var = tk.StringVar(value="Cooperación General")
        # BUGFIX TCL: Inicializar afterID para evitar comandos inválidos
        self._after_id_barra = None
        
        # Flag para inicialización asíncrona
        self._inicializacion_completada = False
        
        # === INICIALIZAR BD Y GESTORES ===
        from src.core.base_datos_sqlite import obtener_bd
        self.bd = obtener_bd()
        
        # Cargar cooperaciones desde BD
        self._cargar_cooperaciones_bd()
        
        self.gestor = obtener_gestor()  # Gestor centralizado
        self.gestor_seguridad = GestorSeguridad()
        self.gestor_historial = GestorHistorial(id_cooperacion='general')
        self.buscador = BuscadorAvanzado()
        self.gestor_backups = GestorBackups()
        
        # Vincular eventos de cambio
        self.tamaño_actual.trace('w', self.aplicar_tamaño)

        # Configurar estilos iniciales
        self.configurar_estilos()
        
        self.nombre_visible = tk.BooleanVar(value=True)
        self.folio_visible = tk.BooleanVar(value=True)
        self.cifras_visibles = True  # Para ocultar/mostrar cifras sensibles
        
        # Barra de estado
        self.barra_estado = None
        self.cambios_pendientes = 0
        
        # Timer para búsqueda con debounce
        self._timer_busqueda = None
        
        # Variables para ordenamiento (MEJORA 4)
        self.columna_ordenamiento = None
        self.orden_ascendente = True
        self.habilitar_ordenamiento_var = tk.BooleanVar(value=False)
        
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
    
    def set_usuario(self, usuario, gestor_auth):
        """Configurar usuario autenticado"""
        self.usuario_actual = usuario
        self.gestor_auth = gestor_auth
        self.permisos_rol = self.gestor_auth.ROLES if self.gestor_auth else {}
        registrar_operacion('LOGIN', 'Usuario inició sesión', 
            {'usuario': usuario['nombre'], 'rol': usuario['rol']}, usuario['nombre'])
        
        # Aplicar cooperación activa
        self.aplicar_cooperacion_activa()
        
        # Configurar la interfaz con el usuario establecido
        try:
            self.configurar_interfaz()
        except Exception as e:
            registrar_error('control_pagos', 'set_usuario', str(e))
            import traceback
            traceback.print_exc()
            raise

    def _tiene_permiso(self, permiso):
        """Verifica permisos según rol actual"""
        if not self.usuario_actual:
            return True  # fallback
        rol = self.usuario_actual.get('rol')
        if not rol or rol not in self.permisos_rol:
            return True
        permisos = self.permisos_rol[rol].get('permisos', [])
        if '*' in permisos or permiso in permisos:
            return True
        messagebox.showerror("Permisos", f"Tu rol no permite realizar esta acción ({permiso}).")
        return False
    
    def obtener_colores(self):
        """Obtener paleta de colores del tema global"""
        return self.tema_global

    def configurar_estilos(self):
        """Configura estilos ttk usando tema global claro"""
        colores = self.obtener_colores()
        base_bg = colores.get('bg_principal')
        base_fg = colores.get('fg_principal')
        secondary_bg = colores.get('bg_secundario')
        accent_primary = colores.get('accent_primary')
        accent_secondary = colores.get('accent_secondary')

        self.style.theme_use('clam')
        self.style.configure('TFrame', background=base_bg)
        self.style.configure('TLabelframe', background=secondary_bg, foreground=base_fg, font=FUENTES['subtitulo'])
        self.style.configure('TLabelframe.Label', background=secondary_bg, foreground=base_fg, font=FUENTES['subtitulo'])
        self.style.configure('TLabel', background=base_bg, foreground=base_fg, font=FUENTES['normal'])
        self.style.configure('TButton', background=accent_primary, foreground='#ffffff', padding=8, borderwidth=0, font=FUENTES['botones'])
        self.style.map('TButton', background=[('active', accent_secondary)], foreground=[('active', '#ffffff')])
        self.style.configure('TCheckbutton', background=base_bg, foreground=base_fg, font=FUENTES['normal'])
        self.style.configure('TEntry', fieldbackground=colores.get('input_bg', '#ffffff'), borderwidth=1)
        self.style.configure('Treeview', background=colores.get('bg_secundario'), fieldbackground=colores.get('bg_secundario'),
                             foreground=base_fg, borderwidth=0, rowheight=26, font=FUENTES['normal'])
        self.style.map('Treeview', background=[('selected', accent_primary)], foreground=[('selected', '#ffffff')])
        self.style.configure('Treeview.Heading', background=colores.get('bg_tertiary'), foreground=base_fg,
                             padding=8, font=FUENTES['subtitulo'], borderwidth=1, relief='flat')
    
    def obtener_tamaños(self):
        """Obtener tamaños de letra"""
        return self.TAMAÑOS_LETRA[self.tamaño_actual.get()]
    

    
    def aplicar_tamaño(self, *args):
        """Aplicar cambios de tamaño de letra inmediatamente"""
        if not hasattr(self, 'tree'):
            return  # Aún no se ha creado la interfaz
        
        tamaños = self.obtener_tamaños()
        
        # Actualizar fuentes de las etiquetas principales
        if hasattr(self, 'total_pagado_label'):
            self.total_pagado_label.config(font=('Arial', tamaños['titulo'], 'bold'))
        if hasattr(self, 'total_pendiente_label'):
            self.total_pendiente_label.config(font=('Arial', tamaños['grande'], 'bold'))
        if hasattr(self, 'personas_pagadas_label'):
            self.personas_pagadas_label.config(font=('Arial', tamaños['normal']))
        
        self.guardar_datos(mostrar_alerta=False)

    
    def hash_password(self, password):
        """Crear hash seguro de la contraseña con bcrypt"""
        return seguridad.hash_password(password).decode('utf-8')
    
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
        """Solicita contraseña del usuario actual para operaciones sensibles"""
        # Verificar que hay un usuario logueado
        if not self.usuario_actual:
            messagebox.showerror("Error", "No hay usuario autenticado")
            return False
        
        dialog = tk.Toplevel(self.root)
        dialog.title("🔒 Confirmar Identidad")
        dialog.geometry("450x300")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.configure(bg=self.tema_global.get('bg_principal', '#ffffff'))
        
        # Centrar ventana
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 225
        y = (dialog.winfo_screenheight() // 2) - 150
        dialog.geometry(f"450x300+{x}+{y}")
        
        # Header con icono
        header = tk.Frame(dialog, bg='#e67e22', height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="🔒", font=('Segoe UI', 32),
                bg='#e67e22', fg='#ffffff').pack(pady=15)
        
        # Contenido
        content = tk.Frame(dialog, bg=self.tema_global.get('bg_principal', '#ffffff'))
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=25)
        
        tk.Label(content, text="Confirmar tu Identidad", 
                font=('Arial', 13, 'bold'),
                bg=self.tema_global.get('bg_principal', '#ffffff'),
                fg=self.tema_global.get('fg_principal', '#333333')).pack(pady=(0, 5))
        
        # Mostrar usuario actual
        tk.Label(content, text=f"Usuario: {self.usuario_actual.get('nombre', self.usuario_actual.get('usuario', 'Desconocido'))}", 
                font=('Arial', 10, 'bold'),
                bg=self.tema_global.get('bg_principal', '#ffffff'),
                fg='#e67e22').pack(pady=(0, 5))
        
        tk.Label(content, text="Ingresa tu contraseña para confirmar:", 
                font=('Arial', 10),
                bg=self.tema_global.get('bg_principal', '#ffffff'),
                fg=self.tema_global.get('fg_secundario', '#666666')).pack(pady=(0, 15))
        
        # Campo de contraseña
        pass_frame = tk.Frame(content, bg=self.tema_global.get('bg_principal', '#ffffff'))
        pass_frame.pack(fill=tk.X, pady=(0, 20))
        
        pass_entry = tk.Entry(pass_frame, show="●", width=35, font=('Arial', 11),
                             bg=self.tema_global.get('input_bg', '#ffffff'),
                             fg=self.tema_global.get('fg_principal', '#333333'),
                             relief=tk.SOLID, bd=1, insertbackground='#e67e22')
        pass_entry.pack(ipady=8)
        
        resultado = {'success': False}
        
        def verificar(event=None):
            password = pass_entry.get()
            if not password:
                messagebox.showwarning("Advertencia", "Por favor ingrese la contraseña")
                pass_entry.focus()
                return
            
            try:
                # Verificar contraseña usando el sistema de autenticación
                import hashlib
                hash_ingresado = hashlib.sha256(password.encode()).hexdigest()
                
                # Obtener el nombre de usuario correcto del objeto usuario_actual
                # Puede estar en 'usuario' o 'nombre'
                nombre_usuario = self.usuario_actual.get('usuario') or self.usuario_actual.get('nombre')
                
                # Obtener datos del usuario desde la BD
                usuario_bd = self.bd.obtener_usuario(nombre_usuario)
                
                if not usuario_bd:
                    messagebox.showerror("Error", f"Usuario '{nombre_usuario}' no encontrado en la base de datos")
                    pass_entry.delete(0, tk.END)
                    pass_entry.focus()
                    return
                
                if hash_ingresado == usuario_bd['contraseña']:
                    resultado['success'] = True
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Contraseña incorrecta")
                    pass_entry.delete(0, tk.END)
                    pass_entry.focus()
            except Exception as e:
                registrar_error('control_pagos', 'solicitar_password', str(e))
                messagebox.showerror("Error", f"Error al verificar contraseña: {str(e)}")
                pass_entry.delete(0, tk.END)
                pass_entry.focus()
        
        # Botones
        btn_frame = tk.Frame(content, bg=self.tema_global.get('bg_principal', '#ffffff'))
        btn_frame.pack(fill=tk.X, pady=(0, 0))
        
        btn_verificar = tk.Button(btn_frame, text="✓ Verificar", command=verificar,
                                 bg='#e67e22', fg='#ffffff',
                                 font=('Arial', 11, 'bold'), padx=30, pady=10,
                                 relief=tk.FLAT, bd=0, cursor='hand2',
                                 activebackground='#d35400')
        btn_verificar.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        btn_cancelar = tk.Button(btn_frame, text="✕ Cancelar", command=dialog.destroy,
                                bg=self.tema_global.get('bg_secundario', '#f0f0f0'),
                                fg=self.tema_global.get('fg_principal', '#333333'),
                                font=('Arial', 11), padx=30, pady=10,
                                relief=tk.FLAT, bd=1, cursor='hand2',
                                activebackground='#e0e0e0')
        btn_cancelar.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Efectos hover
        def on_enter_verificar(e):
            btn_verificar.config(bg='#d35400')
        
        def on_leave_verificar(e):
            btn_verificar.config(bg='#e67e22')
        
        def on_enter_cancelar(e):
            btn_cancelar.config(bg='#e0e0e0')
        
        def on_leave_cancelar(e):
            btn_cancelar.config(bg=self.tema_global.get('bg_secundario', '#f0f0f0'))
        
        btn_verificar.bind("<Enter>", on_enter_verificar)
        btn_verificar.bind("<Leave>", on_leave_verificar)
        btn_cancelar.bind("<Enter>", on_enter_cancelar)
        btn_cancelar.bind("<Leave>", on_leave_cancelar)
        
        # Enter para verificar, Escape para cancelar
        dialog.bind("<Return>", verificar)
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        pass_entry.focus()
        
        dialog.wait_window()
        return resultado['success']
        btn_frame = tk.Frame(content, bg=self.tema_global.get('bg_principal', '#ffffff'))
        btn_frame.pack(fill=tk.X, pady=(0, 0))
        
        btn_verificar = tk.Button(btn_frame, text="✓ Verificar", command=verificar,
                                 bg='#e67e22', fg='#ffffff',
                                 font=('Arial', 11, 'bold'), padx=30, pady=10,
                                 relief=tk.FLAT, bd=0, cursor='hand2',
                                 activebackground='#d35400')
        btn_verificar.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        btn_cancelar = tk.Button(btn_frame, text="✕ Cancelar", command=dialog.destroy,
                                bg=self.tema_global.get('bg_secundario', '#f0f0f0'),
                                fg=self.tema_global.get('fg_principal', '#333333'),
                                font=('Arial', 11), padx=30, pady=10,
                                relief=tk.FLAT, bd=1, cursor='hand2',
                                activebackground='#e0e0e0')
        btn_cancelar.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Efectos hover
        def on_enter_verificar(e):
            btn_verificar.config(bg='#d35400')
        
        def on_leave_verificar(e):
            btn_verificar.config(bg='#e67e22')
        
        def on_enter_cancelar(e):
            btn_cancelar.config(bg='#e0e0e0')
        
        def on_leave_cancelar(e):
            btn_cancelar.config(bg=self.tema_global.get('bg_secundario', '#f0f0f0'))
        
        btn_verificar.bind("<Enter>", on_enter_verificar)
        btn_verificar.bind("<Leave>", on_leave_verificar)
        btn_cancelar.bind("<Enter>", on_enter_cancelar)
        btn_cancelar.bind("<Leave>", on_leave_cancelar)
        
        # Enter para verificar, Escape para cancelar
        dialog.bind("<Return>", verificar)
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        pass_entry.focus()
        
        dialog.wait_window()
        return resultado['success']

    # ====== GESTION DE COOPERACIONES ======
    def obtener_cooperacion_activa(self):
        """Obtiene la cooperación activa desde la lista en memoria (de BD)"""
        if self.coop_activa_id:
            for coop in self.cooperaciones:
                if coop.get('id') == self.coop_activa_id:
                    return coop
        
        # Si no encuentra, retornar la primera
        return self.cooperaciones[0] if self.cooperaciones else None

    def _cargar_cooperaciones_bd(self):
        """Carga cooperaciones desde BD SQLite"""
        try:
            cursor = self.bd.conexion.cursor()
            
            # Obtener todas las cooperaciones
            cursor.execute('''
                SELECT id, nombre, proyecto, monto_cooperacion, activa, fecha_creacion
                FROM cooperaciones
                ORDER BY fecha_creacion DESC
            ''')
            
            self.cooperaciones = []
            cooperacion_activa = None
            
            for coop_id, nombre, proyecto, monto, activa, fecha_creacion in cursor.fetchall():
                # Obtener personas de esta cooperación
                personas = self._obtener_personas_coop_bd(coop_id)
                
                coop = {
                    'id': coop_id,
                    'nombre': nombre,
                    'proyecto': proyecto,
                    'monto_cooperacion': monto,
                    'personas': personas,
                    'activa': bool(activa),
                    'fecha_creacion': fecha_creacion
                }
                self.cooperaciones.append(coop)
                
                if bool(activa):
                    cooperacion_activa = coop
                    self.coop_activa_id = coop_id
            
            # Si no hay cooperación activa pero existen, activar la primera
            if not cooperacion_activa and self.cooperaciones:
                self.coop_activa_id = self.cooperaciones[0]['id']
                self.personas = self.cooperaciones[0]['personas']
                self.proyecto_actual = self.cooperaciones[0]['proyecto']
                self.cooperacion_actual = self.cooperaciones[0]['nombre']
                self.monto_cooperacion = self.cooperaciones[0]['monto_cooperacion']
            elif cooperacion_activa:
                self.personas = cooperacion_activa['personas']
                self.proyecto_actual = cooperacion_activa['proyecto']
                self.cooperacion_actual = cooperacion_activa['nombre']
                self.monto_cooperacion = cooperacion_activa['monto_cooperacion']
            else:
                self.personas = []
                self.monto_cooperacion = 300.0
        
        except Exception as e:
            print(f"Error cargando cooperaciones desde BD: {e}")
            self.cooperaciones = []
            self.personas = []
            self.monto_cooperacion = 300.0
    
    def _obtener_personas_coop_bd(self, coop_id):
        """Obtiene todas las personas de una cooperación desde BD"""
        try:
            cursor = self.bd.conexion.cursor()
            
            cursor.execute('''
                SELECT pc.id, pc.habitante_id, h.folio, h.nombre, 
                       pc.monto_esperado, pc.estado, pc.notas, pc.fecha_agregado
                FROM personas_cooperacion pc
                LEFT JOIN habitantes h ON pc.habitante_id = h.id
                WHERE pc.cooperacion_id = ?
                ORDER BY h.nombre
            ''', (coop_id,))
            
            personas = []
            for pc_id, habitante_id, folio, nombre, monto_esp, estado, notas, fecha_agg in cursor.fetchall():
                
                # Obtener pagos de esta persona
                pagos = self._obtener_pagos_persona_bd(pc_id)
                
                persona = {
                    'id': habitante_id,
                    'folio': folio or 'SIN-FOLIO',
                    'nombre': nombre or 'SIN-NOMBRE',
                    'monto_esperado': monto_esp,
                    'monto': monto_esp,
                    'pagos': pagos,
                    'notas': notas or '',
                    'estado': estado,
                    'persona_coop_id': pc_id
                }
                personas.append(persona)
            
            return personas
        
        except Exception as e:
            print(f"Error obteniendo personas: {e}")
            return []
    
    def _obtener_pagos_persona_bd(self, persona_coop_id):
        """Obtiene todos los pagos de una persona desde BD"""
        try:
            cursor = self.bd.conexion.cursor()
            
            cursor.execute('''
                SELECT id, monto, fecha_pago, hora_pago, concepto, anulado
                FROM pagos_coop
                WHERE persona_coop_id = ?
                ORDER BY fecha_pago DESC
            ''', (persona_coop_id,))
            
            pagos = []
            for pago_id, monto, fecha, hora, concepto, anulado in cursor.fetchall():
                pagos.append({
                    'id': pago_id,
                    'monto': monto,
                    'fecha': fecha,
                    'hora': hora or '00:00',
                    'concepto': concepto or 'Pago cooperación',
                    'anulado': bool(anulado)
                })
            
            return pagos
        
        except Exception as e:
            print(f"Error obteniendo pagos: {e}")
            return []
    
    def aplicar_cooperacion_activa(self):
        """Aplica cooperación activa desde BD"""
        if not self.cooperaciones:
            return
        
        coop = next((c for c in self.cooperaciones if c['id'] == self.coop_activa_id), None)
        if not coop:
            coop = self.cooperaciones[0]
            self.coop_activa_id = coop['id']
        
        self.personas = coop.get('personas', [])
        self.monto_cooperacion = coop.get('monto_cooperacion', 300.0)
        self.proyecto_actual = coop.get('proyecto', 'Cooperación General')
        self.cooperacion_actual = coop.get('nombre', 'Cooperación')
        
        # Sincronizar StringVars
        self.proyecto_var.set(self.proyecto_actual)
        self.monto_var.set(self.monto_cooperacion)

    def refrescar_selector_cooperacion(self, seleccionar_activa=True):
        """BUGFIX: Refrescar selector y disparar cambio de cooperación manualmente si es necesario"""
        nombres = [c.get('nombre', 'Sin nombre') for c in self.cooperaciones]
        self.coop_selector['values'] = nombres
        if seleccionar_activa:
            activa = self.obtener_cooperacion_activa()
            if activa and activa.get('nombre') in nombres:
                idx = nombres.index(activa['nombre'])
                # BUGFIX: No disparar evento automáticamente, hacerlo manualmente después
                self.coop_selector.current(idx)

    def on_cambio_cooperacion(self, event=None):
        """BUGFIX: Cambiar a una cooperación diferente - sincronización COMPLETA"""
        # BUGFIX: Obtener el nombre del selector
        nombre = self.coop_selector.get()
        
        # Si está vacío, ignorar
        if not nombre or nombre.strip() == '':
            return
        
        # Buscar cooperación por nombre
        destino = next((c for c in self.cooperaciones if c.get('nombre') == nombre), None)
        if not destino:
            registrar_error('control_pagos', 'cambiar_cooperacion', f'No se encontró cooperación: {nombre}')
            return
        
        # BUGFIX: Solo cambiar si es diferente de la actual
        if self.coop_activa_id == destino.get('id'):
            return
        
        self.coop_activa_id = destino.get('id')
        
        # Sincronización COMPLETA en orden correcto:
        # 1. Aplicar datos de cooperación (actualiza personas, monto, proyecto, historial)
        self.aplicar_cooperacion_activa()
        
        # 2. Refrescar UI (actualiza labels con nuevos valores)
        self.refrescar_interfaz_cooperacion()
        
        # 3. Actualizar tabla con nuevas personas
        self.actualizar_tabla()
        
        # 4. Actualizar totales con nuevos cálculos
        self.actualizar_totales()
        
        # 5. Actualizar contador de resultados
        self._actualizar_contador_resultados()
        
        # 6. Sincronizar con censo si es necesario
        self.sincronizar_coop_con_censo(mostrar_mensaje=False)
        
        # 7. Guardar cambios
        self.guardar_datos(mostrar_alerta=False, inmediato=True)
    
    def nueva_cooperacion(self):
        """BUGFIX: Crear nueva cooperación con sincronización completa"""
        def on_cooperacion_creada(nueva):
            self.cooperaciones.append(nueva)
            self.coop_activa_id = nueva['id']
            self.proyecto_actual = nueva['proyecto']
            self.monto_cooperacion = nueva['monto_cooperacion']
            
            # BUGFIX: Aplicar cambia automáticamente el historial y sincroniza
            self.aplicar_cooperacion_activa()
            self.refrescar_selector_cooperacion()
            self.refrescar_interfaz_cooperacion()
            self.sincronizar_coop_con_censo(mostrar_mensaje=False)
            self.actualizar_tabla()
            self.actualizar_totales()
            self.guardar_datos(mostrar_alerta=False, inmediato=True)
        
        DialogoNuevaCooperacion.mostrar(
            parent=self.root,
            monto_default=self.monto_cooperacion,
            proyecto_default=self.proyecto_var.get(),
            cooperaciones_lista=self.cooperaciones,
            gestor_historial=self.gestor_historial,
            usuario_actual=self.usuario_actual,
            callback_ok=on_cooperacion_creada,
            tema_global=self.tema_global
        )

    def editar_cooperacion(self):
        """BUGFIX: Editar cooperación con actualización completa"""
        coop = self.obtener_cooperacion_activa()
        if not coop:
            messagebox.showerror("Error", "No hay cooperación activa")
            return
        
        def on_cooperacion_editada(cooperacion, cambios):
            # BUGFIX: Actualizar la cooperación en la lista
            idx = next((i for i, c in enumerate(self.cooperaciones) if c['id'] == cooperacion['id']), None)
            if idx is not None:
                self.cooperaciones[idx] = cooperacion
            
            self.monto_cooperacion = cooperacion['monto_cooperacion']
            self.proyecto_actual = cooperacion['proyecto']
            self.cooperacion_actual = cooperacion.get('nombre', 'Cooperación')
            
            # BUGFIX: Reaplica para actualizar historial y UI
            self.aplicar_cooperacion_activa()
            self.refrescar_selector_cooperacion()
            self.refrescar_interfaz_cooperacion()
            self.actualizar_tabla()
            self.actualizar_totales()
            self.guardar_datos(mostrar_alerta=False, inmediato=True)
        
        DialogoEditarCooperacion.mostrar(
            parent=self.root,
            cooperacion=coop,
            cooperaciones_lista=self.cooperaciones,
            gestor_historial=self.gestor_historial,
            usuario_actual=self.usuario_actual,
            callback_ok=on_cooperacion_editada,
            tema_global=self.tema_global
        )

    def sincronizar_coop_con_censo(self, mostrar_mensaje=True):
        coop = self.obtener_cooperacion_activa()
        if not coop:
            messagebox.showerror("Error", "No hay cooperacion activa")
            return
        agregados = 0
        try:
            # Obtener habitantes desde gestor centralizado
            habitantes = self.gestor.obtener_habitantes(incluir_inactivos=True)
            total_censo = len(habitantes)
            
            nombres_censo = {h.get('nombre', '').strip().lower() for h in habitantes}
            personas_no_en_censo = [p for p in coop.get('personas', []) 
                                   if p.get('nombre', '').strip().lower() not in nombres_censo]
            
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
            self.guardar_datos(mostrar_alerta=False)
            
            if mostrar_mensaje:
                mensaje = f"Sincronización con Censo\n\n"
                mensaje += f"Habitantes en censo: {total_censo}\n"
                mensaje += f"Personas en cooperacion: {len(self.personas)}\n"
                mensaje += f"Agregados desde censo: {agregados}\n"
                
                if personas_no_en_censo:
                    mensaje += f"\nAdvertencia: {len(personas_no_en_censo)} personas en cooperacion no estan en el censo:\n\n"
                    for p in personas_no_en_censo[:5]:
                        mensaje += f"  - {p.get('nombre', 'Sin nombre')}\n"
                    if len(personas_no_en_censo) > 5:
                        mensaje += f"  ... y {len(personas_no_en_censo) - 5} mas\n"
                    mensaje += f"\nDeseas eliminar estas personas de la cooperacion?"
                    
                    if messagebox.askyesno("Sincronizacion", mensaje):
                        coop['personas'] = [p for p in coop['personas'] 
                                          if p.get('nombre', '').strip().lower() in nombres_censo]
                        self.personas = coop['personas']
                        self.actualizar_tabla()
                        self.actualizar_totales()
                        self.guardar_datos(mostrar_alerta=False)
                        messagebox.showinfo("Exito", f"Se eliminaron {len(personas_no_en_censo)} personas.\nTotal actual: {len(self.personas)}")
                else:
                    if agregados > 0:
                        messagebox.showinfo("Sincronizacion", mensaje + "\nSincronizacion completada correctamente")
                    else:
                        messagebox.showinfo("Sincronizacion", mensaje + "\nYa esta sincronizado")
        except Exception as e:
            if mostrar_mensaje:
                messagebox.showerror("Error", f"No se pudo sincronizar con el censo: {e}")
    
    def corregir_folios(self):
        """Detecta y corrige folios duplicados sincronizando con el censo"""
        if not self._tiene_permiso('editar'):
            return
            
        from src.core.utilidades import detectar_folios_duplicados, corregir_folios_duplicados
        
        if not self.personas:
            messagebox.showwarning("Advertencia", "No hay personas en la cooperación actual")
            return
        
        # Detectar duplicados
        duplicados = detectar_folios_duplicados(self.personas)
        
        if not duplicados:
            messagebox.showinfo("✓ Sin Problemas", 
                f"No se encontraron folios duplicados\n\n"
                f"Total personas revisadas: {len(self.personas)}")
            return
        
        # Mostrar información de duplicados
        mensaje_duplicados = "⚠️ FOLIOS DUPLICADOS ENCONTRADOS\n\n"
        total_afectados = 0
        for folio, nombres in duplicados.items():
            mensaje_duplicados += f"Folio {folio} ({len(nombres)} personas):\n"
            for nombre in nombres:
                mensaje_duplicados += f"  • {nombre}\n"
                total_afectados += 1
            mensaje_duplicados += "\n"
        
        mensaje_duplicados += f"Total de personas afectadas: {total_afectados}\n\n"
        mensaje_duplicados += "¿Desea corregir automáticamente sincronizando con el censo?"
        
        if not messagebox.askyesno("Folios Duplicados Detectados", mensaje_duplicados):
            return
        
        # Corregir usando gestor centralizado
        gestor = obtener_gestor()
        resultado = gestor.sincronizar_folios(self.personas)
        
        if resultado['exito']:
            # Guardar cambios inmediatamente
            self.guardar_datos(mostrar_alerta=False, inmediato=True)
            self.actualizar_tabla()
            
            mensaje = f"✓ CORRECCIÓN COMPLETADA\n\n"
            mensaje += f"{resultado['mensaje']}\n\n"
            mensaje += f"Duplicados encontrados: {resultado.get('duplicados_encontrados', 0)}\n"
            mensaje += f"Folios corregidos: {resultado.get('corregidos', 0)}"
            
            if resultado.get('errores'):
                mensaje += f"\n⚠️ Errores encontrados: {len(resultado['errores'])}"
            
            # Registrar operación
            registrar_operacion('CORREGIR_FOLIOS', 'Folios duplicados corregidos', {
                'duplicados': resultado.get('duplicados_encontrados', 0),
                'corregidos': resultado.get('corregidos', 0),
                'cooperacion': self.cooperacion_actual
            }, self.usuario_actual['nombre'] if self.usuario_actual else 'Sistema')
            
            messagebox.showinfo("Corrección Completada", mensaje)
        else:
            messagebox.showerror("Error", f"Error al corregir folios:\n{resultado.get('error', 'Desconocido')}")

    def refrescar_interfaz_cooperacion(self):
        """BUGFIX: Actualiza todos los elementos UI cuando cambia cooperación"""
        coop = self.obtener_cooperacion_activa()
        if not coop:
            return
        
        # Actualizar personas y datos
        self.personas = coop.setdefault('personas', [])
        self.monto_cooperacion = coop.get('monto_cooperacion', self.monto_cooperacion)
        self.proyecto_actual = coop.get('proyecto', self.proyecto_actual)
        self.cooperacion_actual = coop.get('nombre', 'Cooperación')
        
        # BUGFIX: Actualizar TODOS los widgets de la UI
        if hasattr(self, 'monto_var'):
            self.monto_var.set(self.monto_cooperacion)
        if hasattr(self, 'proyecto_var'):
            self.proyecto_var.set(self.proyecto_actual)
        if hasattr(self, 'total_personas_label'):
            self.total_personas_label.config(text=str(len(self.personas)))
        
        # Actualizar título si existe
        if hasattr(self, 'titulo_coop_label'):
            self.titulo_coop_label.config(text=f"📋 {self.cooperacion_actual}")
        
        
    def configurar_interfaz(self):
        # Frame principal con mejor espaciado
        colores = self.obtener_colores()
        tema_visual = self.tema_global
        
        self.root.configure(bg=tema_visual['bg_principal'])
        
        main_frame = tk.Frame(self.root, bg=tema_visual['bg_principal'])
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=0, pady=0)
        
        # Configurar grid - IMPORTANTE: permitir que todo se expanda
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        # main_frame tiene tres filas: 0 para barra superior, 1 para contenido, 2 para barra estado
        main_frame.rowconfigure(0, weight=0)  # Barra superior (altura fija)
        main_frame.rowconfigure(1, weight=1)  # Contenedor principal (expandible)
        main_frame.rowconfigure(2, weight=0)  # Barra de estado (altura fija)
        
        tamaños = self.obtener_tamaños()
        
        # ===== BARRA SUPERIOR MODERNA =====
        print("[CONFIGURAR_INTERFAZ] Creando BarraSuperior...")
        if not self.barra_superior:
            from src.ui.ui_moderna import BarraSuperior
            # Callback vacío ya que removimos cambio de tema
            self.barra_superior = BarraSuperior(main_frame, self.usuario_actual, lambda: None)
            self.barra_superior.grid(row=0, column=0, sticky=(tk.W, tk.E))
            print("[CONFIGURAR_INTERFAZ] BarraSuperior creada")
        
        # ===== CONTENEDOR PRINCIPAL CON PADDING =====
        scroll_container = tk.Frame(main_frame, bg=tema_visual['bg_principal'])
        scroll_container.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), 
                              padx=ESPACIADO['lg'], pady=ESPACIADO['lg'])
        scroll_container.columnconfigure(0, weight=1)
        scroll_container.rowconfigure(0, weight=1)

        canvas = tk.Canvas(scroll_container, bg=tema_visual['bg_principal'], highlightthickness=0)
        canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar = ttk.Scrollbar(scroll_container, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        canvas.configure(yscrollcommand=scrollbar.set)

        content_container = tk.Frame(canvas, bg=tema_visual['bg_principal'])
        self.content_container = content_container  # Guardar referencia para toggle_fullscreen_tabla
        window_id = canvas.create_window((0, 0), window=content_container, anchor='nw')

        # Ajuste de scroll para ver toda la pantalla y mantener ancho completo
        content_container.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(window_id, width=e.width))
        
        # Scroll del canvas solo cuando el cursor está sobre él
        def _on_canvas_scroll(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        canvas.bind('<MouseWheel>', _on_canvas_scroll)

        content_container.columnconfigure(0, weight=1)
        content_container.columnconfigure(1, weight=1)  # Segunda columna para diseño lado a lado
        # Configurar todas las filas para que se expandan correctamente
        content_container.rowconfigure(0, weight=0)  # Info panel
        content_container.rowconfigure(1, weight=0)  # Acciones
        content_container.rowconfigure(2, weight=1)  # Tabla panel (expandible)
        content_container.rowconfigure(3, weight=0)  # Fila libre/reservada
        
        # ===== PANEL DE INFORMACIÓN (CARD MODERNO COLAPSABLE) =====
        from src.ui.ui_moderna import PanelModerno
        self.info_panel = PanelModerno(content_container, titulo="▼ 📊 Información del Proyecto", tema=tema_visual)
        self.info_panel.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, ESPACIADO['md']))
        # Hacer el título clickeable para colapsar
        self.info_panel.titulo_label.bind('<Button-1>', lambda e: self.toggle_panel(self.info_panel))
        self.info_panel.titulo_label.config(cursor='hand2')
        
        # ===== PANEL DE ACCIONES (CARD MODERNO COLAPSABLE) =====
        # Al integrar la búsqueda en el panel de la lista, este panel ocupa todo el ancho
        self.actions_panel = PanelModerno(content_container, titulo="▼ ⚡ Acciones Rápidas", tema=tema_visual)
        self.actions_panel.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, ESPACIADO['md']))
        # Hacer el título clickeable para colapsar
        self.actions_panel.titulo_label.bind('<Button-1>', lambda e: self.toggle_panel(self.actions_panel))
        self.actions_panel.titulo_label.config(cursor='hand2')
        info_content = self.info_panel.content_frame
        info_content.columnconfigure(1, weight=1)
        info_content.columnconfigure(3, weight=1)
        
        # Fila 1: Proyecto y Fecha
        tk.Label(info_content, text="Proyecto:", font=FUENTES['normal'],
                bg=tema_visual.get('card_bg', tema_visual['bg_secundario']),
                fg=tema_visual['fg_secundario']).grid(row=0, column=0, sticky=tk.W, padx=(0, ESPACIADO['sm']))
        
        self.proyecto_var = tk.StringVar(value="Proyecto Comunitario 2026")
        proyecto_entry = tk.Entry(info_content, textvariable=self.proyecto_var, font=FUENTES['normal'],
                                  bg=tema_visual['input_bg'], fg=tema_visual['fg_principal'],
                                  relief=tk.FLAT, bd=1, width=40)
        proyecto_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, ESPACIADO['lg']))
        
        tk.Label(info_content, text="Fecha:", font=FUENTES['normal'],
                bg=tema_visual.get('card_bg', tema_visual['bg_secundario']),
                fg=tema_visual['fg_secundario']).grid(row=0, column=2, sticky=tk.W, padx=(0, ESPACIADO['sm']))
        
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        tk.Label(info_content, text=fecha_actual, font=FUENTES['subtitulo'],
                bg=tema_visual.get('card_bg', tema_visual['bg_secundario']),
                fg=tema_visual['accent_primary']).grid(row=0, column=3, sticky=tk.W)
        
        # Fila 2: Cooperación activa
        tk.Label(info_content, text="Cooperación:", font=FUENTES['normal'],
                bg=tema_visual.get('card_bg', tema_visual['bg_secundario']),
                fg=tema_visual['fg_secundario']).grid(row=1, column=0, sticky=tk.W, 
                                                     padx=(0, ESPACIADO['sm']), pady=(ESPACIADO['md'], 0))
        
        coop_frame = tk.Frame(info_content, bg=tema_visual.get('card_bg', tema_visual['bg_secundario']))
        coop_frame.grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=(ESPACIADO['md'], 0))
        
        self.coop_selector = ttk.Combobox(coop_frame, state="readonly", width=35, font=FUENTES['normal'])
        self.coop_selector.pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        self.coop_selector.bind("<<ComboboxSelected>>", self.on_cambio_cooperacion)
        
        from src.ui.ui_moderna import BotonModerno
        BotonModerno(coop_frame, f"{ICONOS['agregar']} Nueva", tema=tema_visual, tipo='success',
                    command=self.nueva_cooperacion).pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        BotonModerno(coop_frame, f"{ICONOS['editar']} Editar", tema=tema_visual, tipo='ghost',
                    command=self.editar_cooperacion).pack(side=tk.LEFT)
        
        # Fila 3: Monto y estadísticas
        stats_frame = tk.Frame(info_content, bg=tema_visual.get('card_bg', tema_visual['bg_secundario']))
        stats_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(ESPACIADO['lg'], 0))
        
        # Monto
        monto_container = tk.Frame(stats_frame, bg=tema_visual.get('card_bg', tema_visual['bg_secundario']))
        monto_container.pack(side=tk.LEFT, padx=(0, ESPACIADO['xl']))
        
        tk.Label(monto_container, text="Monto de Cooperación:", font=FUENTES['pequeño'],
                bg=tema_visual.get('card_bg', tema_visual['bg_secundario']),
                fg=tema_visual['fg_secundario']).pack(anchor=tk.W)
        
        monto_input_frame = tk.Frame(monto_container, bg=tema_visual.get('card_bg', tema_visual['bg_secundario']))
        monto_input_frame.pack(anchor=tk.W, pady=(ESPACIADO['xs'], 0))
        
        self.monto_var = tk.DoubleVar(value=self.monto_cooperacion)
        tk.Label(monto_input_frame, text="$", font=FUENTES['subtitulo'],
                bg=tema_visual.get('card_bg', tema_visual['bg_secundario']),
                fg=tema_visual['accent_primary']).pack(side=tk.LEFT)
        
        monto_entry = tk.Entry(monto_input_frame, textvariable=self.monto_var, font=FUENTES['subtitulo'],
                              bg=tema_visual['input_bg'], fg=tema_visual['fg_principal'],
                              relief=tk.FLAT, bd=1, width=12)
        monto_entry.pack(side=tk.LEFT, padx=(ESPACIADO['xs'], ESPACIADO['sm']))
        
        BotonModerno(monto_input_frame, "Actualizar", tema=tema_visual, tipo='primary',
                    command=self.actualizar_monto).pack(side=tk.LEFT)
        
        # Total personas
        personas_container = tk.Frame(stats_frame, bg=tema_visual.get('card_bg', tema_visual['bg_secundario']))
        personas_container.pack(side=tk.LEFT, padx=(0, ESPACIADO['xl']))
        
        tk.Label(personas_container, text="Total Personas", font=FUENTES['pequeño'],
                bg=tema_visual.get('card_bg', tema_visual['bg_secundario']),
                fg=tema_visual['fg_secundario']).pack(anchor=tk.W)
        
        self.total_personas_label = tk.Label(personas_container, text=str(len(self.personas)), 
                                            font=FUENTES_DISPLAY['hero'],
                                            bg=tema_visual.get('card_bg', tema_visual['bg_secundario']),
                                            fg=tema_visual['accent_primary'])
        self.total_personas_label.pack(anchor=tk.W)
        
        # Total pagado
        pagado_container = tk.Frame(stats_frame, bg=tema_visual.get('card_bg', tema_visual['bg_secundario']))
        pagado_container.pack(side=tk.LEFT, padx=(0, ESPACIADO['xl']))
        
        tk.Label(pagado_container, text="Total Recaudado", font=FUENTES['pequeño'],
                bg=tema_visual.get('card_bg', tema_visual['bg_secundario']),
                fg=tema_visual['fg_secundario']).pack(anchor=tk.W)
        
        self.total_pagado_label = tk.Label(pagado_container, text="$0.00", 
                                           font=FUENTES_DISPLAY['hero'],
                                           bg=tema_visual.get('card_bg', tema_visual['bg_secundario']),
                                           fg=tema_visual['success'])
        self.total_pagado_label.pack(anchor=tk.W)
        
        # Total pendiente
        pendiente_container = tk.Frame(stats_frame, bg=tema_visual.get('card_bg', tema_visual['bg_secundario']))
        pendiente_container.pack(side=tk.LEFT)
        
        tk.Label(pendiente_container, text="Total Pendiente", font=FUENTES['pequeño'],
                bg=tema_visual.get('card_bg', tema_visual['bg_secundario']),
                fg=tema_visual['fg_secundario']).pack(anchor=tk.W)
        
        self.total_pendiente_label = tk.Label(pendiente_container, text="$0.00", 
                                             font=FUENTES_DISPLAY['hero'],
                                             bg=tema_visual.get('card_bg', tema_visual['bg_secundario']),
                                             fg=tema_visual['error'])
        self.total_pendiente_label.pack(anchor=tk.W)
        
        # Personas que pagaron
        personas_pagadas_container = tk.Frame(stats_frame, bg=tema_visual.get('card_bg', tema_visual['bg_secundario']))
        personas_pagadas_container.pack(side=tk.LEFT, padx=(ESPACIADO['xl'], 0))
        
        tk.Label(personas_pagadas_container, text="Pagaron Completo", font=FUENTES['pequeño'],
                bg=tema_visual.get('card_bg', tema_visual['bg_secundario']),
                fg=tema_visual['fg_secundario']).pack(anchor=tk.W)
        
        self.personas_pagadas_label = tk.Label(personas_pagadas_container, text="0 de 0", 
                                              font=FUENTES['subtitulo'],
                                              bg=tema_visual.get('card_bg', tema_visual['bg_secundario']),
                                              fg=tema_visual['accent_primary'])
        self.personas_pagadas_label.pack(anchor=tk.W)
        
        # Botón para ocultar/mostrar cifras
        ocultar_container = tk.Frame(stats_frame, bg=tema_visual.get('card_bg', tema_visual['bg_secundario']))
        ocultar_container.pack(side=tk.RIGHT, padx=(ESPACIADO['xl'], 0))
        
        self.btn_toggle_cifras = BotonModerno(ocultar_container, f"👁️ Ocultar cifras", 
                                              tema=tema_visual, tipo='ghost',
                                              command=self.toggle_cifras_visibles)
        self.btn_toggle_cifras.pack()
        
        # ===== TABLA MODERNA =====
        self.table_panel = PanelModerno(content_container, titulo="📋 Lista de Personas", tema=tema_visual)
        self.table_panel.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Agregar barra de búsqueda integrada dentro del mismo panel de la lista
        table_header = self.table_panel.card.winfo_children()[0]  # header_frame del card
        controles_header = tk.Frame(table_header, bg=tema_visual.get('card_bg', tema_visual['bg_secundario']))
        controles_header.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=ESPACIADO['lg'], pady=(ESPACIADO['lg'], 0))
        controles_header.columnconfigure(0, weight=1)  # La búsqueda se expande

        from src.ui.ui_componentes_extra import SearchBox
        self.search_box = SearchBox(controles_header, placeholder="Buscar por nombre, folio o estado...",
                        tema=tema_visual, callback=self.buscar_tiempo_real)
        self.search_box.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, ESPACIADO['md']))
        # Callback directo sin lambda - SearchBox maneja el debouncing automáticamente

        btn_limpiar = BotonModerno(controles_header, f"{ICONOS['cerrar']} Limpiar", tema=tema_visual, tipo='secondary',
                 command=self.limpiar_busqueda)
        btn_limpiar.grid(row=0, column=1, padx=(0, ESPACIADO['sm']))
        TooltipModerno(btn_limpiar, "Limpiar búsqueda y mostrar todas las personas", tema_visual)

        # Controles de visibilidad y ordenamiento integrados al header
        checks_container = tk.Frame(controles_header, bg=tema_visual.get('card_bg', tema_visual['bg_secundario']))
        checks_container.grid(row=0, column=2, padx=(ESPACIADO['md'], 0))
        ttk.Checkbutton(checks_container, text="Mostrar folio", variable=self.folio_visible,
                command=self.actualizar_visibilidad_columnas).pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        ttk.Checkbutton(checks_container, text="Mostrar nombre", variable=self.nombre_visible,
                command=self.actualizar_visibilidad_columnas).pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        
        # BUGFIX: Checkbox para habilitar/deshabilitar ordenamiento
        ttk.Checkbutton(checks_container, text="Ordenar por columna", variable=self.habilitar_ordenamiento_var).pack(side=tk.LEFT)
        
        actions_content = self.actions_panel.content_frame
        
        # Fila 1 de botones
        btn_row1 = tk.Frame(actions_content, bg=tema_visual.get('card_bg', tema_visual['bg_secundario']))
        btn_row1.pack(fill=tk.X, pady=(0, ESPACIADO['sm']))
        
        btn_agregar = BotonModerno(btn_row1, f"{ICONOS['agregar']} Agregar Persona", tema=tema_visual, tipo='success',
                    command=self.agregar_persona)
        btn_agregar.pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        TooltipModerno(btn_agregar, "Agregar nueva persona a la cooperación", tema_visual)
        
        btn_editar = BotonModerno(btn_row1, f"{ICONOS['editar']} Editar", tema=tema_visual, tipo='ghost',
                    command=self.editar_persona)
        btn_editar.pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        TooltipModerno(btn_editar, "Editar información de la persona seleccionada", tema_visual)
        
        btn_eliminar = BotonModerno(btn_row1, f"{ICONOS['eliminar']} Eliminar", tema=tema_visual, tipo='error',
                    command=self.eliminar_persona)
        btn_eliminar.pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        TooltipModerno(btn_eliminar, "Eliminar la persona seleccionada (sin confirmación)", tema_visual)
        
        btn_pago = BotonModerno(btn_row1, f"{ICONOS['dinero']} Registrar Pago", tema=tema_visual, tipo='primary',
                    command=self.registrar_pago)
        btn_pago.pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        TooltipModerno(btn_pago, "Registrar un nuevo pago para la persona seleccionada", tema_visual)
        
        btn_historial = BotonModerno(btn_row1, f"{ICONOS['reporte']} Ver Historial", tema=tema_visual, tipo='ghost',
                    command=self.ver_historial_completo)
        btn_historial.pack(side=tk.LEFT)
        TooltipModerno(btn_historial, "Ver historial completo de pagos de todas las personas", tema_visual)
        
        # Fila 2 de botones
        btn_row2 = tk.Frame(actions_content, bg=tema_visual.get('card_bg', tema_visual['bg_secundario']))
        btn_row2.pack(fill=tk.X)
        
        btn_sync = BotonModerno(btn_row2, f"{ICONOS['sincronizar']} Sincronizar con Censo", tema=tema_visual, tipo='ghost',
                    command=self.sincronizar_coop_con_censo)
        btn_sync.pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        TooltipModerno(btn_sync, "Sincronizar personas con el sistema de censo", tema_visual)
        
        btn_folios = BotonModerno(btn_row2, f"{ICONOS['herramientas']} Corregir Folios", tema=tema_visual, tipo='warning',
                    command=self.corregir_folios)
        btn_folios.pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        TooltipModerno(btn_folios, "Detectar y corregir folios duplicados automáticamente", tema_visual)
        
        btn_excel = BotonModerno(btn_row2, f"{ICONOS['exportar']} Exportar Excel", tema=tema_visual, tipo='ghost',
                    command=self.exportar_excel)
        btn_excel.pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        TooltipModerno(btn_excel, "Exportar datos a archivo Excel para reportes", tema_visual)
        
        btn_backup = BotonModerno(btn_row2, f"{ICONOS['guardar']} Crear Backup", tema=tema_visual, tipo='ghost',
                    command=self.crear_backup)
        btn_backup.pack(side=tk.LEFT, padx=(0, ESPACIADO['sm']))
        TooltipModerno(btn_backup, "Crear copia de seguridad de todos los datos", tema_visual)
        
        # Botón de pantalla completa en la esquina superior derecha del header
        titulo_frame = self.table_panel.card.winfo_children()[0]  # El header_frame
        btn_fullscreen = tk.Button(titulo_frame, text="⛶", font=('Arial', 14), 
                       bg=tema_visual.get('card_bg', tema_visual['bg_secundario']),
                       fg=tema_visual['accent_primary'], relief=tk.FLAT,
                       cursor='hand2', command=self.toggle_fullscreen_tabla)
        btn_fullscreen.place(relx=1.0, rely=0.0, x=-ESPACIADO['lg'], y=ESPACIADO['lg'], anchor='ne')
        btn_fullscreen.lift()  # Asegurar que quede encima del resto del header
        
        table_content = self.table_panel.content_frame
        table_content.columnconfigure(0, weight=1)
        table_content.rowconfigure(0, weight=1)
        
        # Scrollbars
        scrollbar_y = ttk.Scrollbar(table_content, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(table_content, orient=tk.HORIZONTAL)
        
        # Treeview (tabla) con mejor estilo
        self.tree = ttk.Treeview(table_content, 
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
        
        self.tree.column('folio', width=95, anchor=tk.CENTER, stretch=False)
        self.tree.column('nombre', width=260, anchor=tk.W)
        self.tree.column('monto_esperado', width=120, anchor=tk.CENTER)
        self.tree.column('pagado', width=110, anchor=tk.CENTER)
        self.tree.column('pendiente', width=110, anchor=tk.CENTER)
        self.tree.column('estado', width=110, anchor=tk.CENTER)
        self.tree.column('ultimo_pago', width=170, anchor=tk.CENTER)
        self.tree.column('notas', width=240, anchor=tk.W)
        
        # Posicionar elementos
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        # Configurar tags de colores para estados
        colores = self.obtener_colores()
        tema_visual = self.tema_global
        self.tree.tag_configure('fila_par', background=tema_visual.get('bg_secundario'), foreground=tema_visual['fg_principal'])
        self.tree.tag_configure('fila_impar', background=tema_visual.get('bg_tertiary'), foreground=tema_visual['fg_principal'])
        self.tree.tag_configure('pagado', foreground=tema_visual['success'])
        self.tree.tag_configure('pendiente', foreground=tema_visual['error'])
        self.tree.tag_configure('parcial', foreground=tema_visual['warning'])
        
        # Menú contextual sobre filas con mejor estilo
        self.menu_persona = tk.Menu(self.root, tearoff=0,
                        bg=tema_visual.get('card_bg', tema_visual['bg_secundario']),
                        fg=tema_visual['fg_principal'],
                        activebackground=tema_visual['accent_primary'],
                        activeforeground='#ffffff',
                        font=FUENTES['normal'],
                        borderwidth=1, relief=tk.FLAT)
        self.menu_persona.add_command(label=f"{ICONOS['editar']} Editar persona", command=self.editar_persona)
        self.menu_persona.add_command(label=f"{ICONOS['dinero']} Registrar pago", command=self.registrar_pago)
        self.menu_persona.add_command(label=f"{ICONOS['advertencia']} Anular pago", command=self.anular_pago)
        self.menu_persona.add_command(label=f"{ICONOS['eliminar']} Eliminar", command=self.eliminar_persona)
        self.menu_persona.add_separator()
        self.menu_persona.add_command(label=f"{ICONOS['reporte']} Ver historial", command=self.ver_historial_completo)
        self.tree.bind('<Button-3>', self._mostrar_menu_persona)
        self.tree.bind('<Double-Button-1>', self._on_tree_double_click)  # MEJORA 2: Doble clic
        self.tree.bind('<Button-1>', self._on_tree_heading_click)  # MEJORA 4: Clic en header para ordenar
        
        self.actualizar_visibilidad_columnas()
        self.refrescar_selector_cooperacion()
        self.refrescar_interfaz_cooperacion()
        self.sincronizar_coop_con_censo(mostrar_mensaje=False)
        
        # Cargar datos en la tabla - usar after() para asegurar que todo esté inicializado
        # 50ms inicial para crear widgets, luego otro para refresco de datos
        self.root.after(50, self._inicializar_datos_ui_final)
        self.root.after(150, self._refresco_inicial)
        
        # ===== BARRA DE ESTADO INFERIOR =====

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
    
    def toggle_panel(self, panel):
        """Colapsa o expande un panel al hacer clic en su título"""
        # Como content_frame usa pack(), necesitamos usar pack_forget() y pack()
        if panel.content_frame.winfo_ismapped():
            panel.content_frame.pack_forget()
            # Cambiar el icono del título para indicar que está colapsado
            titulo_actual = panel.titulo_label.cget('text')
            nuevo_titulo = titulo_actual.replace('▼', '▶')
            panel.titulo_label.config(text=nuevo_titulo)
        else:
            panel.content_frame.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['lg'], pady=ESPACIADO['lg'])
            # Cambiar el icono del título para indicar que está expandido
            titulo_actual = panel.titulo_label.cget('text')
            nuevo_titulo = titulo_actual.replace('▶', '▼')
            panel.titulo_label.config(text=nuevo_titulo)
    
    def toggle_cifras_visibles(self):
        """Alterna entre mostrar y ocultar cifras sensibles"""
        self.cifras_visibles = not self.cifras_visibles
        
        # Actualizar texto del botón
        if hasattr(self, 'btn_toggle_cifras'):
            if self.cifras_visibles:
                self.btn_toggle_cifras.config(text="👁️ Ocultar cifras")
            else:
                self.btn_toggle_cifras.config(text="🙈 Mostrar cifras")
        
        # Actualizar totales inmediatamente
        self.actualizar_totales()
        
        # Actualizar tabla para reflejar cambios de cifras en filas
        if hasattr(self, 'tree'):
            self.actualizar_tabla()
    
    def toggle_fullscreen_tabla(self):
        """Alterna entre pantalla completa de la tabla y vista normal"""
        if not hasattr(self, 'tabla_fullscreen'):
            self.tabla_fullscreen = False
        
        self.tabla_fullscreen = not self.tabla_fullscreen
        
        if self.tabla_fullscreen:
            # Ocultar otros paneles y expandir tabla
            if hasattr(self, 'info_panel') and self.info_panel.winfo_ismapped():
                self.info_panel.grid_remove()
            if hasattr(self, 'actions_panel') and self.actions_panel.winfo_ismapped():
                self.actions_panel.grid_remove()
            if hasattr(self, 'total_frame') and self.total_frame.winfo_ismapped():
                self.total_frame.grid_remove()
            # Ocultar barra superior para ganar más espacio
            if hasattr(self, 'barra_superior') and self.barra_superior.frame.winfo_ismapped():
                self.barra_superior.frame.grid_remove()
            
            # Hacer que la tabla ocupe toda la pantalla
            if hasattr(self, 'table_panel'):
                self.table_panel.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
                # Asegurar que el contenedor se expanda completamente
                if hasattr(self, 'content_container'):
                    self.content_container.columnconfigure(0, weight=1)
                    self.content_container.rowconfigure(0, weight=0)  # info panel
                    self.content_container.rowconfigure(1, weight=0)  # actions panel
                    self.content_container.rowconfigure(2, weight=1)  # tabla - peso 1 para expandir
        else:
            # Restaurar vista normal
            if hasattr(self, 'info_panel'):
                self.info_panel.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
            if hasattr(self, 'actions_panel'):
                self.actions_panel.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
            if hasattr(self, 'barra_superior'):
                self.barra_superior.frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
            
            # Restaurar configuración normal de la tabla
            if hasattr(self, 'table_panel'):
                self.table_panel.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
                # Restaurar pesos originales
                if hasattr(self, 'content_container'):
                    self.content_container.rowconfigure(2, weight=1)
        
    def sincronizar_con_censo(self, nombre):
        """Sincronizar persona con la base de datos de censo - buscar/crear folio permanente"""
        try:
            # Verificar si ya existe en pagos
            nombre_lower = nombre.lower().strip()
            for persona in self.personas:
                if persona['nombre'].lower().strip() == nombre_lower:
                    return persona.get('folio')
            
            # Buscar en censo usando gestor
            habitante = self.gestor.obtener_habitante_por_nombre(nombre)
            if habitante:
                folio = habitante['folio']
                return folio
            
            # Si no existe, crear en censo
            habitante, mensaje = self.gestor.agregar_habitante(nombre)
            
            if habitante:
                folio = habitante['folio']
                return folio
            else:
                registrar_error('control_pagos', 'sincronizar_con_censo', f'Error al agregar: {mensaje}')
                return None
                
        except Exception as e:
            registrar_error('control_pagos', 'sincronizar_con_censo', str(e))
            return None

    def generar_folio_local(self):
        """Usar folio del gestor centralizado"""
        return self.gestor.obtener_siguiente_folio()
    
    def actualizar_monto(self):
        """Actualiza el monto de cooperación con confirmación mejorada"""
        if not self._tiene_permiso('editar'):
            return
        
        try:
            nuevo_monto = self.monto_var.get()
            if nuevo_monto <= 0:
                messagebox.showerror("Error", "El monto debe ser mayor a 0")
                self.monto_var.set(self.monto_cooperacion)
                return
            
            # Si el monto es igual, no hacer nada
            if nuevo_monto == self.monto_cooperacion:
                messagebox.showinfo("Información", "El monto ingresado es el mismo que el actual.")
                return
            
            # Mostrar ventana de confirmación mejorada
            confirmar = ConfirmacionMejorada.confirmar_actualizar_monto(
                self.root,
                self.monto_cooperacion,
                nuevo_monto,
                len(self.personas),
                self.tema_global
            )
            
            if not confirmar:
                # Usuario canceló, restaurar valor anterior
                self.monto_var.set(self.monto_cooperacion)
                return
            
            # Solicitar contraseña después de confirmar
            if not self.solicitar_password():
                messagebox.showwarning("Cancelado", "Operación cancelada")
                self.monto_var.set(self.monto_cooperacion)
                return
            
            # Guardar monto anterior para el historial
            monto_anterior = self.monto_cooperacion
            
            # Actualizar monto de cooperación
            self.monto_cooperacion = nuevo_monto
            coop = self.obtener_cooperacion_activa()
            if coop:
                coop['monto_cooperacion'] = nuevo_monto
            
            # Actualizar monto_esperado de todas las personas existentes
            num_personas_afectadas = len(self.personas)
            for persona in self.personas:
                persona['monto_esperado'] = nuevo_monto
            
            # Registrar en el historial
            registrar_operacion('CAMBIO_MONTO', 'Monto de cooperación actualizado', {
                'cooperacion': self.cooperacion_actual or 'Sin nombre',
                'monto_anterior': f"${monto_anterior:.2f}",
                'monto_nuevo': f"${nuevo_monto:.2f}",
                'personas_afectadas': num_personas_afectadas,
                'usuario': self.usuario_actual['nombre'] if self.usuario_actual else 'Desconocido'
            }, self.usuario_actual['nombre'] if self.usuario_actual else 'Admin')
            
            # Registrar cambio detallado en historial
            usuario = self.usuario_actual['nombre'] if self.usuario_actual else 'Admin'
            self.gestor_historial.registrar_cambio('EDITAR', 'COOPERACION', 
                self.coop_activa_id or 'cooperacion-actual',
                {'monto_cooperacion': {'anterior': f"${monto_anterior:.2f}", 'nuevo': f"${nuevo_monto:.2f}"}},
                usuario)
            
            # Guardar y actualizar UI
            self.guardar_datos(mostrar_alerta=False)
            self.actualizar_tabla()
            self.actualizar_totales()
            
            # Mensaje de éxito
            messagebox.showinfo("✓ Éxito", 
                f"Monto actualizado correctamente\n\n"
                f"Monto anterior: ${monto_anterior:.2f}\n"
                f"Monto nuevo: ${nuevo_monto:.2f}\n\n"
                f"Se actualizó el monto esperado de {num_personas_afectadas} persona(s).")
            
        except tk.TclError:
            messagebox.showerror("Error", "Por favor ingrese un monto válido (solo números)")
            self.monto_var.set(self.monto_cooperacion)
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar monto:\n{str(e)}")
            self.monto_var.set(self.monto_cooperacion)
    
    def agregar_persona(self):
        if not self._tiene_permiso('crear'):
            return
        
        def on_persona_agregada(persona):
            self.personas.append(persona)
            self.actualizar_tabla()
            self.actualizar_totales()
            self.guardar_datos(mostrar_alerta=False)
        
        DialogoAgregarPersona.mostrar(
            parent=self.root,
            monto_cooperacion=self.monto_cooperacion,
            cooperacion_actual=self.coop_selector.get() or 'Actual',
            gestor_personas=self.gestor_personas,
            gestor_historial=self.gestor_historial,
            usuario_actual=self.usuario_actual,
            callback_sincronizar_censo=self.sincronizar_con_censo,
            callback_generar_folio=self.generar_folio_local,
            callback_ok=on_persona_agregada,
            tema_global=self.tema_global
        )
    
    def editar_persona(self):
        if not self._tiene_permiso('editar'):
            return
        
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Por favor seleccione una persona")
            return
        
        item = seleccion[0]
        persona = self.tree_persona_map.get(item)
        if not persona:
            messagebox.showerror("Error", "No se pudo localizar la persona seleccionada")
            return
        
        try:
            index = self.personas.index(persona)
        except ValueError:
            messagebox.showerror("Error", "La persona seleccionada ya no existe en la lista")
            return
        
        def on_persona_editada(persona, cambios):
            # Guardar datos inmediatamente
            self.guardar_datos(mostrar_alerta=False)
            self.actualizar_tabla()
            self.actualizar_totales()
            
            # Mensaje de confirmación con detalles de cambios
            if cambios:
                campos_cambiados = ", ".join(cambios.keys())
                messagebox.showinfo("✓ Éxito", 
                    f"Persona editada correctamente\n\n"
                    f"Nombre: {persona['nombre']}\n"
                    f"Campos actualizados: {campos_cambiados}")
        
        DialogoEditarPersona.mostrar(
            parent=self.root,
            persona=persona,
            personas_lista=self.personas,
            gestor_historial=self.gestor_historial,
            usuario_actual=self.usuario_actual,
            tema_global=self.tema_global,
            gestor_global=self.gestor,  # Pasar gestor global para sincronización
            callback_ok=on_persona_editada
        )
    
    def eliminar_persona(self):
        if not self._tiene_permiso('editar'):
            return
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Por favor seleccione una persona")
            return
        
        item = seleccion[0]
        persona = self.tree_persona_map.get(item)
        if not persona:
            messagebox.showerror("Error", "No se pudo localizar la persona seleccionada")
            return
        try:
            index = self.personas.index(persona)
        except ValueError:
            messagebox.showerror("Error", "La persona seleccionada ya no existe en la lista")
            return
        
        # MEJORA 6: Usar confirmación mejorada con más información
        # Excluir pagos anulados del cálculo
        monto_pagado = sum(pago['monto'] for pago in persona.get('pagos', []) if not pago.get('anulado', False))
        monto_esperado = persona.get('monto_esperado', 100)
        
        if ConfirmacionMejorada.confirmar_eliminacion(
            self.root,
            nombre_persona=persona['nombre'],
            folio=persona.get('folio', 'SIN-FOLIO'),
            total_pagado=monto_pagado,
            monto_esperado=monto_esperado,
            tema_global=self.tema_global
        ):
            usuario = self.usuario_actual['nombre'] if self.usuario_actual else 'Sistema'
            
            # BUG FIX #5: Hacer backup seguro ANTES de eliminar
            try:
                from src.modules.pagos.pagos_eliminacion_segura import GestorEliminacionSegura
                GestorEliminacionSegura.hacer_backup_persona(
                    persona,
                    motivo='Eliminación por usuario',
                    usuario=usuario
                )
            except Exception as e:
                registrar_error('control_pagos', 'eliminar_persona_backup', str(e))
                # Continuar incluso si falla el backup
            
            # Registrar en historial antes de eliminar
            self.gestor_historial.registrar_cambio('ELIMINAR', 'PERSONA', persona.get('folio', ''), 
                {'persona_eliminada': persona}, usuario)
            
            # Registrar en log de operaciones
            registrar_operacion('ELIMINAR_PERSONA', 'Persona eliminada del sistema', {
                'cooperacion': self.cooperacion_actual or 'Sin nombre',
                'folio': persona.get('folio', 'SIN-FOLIO'),
                'nombre': persona['nombre'],
                'monto_esperado': f"${monto_esperado:.2f}",
                'pagado': f"${monto_pagado:.2f}",
                'usuario': usuario
            }, usuario)
            
            # Eliminar después de guardar backup
            self.personas.pop(index)
            self.actualizar_tabla()
            self.actualizar_totales()
            
            # Guardar cambios inmediatamente
            self.guardar_datos(mostrar_alerta=False, inmediato=True)
            
            messagebox.showinfo("Exito", f"Persona '{persona['nombre']}' eliminada correctamente.\nSus datos han sido guardados en auditoría.")
    
    def registrar_pago(self):
        """Registrar un pago (puede ser parcial)"""
        if not self._tiene_permiso('pagar'):
            return
        
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Por favor seleccione una persona")
            return
        
        item = seleccion[0]
        persona = self.tree_persona_map.get(item)
        if not persona:
            messagebox.showerror("Error", "No se pudo localizar la persona seleccionada")
            return
        
        # Obtener monto esperado
        monto_esperado = persona.get('monto_esperado', persona.get('monto', 100))
        
        # Callback para cuando se registre el pago exitosamente
        def on_pago_registrado(persona, monto_pago, nuevo_total, monto_esperado):
            # Refrescar datos y UI
            self.actualizar_totales()
            self.guardar_datos(mostrar_alerta=False)
            self.actualizar_tabla()
            
            # Visual feedback: animar la fila
            try:
                new_item = self._persona_iid(persona)
                if self.tree.exists(new_item):
                    if nuevo_total >= monto_esperado:
                        self.animar_fila_pagada(new_item, "completado")
                    else:
                        self.animar_fila_pagada(new_item, "parcial")
            except Exception as anim_err:
                # No interrumpir si solo falla la animación
                registrar_error('control_pagos', 'animar_fila_pagada', str(anim_err))
        
        # Mostrar diálogo
        DialogoRegistrarPago.mostrar(
            parent=self.root,
            persona=persona,
            monto_esperado=monto_esperado,
            gestor_historial=self.gestor_historial,
            usuario_actual=self.usuario_actual,
            callback_ok=on_pago_registrado,
            cooperacion_actual=self.cooperacion_actual,
            tema_global=self.tema_global
        )
    
    def anular_pago(self):
        """Anular un pago existente con autenticación por contraseña"""
        if not self._tiene_permiso('pagar'):  # Requerir mismo permiso que registrar
            return
        
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Por favor seleccione una persona")
            return
        
        item = seleccion[0]
        persona = self.tree_persona_map.get(item)
        if not persona:
            messagebox.showerror("Error", "No se pudo localizar la persona seleccionada")
            return
        
        # Verificar que haya pagos
        if not persona.get('pagos'):
            messagebox.showinfo("Información", "Esta persona no tiene pagos registrados")
            return
        
        # Callback para cuando se anule el pago exitosamente
        def on_pago_anulado(persona, monto_anulado, nuevo_total):
            # Refrescar datos y UI
            self.actualizar_totales()
            self.guardar_datos(mostrar_alerta=False)
            self.actualizar_tabla()
            
            # Visual feedback: animar la fila
            try:
                new_item = self._persona_iid(persona)
                if self.tree.exists(new_item):
                    self.animar_fila_anulada(new_item)
            except Exception as anim_err:
                registrar_error('control_pagos', 'animar_fila_anulada', str(anim_err))
        
        # Mostrar diálogo de anulación
        from src.modules.pagos.pagos_dialogos import DialogoAnularPago
        
        DialogoAnularPago.mostrar(
            parent=self.root,
            persona=persona,
            gestor_auth=self.gestor_auth,
            gestor_historial=self.gestor_historial,
            usuario_actual=self.usuario_actual,
            callback_ok=on_pago_anulado,
            cooperacion_actual=self.cooperacion_actual,
            tema_global=self.tema_global
        )
    
    def animar_fila_anulada(self, item):
        """Animar la fila con pulso naranja cuando se anula un pago"""
        tema_visual = self.obtener_colores()
        
        def pulso(idx=0):
            if idx < 4:
                # Cambiar color durante animación
                color_actual = tema_visual['warning'] if idx % 2 == 0 else tema_visual['fg_principal']
                self.tree.item(item, tags=('anulacion_' + str(idx),))
                self.tree.tag_configure('anulacion_' + str(idx), foreground=color_actual)
                self.root.after(200, lambda: pulso(idx + 1))
            else:
                # Restaurar color basado en estado actual
                persona = self.tree_persona_map.get(item)
                if not persona:
                    return
                
                total_pagado = sum(p['monto'] for p in persona.get('pagos', []) if not p.get('anulado', False))
                monto_esperado = persona.get('monto_esperado', 100)
                
                from src.modules.pagos.pagos_estado import GestorEstadoPago
                estado_clave = GestorEstadoPago.obtener_estado(total_pagado, monto_esperado)
                
                tag_estado_map = {
                    'completado': 'pagado',
                    'excedente': 'pagado',
                    'parcial': 'parcial',
                    'pendiente': 'pendiente'
                }
                tag = tag_estado_map.get(estado_clave, 'pendiente')
                self.tree.item(item, tags=(tag,))
        
        pulso()
    
    def animar_fila_pagada(self, item, tipo='completado'):
        """Animar la fila con pulso de color - BUG FIX #1: Usa GestorEstadoPago"""
        from src.modules.pagos.pagos_estado import GestorEstadoPago
        
        tema_visual = self.obtener_colores()
        
        def pulso(idx=0):
            if idx < 4:
                # Cambiar color de texto durante animación
                self.tree.item(item, tags=('pago_ok' if tipo == 'completado' else 'pago_parcial',))
                self.root.after(150, lambda: pulso(idx + 1))
            else:
                # Restaurar color normal basado en estado ACTUAL (BUG FIX #1)
                persona = self.tree_persona_map.get(item)
                if not persona:
                    return
                
                total_pagado = sum(p['monto'] for p in persona.get('pagos', []))
                monto_esperado = persona.get('monto_esperado', 100)
                
                # Usar GestorEstadoPago para obtener estado consistente
                estado_clave = GestorEstadoPago.obtener_estado(total_pagado, monto_esperado)
                
                tag_estado_map = {
                    'completado': 'pagado',
                    'excedente': 'pagado',
                    'parcial': 'parcial',
                    'pendiente': 'pendiente'
                }
                tag = tag_estado_map.get(estado_clave, 'pendiente')
                self.tree.item(item, tags=(tag,))
        
        pulso()
    
    def ver_historial(self):
        """Ver historial de pagos de una persona"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Por favor seleccione una persona")
            return
        
        item = seleccion[0]
        persona = self.tree_persona_map.get(item)
        if not persona:
            messagebox.showerror("Error", "No se pudo localizar la persona seleccionada")
            return
        
        DialogoVerHistorial.mostrar(self.root, persona)
    
    def buscar_tiempo_real(self):
        """Búsqueda en tiempo real - llamada directamente por SearchBox con debounce"""
        # SearchBox ya maneja el debouncing, solo ejecutar la búsqueda
        self.actualizar_tabla()
        self._actualizar_contador_resultados()
        # Actualizar totales cada búsqueda para reflejar cambios de la cooperación activa
        self.actualizar_totales()
    
    def _actualizar_contador_resultados(self):
        """Muestra el contador de resultados de búsqueda en la barra de estado"""
        criterio = self.search_box.get().strip().lower() if hasattr(self, 'search_box') else ''
        
        if criterio:
            resultados = [p for p in self.personas 
                         if criterio in p['nombre'].lower() or 
                         criterio in p.get('folio', '').lower()]
            total = len(self.personas)
            encontrados = len(resultados)
            
            if hasattr(self, 'barra_estado') and self.barra_estado:
                self.barra_estado.actualizar_sync(f"Búsqueda: {encontrados} de {total}")
        else:
            # Sin búsqueda activa
            if hasattr(self, 'barra_estado') and self.barra_estado:
                self.barra_estado.actualizar_sync("Sincronizado")
    
    def limpiar_busqueda(self):
        """Limpiar busqueda"""
        if hasattr(self, 'search_box'):
            self.search_box.clear()
        self.actualizar_tabla()
        self.actualizar_totales()
        self._actualizar_contador_resultados()
    
    def actualizar_tabla(self):
        # Importar GestorEstadoPago para usar lógica centralizada (BUG FIX #1 y #4)
        from src.modules.pagos.pagos_estado import GestorEstadoPago
        
        # Limpiar tabla pero guardar selección actual (BUG FIX #6)
        seleccion_anterior = self.tree.selection()
        persona_seleccionada = None
        if seleccion_anterior:
            persona_seleccionada = self.tree_persona_map.get(seleccion_anterior[0])
        
        # Deshabilitar redibujado temporal para mejor rendimiento
        self.tree.configure(takefocus=False)
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree_persona_map = {}
        
        # Filtrar personas si hay búsqueda activa (optimizado)
        criterio = self.search_box.get().strip().lower() if hasattr(self, 'search_box') else ''
        
        if criterio:
            personas_mostrar = [
                p for p in self.personas 
                if criterio in p.get('nombre', 'SIN-NOMBRE').lower() or 
                   criterio in p.get('folio', 'SIN-FOLIO').lower()
            ]
        else:
            personas_mostrar = self.personas
        
        # Agregar personas
        for idx, persona in enumerate(personas_mostrar):
            # Migrar datos antiguos si es necesario
            if 'monto_esperado' not in persona:
                persona['monto_esperado'] = persona.get('monto', 100)
            if 'pagos' not in persona:
                persona['pagos'] = []
            if 'folio' not in persona:
                persona['folio'] = 'SIN-FOLIO'
            if 'nombre' not in persona:
                persona['nombre'] = 'SIN-NOMBRE'
            
            monto_esperado = persona['monto_esperado']
            # Excluir pagos anulados del total
            total_pagado = sum(pago['monto'] for pago in persona['pagos'] if not pago.get('anulado', False))
            pendiente = max(0, monto_esperado - total_pagado)
            
            # BUG FIX #1 y #4: Usar GestorEstadoPago centralizado para determinar estado
            estado_clave = GestorEstadoPago.obtener_estado(total_pagado, monto_esperado)
            datos_estado = GestorEstadoPago.obtener_datos_estado(estado_clave)
            
            estado = datos_estado['nombre']
            indicador = datos_estado['emoji'] + ' '
            
            # Obtener fecha del último pago
            ultimo_pago = ''
            if persona['pagos']:
                ultimo = persona['pagos'][-1]
                ultimo_pago = f"{ultimo['fecha']} {ultimo['hora']}"
            
            iid = self._persona_iid(persona)
            row_tag = 'fila_par' if idx % 2 == 0 else 'fila_impar'
            
            self.tree.insert('', tk.END, iid=iid,
                           values=(persona.get('folio', 'SIN-FOLIO'),
                                  indicador + persona['nombre'],
                                  f"${monto_esperado:.2f}",
                                  f"${total_pagado:.2f}",
                                  f"${pendiente:.2f}",
                                  estado,
                                  ultimo_pago,
                                  persona.get('notas', '')),
                           tags=(row_tag,))
            self.tree_persona_map[iid] = persona
            
            # BUG FIX #6: Restaurar selección si era la misma persona
            if persona_seleccionada and persona == persona_seleccionada:
                self.tree.selection_set(iid)
        
        # Reactivar redibujado
        self.tree.configure(takefocus=True)
        
        # Actualizar contador de personas
        total_mostradas = len(personas_mostrar)
        total_general = len(self.personas)
        if total_mostradas == total_general:
            self.total_personas_label.config(text=str(total_general))
        else:
            self.total_personas_label.config(text=f"{total_mostradas} de {total_general}")
    
    def _mostrar_menu_persona(self, event):
        """Mostrar menú contextual sobre la fila seleccionada"""
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        self.tree.selection_set(iid)
        try:
            self.menu_persona.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu_persona.grab_release()
    
    def _on_tree_double_click(self, event):
        """MEJORA 2: Doble clic en fila abre diálogo de pago directo"""
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        self.tree.selection_set(iid)
        # Abrir diálogo de pago directamente
        self.registrar_pago()
    
    def _on_tree_heading_click(self, event):
        """BUGFIX: Clic en header de columna para ordenamiento - SOLO si checkbox está activo"""
        # Identificar si se hizo clic en un heading
        col = self.tree.identify_column(event.x)
        region = self.tree.identify_region(event.x, event.y)
        
        # BUGFIX: Solo procesar si fue click en un heading (no en fila)
        if region != 'heading':
            return
        
        if col == '#0':  # Clic en columna de árbol, ignorar
            return
        
        # BUGFIX: Solo permitir ordenamiento si el checkbox está activado
        if not hasattr(self, 'habilitar_ordenamiento_var') or not self.habilitar_ordenamiento_var.get():
            return
        
        # Mapear número de columna a nombre de columna
        col_num = int(col[1:]) - 1
        columnas = ('folio', 'nombre', 'monto_esperado', 'pagado', 'pendiente', 'estado', 'ultimo_pago', 'notas')
        
        if col_num < 0 or col_num >= len(columnas):
            return
        
        col_name = columnas[col_num]
        
        # BUGFIX: Solo permitir ordenamiento por columnas específicas - silenciosamente ignorar otros
        columnas_permitidas = ('pagado', 'pendiente', 'ultimo_pago')
        if col_name not in columnas_permitidas:
            # Silenciosamente ignorar clics en otras columnas en lugar de mostrar alerta
            return
        
        # Si se clickea la misma columna, invertir dirección
        if self.columna_ordenamiento == col_name:
            self.orden_ascendente = not self.orden_ascendente
        else:
            self.columna_ordenamiento = col_name
            self.orden_ascendente = True
        
        # Ordenar y actualizar tabla
        self._ordenar_tabla_por_columna(col_name)
    
    def _ordenar_tabla_por_columna(self, col_name):
        """Ordena la tabla por la columna especificada y actualiza los headers"""
        # Convertir datos mostrados a lista para ordenar
        items_mostrados = list(self.tree.get_children())
        personas_mostradas = []
        
        for iid in items_mostrados:
            # Encontrar persona correspondiente
            folio = self.tree.item(iid)['values'][0]
            for p in self.personas:
                if p.get('folio', 'SIN-FOLIO') == folio:
                    personas_mostradas.append(p)
                    break
        
        # Función para obtener valor de ordenamiento
        def get_sort_key(persona):
            monto_esperado = persona.get('monto_esperado', 100)
            # Excluir pagos anulados
            pagado = sum(pago['monto'] for pago in persona.get('pagos', []) if not pago.get('anulado', False))
            pendiente = max(0, monto_esperado - pagado)
            
            if col_name == 'folio':
                return persona.get('folio', 'SIN-FOLIO').lower()
            elif col_name == 'nombre':
                return persona.get('nombre', '').lower()
            elif col_name == 'monto_esperado':
                return float(monto_esperado)
            elif col_name == 'pagado':
                return float(pagado)
            elif col_name == 'pendiente':
                return float(pendiente)
            elif col_name == 'estado':
                if pagado >= monto_esperado:
                    return 0  # Pagado
                elif pagado > 0:
                    return 1  # Parcial
                else:
                    return 2  # Pendiente
            elif col_name == 'ultimo_pago':
                if persona.get('pagos'):
                    return persona['pagos'][-1].get('fecha', '')
                return ''
            elif col_name == 'notas':
                return persona.get('notas', '').lower()
            return ''
        
        # Ordenar
        personas_mostradas.sort(key=get_sort_key, reverse=not self.orden_ascendente)
        
        # Guardar orden en lista principal
        self.personas = personas_mostradas
        
        # Actualizar tabla con nuevo orden
        self.actualizar_tabla()
        
        # Actualizar headers con indicadores visuales
        self._actualizar_headers_ordenamiento(col_name)
    
    def _actualizar_headers_ordenamiento(self, col_name):
        """Actualiza los headers para mostrar columna ordenada con indicador"""
        columnas = ('folio', 'nombre', 'monto_esperado', 'pagado', 'pendiente', 'estado', 'ultimo_pago', 'notas')
        textos_originales = ('Folio', 'Nombre Completo', 'Monto Esperado', 'Pagado', 'Pendiente', 'Estado', 'Ultimo Pago', 'Notas')
        
        for col, texto in zip(columnas, textos_originales):
            if col == col_name:
                # Agregar indicador de orden
                indicador = ' ▲' if self.orden_ascendente else ' ▼'
                self.tree.heading(col, text=texto + indicador)
            else:
                # Remover indicador
                self.tree.heading(col, text=texto)
    
    def _inicializar_datos_ui_final(self):
        """Inicializa datos UI de forma diferida para asegurar widgets listos"""
        try:
            # Verificar que los widgets críticos existan
            if not hasattr(self, 'tree') or not self.tree:
                return
            if not hasattr(self, 'search_box') or not self.search_box:
                return
                
            self.actualizar_tabla()
            self.actualizar_totales()
            self._actualizar_contador_resultados()
            self._inicializacion_completada = True
        except Exception as e:
            registrar_error('control_pagos', '_inicializar_datos_ui_final', str(e))

    def _refresco_inicial(self):
        """Refresco final para asegurar que todo esté visible correctamente"""
        try:
            if not hasattr(self, 'tree') or not self.tree:
                return
            # Forzar actualización de la tabla
            self.root.update_idletasks()
            self.actualizar_tabla()
            self.actualizar_totales()
        except Exception as e:
            registrar_error('control_pagos', '_refresco_inicial', str(e))

    def _configurar_atajos_teclado(self):
        """MEJORA 7: Configura atajos de teclado para acciones comunes"""
        # Ctrl+F: Enfocar en la caja de búsqueda
        self.root.bind('<Control-f>', lambda e: self.search_box.entry.focus() if hasattr(self, 'search_box') else None)
        
        # Ctrl+P: Registrar pago
        self.root.bind('<Control-p>', lambda e: self.registrar_pago())
        
        # Ctrl+E: Editar persona
        self.root.bind('<Control-e>', lambda e: self.editar_persona())
        
        # Ctrl+H: Ver historial
        self.root.bind('<Control-h>', lambda e: self.ver_historial_completo())
        
        # Ctrl+S: Sincronizar/Guardar
        self.root.bind('<Control-s>', lambda e: self.sincronizar_coop_con_censo())
        
        # F5: Refrescar tabla
        self.root.bind('<F5>', lambda e: self.actualizar_tabla())
        
        # Delete: Eliminar persona seleccionada
        self.root.bind('<Delete>', lambda e: self.eliminar_persona())
        
        # Escape: Limpiar búsqueda
        self.root.bind('<Escape>', lambda e: self.limpiar_busqueda())
        
        # Ctrl+1, Ctrl+2, Ctrl+3: Cambiar entre cooperaciones
        self.root.bind('<Control-1>', lambda e: self._cambiar_cooperacion_por_indice(0))
        self.root.bind('<Control-2>', lambda e: self._cambiar_cooperacion_por_indice(1))
        self.root.bind('<Control-3>', lambda e: self._cambiar_cooperacion_por_indice(2))
    
    def _cambiar_cooperacion_por_indice(self, indice):
        """Cambia a la cooperación en el índice especificado"""
        if indice < len(self.cooperaciones):
            self.coop_selector.current(indice)
            self.on_cambio_cooperacion()
    
    def actualizar_totales(self):
        """Actualizar los totales en el panel de información del proyecto"""
        total_pagado = 0
        total_pendiente = 0
        personas_pagadas = 0
        
        for persona in self.personas:
            monto_esperado = persona.get('monto_esperado', persona.get('monto', 100))
            # Excluir pagos anulados
            pagado = sum(pago['monto'] for pago in persona.get('pagos', []) if not pago.get('anulado', False))
            pendiente = max(0, monto_esperado - pagado)
            
            total_pagado += pagado
            total_pendiente += pendiente
            
            # Contar personas que completaron pago
            if pagado >= monto_esperado:
                personas_pagadas += 1
        
        # Actualizar labels principales en panel de información
        if hasattr(self, 'total_pagado_label'):
            if self.cifras_visibles:
                self.total_pagado_label.config(text=f"${total_pagado:.2f}")
            else:
                self.total_pagado_label.config(text="••••••")
        
        if hasattr(self, 'total_pendiente_label'):
            if self.cifras_visibles:
                self.total_pendiente_label.config(text=f"${total_pendiente:.2f}")
            else:
                self.total_pendiente_label.config(text="••••••")
        
        if hasattr(self, 'personas_pagadas_label'):
            self.personas_pagadas_label.config(text=f"{personas_pagadas} de {len(self.personas)}")
    
    def actualizar_estado_barra(self):
        """Actualiza la barra de estado con información del sistema"""
        # BUGFIX: Verificar que el root y barra_estado existan y sean válidos
        if not hasattr(self, 'root') or not self.root:
            return
        
        # Verificar que el widget root aún exista en Tk
        try:
            # Intenta acceder a una propiedad del widget para verificar que existe
            self.root.winfo_exists()
        except:
            # El widget fue destruido, salir sin reprogramar
            return
        
        if not hasattr(self, 'barra_estado') or not self.barra_estado:
            return
        
        try:
            # Determinar estado de API
            api_online = getattr(self, 'api_activa', False)
            self.barra_estado.actualizar_api(api_online)
            
            # Determinar estado de guardado
            guardado = self.guardado_pendiente is None
            cambios = 0 if guardado else 1
            self.barra_estado.actualizar_saved(guardado, cambios)
            
            # Actualizar sincronización
            if len(self.personas) > 0:
                self.barra_estado.actualizar_sync("Sincronizado")
            else:
                self.barra_estado.actualizar_sync("Sin datos")
        except tk.TclError:
            # El widget fue destruido durante la actualización, no reprogramar
            return
        except Exception as e:
            # Cualquier otro error, registrar y no reprogramar
            registrar_error('control_pagos', 'actualizar_estado_barra', str(e))
            return
        
        # Reprogramar siguiente actualización SOLO si el widget sigue vivo
        if self.root and self.root.winfo_exists():
            self._after_id_barra = self.root.after(2000, self.actualizar_estado_barra)
    
    def _persona_iid(self, persona):
        """Devuelve un iid estable para el Treeview basado en el objeto persona"""
        folio = persona.get('folio', 'SIN-FOLIO')
        return f"{folio}|{id(persona)}"
    
    def guardar_datos(self, mostrar_alerta=True, inmediato=False):
        """Guardar datos en BD SQLite (ya no usa JSON)"""
        try:
            # Los datos se guardan directamente en BD mediante transacciones
            # Esta función ahora es un placeholder por compatibilidad
            if mostrar_alerta and inmediato:
                messagebox.showinfo("✓ Guardado", "Datos sincronizados con BD")
        except Exception as e:
            if mostrar_alerta:
                messagebox.showerror("Error", f"Error: {str(e)}")
    
    def _ejecutar_guardado(self, mostrar_alerta=True):
        """Ya no necesario con BD"""
        pass

    def cargar_datos(self):
        """Ya no carga desde JSON, todo viene de BD en _cargar_cooperaciones_bd()"""
        pass
    
    def guardar_datos(self, mostrar_alerta=True, inmediato=False):
        """Guarda datos en BD SQLite (ya no usa JSON)"""
        try:
            # Los datos ya se guardan en BD mediante transacciones
            # Esta función ahora es un placeholder por compatibilidad
            if mostrar_alerta:
                messagebox.showinfo("Guardado", "Datos guardados en BD")
        except Exception as e:
            registrar_error('control_pagos', 'guardar_datos', str(e))
    
    def exportar_excel(self):
        """Exportar cooperación actual a Excel"""
        if not self._tiene_permiso('exportar'):
            return
        if not self.personas:
            messagebox.showwarning("Advertencia", "No hay datos para exportar")
            return
        
        try:
            # Obtener nombre de cooperación actual
            coop_actual = next((c for c in self.cooperaciones if c['id'] == self.coop_activa_id), None)
            nombre_coop = coop_actual['nombre'] if coop_actual else "Cooperacion"
            
            # Sanitizar nombre de archivo (eliminar caracteres inválidos)
            nombre_coop_safe = "".join(c for c in nombre_coop if c.isalnum() or c in (' ', '-', '_')).strip()
            
            # Solicitar ubicación de guardado
            archivo = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"{nombre_coop_safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if not archivo:
                return  # Usuario canceló
            
            # Exportar usando el módulo exportador
            exportador = ExportadorExcel()
            ruta_archivo = exportador.exportar_personas_cooperacion(
                self.personas, nombre_coop, os.path.basename(archivo)
            )
            
            if ruta_archivo and os.path.exists(ruta_archivo):
                registrar_operacion('EXPORTAR_EXCEL', 'Datos exportados a Excel', 
                    {'cooperacion': nombre_coop, 'archivo': ruta_archivo, 'total_personas': len(self.personas)},
                    self.usuario_actual['nombre'] if self.usuario_actual else 'Sistema')
                messagebox.showinfo("✓ Éxito", 
                    f"Datos exportados correctamente\n\n"
                    f"Cooperación: {nombre_coop}\n"
                    f"Total personas: {len(self.personas)}\n"
                    f"Archivo: {os.path.basename(ruta_archivo)}")
            else:
                messagebox.showerror("Error", "No se pudo crear el archivo Excel")
        except Exception as e:
            registrar_error('control_pagos', 'exportar_excel', str(e))
            registrar_error('EXPORTAR_EXCEL', str(e))
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")
    
    def crear_backup(self):
        """Crear un backup completo del sistema"""
        if not self._tiene_permiso('exportar'):
            return
        try:
            resultado = self.gestor_backups.crear_backup_completo()
            if resultado['exito']:
                registrar_operacion('CREAR_BACKUP', 'Backup creado manualmente', {'archivo': resultado['nombre_carpeta']})
                messagebox.showinfo("Éxito", f"Backup creado correctamente:\n{resultado['nombre_carpeta']}")
            else:
                messagebox.showerror("Error", f"Error al crear backup: {resultado.get('error', 'Desconocido')}")
        except Exception as e:
            registrar_error('CREAR_BACKUP', str(e))
            messagebox.showerror("Error", f"Error al crear backup: {str(e)}")
    
    def ver_historial_completo(self):
        """Abrir ventana de historial completo"""
        from src.modules.historial.ventana_historial import VentanaHistorial
        # Pasar el gestor_historial de la aplicación para que use los datos actuales
        VentanaHistorial(self.root, gestor_historial=self.gestor_historial)
    
    def _auditar_coherencia_inicial(self):
        """BUGFIX: Auditar coherencia de cooperaciones al iniciar - sin romper UI"""
        try:
            from src.modules.pagos.pagos_validador_coherencia import ValidadorCoherenciaCooperaciones
            
            # Ejecutar auditoría silenciosa
            informe = ValidadorCoherenciaCooperaciones.auditar_integridad_completa(self.cooperaciones)
            
            # Registrar resultado
            if informe['estado'] != 'OK':
                registrar_operacion(
                    'AUDITORÍA_INICIAL',
                    f"Auditoría de coherencia: {informe['estado']}",
                    informe['resumen']
                )
            
            # Si hay advertencias importantes, registrar pero no mostrar popup (para no bloquear UI)
            if informe['recomendaciones']:
                for recomendación in informe['recomendaciones'][:3]:  # Log solo primeras 3
                    registrar_error('control_pagos', '_auditar_coherencia_inicial', recomendación)
        
        except Exception as e:
            registrar_error('control_pagos', '_auditar_coherencia_inicial', str(e))
    
    def _sincronizar_nombres_desde_bd(self):
        """Ya no necesario - los nombres vienen sincronizados desde BD"""
        pass
    
    def cerrar_aplicacion(self):
        """Cerrar aplicación con backup automático silencioso"""
        try:
            # Hacer backup silencioso (los datos ya se guardan en tiempo real con guardar_datos)
            try:
                resultado = self.gestor_backups.crear_backup_completo()
                if resultado['exito']:
                    # Limpiar backups antiguos (mantener solo últimos 10)
                    self.gestor_backups.limpiar_backups_antiguos(10)
                    registrar_operacion('BACKUP_AUTO', 'Backup automático creado al cerrar', 
                        {'archivo': resultado['nombre_carpeta']})
            except:
                pass  # No es crítico si falla el backup
            
            # Cerrar sesión si hay usuario activo
            if self.usuario_actual and self.gestor_auth:
                registrar_operacion('LOGOUT', 'Usuario cerró sesión', 
                    {'usuario': self.usuario_actual['nombre']}, self.usuario_actual['nombre'])
            
            # Cerrar aplicación
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            registrar_error('CERRAR_APP', str(e))
            self.root.quit()
            self.root.destroy()

def main():
    """Punto de entrada principal con autenticación"""
    from src.auth.login_window import VentanaLogin
    
    # Crear ventana de login
    login_root = tk.Tk()
    
    def on_login_exitoso(usuario, gestor_auth):
        """Callback cuando el login es exitoso"""
        # Cerrar ventana de login
        login_root.destroy()
        
        # Crear ventana principal
        root = tk.Tk()
        root.title(f"Sistema de Control de Pagos - {usuario['nombre']} ({usuario['rol']})")
        
        # Crear aplicación
        app = SistemaControlPagos(root)
        app.set_usuario(usuario, gestor_auth)
        
        # Cargar nombre de proyecto guardado si existe
        if hasattr(app, '_proyecto_guardado'):
            app.proyecto_var.set(app._proyecto_guardado)
        
        # Iniciar mainloop de la ventana principal
        root.mainloop()
    
    VentanaLogin(login_root, on_login_exitoso)
    login_root.mainloop()

if __name__ == "__main__":
    main()
