import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional
import math


class DashboardFaenas:
    def __init__(self, parent, datos_callback: Callable):
        self.parent = parent
        self.datos_callback = datos_callback
        self.frame = tk.Frame(parent, bg="#f5f7fa")
        
    def pack(self, **kwargs):
        pack_kwargs = {k: v for k, v in kwargs.items() if k in ['fill', 'expand', 'padx', 'pady', 'side', 'anchor', 'ipadx', 'ipady']}
        self.frame.pack(**pack_kwargs)
        self._crear_widgets()
        
    def _crear_widgets(self):
        container = tk.Frame(self.frame, bg="#f5f7fa")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        datos = self.datos_callback()
        
        grid = tk.Frame(container, bg="#f5f7fa")
        grid.pack(fill=tk.BOTH, expand=True)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(2, weight=1)
        
        self._tarjeta_kpi(grid, 0, 0, "Faenas este mes", 
                         str(datos.get('faenas_mes', 0)), "#3498db")
        self._tarjeta_kpi(grid, 0, 1, "Horas trabajadas",
                         f"{datos.get('horas_mes', 0):.1f}h", "#2ecc71")
        self._tarjeta_kpi(grid, 0, 2, "Participantes activos",
                         str(datos.get('participantes', 0)), "#9b59b6")
        
        self._tarjeta_kpi(grid, 1, 0, "Pendiente de pago",
                         f"${datos.get('pendiente_pago', 0):.0f}", "#e74c3c")
        self._tarjeta_kpi(grid, 1, 1, "Completadas",
                         str(datos.get('completadas', 0)), "#16a085")
        self._tarjeta_kpi(grid, 1, 2, "Promedio horas",
                         f"{datos.get('promedio_horas', 0):.1f}h", "#f39c12")
        
    def _tarjeta_kpi(self, parent, row, col, titulo, valor, color):
        tarjeta = tk.Frame(parent, bg="white", relief=tk.FLAT, bd=1)
        tarjeta.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        tarjeta.columnconfigure(0, weight=1)
        
        barra = tk.Frame(tarjeta, bg=color, height=4)
        barra.pack(fill=tk.X)
        barra.pack_propagate(False)
        
        content = tk.Frame(tarjeta, bg="white")
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        lbl_titulo = tk.Label(content, text=titulo, font=("Arial", 9),
                             bg="white", fg="#7f8c8d")
        lbl_titulo.pack(anchor=tk.W)
        
        lbl_valor = tk.Label(content, text=valor, font=("Arial", 24, "bold"),
                            bg="white", fg=color)
        lbl_valor.pack(anchor=tk.W, pady=(5, 0))
        
    def actualizar(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        self._crear_widgets()
