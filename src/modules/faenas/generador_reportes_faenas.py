import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Callable
from datetime import datetime
import math


class GeneradorReportesFaenas:
    def __init__(self, db):
        self.db = db
        
    def obtener_datos_por_mes(self, mes: int, anio: int) -> Dict:
        faenas = self.db.obtener_faenas_por_periodo(mes, anio)
        
        horas_total = sum([f.get('horas_trabajadas', 0) for f in faenas])
        participantes_unicos = set()
        
        for faena in faenas:
            for part in faena.get('participantes', []):
                participantes_unicos.add(part.get('id'))
                
        return {
            'total_faenas': len(faenas),
            'horas_totales': horas_total,
            'participantes': len(participantes_unicos),
            'promedio_horas_faena': horas_total / len(faenas) if faenas else 0,
            'faenas': faenas
        }
        
    def obtener_top_participantes(self, limite: int = 10) -> List[Dict]:
        habitantes = self.db.obtener_todos_habitantes()
        resultados = []
        
        for hab in habitantes:
            faenas = self.db.obtener_faenas_habitante(hab.get('id'))
            horas = sum([f.get('horas_trabajadas', 0) for f in faenas])
            
            resultados.append({
                'nombre': hab.get('nombre'),
                'horas_totales': horas,
                'faenas_participadas': len(faenas)
            })
            
        return sorted(resultados, key=lambda x: x['horas_totales'], reverse=True)[:limite]
        
    def obtener_distribucion_tipos_faena(self) -> Dict[str, int]:
        faenas = self.db.obtener_todas_faenas()
        distribucion = {}
        
        for faena in faenas:
            nombre = faena.get('nombre', 'Otros')
            distribucion[nombre] = distribucion.get(nombre, 0) + 1
            
        return distribucion


class PanelReportesFaenas:
    def __init__(self, parent, generador_reportes):
        self.parent = parent
        self.generador = generador_reportes
        self.frame = tk.Frame(parent, bg="#f5f7fa")
        
    def pack(self, **kwargs):
        pack_kwargs = {k: v for k, v in kwargs.items() if k in ['fill', 'expand', 'padx', 'pady', 'side', 'anchor', 'ipadx', 'ipady']}
        self.frame.pack(**pack_kwargs)
        self._crear_widgets()
        
    def _crear_widgets(self):
        notebook = ttk.Notebook(self.frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tab_mensual = tk.Frame(notebook, bg="white")
        notebook.add(tab_mensual, text='Resumen mensual')
        self._crear_tab_mensual(tab_mensual)
        
        tab_top = tk.Frame(notebook, bg="white")
        notebook.add(tab_top, text='Top participantes')
        self._crear_tab_top(tab_top)
        
        tab_distribucion = tk.Frame(notebook, bg="white")
        notebook.add(tab_distribucion, text='Distribucion')
        self._crear_tab_distribucion(tab_distribucion)
        
    def _crear_tab_mensual(self, parent):
        frame = tk.Frame(parent, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        ahora = datetime.now()
        datos = self.generador.obtener_datos_por_mes(ahora.month, ahora.year)
        
        grid = tk.Frame(frame, bg="white")
        grid.pack(fill=tk.X, pady=10)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        
        self._estadistica_card(grid, 0, "Faenas registradas",
                              str(datos['total_faenas']), "#3498db")
        self._estadistica_card(grid, 1, "Horas totales",
                              f"{datos['horas_totales']:.1f}h", "#2ecc71")
        
        self._estadistica_card(grid, 2, "Participantes unicos",
                              str(datos['participantes']), "#9b59b6")
        self._estadistica_card(grid, 3, "Promedio por faena",
                              f"{datos['promedio_horas_faena']:.1f}h", "#f39c12")
        
    def _crear_tab_top(self, parent):
        frame = tk.Frame(parent, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tree = ttk.Treeview(frame, columns=('Nombre', 'Horas', 'Faenas'),
                           height=15, show='headings')
        
        tree.column('Nombre', width=200, anchor=tk.W)
        tree.column('Horas', width=100, anchor=tk.CENTER)
        tree.column('Faenas', width=100, anchor=tk.CENTER)
        
        tree.heading('Nombre', text='Nombre')
        tree.heading('Horas', text='Horas totales')
        tree.heading('Faenas', text='Faenas')
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        top_participantes = self.generador.obtener_top_participantes(10)
        
        for idx, persona in enumerate(top_participantes):
            tree.insert('', 'end', values=(
                persona['nombre'],
                f"{persona['horas_totales']:.1f}h",
                str(persona['faenas_participadas'])
            ), tags=('par',) if idx % 2 else ())
            
        tree.tag_configure('par', background='#ecf0f1')
        
    def _crear_tab_distribucion(self, parent):
        frame = tk.Frame(parent, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        distribucion = self.generador.obtener_distribucion_tipos_faena()
        
        total_faenas = sum(distribucion.values())
        
        canvas = tk.Canvas(frame, bg="white", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        canvas_width = canvas.winfo_width() if canvas.winfo_width() > 1 else 500
        canvas_height = canvas.winfo_height() if canvas.winfo_height() > 1 else 300
        
        self._dibujar_pie_chart(canvas, distribucion, total_faenas,
                               canvas_width, canvas_height)
        
        canvas.bind('<Configure>', lambda e: self._dibujar_pie_chart(
            canvas, distribucion, total_faenas, e.width, e.height))
            
    def _estadistica_card(self, parent, col, titulo, valor, color):
        card = tk.Frame(parent, bg=color, relief=tk.FLAT)
        card.grid(row=col//2, column=col%2, padx=5, pady=5, sticky="nsew")
        
        tk.Label(card, text=titulo, font=("Arial", 9),
                bg=color, fg="white").pack(pady=(10, 0))
        tk.Label(card, text=valor, font=("Arial", 18, "bold"),
                bg=color, fg="white").pack(pady=(5, 10))
                
    def _dibujar_pie_chart(self, canvas, distribucion, total, width, height):
        canvas.delete('all')
        
        if not distribucion or total == 0:
            canvas.create_text(width//2, height//2, text="Sin datos",
                             font=("Arial", 12), fill="#95a5a6")
            return
            
        cx, cy = width * 0.4, height * 0.5
        radio = min(width, height) * 0.25
        
        colores = ["#3498db", "#2ecc71", "#f39c12", "#e74c3c", "#9b59b6",
                  "#1abc9c", "#34495e", "#e67e22"]
        
        angulo_inicio = 0
        for idx, (nombre, cantidad) in enumerate(distribucion.items()):
            porcentaje = cantidad / total
            angulo_fin = angulo_inicio + (porcentaje * 360)
            
            color = colores[idx % len(colores)]
            
            canvas.create_arc(cx - radio, cy - radio, cx + radio, cy + radio,
                            start=angulo_inicio, extent=angulo_fin - angulo_inicio,
                            fill=color, outline=color)
            
            angulo_medio = (angulo_inicio + angulo_fin) / 2
            angulo_rad = math.radians(angulo_medio)
            
            label_x = cx + (radio * 0.6) * math.cos(angulo_rad)
            label_y = cy + (radio * 0.6) * math.sin(angulo_rad)
            
            porcentaje_texto = f"{int(porcentaje * 100)}%"
            canvas.create_text(label_x, label_y, text=porcentaje_texto,
                             font=("Arial", 9, "bold"), fill="white")
            
            angulo_inicio = angulo_fin
            
        leyenda_x = cx + radio + 30
        leyenda_y = cy - 100
        
        for idx, nombre in enumerate(distribucion.keys()):
            color = colores[idx % len(colores)]
            
            canvas.create_rectangle(leyenda_x, leyenda_y + (idx * 20),
                                  leyenda_x + 10, leyenda_y + (idx * 20) + 10,
                                  fill=color, outline=color)
            
            canvas.create_text(leyenda_x + 20, leyenda_y + 5 + (idx * 20),
                             text=f"{nombre} ({distribucion[nombre]})",
                             font=("Arial", 9), anchor=tk.W)
