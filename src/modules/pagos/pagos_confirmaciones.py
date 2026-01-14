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
        dialog.title("⚠️  Confirmar Eliminación")
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
        
        tk.Label(header, text="⚠️  ADVERTENCIA", font=('Arial', 16, 'bold'),
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
        dialog.title("💰 Confirmar Pago")
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
        
        tk.Label(header, text="💰 REGISTRAR PAGO", font=('Arial', 16, 'bold'),
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
