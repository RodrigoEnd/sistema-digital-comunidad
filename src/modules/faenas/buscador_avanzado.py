import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Callable, Optional


class BuscadorAvanzadoFaenas:
    def __init__(self, parent, on_busqueda: Callable):
        self.parent = parent
        self.on_busqueda = on_busqueda
        self.frame = tk.Frame(parent, bg="#f5f7fa")
        self.historial = []
        self.filtros_guardados = {}
        
    def pack(self, **kwargs):
        pack_kwargs = {k: v for k, v in kwargs.items() if k in ['fill', 'expand', 'padx', 'pady', 'side', 'anchor', 'ipadx', 'ipady']}
        self.frame.pack(**pack_kwargs)
        self._crear_widgets()
        
    def _crear_widgets(self):
        barra_busqueda = tk.Frame(self.frame, bg="white")
        barra_busqueda.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(barra_busqueda, text="Busqueda avanzada:",
                font=("Arial", 10), bg="white").pack(side=tk.LEFT, padx=5)
        
        self.entrada = tk.Entry(barra_busqueda, width=40, font=("Arial", 10))
        self.entrada.pack(side=tk.LEFT, padx=5)
        self.entrada.bind('<KeyRelease>', self._on_cambio_entrada)
        
        btn_buscar = tk.Button(barra_busqueda, text="Buscar",
                               command=self._ejecutar_busqueda)
        btn_buscar.pack(side=tk.LEFT, padx=5)
        
        btn_limpiar = tk.Button(barra_busqueda, text="Limpiar",
                                command=self._limpiar)
        btn_limpiar.pack(side=tk.LEFT, padx=5)
        
        tk.Label(barra_busqueda, text="Sintaxis: fecha:2026-01-14 participante:Juan peso:>5",
                font=("Arial", 8), bg="white", fg="#7f8c8d").pack(side=tk.LEFT, padx=5)
        
        panel_filtros = tk.LabelFrame(self.frame, text="Filtros rapidos",
                                      bg="#f5f7fa", font=("Arial", 10))
        panel_filtros.pack(fill=tk.X, padx=10, pady=10)
        
        self.var_estado = tk.StringVar(value="todos")
        ttk.Combobox(panel_filtros, textvariable=self.var_estado,
                    values=["todos", "registrada", "completada", "pagada"],
                    state="readonly", width=15).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.var_mes = tk.StringVar(value="todos")
        ttk.Combobox(panel_filtros, textvariable=self.var_mes,
                    values=["todos", "enero", "febrero", "marzo", "abril",
                           "mayo", "junio", "julio", "agosto", "septiembre",
                           "octubre", "noviembre", "diciembre"],
                    state="readonly", width=15).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.var_participante = tk.StringVar()
        ttk.Entry(panel_filtros, textvariable=self.var_participante,
                 width=20).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Label(panel_filtros, text="Participante",
                bg="#f5f7fa", font=("Arial", 9)).pack(side=tk.LEFT, padx=0, pady=5)
        
        btn_aplicar = tk.Button(panel_filtros, text="Aplicar filtros",
                                command=self._aplicar_filtros)
        btn_aplicar.pack(side=tk.LEFT, padx=5, pady=5)
        
    def _on_cambio_entrada(self, event=None):
        texto = self.entrada.get()
        if len(texto) > 2:
            self._ejecutar_busqueda()
            
    def _ejecutar_busqueda(self):
        criterio = self.entrada.get()
        if criterio.strip():
            self.historial.insert(0, criterio)
            self.historial = self.historial[:20]
            
        filtros = self._parsear_criterio(criterio)
        self.on_busqueda(filtros)
        
    def _parsear_criterio(self, criterio: str) -> Dict:
        filtros = {
            'texto': criterio,
            'fecha': None,
            'participante': None,
            'peso_min': None,
            'peso_max': None,
            'estado': None
        }
        
        partes = criterio.split()
        for parte in partes:
            if ':' in parte:
                clave, valor = parte.split(':', 1)
                if clave == 'fecha':
                    filtros['fecha'] = valor
                elif clave == 'participante':
                    filtros['participante'] = valor.lower()
                elif clave == 'peso':
                    if valor.startswith('>'):
                        filtros['peso_min'] = float(valor[1:])
                    elif valor.startswith('<'):
                        filtros['peso_max'] = float(valor[1:])
                elif clave == 'estado':
                    filtros['estado'] = valor.lower()
        
        return filtros
        
    def _aplicar_filtros(self):
        filtros = {
            'estado': self.var_estado.get() if self.var_estado.get() != 'todos' else None,
            'mes': self.var_mes.get() if self.var_mes.get() != 'todos' else None,
            'participante': self.var_participante.get() or None
        }
        self.on_busqueda(filtros)
        
    def _limpiar(self):
        self.entrada.delete(0, tk.END)
        self.var_estado.set('todos')
        self.var_mes.set('todos')
        self.var_participante.delete(0, tk.END)
        self.on_busqueda({})
        
    def obtener_historial(self) -> List[str]:
        return self.historial
        
    def guardar_filtro(self, nombre: str, filtros: Dict):
        self.filtros_guardados[nombre] = filtros
        
    def obtener_filtro(self, nombre: str) -> Optional[Dict]:
        return self.filtros_guardados.get(nombre)
        
    def listar_filtros_guardados(self) -> List[str]:
        return list(self.filtros_guardados.keys())
