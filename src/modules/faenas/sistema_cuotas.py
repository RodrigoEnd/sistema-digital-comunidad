import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Callable, Optional


class SistemaCuotas:
    def __init__(self, db):
        self.db = db
        
    def obtener_cuota_mes(self, habitante_id: str, mes: int, anio: int) -> Dict:
        faenas = self.db.obtener_faenas_habitante(habitante_id)
        horas_mes = sum([f.get('horas_trabajadas', 0) for f in faenas 
                        if self._es_mismo_mes(f.get('fecha'), mes, anio)])
        
        return {
            'horas_realizadas': horas_mes,
            'horas_minimas': 10,
            'porcentaje': min(100, int((horas_mes / 10) * 100)),
            'en_riesgo': horas_mes < 5,
            'completada': horas_mes >= 10
        }
    
    def obtener_cuota_anual(self, habitante_id: str, anio: int) -> Dict:
        faenas = self.db.obtener_faenas_habitante(habitante_id)
        horas_anio = sum([f.get('horas_trabajadas', 0) for f in faenas 
                         if f.get('fecha', '')[:4] == str(anio)])
        
        return {
            'horas_realizadas': horas_anio,
            'horas_minimas': 120,
            'porcentaje': min(100, int((horas_anio / 120) * 100)),
            'en_riesgo': horas_anio < 60,
            'completada': horas_anio >= 120
        }
    
    def obtener_resumen_habitantes(self, mes: int, anio: int) -> List[Dict]:
        habitantes = self.db.obtener_todos_habitantes()
        resumen = []
        
        for hab in habitantes:
            cuota = self.obtener_cuota_mes(hab.get('id'), mes, anio)
            resumen.append({
                'nombre': hab.get('nombre'),
                'cuota': cuota,
                'en_riesgo': cuota['en_riesgo']
            })
        
        return sorted(resumen, key=lambda x: x['cuota']['porcentaje'], reverse=True)
    
    def _es_mismo_mes(self, fecha_str: str, mes: int, anio: int) -> bool:
        if not fecha_str:
            return False
        try:
            partes = fecha_str.split('/')
            return int(partes[1]) == mes and int(partes[2]) == anio
        except:
            return False


class PanelCuotasUI:
    def __init__(self, parent, sistema_cuotas):
        self.parent = parent
        self.sistema_cuotas = sistema_cuotas
        self.frame = tk.Frame(parent, bg="#f5f7fa")
        
    def pack(self, **kwargs):
        pack_kwargs = {k: v for k, v in kwargs.items() if k in ['fill', 'expand', 'padx', 'pady', 'side', 'anchor', 'ipadx', 'ipady']}
        self.frame.pack(**pack_kwargs)
        self._crear_widgets()
        
    def _crear_widgets(self):
        header = tk.Frame(self.frame, bg="#2c3e50")
        header.pack(fill=tk.X)
        
        tk.Label(header, text="Cumplimiento de Cuotas Mensuales",
                font=("Arial", 14, "bold"), bg="#2c3e50", fg="white").pack(pady=10)
        
        container = tk.Frame(self.frame, bg="#f5f7fa")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.tree = ttk.Treeview(container, columns=('Nombre', 'Horas', 'Meta', 'Progreso', 'Estado'),
                                height=15, show='headings')
        
        self.tree.column('Nombre', width=150, anchor=tk.W)
        self.tree.column('Horas', width=80, anchor=tk.CENTER)
        self.tree.column('Meta', width=80, anchor=tk.CENTER)
        self.tree.column('Progreso', width=150, anchor=tk.W)
        self.tree.column('Estado', width=100, anchor=tk.CENTER)
        
        self.tree.heading('Nombre', text='Nombre')
        self.tree.heading('Horas', text='Horas')
        self.tree.heading('Meta', text='Meta')
        self.tree.heading('Progreso', text='Progreso')
        self.tree.heading('Estado', text='Estado')
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self._actualizar_datos()
        
    def _actualizar_datos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        from datetime import datetime
        ahora = datetime.now()
        resumen = self.sistema_cuotas.obtener_resumen_habitantes(ahora.month, ahora.year)
        
        for persona in resumen:
            cuota = persona['cuota']
            porcentaje = cuota['porcentaje']
            barra = self._crear_barra_progreso(porcentaje)
            estado = "EN RIESGO" if persona['en_riesgo'] else "OK"
            
            self.tree.insert('', 'end', values=(
                persona['nombre'],
                f"{cuota['horas_realizadas']:.1f}h",
                f"{cuota['horas_minimas']}h",
                barra,
                estado
            ), tags=('en_riesgo',) if persona['en_riesgo'] else ())
        
        self.tree.tag_configure('en_riesgo', background='#ffcccc')
        
    def _crear_barra_progreso(self, porcentaje: int) -> str:
        bloques = int(porcentaje / 10)
        return '[' + ('=' * bloques) + (' ' * (10 - bloques)) + '] ' + f'{porcentaje}%'
