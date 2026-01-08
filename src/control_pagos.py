import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime
import requests
import subprocess
import sys
import time
import threading
from seguridad import seguridad
from logger import registrar_operacion, registrar_error, registrar_transaccion
from config import TEMAS, TAMAÑOS_LETRA, API_URL, PASSWORD_CIFRADO, ARCHIVO_PAGOS, MODO_OFFLINE
from validadores import validar_nombre, validar_monto, ErrorValidacion
from exportador import ExportadorExcel
from backups import GestorBackups
from historial import GestorHistorial
from buscador import BuscadorAvanzado
from tema_moderno import TEMA_CLARO, TEMA_OSCURO, FUENTES, ESPACIADO, ICONOS
from ui_moderna import BarraSuperior, PanelModerno, BotonModerno

class SistemaControlPagos:
    # Los temas y tamaños ahora vienen de config.py

    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Control de Pagos - Proyectos Comunitarios")
        self.root.state('zoomed')  # Pantalla completa en Windows

        # Configuración visual proveniente de config.py y tema moderno
        self.TEMAS = TEMAS
        self.TAMAÑOS_LETRA = TAMAÑOS_LETRA
        self.tema_claro = TEMA_CLARO
        self.tema_oscuro = TEMA_OSCURO
        self.style = ttk.Style()
        # Tema y accesibilidad
        self.tema_actual = tk.StringVar(value='claro')
        self.tamaño_actual = tk.StringVar(value='normal')
        
        # Datos
        self.coop_activa_id = None
        self.cooperacion_actual = None  # Nombre descriptivo de la cooperacion activa
        self.personas = []
        self.monto_cooperacion = 100.0
        self.proyecto_actual = "Proyecto Comunitario 2026"
        self.mostrar_total = False
        self.archivo_datos = ARCHIVO_PAGOS
        self.password_archivo = PASSWORD_CIFRADO
        self.password_hash = None
        self.api_url = API_URL
        self.fila_animada = None
        self.guardado_pendiente = None  # Timer para debounce de guardado
        self.usuario_actual = None  # Usuario autenticado
        self.gestor_auth = None  # Gestor de autenticación
        self.gestor_historial = GestorHistorial()  # Gestor de historial
        self.buscador = BuscadorAvanzado()  # Buscador avanzado
        self.gestor_backups = GestorBackups()  # Gestor de backups
        self.tree_persona_map = {}  # Mapea iids del tree a objetos persona
        self.permisos_rol = self.gestor_auth.ROLES if self.gestor_auth else {}
        self.api_caida_notificada = False
        self.barra_superior = None  # Referencia a barra superior para actualizaciones
        
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

        # Configurar estilos iniciales
        self.configurar_estilos()
        
        # Verificar/iniciar API local
        if not self.asegurar_api_activa():
            messagebox.showerror("Error", "No se pudo iniciar ni conectar con la API local")
            return
        self.iniciar_watchdog_api()
        
        # Verificar/establecer contraseña primera vez
        if not self.verificar_password_inicial():
            return
        
        self.nombre_visible = tk.BooleanVar(value=True)
        self.folio_visible = tk.BooleanVar(value=True)
        
        # Configurar interfaz
        self.configurar_interfaz()
        self.aplicar_tema()  # Aplicar tema inicial
        
        # Configurar backup automático al cerrar
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
    
    def set_usuario(self, usuario, gestor_auth):
        """Configurar usuario autenticado"""
        self.usuario_actual = usuario
        self.gestor_auth = gestor_auth
        self.permisos_rol = self.gestor_auth.ROLES if self.gestor_auth else {}
        registrar_operacion('LOGIN', 'Usuario inició sesión', 
            {'usuario': usuario['nombre'], 'rol': usuario['rol']}, usuario['nombre'])

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
        """Obtener paleta de colores del tema actual"""
        return self.TEMAS[self.tema_actual.get()]

    def configurar_estilos(self):
        """Configura estilos ttk segun tema actual"""
        colores = self.obtener_colores()
        tema_visual = TEMA_CLARO if self.tema_actual.get() == 'claro' else TEMA_OSCURO
        base_bg = colores.get('bg', tema_visual['bg_principal'])
        base_fg = colores.get('fg', tema_visual['fg_principal'])

        self.style.theme_use('clam')
        self.style.configure('TFrame', background=base_bg)
        self.style.configure('TLabelframe', background=colores['frame_bg'], foreground=base_fg, font=FUENTES['subtitulo'])
        self.style.configure('TLabelframe.Label', background=colores['frame_bg'], foreground=base_fg, font=FUENTES['subtitulo'])
        self.style.configure('TLabel', background=base_bg, foreground=base_fg, font=FUENTES['normal'])
        self.style.configure('TButton', background=tema_visual['accent_primary'], foreground='#ffffff', padding=8, borderwidth=0, font=FUENTES['botones'])
        self.style.map('TButton', background=[('active', tema_visual['accent_secondary'])], foreground=[('active', '#ffffff')])
        self.style.configure('TCheckbutton', background=base_bg, foreground=base_fg, font=FUENTES['normal'])
        self.style.configure('TEntry', fieldbackground=colores['entrada_bg'], borderwidth=1)
        self.style.configure('Treeview', background=tema_visual['table_row_even'], fieldbackground=tema_visual['table_row_even'],
                             foreground=base_fg, borderwidth=0, rowheight=26, font=FUENTES['normal'])
        self.style.map('Treeview', background=[('selected', tema_visual['table_selected'])], foreground=[('selected', tema_visual['fg_principal'])])
        self.style.configure('Treeview.Heading', background=tema_visual['table_header'], foreground=base_fg,
                             padding=8, font=FUENTES['subtitulo'], borderwidth=1, relief='flat')
    
    def obtener_tamaños(self):
        """Obtener tamaños de letra"""
        return self.TAMAÑOS_LETRA[self.tamaño_actual.get()]
    
    def aplicar_tema(self, *args):
        """Aplicar cambios de tema a toda la interfaz inmediatamente"""
        if not hasattr(self, 'tree'):
            return  # Aún no se ha creado la interfaz

        colores = self.obtener_colores()
        tema_visual = TEMA_CLARO if self.tema_actual.get() == 'claro' else TEMA_OSCURO
        self.configurar_estilos()
        try:
            self.root.configure(bg=colores['bg'])
        except:
            pass
        
        # Zebra + estados con alto contraste
        self.tree.tag_configure('fila_par', background=tema_visual['table_row_even'], foreground=tema_visual['fg_principal'])
        self.tree.tag_configure('fila_impar', background=tema_visual['table_row_odd'], foreground=tema_visual['fg_principal'])
        self.tree.tag_configure('pagado', foreground=colores['exito_fg'])
        self.tree.tag_configure('pendiente', foreground=colores['error_fg'])
        self.tree.tag_configure('parcial', foreground=colores['alerta_fg'])
        self.tree.tag_configure('pago_ok', background=colores['exito_fg'], foreground='#fff')
        self.tree.tag_configure('pago_parcial', background=colores['alerta_fg'], foreground='#1a1a1a')

        if hasattr(self, 'menu_persona'):
            self.menu_persona.configure(
                bg=tema_visual['bg_secundario'],
                fg=tema_visual['fg_principal'],
                activebackground=tema_visual['accent_secondary'],
                activeforeground=tema_visual['fg_principal']
            )
        
        # Actualizar etiquetas de total
        if hasattr(self, 'total_pagado_label'):
            self.total_pagado_label.config(foreground=colores['exito_fg'])
        if hasattr(self, 'total_pendiente_label'):
            self.total_pendiente_label.config(foreground=colores['error_fg'])
        
        # Refrescar tabla para aplicar cambios
        self.actualizar_tabla()
        self.guardar_datos(mostrar_alerta=False)
    
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
            if seguridad.verificar_password(password, self.password_hash):
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
        self.cooperacion_actual = coop.get('nombre', 'Cooperacion')

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
    
    def corregir_folios(self):
        """Detecta y corrige folios duplicados sincronizando con el censo"""
        from utilidades import detectar_folios_duplicados, corregir_folios_duplicados
        
        # Detectar duplicados
        duplicados = detectar_folios_duplicados(self.personas)
        
        if not duplicados:
            messagebox.showinfo("Sin Problemas", "No se encontraron folios duplicados en esta cooperación")
            return
        
        # Mostrar información de duplicados
        mensaje_duplicados = "Folios duplicados encontrados:\n\n"
        for folio, nombres in duplicados.items():
            mensaje_duplicados += f"Folio {folio}:\n"
            for nombre in nombres:
                mensaje_duplicados += f"  - {nombre}\n"
            mensaje_duplicados += "\n"
        
        mensaje_duplicados += "\n¿Desea corregir automáticamente sincronizando con el censo?"
        
        if not messagebox.askyesno("Folios Duplicados Detectados", mensaje_duplicados):
            return
        
        # Corregir
        resultado = corregir_folios_duplicados(self.personas, self.api_url)
        
        if resultado['exito']:
            self.actualizar_tabla()
            self.guardar_datos(mostrar_alerta=False, inmediato=True)
            
            mensaje = f"{resultado['mensaje']}\n\n"
            mensaje += f"Duplicados encontrados: {resultado.get('duplicados_encontrados', 0)}\n"
            mensaje += f"Folios corregidos: {resultado.get('corregidos', 0)}"
            
            if resultado.get('errores'):
                mensaje += f"\n\nErrores: {len(resultado['errores'])}"
            
            messagebox.showinfo("Corrección Completada", mensaje)
        else:
            messagebox.showerror("Error", f"Error al corregir folios: {resultado.get('error', 'Desconocido')}")

    def refrescar_interfaz_cooperacion(self):
        coop = self.obtener_cooperacion_activa()
        if not coop:
            return
        self.personas = coop.setdefault('personas', [])
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
        main_frame.rowconfigure(5, weight=1)  # Fila 5 es donde está la tabla
        
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
        ttk.Button(control_frame, text="🔍 Búsqueda Avanzada", command=self.abrir_busqueda_avanzada, width=18).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Editar Seleccionado", command=self.editar_persona, width=16).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Eliminar Seleccionado", command=self.eliminar_persona, width=16).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Registrar Pago", command=self.registrar_pago, width=16).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="📜 Ver Historial", command=self.ver_historial_completo, width=15).pack(side=tk.LEFT, padx=5)
        
        # Segunda fila de botones
        control_frame2 = ttk.Frame(main_frame)
        control_frame2.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(control_frame2, text="Sincronizar con Censo", command=self.sincronizar_coop_con_censo, width=18).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame2, text="Corregir Folios Duplicados", command=self.corregir_folios, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame2, text="Exportar a Excel", command=self.exportar_excel, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame2, text="Crear Backup", command=self.crear_backup, width=15).pack(side=tk.LEFT, padx=5)
        
        # Botón para mostrar/ocultar total
        self.btn_toggle_total = ttk.Button(control_frame2, text="Mostrar Total Recaudado", command=self.toggle_total, width=20)
        self.btn_toggle_total.pack(side=tk.RIGHT, padx=5)
        
        # ===== PANEL DE TOTAL (OCULTO INICIALMENTE) =====
        self.total_frame = ttk.LabelFrame(main_frame, text="Resumen Financiero", padding="10")
        self.total_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
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
        table_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
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
        
        # Menú contextual sobre filas
        tema_visual = TEMA_CLARO if self.tema_actual.get() == 'claro' else TEMA_OSCURO
        self.menu_persona = tk.Menu(self.root, tearoff=0,
                        bg=tema_visual['bg_secundario'],
                        fg=tema_visual['fg_principal'],
                        activebackground=tema_visual['accent_secondary'],
                        activeforeground=tema_visual['fg_principal'])
        self.menu_persona.add_command(label=f"{ICONOS['editar']} Editar persona", command=self.editar_persona)
        self.menu_persona.add_command(label=f"{ICONOS['guardar']} Registrar pago", command=self.registrar_pago)
        self.menu_persona.add_command(label=f"{ICONOS['eliminar']} Eliminar", command=self.eliminar_persona)
        self.menu_persona.add_separator()
        self.menu_persona.add_command(label=f"{ICONOS['buscar']} Ver historial", command=self.ver_historial_completo)
        self.tree.bind('<Button-3>', self._mostrar_menu_persona)
        
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
        if MODO_OFFLINE:
            return self.generar_folio_local()
        try:
            # Buscar por nombre exacto
            response = requests.get(f"{self.api_url}/habitantes/nombre/{nombre}",
                                    timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['success'] and data['habitante']:
                    folio = data['habitante']['folio']
                    # Verificar que el folio no esté duplicado en esta cooperación
                    if not any(p.get('folio') == folio and p['nombre'].lower() != nombre.lower() for p in self.personas):
                        return folio
                    else:
                        print(f"Advertencia: Folio {folio} ya usado en cooperación por otra persona")
                        return None
        except Exception as e:
            print(f"Error al buscar en censo: {e}")
        
        # Si no existe, intentar agregarlo al censo
        try:
            response = requests.post(f"{self.api_url}/habitantes",
                                    json={'nombre': nombre},
                                    timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['success'] and data['habitante']:
                    folio = data['habitante']['folio']
                    # Verificar que el folio no esté duplicado
                    if not any(p.get('folio') == folio for p in self.personas):
                        return folio
                    else:
                        print(f"Advertencia: Folio {folio} duplicado")
                        return None
        except Exception as e:
            print(f"Error al agregar al censo: {e}")
        
        # Si todo falla, no retornar nada
        return None

    def asegurar_api_activa(self):
        """Comprueba la API y la levanta si no está activa"""
        if MODO_OFFLINE:
            return True
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
        if MODO_OFFLINE:
            return True
        try:
            response = requests.get(f"{self.api_url}/ping", timeout=1.5)
            return response.status_code == 200
        except:
            return False

    def iniciar_watchdog_api(self):
        """Hilo de monitoreo ligero para reintentar API local"""
        def monitor():
            while True:
                time.sleep(10)
                if self.verificar_api():
                    self.api_caida_notificada = False
                    continue
                # intentar reiniciar
                if self.asegurar_api_activa():
                    self.api_caida_notificada = False
                    continue
                if not self.api_caida_notificada:
                    registrar_error('API', 'watchdog', 'API local no responde')
                    try:
                        messagebox.showwarning("API", "API local no responde; reintentando en segundo plano")
                    except:
                        pass
                    self.api_caida_notificada = True
        hilo = threading.Thread(target=monitor, daemon=True)
        hilo.start()

    def generar_folio_local(self):
        """Genera un folio local único cuando no hay API"""
        base = "LOC"
        intento = 0
        while True:
            sufijo = int(time.time() * 1000) % 1000000
            folio = f"{base}-{sufijo:06d}"
            if not any(p.get('folio') == folio for p in self.personas):
                return folio
            intento += 1
            if intento > 3:
                folio = f"{base}-{sufijo:06d}-{intento}"
                if not any(p.get('folio') == folio for p in self.personas):
                    return folio
    
    def actualizar_monto(self):
        if not self._tiene_permiso('editar'):
            return
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
        if not self._tiene_permiso('crear'):
            return
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
                messagebox.showwarning("Aviso", "No se pudo obtener folio desde censo. Se generará folio local.")
                folio = self.generar_folio_local()
            
            persona = {
                'nombre': nombre,
                'folio': folio,
                'monto_esperado': self.monto_cooperacion,
                'pagos': [],  # Lista de pagos parciales
                'notas': notas_entry.get().strip()
            }
            
            self.personas.append(persona)
            
            # Registrar en historial
            usuario = self.usuario_actual['nombre'] if self.usuario_actual else 'Sistema'
            self.gestor_historial.registrar_creacion('PERSONA', folio, persona, usuario)
            
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
            
            # Guardar valores anteriores para historial
            cambios = {}
            if persona['nombre'] != nombre:
                cambios['nombre'] = {'anterior': persona['nombre'], 'nuevo': nombre}
            if persona.get('notas', '') != notas_entry.get().strip():
                cambios['notas'] = {'anterior': persona.get('notas', ''), 'nuevo': notas_entry.get().strip()}
            
            self.personas[index]['nombre'] = nombre
            self.personas[index]['notas'] = notas_entry.get().strip()
            
            # Registrar en historial si hubo cambios
            if cambios:
                usuario = self.usuario_actual['nombre'] if self.usuario_actual else 'Sistema'
                self.gestor_historial.registrar_cambio('EDITAR', 'PERSONA', persona.get('folio', ''), cambios, usuario)
            
            self.actualizar_tabla()
            self.actualizar_totales()
            dialog.destroy()
            messagebox.showinfo("Exito", "Persona actualizada correctamente")
        
        ttk.Button(dialog, text="Guardar Cambios", command=guardar).pack(pady=15)
    
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
        
        if messagebox.askyesno("Confirmar", f"¿Esta seguro de eliminar a {persona['nombre']}?"):
            # Registrar en historial antes de eliminar
            usuario = self.usuario_actual['nombre'] if self.usuario_actual else 'Sistema'
            self.gestor_historial.registrar_cambio('ELIMINAR', 'PERSONA', persona.get('folio', ''), 
                {'persona_eliminada': persona}, usuario)
            
            self.personas.pop(index)
            self.actualizar_tabla()
            self.actualizar_totales()
            messagebox.showinfo("Exito", "Persona eliminada correctamente")
    
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
        dialog.geometry("520x420")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tamaños = self.obtener_tamaños()
        colores = self.obtener_colores()
        tema_visual = TEMA_CLARO if self.tema_actual.get() == 'claro' else TEMA_OSCURO
        dialog.configure(bg=tema_visual['bg_principal'])

        header = tk.Frame(dialog, bg=tema_visual['bg_secundario'])
        header.pack(fill=tk.X, padx=14, pady=(14, 10))
        tk.Label(header, text=ICONOS['usuario'], font=('Segoe UI', 28),
                 bg=tema_visual['bg_secundario'], fg=tema_visual['accent_primary']).pack(side=tk.LEFT, padx=(0, 12))
        info_text = tk.Frame(header, bg=tema_visual['bg_secundario'])
        info_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(info_text, text=persona['nombre'], font=FUENTES['titulo'],
                 bg=tema_visual['bg_secundario'], fg=tema_visual['fg_principal']).pack(anchor=tk.W)
        tk.Label(info_text, text=f"Folio {persona.get('folio', 'SIN-FOLIO')}", font=FUENTES['pequeño'],
                 bg=tema_visual['bg_secundario'], fg=tema_visual['fg_secundario']).pack(anchor=tk.W)

        resumen = tk.Frame(dialog, bg=tema_visual['bg_principal'])
        resumen.pack(fill=tk.X, padx=16, pady=(4, 12))
        def chip(parent, label, valor, color_fg):
            cont = tk.Frame(parent, bg=tema_visual['bg_secundario'], padx=10, pady=8)
            cont.pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)
            tk.Label(cont, text=label, font=FUENTES['pequeño'],
                     bg=tema_visual['bg_secundario'], fg=tema_visual['fg_secundario']).pack(anchor=tk.W)
            tk.Label(cont, text=valor, font=FUENTES['titulo'],
                     bg=tema_visual['bg_secundario'], fg=color_fg).pack(anchor=tk.W)
        chip(resumen, "Esperado", f"${monto_esperado:.2f}", tema_visual['fg_principal'])
        chip(resumen, "Pagado", f"${total_pagado:.2f}", colores['exito_fg'])
        chip(resumen, "Pendiente", f"${pendiente:.2f}", colores['error_fg'])

        form = tk.Frame(dialog, bg=tema_visual['bg_principal'])
        form.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))
        tk.Label(form, text="Monto de este pago", font=FUENTES['subtitulo'],
                 bg=tema_visual['bg_principal'], fg=tema_visual['fg_principal']).pack(anchor=tk.W, pady=(0, 6))
        monto_var = tk.DoubleVar(value=pendiente)
        monto_entry = tk.Entry(form, textvariable=monto_var, font=FUENTES['titulo'], width=18,
                               bg=tema_visual['input_bg'], fg=tema_visual['fg_principal'],
                               relief=tk.SOLID, bd=1, insertbackground=tema_visual['accent_primary'])
        monto_entry.pack(anchor=tk.W, pady=(0, 10))
        tk.Label(form, text="Puedes registrar pagos parciales. Si ingresas más que el pendiente se te pedirá confirmar.",
                 font=FUENTES['pequeño'], bg=tema_visual['bg_principal'], fg=tema_visual['fg_secundario'], wraplength=460,
                 justify=tk.LEFT).pack(anchor=tk.W)
        
        def guardar_pago(event=None):
            try:
                monto_pago = monto_var.get()
                
                # Validar el monto (lanza ErrorValidacion si es invalido)
                try:
                    monto_pago = validar_monto(monto_pago)
                except ErrorValidacion as e:
                    messagebox.showerror("Error", str(e))
                    return
                
                if monto_pago > pendiente:
                    if not messagebox.askyesno("Confirmar", 
                        f"El monto (${monto_pago:.2f}) es mayor al pendiente (${pendiente:.2f}).\n¿Desea continuar?"):
                        return
                
                # Registrar el pago
                pago = {
                    'monto': monto_pago,
                    'fecha': datetime.now().strftime("%d/%m/%Y"),
                    'hora': datetime.now().strftime("%H:%M:%S"),
                    'usuario': self.usuario_actual['nombre'] if self.usuario_actual else 'Sistema'
                }
                
                if 'pagos' not in persona:
                    persona['pagos'] = []
                
                persona['pagos'].append(pago)

                # Registrar en historial de auditoría
                cambios_hist = {
                    'monto': monto_pago,
                    'total_anterior': total_pagado,
                    'total_nuevo': total_pagado + monto_pago,
                    'pendiente_anterior': pendiente,
                    'pendiente_nuevo': max(0, pendiente - monto_pago)
                }
                self.gestor_historial.registrar_cambio(
                    'PAGO',
                    'PERSONA',
                    persona.get('folio', 'SIN-FOLIO'),
                    cambios_hist,
                    self.usuario_actual['nombre'] if self.usuario_actual else 'Sistema'
                )
                
                # Registrar en log
                registrar_operacion('PAGO_REGISTRADO', 'Pago registrado correctamente', {
                    'nombre': persona['nombre'],
                    'folio': persona.get('folio', 'SIN-FOLIO'),
                    'monto': monto_pago,
                    'cooperacion': self.cooperacion_actual
                })
                
                # Refrescar datos y UI
                self.actualizar_totales()
                self.guardar_datos(mostrar_alerta=False)
                self.actualizar_tabla()
                dialog.destroy()

                # Visual feedback: animar la fila (puede cambiar el item tras refresco)
                nuevo_total = sum(p['monto'] for p in persona['pagos'])
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
                
            except Exception as e:
                # Mostrar el error inesperado para que no falle silencioso
                registrar_error('control_pagos', 'registrar_pago', str(e))
                messagebox.showerror("Error", f"No se pudo registrar el pago: {e}")
        
        botones = tk.Frame(dialog, bg=tema_visual['bg_principal'])
        botones.pack(fill=tk.X, pady=18, padx=16)
        tk.Button(botones, text=f"{ICONOS['guardar']} Registrar", command=guardar_pago,
              font=FUENTES['botones'], bg=tema_visual['accent_primary'], fg='#ffffff',
              relief=tk.FLAT, padx=16, pady=10, cursor='hand2',
              activebackground=tema_visual['accent_secondary']).pack(side=tk.LEFT, padx=(0, 10), expand=True, fill=tk.X)
        tk.Button(botones, text=f"{ICONOS['cerrar']} Cancelar", command=dialog.destroy,
              font=FUENTES['botones'], bg=tema_visual['error'], fg='#ffffff',
              relief=tk.FLAT, padx=14, pady=10, cursor='hand2',
              activebackground='#bb2d3b').pack(side=tk.LEFT, expand=True, fill=tk.X)
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
                persona = self.tree_persona_map.get(item)
                if not persona:
                    return
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
        persona = self.tree_persona_map.get(item)
        if not persona:
            messagebox.showerror("Error", "No se pudo localizar la persona seleccionada")
            return
        
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
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree_persona_map = {}
        
        # Filtrar personas si hay búsqueda activa
        personas_mostrar = self.personas
        criterio = self.search_var.get().strip().lower()
        
        if criterio:
            personas_mostrar = [p for p in self.personas 
                               if criterio in p['nombre'].lower() or 
                               criterio in p.get('folio', '').lower()]
        
        # Agregar personas
        for idx, persona in enumerate(personas_mostrar):
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
            
            iid = self._persona_iid(persona)
            self.tree.insert('', tk.END, iid=iid,
                           values=(persona.get('folio', 'SIN-FOLIO'),
                                  persona['nombre'],
                                  f"${monto_esperado:.2f}",
                                  f"${total_pagado:.2f}",
                                  f"${pendiente:.2f}",
                                  estado,
                                  ultimo_pago,
                                  persona.get('notas', '')),
                           tags=(tag, 'fila_par' if idx % 2 == 0 else 'fila_impar'))
            self.tree_persona_map[iid] = persona
        
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

    def _persona_iid(self, persona):
        """Devuelve un iid estable para el Treeview basado en el objeto persona"""
        folio = persona.get('folio', 'SIN-FOLIO')
        return f"{folio}|{id(persona)}"
    
    def guardar_datos(self, mostrar_alerta=True, inmediato=False):
        """Guardar datos con debounce para evitar conflictos"""
        if inmediato:
            self._ejecutar_guardado(mostrar_alerta)
        else:
            # Cancelar guardado pendiente
            if self.guardado_pendiente:
                self.root.after_cancel(self.guardado_pendiente)
            # Programar nuevo guardado en 500ms
            self.guardado_pendiente = self.root.after(500, lambda: self._ejecutar_guardado(mostrar_alerta))
    
    def _ejecutar_guardado(self, mostrar_alerta=True):
        """Ejecuta el guardado real de datos"""
        try:
            self.guardado_pendiente = None
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
            
            # Guardar cifrado en ubicación segura
            if seguridad.cifrar_archivo(datos, self.archivo_datos, self.password_archivo):
                if mostrar_alerta:
                    messagebox.showinfo("Exito", "Datos guardados correctamente")
            else:
                if mostrar_alerta:
                    messagebox.showerror("Error", "Error al guardar los datos")
        except Exception as e:
            if mostrar_alerta:
                messagebox.showerror("Error", f"Error al guardar: {str(e)}")

    def cargar_datos(self):
        try:
            if seguridad.archivo_existe(self.archivo_datos):
                datos = seguridad.descifrar_archivo(self.archivo_datos, self.password_archivo)
                if datos:
                    self.password_hash = datos.get('password_hash', self.password_hash)
                    if 'cooperaciones' in datos:
                        self.cooperaciones = datos.get('cooperaciones', [])
                        self.coop_activa_id = datos.get('cooperacion_activa')
                        self.tema_guardado = datos.get('tema', 'claro')
                        self.tamaño_guardado = datos.get('tamaño', 'normal')
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
        except Exception as e:
            print(f"Error al cargar datos: {str(e)}")
    
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
            
            # Solicitar ubicación de guardado
            archivo = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"{nombre_coop}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if not archivo:
                return
            
            # Exportar usando el módulo exportador
            exportador = ExportadorExcel()
            ruta_archivo = exportador.exportar_personas_cooperacion(
                self.personas, nombre_coop, os.path.basename(archivo)
            )
            
            if ruta_archivo:
                registrar_operacion('EXPORTAR_EXCEL', 'Datos exportados a Excel', 
                    {'cooperacion': nombre_coop, 'archivo': ruta_archivo, 'total_personas': len(self.personas)})
                messagebox.showinfo("Éxito", f"Datos exportados correctamente a:\n{ruta_archivo}")
            else:
                messagebox.showerror("Error", "No se pudo exportar el archivo")
        except Exception as e:
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
    
    def set_usuario(self, usuario, gestor_auth):
        """Configurar usuario autenticado"""
        self.usuario_actual = usuario
        self.gestor_auth = gestor_auth
        registrar_operacion('LOGIN', 'Usuario inició sesión', 
            {'usuario': usuario['nombre'], 'rol': usuario['rol']}, usuario['nombre'])
    
    def abrir_busqueda_avanzada(self):
        """Abrir ventana de búsqueda avanzada"""
        if not self.personas:
            messagebox.showinfo("Información", "No hay personas para buscar")
            return
        
        from ventana_busqueda import VentanaBusquedaAvanzada
        VentanaBusquedaAvanzada(self.root, self.personas, self.seleccionar_persona_busqueda)
    
    def seleccionar_persona_busqueda(self, persona):
        """Callback cuando se selecciona una persona en la búsqueda"""
        # Seleccionar el iid asociado en el tree
        iid = self._persona_iid(persona)
        if self.tree.exists(iid):
            self.tree.selection_set(iid)
            self.tree.see(iid)
    
    def ver_historial_completo(self):
        """Abrir ventana de historial completo"""
        from ventana_historial import VentanaHistorial
        VentanaHistorial(self.root)
    
    def cerrar_aplicacion(self):
        """Cerrar aplicación con backup automático"""
        try:
            # Preguntar si desea crear backup
            respuesta = messagebox.askyesno("Backup Automático", 
                "¿Desea crear un backup antes de salir?")
            
            if respuesta:
                registrar_operacion('BACKUP_AUTO', 'Creando backup automático al cerrar', {})
                resultado = self.gestor_backups.crear_backup_completo()
                if resultado['exito']:
                    # Limpiar backups antiguos (mantener solo últimos 10)
                    try:
                        self.gestor_backups.limpiar_backups_antiguos(10)
                    except:
                        pass  # No es crítico si falla
                    messagebox.showinfo("Backup Creado", 
                        f"Backup creado exitosamente:\n{resultado['nombre_carpeta']}")
            
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
    # Crear ventana principal (oculta inicialmente)
    root = tk.Tk()
    root.withdraw()
    
    # Crear ventana de login
    from login_window import VentanaLogin
    
    def on_login_exitoso(usuario, gestor_auth):
        """Callback cuando el login es exitoso"""
        # Mostrar ventana principal
        root.deiconify()
        
        # Crear aplicación
        app = SistemaControlPagos(root)
        app.set_usuario(usuario, gestor_auth)
        
        # Cargar nombre de proyecto guardado si existe
        if hasattr(app, '_proyecto_guardado'):
            app.proyecto_var.set(app._proyecto_guardado)
        
        # Actualizar título con usuario
        root.title(f"Sistema de Control de Pagos - {usuario['nombre']} ({usuario['rol']})")
    
    # Crear ventana de login
    login_root = tk.Tk()
    VentanaLogin(login_root, on_login_exitoso)
    login_root.mainloop()

if __name__ == "__main__":
    main()
