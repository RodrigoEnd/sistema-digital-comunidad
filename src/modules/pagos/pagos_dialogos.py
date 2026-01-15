"""
Módulo de diálogos para el sistema de control de pagos
Contiene todas las ventanas emergentes y diálogos de interacción
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import time

from src.ui.tema_moderno import FUENTES, ICONOS
from src.core.validadores import validar_monto, ErrorValidacion
from src.core.logger import registrar_operacion, registrar_error


class DialogoRegistrarPago:
    """Diálogo para registrar un nuevo pago (completo o parcial)"""
    
    @staticmethod
    def mostrar(parent, persona, monto_esperado, gestor_historial, usuario_actual, 
                callback_ok, cooperacion_actual, tema_global):
        """
        Muestra el diálogo para registrar un pago
        
        Args:
            parent: Ventana padre
            persona: Dict con datos de la persona
            monto_esperado: Monto total esperado
            gestor_historial: Instancia de GestorHistorial
            usuario_actual: Dict con datos del usuario actual
            callback_ok: Función a llamar cuando se registre el pago exitosamente
            cooperacion_actual: Nombre de la cooperación actual
            tema_global: Tema visual
            
        Returns:
            True si se registró el pago, False si se canceló
        """
        # Calcular cuánto falta
        total_pagado = sum(pago['monto'] for pago in persona.get('pagos', []))
        pendiente = monto_esperado - total_pagado
        
        if pendiente <= 0:
            messagebox.showinfo("Información", "Esta persona ya completó su pago")
            return False
        
        # Crear diálogo
        dialog = tk.Toplevel(parent)
        dialog.title("Registrar Pago")
        dialog.geometry("520x420")
        dialog.transient(parent)
        dialog.grab_set()
        dialog.configure(bg=tema_global['bg_principal'])
        
        # Header con información de la persona
        header = tk.Frame(dialog, bg=tema_global['bg_secundario'])
        header.pack(fill=tk.X, padx=14, pady=(14, 10))
        
        tk.Label(header, text=ICONOS['usuario'], font=('Segoe UI', 28),
                 bg=tema_global['bg_secundario'], fg=tema_global['accent_primary']).pack(
                     side=tk.LEFT, padx=(0, 12))
        
        info_text = tk.Frame(header, bg=tema_global['bg_secundario'])
        info_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(info_text, text=persona['nombre'], font=FUENTES['titulo'],
                 bg=tema_global['bg_secundario'], fg=tema_global['fg_principal']).pack(anchor=tk.W)
        tk.Label(info_text, text=f"Folio {persona.get('folio', 'SIN-FOLIO')}", font=FUENTES['pequeño'],
                 bg=tema_global['bg_secundario'], fg=tema_global['fg_secundario']).pack(anchor=tk.W)
        
        # Resumen con chips
        resumen = tk.Frame(dialog, bg=tema_global['bg_principal'])
        resumen.pack(fill=tk.X, padx=16, pady=(4, 12))
        
        def chip(parent_frame, label, valor, color_fg):
            cont = tk.Frame(parent_frame, bg=tema_global['bg_secundario'], padx=10, pady=8)
            cont.pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)
            tk.Label(cont, text=label, font=FUENTES['pequeño'],
                     bg=tema_global['bg_secundario'], fg=tema_global['fg_secundario']).pack(anchor=tk.W)
            tk.Label(cont, text=valor, font=FUENTES['titulo'],
                     bg=tema_global['bg_secundario'], fg=color_fg).pack(anchor=tk.W)
        
        chip(resumen, "Esperado", f"${monto_esperado:.2f}", tema_global['fg_principal'])
        chip(resumen, "Pagado", f"${total_pagado:.2f}", tema_global['success'])
        chip(resumen, "Pendiente", f"${pendiente:.2f}", tema_global['error'])
        
        # Formulario de monto
        form = tk.Frame(dialog, bg=tema_global['bg_principal'])
        form.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))
        
        tk.Label(form, text="Monto de este pago", font=FUENTES['subtitulo'],
                 bg=tema_global['bg_principal'], fg=tema_global['fg_principal']).pack(
                     anchor=tk.W, pady=(0, 6))
        
        monto_var = tk.DoubleVar(value=pendiente)
        monto_entry = tk.Entry(form, textvariable=monto_var, font=FUENTES['titulo'], width=18,
                               bg=tema_global['input_bg'], fg=tema_global['fg_principal'],
                               relief=tk.SOLID, bd=1, insertbackground=tema_global['accent_primary'])
        monto_entry.pack(anchor=tk.W, pady=(0, 10))
        
        tk.Label(form, text="Puedes registrar pagos parciales. Si ingresas más que el pendiente se te pedirá confirmar.",
                 font=FUENTES['pequeño'], bg=tema_global['bg_principal'], fg=tema_global['fg_secundario'],
                 wraplength=460, justify=tk.LEFT).pack(anchor=tk.W)
        
        # Variable para saber si se guardó
        pago_registrado = {'success': False}
        
        def guardar_pago(event=None):
            try:
                monto_pago = monto_var.get()
                
                # Validar el monto
                try:
                    monto_pago = validar_monto(monto_pago)
                except ErrorValidacion as e:
                    messagebox.showerror("Error", str(e))
                    return
                
                # Confirmar si el monto es mayor al pendiente
                if monto_pago > pendiente:
                    if not messagebox.askyesno("Confirmar Monto", 
                        f"El monto (${monto_pago:.2f}) es mayor al pendiente (${pendiente:.2f}).\n\n¿Desea continuar con el pago?"):
                        return
                
                # Registrar el pago directamente sin confirmación adicional
                
                # Registrar el pago
                pago = {
                    'monto': monto_pago,
                    'fecha': datetime.now().strftime("%d/%m/%Y"),
                    'hora': datetime.now().strftime("%H:%M:%S"),
                    'usuario': usuario_actual['nombre'] if usuario_actual else 'Sistema'
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
                    'pendiente_nuevo': max(0, pendiente - monto_pago),
                    'nombre': persona.get('nombre', '')
                }
                gestor_historial.registrar_cambio(
                    'PAGO',
                    'PERSONA',
                    persona.get('folio', 'SIN-FOLIO'),
                    cambios_hist,
                    usuario_actual['nombre'] if usuario_actual else 'Sistema'
                )
                
                # Registrar en log
                registrar_operacion('PAGO_REGISTRADO', 'Pago registrado correctamente', {
                    'nombre': persona['nombre'],
                    'folio': persona.get('folio', 'SIN-FOLIO'),
                    'monto': monto_pago,
                    'cooperacion': cooperacion_actual
                })
                
                pago_registrado['success'] = True
                dialog.destroy()
                
                # Llamar callback
                if callback_ok:
                    callback_ok(persona, monto_pago, total_pagado + monto_pago, monto_esperado)
                
            except Exception as e:
                registrar_error('pagos_dialogos', 'DialogoRegistrarPago.guardar_pago', str(e))
                messagebox.showerror("Error", f"No se pudo registrar el pago: {e}")
        
        # Botones
        botones = tk.Frame(dialog, bg=tema_global['bg_principal'])
        botones.pack(fill=tk.X, pady=18, padx=16)
        
        tk.Button(botones, text=f"{ICONOS['guardar']} Registrar", command=guardar_pago,
                  font=FUENTES['botones'], bg=tema_global['accent_primary'], fg='#ffffff',
                  relief=tk.FLAT, padx=16, pady=10, cursor='hand2',
                  activebackground=tema_global['accent_secondary']).pack(
                      side=tk.LEFT, padx=(0, 10), expand=True, fill=tk.X)
        
        tk.Button(botones, text=f"{ICONOS['cerrar']} Cancelar", command=dialog.destroy,
                  font=FUENTES['botones'], bg=tema_global['error'], fg='#ffffff',
                  relief=tk.FLAT, padx=14, pady=10, cursor='hand2',
                  activebackground='#bb2d3b').pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        dialog.bind("<Return>", guardar_pago)
        monto_entry.focus()
        monto_entry.select_range(0, tk.END)
        
        # Centrar diálogo
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Esperar a que se cierre
        dialog.wait_window()
        
        return pago_registrado['success']


class DialogoAgregarPersona:
    """Diálogo para agregar una nueva persona al sistema"""
    
    @staticmethod
    def mostrar(parent, monto_cooperacion, cooperacion_actual, gestor_personas, 
                gestor_historial, usuario_actual, callback_sincronizar_censo,
                callback_generar_folio, callback_ok, tema_global=None):
        """
        Muestra el diálogo para agregar una nueva persona
        
        Args:
            parent: Ventana padre
            monto_cooperacion: Monto base de la cooperación
            cooperacion_actual: Nombre de la cooperación actual
            gestor_personas: Instancia de GestorPersonas
            gestor_historial: Instancia de GestorHistorial
            usuario_actual: Dict con datos del usuario actual
            callback_sincronizar_censo: Función para sincronizar con censo
            callback_generar_folio: Función para generar folio local
            callback_ok: Función a llamar cuando se agregue exitosamente
            tema_global: Dict con colores del tema visual
        """
        # Tema por defecto si no se proporciona
        if not tema_global:
            tema_global = {
                'bg_principal': '#f5f5f5',
                'bg_secundario': '#ffffff',
                'fg_principal': '#333333',
                'fg_secundario': '#666666',
                'input_bg': '#ffffff',
                'accent_primary': '#0078d4'
            }
        
        dialog = tk.Toplevel(parent)
        dialog.title("Agregar Nueva Persona")
        dialog.geometry("520x300")
        dialog.transient(parent)
        dialog.grab_set()
        dialog.configure(bg=tema_global['bg_principal'])
        
        # Campos con tema correcto
        tk.Label(dialog, text="Nombre Completo:", font=('Arial', 10, 'bold'),
                bg=tema_global['bg_principal'], fg=tema_global['fg_principal']).pack(
                pady=5, padx=20, anchor=tk.W)
        nombre_entry = tk.Entry(dialog, width=50, font=('Arial', 10),
                               bg=tema_global['input_bg'], fg=tema_global['fg_principal'],
                               relief=tk.SOLID, bd=1)
        nombre_entry.pack(pady=5, padx=20)
        
        tk.Label(dialog, text=f"Monto de cooperación: ${monto_cooperacion:.2f}", 
                font=('Arial', 9, 'italic'),
                bg=tema_global['bg_principal'], fg=tema_global['fg_secundario']).pack(pady=5, padx=20, anchor=tk.W)
        tk.Label(dialog, text=f"Cooperación activa: {cooperacion_actual or 'Actual'}", 
                font=('Arial', 9, 'italic'),
                bg=tema_global['bg_principal'], fg=tema_global['fg_secundario']).pack(pady=2, padx=20, anchor=tk.W)
        
        tk.Label(dialog, text="Notas (opcional):", font=('Arial', 10, 'bold'),
                bg=tema_global['bg_principal'], fg=tema_global['fg_principal']).pack(
                pady=5, padx=20, anchor=tk.W)
        notas_entry = tk.Entry(dialog, width=50, font=('Arial', 10),
                              bg=tema_global['input_bg'], fg=tema_global['fg_principal'],
                              relief=tk.SOLID, bd=1)
        notas_entry.pack(pady=5, padx=20)
        
        persona_agregada = {'persona': None}
        
        def guardar(event=None):
            nombre = nombre_entry.get().strip()
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
            
            # Verificar duplicados de nombre en pagos (en persona local)
            if not gestor_personas.validar_nombre_unico(nombre, None):
                messagebox.showerror("Error", "Ya existe una persona con ese nombre en esta cooperación")
                return
            
            # Sincronizar con API (verificar/agregar en censo)
            # Esto también evita duplicados en censo
            folio = callback_sincronizar_censo(nombre)
            if not folio:
                # Si no se puede obtener folio de censo, generar local
                folio = callback_generar_folio()
                messagebox.showinfo("Información", f"Se generó folio local: {folio}\nLa persona se agregará al censo cuando sea necesario.")
            else:
                messagebox.showinfo("Éxito", f"Persona vinculada a censo\nFolio: {folio}")
            
            # Validar que el folio no esté duplicado EN ESTA COOPERACIÓN
            if any(p.get('folio') == folio for p in gestor_personas.personas):
                messagebox.showerror("Error", f"Folio {folio} ya está registrado en esta cooperación para otra persona.")
                return
            
            persona = {
                'nombre': nombre,
                'folio': folio,
                'monto_esperado': monto_cooperacion,
                'pagos': [],
                'notas': notas_entry.get().strip()
            }
            
            persona_agregada['persona'] = persona
            
            # Registrar en historial
            usuario = usuario_actual['nombre'] if usuario_actual else 'Sistema'
            gestor_historial.registrar_creacion('PERSONA', folio, persona, usuario)
            
            # Registrar en log
            registrar_operacion('AGREGAR_PERSONA', 'Nueva persona agregada al sistema', {
                'cooperacion': cooperacion_actual or 'Sin nombre',
                'folio': folio,
                'nombre': nombre,
                'monto_esperado': f"${monto_cooperacion:.2f}",
                'notas': notas_entry.get().strip() or 'Sin notas',
                'usuario': usuario
            }, usuario)
            
            # Registrar cambio
            gestor_historial.registrar_cambio('CREAR', 'PERSONA', folio,
                {'nombre': {'anterior': None, 'nuevo': nombre},
                 'monto': {'anterior': None, 'nuevo': f"${monto_cooperacion:.2f}"}},
                usuario)
            
            dialog.destroy()
            
            if callback_ok:
                callback_ok(persona)
            
            messagebox.showinfo("Éxito", f"Persona agregada correctamente\nFolio: {folio}")
        
        botones = tk.Frame(dialog, bg=tema_global['bg_principal'])
        botones.pack(pady=20)
        tk.Button(botones, text="Confirmar", command=guardar, width=20,
                 bg=tema_global['accent_primary'], fg='white',
                 font=('Arial', 10), cursor='hand2', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        tk.Button(botones, text="Cancelar", command=dialog.destroy, width=14,
                 bg='#d32f2f', fg='white',
                 font=('Arial', 10), cursor='hand2', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        dialog.bind("<Return>", guardar)
        nombre_entry.focus()
        
        dialog.wait_window()
        return persona_agregada['persona']


class DialogoEditarPersona:
    """Diálogo para editar información de una persona existente"""
    
    @staticmethod
    def mostrar(parent, persona, personas_lista, gestor_historial, usuario_actual, callback_ok, tema_global=None):
        """
        Muestra el diálogo para editar una persona
        
        Args:
            parent: Ventana padre
            persona: Dict con datos de la persona a editar
            personas_lista: Lista completa de personas (para validar duplicados)
            gestor_historial: Instancia de GestorHistorial
            usuario_actual: Dict con datos del usuario actual
            callback_ok: Función a llamar cuando se edite exitosamente
            tema_global: Dict con colores del tema visual
        """
        # Tema por defecto si no se proporciona
        if not tema_global:
            tema_global = {
                'bg_principal': '#f5f5f5',
                'bg_secundario': '#ffffff',
                'fg_principal': '#333333',
                'fg_secundario': '#666666',
                'input_bg': '#ffffff',
                'accent_primary': '#0078d4'
            }
        
        dialog = tk.Toplevel(parent)
        dialog.title("Editar Persona")
        dialog.geometry("400x200")
        dialog.transient(parent)
        dialog.grab_set()
        dialog.configure(bg=tema_global['bg_principal'])
        
        # Campos prellenados con tema correcto
        tk.Label(dialog, text=f"Folio: {persona.get('folio', 'SIN-FOLIO')}", 
                font=('Arial', 9, 'italic'),
                bg=tema_global['bg_principal'], fg=tema_global['fg_secundario']).pack(pady=5)
        
        tk.Label(dialog, text="Nombre Completo:", font=('Arial', 10, 'bold'),
                bg=tema_global['bg_principal'], fg=tema_global['fg_principal']).pack(pady=5)
        nombre_entry = tk.Entry(dialog, width=40, font=('Arial', 10),
                               bg=tema_global['input_bg'], fg=tema_global['fg_principal'],
                               relief=tk.SOLID, bd=1)
        nombre_entry.insert(0, persona['nombre'])
        nombre_entry.pack(pady=5)
        
        tk.Label(dialog, text="Notas:", font=('Arial', 10, 'bold'),
                bg=tema_global['bg_principal'], fg=tema_global['fg_principal']).pack(pady=5)
        notas_entry = tk.Entry(dialog, width=40, font=('Arial', 10),
                              bg=tema_global['input_bg'], fg=tema_global['fg_principal'],
                              relief=tk.SOLID, bd=1)
        notas_entry.insert(0, persona.get('notas', ''))
        notas_entry.pack(pady=5)
        
        cambios_realizados = {'cambios': None}
        
        def guardar():
            nombre = nombre_entry.get().strip()
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
            
            # Verificar que no exista otro con el mismo nombre
            if nombre.lower() != persona['nombre'].lower():
                if any(p['nombre'].lower() == nombre.lower() for p in personas_lista):
                    messagebox.showerror("Error", "Ya existe una persona con ese nombre")
                    return
            
            # Guardar valores anteriores para historial
            cambios = {}
            if persona['nombre'] != nombre:
                cambios['nombre'] = {'anterior': persona['nombre'], 'nuevo': nombre}
            if persona.get('notas', '') != notas_entry.get().strip():
                cambios['notas'] = {'anterior': persona.get('notas', ''), 'nuevo': notas_entry.get().strip()}
            
            # Registrar cambios si los hubo
            if cambios:
                usuario = usuario_actual['nombre'] if usuario_actual else 'Sistema'
                registrar_operacion('EDITAR_PERSONA', 'Información de persona modificada', {
                    'folio': persona.get('folio', 'SIN-FOLIO'),
                    'cambios': cambios,
                    'usuario': usuario
                }, usuario)
                
                gestor_historial.registrar_cambio('EDITAR', 'PERSONA', 
                    persona.get('folio', 'SIN-FOLIO'), cambios, usuario)
            
            persona['nombre'] = nombre
            persona['notas'] = notas_entry.get().strip()
            
            cambios_realizados['cambios'] = cambios
            dialog.destroy()
            
            if callback_ok:
                callback_ok(persona, cambios)
            
            messagebox.showinfo("Éxito", "Persona actualizada correctamente")
        
        tk.Button(dialog, text="Guardar Cambios", command=guardar,
                 bg=tema_global['accent_primary'], fg='white',
                 font=('Arial', 10), cursor='hand2', relief=tk.FLAT).pack(pady=15)
        
        dialog.wait_window()
        return cambios_realizados['cambios']


class DialogoNuevaCooperacion:
    """Diálogo para crear una nueva cooperación"""
    
    @staticmethod
    def mostrar(parent, monto_default, proyecto_default, cooperaciones_lista, 
                gestor_historial, usuario_actual, callback_ok, tema_global=None):
        """
        Muestra el diálogo para crear una nueva cooperación
        
        Args:
            parent: Ventana padre
            monto_default: Monto por defecto
            proyecto_default: Nombre del proyecto por defecto
            cooperaciones_lista: Lista de cooperaciones existentes
            gestor_historial: Instancia de GestorHistorial
            usuario_actual: Dict con datos del usuario actual
            callback_ok: Función a llamar cuando se cree exitosamente
            tema_global: Dict con colores del tema visual
        """
        # Tema por defecto si no se proporciona
        if not tema_global:
            tema_global = {
                'bg_principal': '#f5f5f5',
                'bg_secundario': '#ffffff',
                'fg_principal': '#333333',
                'fg_secundario': '#666666',
                'input_bg': '#ffffff',
                'accent_primary': '#0078d4'
            }
        
        dialog = tk.Toplevel(parent)
        dialog.title("Nueva Cooperación")
        dialog.geometry("550x380")
        dialog.transient(parent)
        dialog.grab_set()
        dialog.configure(bg=tema_global['bg_principal'])
        
        # Header informativo
        tk.Label(dialog, text="Crear Nueva Cooperación/Proyecto", font=('Arial', 12, 'bold'),
                bg=tema_global['bg_principal'], fg=tema_global['accent_primary']).pack(
                pady=10, padx=20, anchor=tk.W)
        
        # Nombre de la cooperación (LEYENDA: no valor por defecto)
        tk.Label(dialog, text="Nombre de la cooperación:", font=('Arial', 10, 'bold'),
                bg=tema_global['bg_principal'], fg=tema_global['fg_principal']).pack(
                pady=(15, 5), padx=20, anchor=tk.W)
        nombre_var = tk.StringVar()
        nombre_entry = tk.Entry(dialog, textvariable=nombre_var, width=50,
                               font=('Arial', 10), bg=tema_global['input_bg'],
                               fg=tema_global['fg_principal'], relief=tk.SOLID, bd=1)
        nombre_entry.pack(pady=5, padx=20, fill=tk.X)
        tk.Label(dialog, text="Ej: Cooperación del Barrio, Grupo de Acción Local", font=('Arial', 8, 'italic'),
                bg=tema_global['bg_principal'], fg=tema_global['fg_secundario']).pack(
                pady=(0, 10), padx=20, anchor=tk.W)
        
        # Monto base
        tk.Label(dialog, text="Monto base por persona:", font=('Arial', 10, 'bold'),
                bg=tema_global['bg_principal'], fg=tema_global['fg_principal']).pack(
                pady=(10, 5), padx=20, anchor=tk.W)
        monto_var = tk.DoubleVar(value=monto_default)
        monto_entry = tk.Entry(dialog, textvariable=monto_var, width=20,
                              font=('Arial', 10), bg=tema_global['input_bg'],
                              fg=tema_global['fg_principal'], relief=tk.SOLID, bd=1)
        monto_entry.pack(pady=5, padx=20, anchor=tk.W)
        tk.Label(dialog, text=f"Monto actual: ${monto_default:.2f}", font=('Arial', 8, 'italic'),
                bg=tema_global['bg_principal'], fg=tema_global['fg_secundario']).pack(
                pady=(0, 10), padx=20, anchor=tk.W)
        
        # Nombre del proyecto / Descripción (LEYENDA: no valor)
        tk.Label(dialog, text="Nombre del Proyecto / Descripción:", font=('Arial', 10, 'bold'),
                bg=tema_global['bg_principal'], fg=tema_global['fg_principal']).pack(
                pady=(10, 5), padx=20, anchor=tk.W)
        proyecto_var = tk.StringVar()
        proyecto_entry = tk.Entry(dialog, textvariable=proyecto_var, width=50,
                                 font=('Arial', 10), bg=tema_global['input_bg'],
                                 fg=tema_global['fg_principal'], relief=tk.SOLID, bd=1)
        proyecto_entry.pack(pady=5, padx=20, fill=tk.X)
        tk.Label(dialog, text="Ej: Proyecto Comunitario 2026, Iniciativa Social Local", font=('Arial', 8, 'italic'),
                bg=tema_global['bg_principal'], fg=tema_global['fg_secundario']).pack(
                pady=(0, 10), padx=20, anchor=tk.W)
        
        cooperacion_creada = {'cooperacion': None}
        
        def crear(event=None):
            nombre = nombre_var.get().strip()
            proyecto = proyecto_var.get().strip()
            
            # Validación 1: Nombre obligatorio
            if not nombre:
                messagebox.showerror("Error", "El nombre de la cooperación es obligatorio")
                nombre_entry.focus()
                return
            
            # Validación 2: Monto válido
            try:
                monto = float(monto_var.get())
            except ValueError:
                messagebox.showerror("Error", "Monto inválido. Ingrese un número.")
                monto_entry.focus()
                return
            
            if monto <= 0:
                messagebox.showerror("Error", "El monto debe ser mayor a 0")
                monto_entry.focus()
                return
            
            # Validación 3: Proyecto también es obligatorio
            if not proyecto:
                messagebox.showerror("Error", "El nombre del proyecto es obligatorio")
                proyecto_entry.focus()
                return
            
            # Validación 4: No duplicar nombre de cooperación
            if any(nombre.lower() == c.get('nombre', '').lower() for c in cooperaciones_lista):
                messagebox.showerror("Error", f"Ya existe una cooperación llamada '{nombre}'")
                nombre_entry.focus()
                return
            
            nueva = {
                'id': f"coop-{int(time.time()*1000)}",
                'nombre': nombre,
                'proyecto': proyecto_var.get().strip() or nombre,
                'monto_cooperacion': monto,
                'personas': []
            }
            
            cooperacion_creada['cooperacion'] = nueva
            
            # Registrar en log
            usuario = usuario_actual['nombre'] if usuario_actual else 'Admin'
            registrar_operacion('CREAR_COOPERACION', 'Nueva cooperación creada', {
                'cooperacion_id': nueva['id'],
                'nombre': nombre,
                'proyecto': nueva['proyecto'],
                'monto_base': f"${monto:.2f}",
                'usuario': usuario
            }, usuario)
            
            # Registrar en historial
            gestor_historial.registrar_cambio('CREAR', 'COOPERACION', nueva['id'], 
                {'nombre': {'anterior': None, 'nuevo': nombre},
                 'proyecto': {'anterior': None, 'nuevo': nueva['proyecto']},
                 'monto': {'anterior': None, 'nuevo': f"${monto:.2f}"}},
                usuario)
            
            dialog.destroy()
            
            if callback_ok:
                callback_ok(nueva)
            
            messagebox.showinfo("Éxito", f"Cooperación '{nombre}' creada y activada")
        
        botones = tk.Frame(dialog, bg=tema_global['bg_principal'])
        botones.pack(pady=20)
        tk.Button(botones, text="Crear y activar", command=crear, width=20,
                 bg=tema_global['accent_primary'], fg='white',
                 font=('Arial', 10), cursor='hand2', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        tk.Button(botones, text="Cancelar", command=dialog.destroy, width=14,
                 bg='#d32f2f', fg='white',
                 font=('Arial', 10), cursor='hand2', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        dialog.bind("<Return>", crear)
        nombre_entry.focus()
        
        dialog.wait_window()
        return cooperacion_creada['cooperacion']


class DialogoEditarCooperacion:
    """Diálogo para editar una cooperación existente"""
    
    @staticmethod
    def mostrar(parent, cooperacion, cooperaciones_lista, gestor_historial, 
                usuario_actual, callback_ok, tema_global=None):
        """
        Muestra el diálogo para editar una cooperación
        
        Args:
            parent: Ventana padre
            cooperacion: Dict con datos de la cooperación a editar
            cooperaciones_lista: Lista de cooperaciones (para validar duplicados)
            gestor_historial: Instancia de GestorHistorial
            usuario_actual: Dict con datos del usuario actual
            callback_ok: Función a llamar cuando se edite exitosamente
            tema_global: Dict con colores del tema visual
        """
        # Tema por defecto si no se proporciona
        if not tema_global:
            tema_global = {
                'bg_principal': '#f5f5f5',
                'bg_secundario': '#ffffff',
                'fg_principal': '#333333',
                'fg_secundario': '#666666',
                'input_bg': '#ffffff',
                'accent_primary': '#0078d4'
            }
        
        dialog = tk.Toplevel(parent)
        dialog.title("Editar Cooperación")
        dialog.geometry("500x320")
        dialog.transient(parent)
        dialog.grab_set()
        dialog.configure(bg=tema_global['bg_principal'])
        
        tk.Label(dialog, text="Nombre de la cooperación:", font=('Arial', 10, 'bold'),
                bg=tema_global['bg_principal'], fg=tema_global['fg_principal']).pack(
                pady=5, padx=20, anchor=tk.W)
        nombre_var = tk.StringVar(value=cooperacion.get('nombre', ''))
        nombre_entry = tk.Entry(dialog, textvariable=nombre_var, width=50,
                               font=('Arial', 10), bg=tema_global['input_bg'],
                               fg=tema_global['fg_principal'], relief=tk.SOLID, bd=1)
        nombre_entry.pack(pady=5, padx=20)
        
        tk.Label(dialog, text="Monto base por persona:", font=('Arial', 10, 'bold'),
                bg=tema_global['bg_principal'], fg=tema_global['fg_principal']).pack(
                pady=5, padx=20, anchor=tk.W)
        monto_var = tk.DoubleVar(value=cooperacion.get('monto_cooperacion', 100))
        monto_entry = tk.Entry(dialog, textvariable=monto_var, width=20,
                              font=('Arial', 10), bg=tema_global['input_bg'],
                              fg=tema_global['fg_principal'], relief=tk.SOLID, bd=1)
        monto_entry.pack(pady=5, padx=20, anchor=tk.W)
        
        tk.Label(dialog, text="Descripción/Proyecto:", font=('Arial', 10, 'bold'),
                bg=tema_global['bg_principal'], fg=tema_global['fg_principal']).pack(
                pady=5, padx=20, anchor=tk.W)
        proyecto_var = tk.StringVar(value=cooperacion.get('proyecto', ''))
        proyecto_entry = tk.Entry(dialog, textvariable=proyecto_var, width=50,
                                 font=('Arial', 10), bg=tema_global['input_bg'],
                                 fg=tema_global['fg_principal'], relief=tk.SOLID, bd=1)
        proyecto_entry.pack(pady=5, padx=20)
        
        cambios_realizados = {'cambios': None}
        
        def guardar(event=None):
            nombre = nombre_var.get().strip()
            try:
                monto = float(monto_var.get())
            except:
                messagebox.showerror("Error", "Monto inválido")
                return
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
            if monto <= 0:
                messagebox.showerror("Error", "El monto debe ser mayor a 0")
                return
            if any(nombre.lower() == c.get('nombre', '').lower() and 
                   c.get('id') != cooperacion.get('id') for c in cooperaciones_lista):
                messagebox.showerror("Error", "Ya existe otra cooperación con ese nombre")
                return
            
            # Registrar cambios antes de aplicar
            cambios = {}
            if cooperacion.get('nombre') != nombre:
                cambios['nombre'] = {'anterior': cooperacion.get('nombre', ''), 'nuevo': nombre}
            if cooperacion.get('monto_cooperacion') != monto:
                cambios['monto'] = {
                    'anterior': f"${cooperacion.get('monto_cooperacion', 0):.2f}", 
                    'nuevo': f"${monto:.2f}"
                }
            if cooperacion.get('proyecto') != proyecto_var.get().strip():
                cambios['proyecto'] = {
                    'anterior': cooperacion.get('proyecto', ''), 
                    'nuevo': proyecto_var.get().strip() or nombre
                }
            
            cooperacion['nombre'] = nombre
            cooperacion['monto_cooperacion'] = monto
            cooperacion['proyecto'] = proyecto_var.get().strip() or nombre
            
            # Registrar en log si hubo cambios
            if cambios:
                usuario = usuario_actual['nombre'] if usuario_actual else 'Admin'
                registrar_operacion('EDITAR_COOPERACION', 'Cooperación modificada', {
                    'cooperacion_id': cooperacion.get('id', 'desconocido'),
                    'cambios': cambios,
                    'usuario': usuario
                }, usuario)
                
                gestor_historial.registrar_cambio('EDITAR', 'COOPERACION', 
                    cooperacion.get('id', 'desconocido'), cambios, usuario)
            
            cambios_realizados['cambios'] = cambios
            dialog.destroy()
            
            if callback_ok:
                callback_ok(cooperacion, cambios)
            
            messagebox.showinfo("Éxito", "Cooperación actualizada")
        
        botones = tk.Frame(dialog, bg=tema_global['bg_principal'])
        botones.pack(pady=20)
        tk.Button(botones, text="Guardar", command=guardar, width=20,
                 bg=tema_global['accent_primary'], fg='white',
                 font=('Arial', 10), cursor='hand2', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        tk.Button(botones, text="Cancelar", command=dialog.destroy, width=14,
                 bg='#d32f2f', fg='white',
                 font=('Arial', 10), cursor='hand2', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        dialog.bind("<Return>", guardar)
        nombre_entry.focus()
        
        dialog.wait_window()
        return cambios_realizados['cambios']


class DialogoVerHistorial:
    """Diálogo para ver el historial de pagos de una persona"""
    
    @staticmethod
    def mostrar(parent, persona):
        """
        Muestra el historial de pagos de una persona
        
        Args:
            parent: Ventana padre
            persona: Dict con datos de la persona
        """
        dialog = tk.Toplevel(parent)
        dialog.title(f"Historial de Pagos - {persona['nombre']}")
        dialog.geometry("600x400")
        dialog.transient(parent)
        
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
        
        tree_hist = ttk.Treeview(frame, columns=('num', 'monto', 'fecha', 'hora', 'usuario'), 
                                 show='headings', yscrollcommand=scrollbar.set)
        
        tree_hist.heading('num', text='#')
        tree_hist.heading('monto', text='Monto')
        tree_hist.heading('fecha', text='Fecha')
        tree_hist.heading('hora', text='Hora')
        tree_hist.heading('usuario', text='Usuario')
        
        tree_hist.column('num', width=50, anchor=tk.CENTER)
        tree_hist.column('monto', width=100, anchor=tk.CENTER)
        tree_hist.column('fecha', width=100, anchor=tk.CENTER)
        tree_hist.column('hora', width=100, anchor=tk.CENTER)
        tree_hist.column('usuario', width=150, anchor=tk.W)
        
        tree_hist.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=tree_hist.yview)
        
        # Llenar datos
        for i, pago in enumerate(persona.get('pagos', []), 1):
            tree_hist.insert('', tk.END, values=(
                i,
                f"${pago['monto']:.2f}",
                pago.get('fecha', 'N/A'),
                pago.get('hora', 'N/A'),
                pago.get('usuario', 'Sistema')
            ))
        
        if not persona.get('pagos'):
            ttk.Label(dialog, text="No hay pagos registrados", 
                     font=('Arial', 10, 'italic')).pack(pady=10)
        
        ttk.Button(dialog, text="Cerrar", command=dialog.destroy).pack(pady=10)
        
        dialog.wait_window()


