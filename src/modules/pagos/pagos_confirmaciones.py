"""
Diálogos de confirmación mejorados con más información
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class ConfirmacionMejorada:
    """Diálogo de confirmación con más información y detalles"""
    
    @staticmethod
    def confirmar_eliminacion(parent, nombre_persona, folio, total_pagado, monto_esperado, tema_global):
        """
        Muestra diálogo mejorado para confirmar eliminación de persona
        Retorna True si confirma, False si cancela
        """
        dialog = tk.Toplevel(parent)
        dialog.title("  Confirmar Eliminación")
        dialog.geometry("500x380")
        dialog.transient(parent)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Frame principal
        main_frame = tk.Frame(dialog, bg=tema_global.get('bg_principal', '#ffffff'))
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Header rojo
        header = tk.Frame(main_frame, bg='#e74c3c', height=90)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        tk.Label(header, text="  ADVERTENCIA", font=('Arial', 16, 'bold'),
                bg='#e74c3c', fg='#ffffff').pack(pady=(15, 5))
        tk.Label(header, text="Está a punto de eliminar una persona",
                bg='#e74c3c', fg='#ffffff', font=('Arial', 11)).pack()
        
        # Contenido
        content = tk.Frame(main_frame, bg=tema_global.get('bg_principal', '#ffffff'))
        content.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # Información de la persona
        tk.Label(content, text="Información de la Persona:", font=('Arial', 11, 'bold'),
                bg=tema_global.get('bg_principal', '#ffffff'),
                fg=tema_global.get('fg_principal', '#333333')).pack(anchor=tk.W, pady=(0, 12))
        
        # Detalles
        detalle_frame = tk.Frame(content, bg=tema_global.get('bg_secundario', '#f0f0f0'),
                                relief=tk.FLAT, bd=1)
        detalle_frame.pack(fill=tk.X, padx=10, pady=(0, 20))
        
        tk.Label(detalle_frame, text=f"Nombre: {nombre_persona}", font=('Arial', 11),
                bg=tema_global.get('bg_secundario', '#f0f0f0'),
                fg=tema_global.get('fg_principal', '#333333')).pack(anchor=tk.W, padx=12, pady=6)
        
        tk.Label(detalle_frame, text=f"Folio: {folio}", font=('Arial', 11),
                bg=tema_global.get('bg_secundario', '#f0f0f0'),
                fg=tema_global.get('fg_principal', '#333333')).pack(anchor=tk.W, padx=12, pady=6)
        
        tk.Label(detalle_frame, text=f"Pagado: ${total_pagado:.2f} de ${monto_esperado:.2f}",
                font=('Arial', 11), bg=tema_global.get('bg_secundario', '#f0f0f0'),
                fg='#27ae60' if total_pagado >= monto_esperado else '#e74c3c').pack(anchor=tk.W, padx=12, pady=6)
        
        # Mensaje de confirmación
        tk.Label(content, text="Esta acción NO se puede deshacer.",
                font=('Arial', 11, 'bold'), bg=tema_global.get('bg_principal', '#ffffff'),
                fg='#e74c3c').pack(anchor=tk.W, pady=(0, 20))
        
        # Botones
        btn_frame = tk.Frame(main_frame, bg=tema_global.get('bg_principal', '#ffffff'))
        btn_frame.pack(fill=tk.X, padx=25, pady=(0, 20), side=tk.BOTTOM)
        
        resultado = {'confirmado': False}
        
        def confirmar():
            resultado['confirmado'] = True
            dialog.destroy()
        
        def cancelar():
            dialog.destroy()
        
        # Botón de cancelación
        btn_cancelar = tk.Button(btn_frame, text="Cancelar", command=cancelar,
                                bg=tema_global.get('bg_secundario', '#f0f0f0'),
                                fg=tema_global.get('fg_principal', '#333333'),
                                font=('Arial', 11), padx=30, pady=10, relief=tk.FLAT, bd=1,
                                cursor='hand2')
        btn_cancelar.pack(side=tk.LEFT, padx=(0, 12), fill=tk.X, expand=True)
        
        # Botón de confirmación
        btn_confirmar = tk.Button(btn_frame, text="Sí, Eliminar", command=confirmar,
                                 bg='#e74c3c', fg='#ffffff',
                                 font=('Arial', 11, 'bold'), padx=30, pady=10, relief=tk.FLAT, bd=0,
                                 cursor='hand2')
        btn_confirmar.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        dialog.wait_window()
        return resultado['confirmado']
    
    @staticmethod
    def confirmar_pago(parent, nombre_persona, monto_a_pagar, monto_esperado, pagado_actual, tema_global):
        """
        Muestra diálogo mejorado para confirmar pago
        """
        dialog = tk.Toplevel(parent)
        dialog.title(" Confirmar Pago")
        dialog.geometry("450x280")
        dialog.transient(parent)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Frame principal
        main_frame = tk.Frame(dialog, bg=tema_global.get('bg_principal', '#ffffff'))
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Header verde
        header = tk.Frame(main_frame, bg='#27ae60', height=80)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        tk.Label(header, text=" REGISTRAR PAGO", font=('Arial', 16, 'bold'),
                bg='#27ae60', fg='#ffffff').pack(pady=(15, 5))
        tk.Label(header, text=f"${monto_a_pagar:.2f}",
                bg='#27ae60', fg='#ffffff', font=('Arial', 14, 'bold')).pack()
        
        # Contenido
        content = tk.Frame(main_frame, bg=tema_global.get('bg_principal', '#ffffff'))
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content, text=f"Persona: {nombre_persona}", font=('Arial', 10),
                bg=tema_global.get('bg_principal', '#ffffff'),
                fg=tema_global.get('fg_principal', '#333333')).pack(anchor=tk.W, pady=(0, 10))
        
        # Detalles del pago
        detalle_frame = tk.Frame(content, bg=tema_global.get('bg_secundario', '#f0f0f0'),
                                relief=tk.FLAT, bd=1)
        detalle_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        tk.Label(detalle_frame, text=f"Monto a pagar: ${monto_a_pagar:.2f}", font=('Arial', 10, 'bold'),
                bg=tema_global.get('bg_secundario', '#f0f0f0'),
                fg='#27ae60').pack(anchor=tk.W, padx=10, pady=5)
        
        nuevo_total = pagado_actual + monto_a_pagar
        pendiente = max(0, monto_esperado - nuevo_total)
        
        tk.Label(detalle_frame, text=f"Después del pago: ${nuevo_total:.2f} de ${monto_esperado:.2f}",
                font=('Arial', 10), bg=tema_global.get('bg_secundario', '#f0f0f0'),
                fg=tema_global.get('fg_principal', '#333333')).pack(anchor=tk.W, padx=10, pady=5)
        
        if pendiente > 0:
            tk.Label(detalle_frame, text=f"Seguirá pendiente: ${pendiente:.2f}",
                    font=('Arial', 10), bg=tema_global.get('bg_secundario', '#f0f0f0'),
                    fg='#e74c3c').pack(anchor=tk.W, padx=10, pady=5)
        else:
            tk.Label(detalle_frame, text="✓ Persona completará el pago",
                    font=('Arial', 10), bg=tema_global.get('bg_secundario', '#f0f0f0'),
                    fg='#27ae60').pack(anchor=tk.W, padx=10, pady=5)
        
        # Botones
        btn_frame = tk.Frame(main_frame, bg=tema_global.get('bg_principal', '#ffffff'))
        btn_frame.pack(fill=tk.X, padx=20, pady=20)
        
        resultado = {'confirmado': False}
        
        def confirmar():
            resultado['confirmado'] = True
            dialog.destroy()
        
        def cancelar():
            dialog.destroy()
        
        btn_cancelar = tk.Button(btn_frame, text="Cancelar", command=cancelar,
                                bg=tema_global.get('bg_secundario', '#f0f0f0'),
                                fg=tema_global.get('fg_principal', '#333333'),
                                font=('Arial', 10), padx=20, pady=8, relief=tk.FLAT, bd=1)
        btn_cancelar.pack(side=tk.LEFT, padx=(0, 10))
        
        btn_confirmar = tk.Button(btn_frame, text="Sí, Registrar Pago", command=confirmar,
                                 bg='#27ae60', fg='#ffffff',
                                 font=('Arial', 10, 'bold'), padx=20, pady=8, relief=tk.FLAT, bd=0)
        btn_confirmar.pack(side=tk.RIGHT)
        
        dialog.wait_window()
        return resultado['confirmado']
    
    @staticmethod
    def confirmar_actualizar_monto(parent, monto_actual, monto_nuevo, num_personas, tema_global):
        """
        Muestra diálogo mejorado para confirmar actualización de monto
        Retorna True si confirma, False si cancela
        """
        dialog = tk.Toplevel(parent)
        dialog.title(" Confirmar Actualización de Monto")
        dialog.geometry("520x500")
        dialog.transient(parent)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Centrar ventana
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (260)
        y = (dialog.winfo_screenheight() // 2) - (250)
        dialog.geometry(f"520x500+{x}+{y}")
        
        # Frame principal
        main_frame = tk.Frame(dialog, bg=tema_global.get('bg_principal', '#ffffff'))
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Header azul - MÁS COMPACTO
        header = tk.Frame(main_frame, bg='#3498db', height=80)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        tk.Label(header, text="💰 ACTUALIZAR MONTO", font=('Arial', 16, 'bold'),
                bg='#3498db', fg='#ffffff').pack(pady=(15, 3))
        tk.Label(header, text="Cambiar monto de cooperación",
                bg='#3498db', fg='#ffffff', font=('Arial', 11)).pack()
        
        # Contenido - REDUCIR PADDING
        content = tk.Frame(main_frame, bg=tema_global.get('bg_principal', '#ffffff'))
        content.pack(fill=tk.X, padx=25, pady=15)
        
        # Título de la sección
        tk.Label(content, text="Detalle de la Actualización:", font=('Arial', 11, 'bold'),
                bg=tema_global.get('bg_principal', '#ffffff'),
                fg=tema_global.get('fg_principal', '#333333')).pack(anchor=tk.W, pady=(0, 10))
        
        # Frame de comparación
        comparacion_frame = tk.Frame(content, bg=tema_global.get('bg_secundario', '#f8f9fa'),
                                    relief=tk.SOLID, bd=1)
        comparacion_frame.pack(fill=tk.X, padx=5, pady=(0, 12))
        
        # Monto actual
        actual_row = tk.Frame(comparacion_frame, bg=tema_global.get('bg_secundario', '#f8f9fa'))
        actual_row.pack(fill=tk.X, padx=15, pady=(10, 6))
        
        tk.Label(actual_row, text="Monto Actual:", font=('Arial', 10),
                bg=tema_global.get('bg_secundario', '#f8f9fa'),
                fg=tema_global.get('fg_secundario', '#666666')).pack(side=tk.LEFT)
        
        tk.Label(actual_row, text=f"${monto_actual:.2f}", font=('Arial', 11, 'bold'),
                bg=tema_global.get('bg_secundario', '#f8f9fa'),
                fg='#95a5a6').pack(side=tk.RIGHT)
        
        # Flecha
        tk.Label(comparacion_frame, text="↓", font=('Arial', 14, 'bold'),
                bg=tema_global.get('bg_secundario', '#f8f9fa'),
                fg='#3498db').pack(pady=3)
        
        # Monto nuevo
        nuevo_row = tk.Frame(comparacion_frame, bg=tema_global.get('bg_secundario', '#f8f9fa'))
        nuevo_row.pack(fill=tk.X, padx=15, pady=(6, 10))
        
        tk.Label(nuevo_row, text="Monto Nuevo:", font=('Arial', 10),
                bg=tema_global.get('bg_secundario', '#f8f9fa'),
                fg=tema_global.get('fg_secundario', '#666666')).pack(side=tk.LEFT)
        
        tk.Label(nuevo_row, text=f"${monto_nuevo:.2f}", font=('Arial', 13, 'bold'),
                bg=tema_global.get('bg_secundario', '#f8f9fa'),
                fg='#27ae60').pack(side=tk.RIGHT)
        
        # Información adicional
        info_frame = tk.Frame(content, bg='#fff3cd', relief=tk.SOLID, bd=1)
        info_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        tk.Label(info_frame, text=f"⚠️  Se actualizarán {num_personas} persona(s)", 
                font=('Arial', 9, 'bold'),
                bg='#fff3cd', fg='#856404').pack(padx=10, pady=8)
        
        # Mensaje informativo - MÁS COMPACTO
        tk.Label(content, text="Esta acción afectará el monto esperado de todas las personas.",
                font=('Arial', 9), bg=tema_global.get('bg_principal', '#ffffff'),
                fg=tema_global.get('fg_secundario', '#666666'), wraplength=450).pack(pady=(0, 5))
        
        # Botones - REDUCIR PADDING
        btn_frame = tk.Frame(main_frame, bg=tema_global.get('bg_principal', '#ffffff'))
        btn_frame.pack(fill=tk.X, padx=25, pady=(10, 20))
        
        resultado = {'confirmado': False}
        
        def confirmar():
            resultado['confirmado'] = True
            dialog.destroy()
        
        def cancelar():
            dialog.destroy()
        
        # Botón de cancelación
        btn_cancelar = tk.Button(btn_frame, text="✕ Cancelar", command=cancelar,
                                bg=tema_global.get('bg_secundario', '#f0f0f0'),
                                fg=tema_global.get('fg_principal', '#333333'),
                                font=('Arial', 11), padx=35, pady=12, relief=tk.FLAT, bd=1,
                                cursor='hand2')
        btn_cancelar.pack(side=tk.LEFT, padx=(0, 15), fill=tk.X, expand=True)
        
        # Hover effects
        def on_enter_cancelar(e):
            btn_cancelar.config(bg='#e0e0e0')
        
        def on_leave_cancelar(e):
            btn_cancelar.config(bg=tema_global.get('bg_secundario', '#f0f0f0'))
        
        btn_cancelar.bind("<Enter>", on_enter_cancelar)
        btn_cancelar.bind("<Leave>", on_leave_cancelar)
        
        # Botón de confirmación
        btn_confirmar = tk.Button(btn_frame, text="✓ Sí, Actualizar Monto", command=confirmar,
                                 bg='#3498db', fg='#ffffff',
                                 font=('Arial', 11, 'bold'), padx=35, pady=12, relief=tk.FLAT, bd=0,
                                 cursor='hand2')
        btn_confirmar.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Hover effects
        def on_enter_confirmar(e):
            btn_confirmar.config(bg='#2980b9')
        
        def on_leave_confirmar(e):
            btn_confirmar.config(bg='#3498db')
        
        btn_confirmar.bind("<Enter>", on_enter_confirmar)
        btn_confirmar.bind("<Leave>", on_leave_confirmar)
        
        # Foco en botón de confirmación
        btn_confirmar.focus_set()
        
        # Enter para confirmar
        dialog.bind('<Return>', lambda e: confirmar())
        dialog.bind('<Escape>', lambda e: cancelar())
        
        dialog.wait_window()
        return resultado['confirmado']