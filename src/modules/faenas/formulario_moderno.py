import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Dict, List, Optional
import math


class ValidadorFormularioFaena:
    def __init__(self):
        self.errores = {}
        
    def validar(self, datos: Dict) -> bool:
        self.errores = {}
        
        if not datos.get('nombre', '').strip():
            self.errores['nombre'] = 'El nombre es requerido'
            
        if not datos.get('fecha', '').strip():
            self.errores['fecha'] = 'La fecha es requerida'
        else:
            try:
                datetime.strptime(datos['fecha'], '%d/%m/%Y')
            except:
                self.errores['fecha'] = 'Formato de fecha invalido (dd/mm/yyyy)'
                
        peso = datos.get('peso', 0)
        try:
            peso_num = float(peso)
            if peso_num < 1 or peso_num > 20:
                self.errores['peso'] = 'El peso debe estar entre 1 y 20'
        except:
            self.errores['peso'] = 'El peso debe ser un numero'
            
        hora_inicio = datos.get('hora_inicio', '')
        hora_fin = datos.get('hora_fin', '')
        
        if hora_inicio and hora_fin:
            try:
                h_inicio = int(hora_inicio.split(':')[0]) if ':' in hora_inicio else int(hora_inicio)
                h_fin = int(hora_fin.split(':')[0]) if ':' in hora_fin else int(hora_fin)
                
                if h_inicio >= h_fin:
                    self.errores['horario'] = 'La hora de inicio debe ser anterior a la de fin'
            except:
                pass
                
        if not datos.get('participantes'):
            self.errores['participantes'] = 'Debe agregar al menos un participante'
            
        return len(self.errores) == 0
        
    def obtener_errores(self) -> Dict[str, str]:
        return self.errores


class FormularioFaenaModerno:
    def __init__(self, parent, on_guardar, on_cancelar):
        self.parent = parent
        self.on_guardar = on_guardar
        self.on_cancelar = on_cancelar
        self.validador = ValidadorFormularioFaena()
        self.campos_validacion = {}
        self.frame = tk.Frame(parent, bg="#f5f7fa")
        
    def pack(self, **kwargs):
        pack_kwargs = {k: v for k, v in kwargs.items() if k in ['fill', 'expand', 'padx', 'pady', 'side', 'anchor', 'ipadx', 'ipady']}
        self.frame.pack(**pack_kwargs)
        self._crear_widgets()
        
    def _crear_widgets(self):
        notebook = ttk.Notebook(self.frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tab1 = tk.Frame(notebook, bg="white")
        notebook.add(tab1, text='Informacion basica')
        self._crear_tab_basico(tab1)
        
        tab2 = tk.Frame(notebook, bg="white")
        notebook.add(tab2, text='Horarios')
        self._crear_tab_horarios(tab2)
        
        tab3 = tk.Frame(notebook, bg="white")
        notebook.add(tab3, text='Observaciones')
        self._crear_tab_observaciones(tab3)
        
        botones = tk.Frame(self.frame, bg="#f5f7fa")
        botones.pack(fill=tk.X, padx=10, pady=10)
        
        btn_guardar = tk.Button(botones, text="Registrar Faena", bg="#2ecc71",
                               fg="white", font=("Arial", 10, "bold"),
                               command=self._guardar)
        btn_guardar.pack(side=tk.LEFT, padx=5)
        
        btn_cancelar = tk.Button(botones, text="Cancelar", bg="#95a5a6",
                                fg="white", command=self.on_cancelar)
        btn_cancelar.pack(side=tk.LEFT, padx=5)
        
    def _crear_tab_basico(self, parent):
        frame = tk.Frame(parent, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(frame, text="Nombre de la faena", font=("Arial", 10, "bold"),
                bg="white").pack(anchor=tk.W, pady=(0, 5))
        self.entrada_nombre = tk.Entry(frame, width=40, font=("Arial", 10))
        self.entrada_nombre.pack(anchor=tk.W, pady=(0, 15), fill=tk.X)
        self.entrada_nombre.bind('<KeyRelease>', lambda e: self._validar_campo('nombre'))
        
        self.error_nombre = tk.Label(frame, text="", font=("Arial", 8),
                                    bg="white", fg="#e74c3c")
        self.error_nombre.pack(anchor=tk.W, pady=(0, 10))
        
        tk.Label(frame, text="Fecha", font=("Arial", 10, "bold"),
                bg="white").pack(anchor=tk.W, pady=(0, 5))
        self.entrada_fecha = tk.Entry(frame, width=40, font=("Arial", 10))
        self.entrada_fecha.pack(anchor=tk.W, pady=(0, 15), fill=tk.X)
        self.entrada_fecha.insert(0, datetime.now().strftime('%d/%m/%Y'))
        self.entrada_fecha.bind('<KeyRelease>', lambda e: self._validar_campo('fecha'))
        
        self.error_fecha = tk.Label(frame, text="", font=("Arial", 8),
                                   bg="white", fg="#e74c3c")
        self.error_fecha.pack(anchor=tk.W, pady=(0, 10))
        
        tk.Label(frame, text="Peso/Puntos (1-20)", font=("Arial", 10, "bold"),
                bg="white").pack(anchor=tk.W, pady=(0, 5))
        self.entrada_peso = tk.Entry(frame, width=40, font=("Arial", 10))
        self.entrada_peso.pack(anchor=tk.W, pady=(0, 15), fill=tk.X)
        self.entrada_peso.insert(0, "5")
        self.entrada_peso.bind('<KeyRelease>', lambda e: self._validar_campo('peso'))
        
        self.error_peso = tk.Label(frame, text="", font=("Arial", 8),
                                  bg="white", fg="#e74c3c")
        self.error_peso.pack(anchor=tk.W, pady=(0, 10))
        
        tk.Label(frame, text="Descripcion (opcional)", font=("Arial", 10, "bold"),
                bg="white").pack(anchor=tk.W, pady=(0, 5))
        self.entrada_desc = tk.Text(frame, width=40, height=4, font=("Arial", 10))
        self.entrada_desc.pack(anchor=tk.W, pady=(0, 15), fill=tk.X)
        
    def _crear_tab_horarios(self, parent):
        frame = tk.Frame(parent, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(frame, text="Hora de inicio", font=("Arial", 10, "bold"),
                bg="white").pack(anchor=tk.W, pady=(0, 5))
        
        frame_inicio = tk.Frame(frame, bg="white")
        frame_inicio.pack(anchor=tk.W, pady=(0, 15), fill=tk.X)
        
        self.entrada_hora_inicio = tk.Entry(frame_inicio, width=5, font=("Arial", 10))
        self.entrada_hora_inicio.pack(side=tk.LEFT, padx=5)
        self.entrada_hora_inicio.insert(0, "09")
        
        tk.Label(frame_inicio, text=":", font=("Arial", 10),
                bg="white").pack(side=tk.LEFT)
        
        self.entrada_min_inicio = tk.Entry(frame_inicio, width=5, font=("Arial", 10))
        self.entrada_min_inicio.pack(side=tk.LEFT, padx=5)
        self.entrada_min_inicio.insert(0, "00")
        
        tk.Label(frame, text="Hora de fin", font=("Arial", 10, "bold"),
                bg="white").pack(anchor=tk.W, pady=(0, 5))
        
        frame_fin = tk.Frame(frame, bg="white")
        frame_fin.pack(anchor=tk.W, pady=(0, 15), fill=tk.X)
        
        self.entrada_hora_fin = tk.Entry(frame_fin, width=5, font=("Arial", 10))
        self.entrada_hora_fin.pack(side=tk.LEFT, padx=5)
        self.entrada_hora_fin.insert(0, "17")
        
        tk.Label(frame_fin, text=":", font=("Arial", 10),
                bg="white").pack(side=tk.LEFT)
        
        self.entrada_min_fin = tk.Entry(frame_fin, width=5, font=("Arial", 10))
        self.entrada_min_fin.pack(side=tk.LEFT, padx=5)
        self.entrada_min_fin.insert(0, "00")
        
        tk.Label(frame, text="Duracion estimada", font=("Arial", 10, "bold"),
                bg="white").pack(anchor=tk.W, pady=(15, 5))
        
        self.duracion_label = tk.Label(frame, text="8.0 horas", font=("Arial", 12),
                                      bg="white", fg="#3498db")
        self.duracion_label.pack(anchor=tk.W)
        
        self.entrada_hora_inicio.bind('<KeyRelease>', self._calcular_duracion)
        self.entrada_hora_fin.bind('<KeyRelease>', self._calcular_duracion)
        
    def _crear_tab_observaciones(self, parent):
        frame = tk.Frame(parent, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(frame, text="Anotaciones", font=("Arial", 10, "bold"),
                bg="white").pack(anchor=tk.W, pady=(0, 5))
        
        self.entrada_notas = tk.Text(frame, width=40, height=10, font=("Arial", 10))
        self.entrada_notas.pack(fill=tk.BOTH, expand=True)
        
    def _validar_campo(self, campo: str):
        datos = self.obtener_datos()
        
        if campo == 'nombre':
            if not datos.get('nombre', '').strip():
                self.error_nombre.config(text="Campo requerido")
            else:
                self.error_nombre.config(text="")
                
        elif campo == 'fecha':
            if not datos.get('fecha', '').strip():
                self.error_fecha.config(text="Campo requerido")
            else:
                try:
                    datetime.strptime(datos['fecha'], '%d/%m/%Y')
                    self.error_fecha.config(text="")
                except:
                    self.error_fecha.config(text="Formato invalido (dd/mm/yyyy)")
                    
        elif campo == 'peso':
            try:
                peso = float(datos.get('peso', 0))
                if peso < 1 or peso > 20:
                    self.error_peso.config(text="Debe estar entre 1 y 20")
                else:
                    self.error_peso.config(text="")
            except:
                self.error_peso.config(text="Debe ser un numero")
                
    def _calcular_duracion(self, event=None):
        try:
            h_inicio = int(self.entrada_hora_inicio.get())
            h_fin = int(self.entrada_hora_fin.get())
            
            if h_fin > h_inicio:
                duracion = h_fin - h_inicio
                self.duracion_label.config(text=f"{duracion}.0 horas")
        except:
            pass
            
    def _guardar(self):
        datos = self.obtener_datos()
        
        if self.validador.validar(datos):
            self.on_guardar(datos)
        else:
            errores = self.validador.obtener_errores()
            mensaje = "Errores encontrados:\n\n"
            for campo, error in errores.items():
                mensaje += f"- {campo}: {error}\n"
            messagebox.showerror("Validacion", mensaje)
            
    def obtener_datos(self) -> Dict:
        return {
            'nombre': self.entrada_nombre.get(),
            'fecha': self.entrada_fecha.get(),
            'peso': self.entrada_peso.get(),
            'descripcion': self.entrada_desc.get('1.0', tk.END).strip(),
            'hora_inicio': f"{self.entrada_hora_inicio.get()}:{self.entrada_min_inicio.get()}",
            'hora_fin': f"{self.entrada_hora_fin.get()}:{self.entrada_min_fin.get()}",
            'notas': self.entrada_notas.get('1.0', tk.END).strip(),
            'participantes': []
        }
