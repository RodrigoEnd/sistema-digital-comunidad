import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Callable, Optional


class SistemaNotificaciones:
    def __init__(self, root):
        self.root = root
        self.notificaciones = []
        self.ventana_notif = None
        
    def mostrar(self, titulo: str, mensaje: str, tipo: str = "info", duracion: int = 3000):
        self._crear_ventana_notificacion(titulo, mensaje, tipo, duracion)
        self.notificaciones.append({
            'titulo': titulo,
            'mensaje': mensaje,
            'tipo': tipo
        })
        
    def _crear_ventana_notificacion(self, titulo: str, mensaje: str, 
                                    tipo: str, duracion: int):
        if self.ventana_notif and self.ventana_notif.winfo_exists():
            self.ventana_notif.destroy()
        
        self.ventana_notif = tk.Toplevel(self.root)
        self.ventana_notif.overrideredirect(True)
        
        colores = {
            'exito': ('#2ecc71', 'white'),
            'error': ('#e74c3c', 'white'),
            'advertencia': ('#f39c12', 'white'),
            'info': ('#3498db', 'white')
        }
        
        bg, fg = colores.get(tipo, colores['info'])
        
        self.ventana_notif.configure(bg=bg)
        
        ancho_pantalla = self.root.winfo_screenwidth()
        alto_pantalla = self.root.winfo_screenheight()
        
        self.ventana_notif.geometry(f"400x100+{ancho_pantalla-420}+{alto_pantalla-150}")
        
        frame = tk.Frame(self.ventana_notif, bg=bg)
        frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        titulo_label = tk.Label(frame, text=titulo, font=("Arial", 11, "bold"),
                               bg=bg, fg=fg)
        titulo_label.pack(anchor=tk.W, padx=15, pady=(10, 0))
        
        mensaje_label = tk.Label(frame, text=mensaje, font=("Arial", 10),
                                bg=bg, fg=fg, wraplength=350, justify=tk.LEFT)
        mensaje_label.pack(anchor=tk.W, padx=15, pady=(5, 10))
        
        self.ventana_notif.after(duracion, lambda: self._cerrar_notificacion())
        
    def _cerrar_notificacion(self):
        if self.ventana_notif and self.ventana_notif.winfo_exists():
            self.ventana_notif.destroy()
            self.ventana_notif = None
            
    def obtener_historial(self) -> List[Dict]:
        return self.notificaciones


class PanelParticipantesModerno:
    def __init__(self, parent, participantes_data: List[Dict], 
                 on_eliminar: Callable, on_editar: Callable):
        self.parent = parent
        self.participantes_data = participantes_data
        self.on_eliminar = on_eliminar
        self.on_editar = on_editar
        self.frame = tk.Frame(parent, bg="#f5f7fa")
        
    def pack(self, **kwargs):
        pack_kwargs = {k: v for k, v in kwargs.items() if k in ['fill', 'expand', 'padx', 'pady', 'side', 'anchor', 'ipadx', 'ipady']}
        self.frame.pack(**pack_kwargs)
        self._crear_widgets()
        
    def _crear_widgets(self):
        header = tk.Frame(self.frame, bg="#2c3e50")
        header.pack(fill=tk.X)
        
        tk.Label(header, text="Participantes", font=("Arial", 12, "bold"),
                bg="#2c3e50", fg="white").pack(pady=8, padx=10, anchor=tk.W)
        
        self.canvas = tk.Canvas(self.frame, bg="#f5f7fa", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.frame_contenedor = tk.Frame(self.canvas, bg="#f5f7fa")
        self.canvas.create_window((0, 0), window=self.frame_contenedor, anchor='nw')
        
        self._actualizar_participantes()
        
        self.frame_contenedor.bind('<Configure>', 
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        
    def _actualizar_participantes(self):
        for widget in self.frame_contenedor.winfo_children():
            widget.destroy()
        
        for idx, part in enumerate(self.participantes_data):
            self._crear_tarjeta_participante(idx, part)
            
    def _crear_tarjeta_participante(self, idx: int, participante: Dict):
        tarjeta = tk.Frame(self.frame_contenedor, bg="white", relief=tk.FLAT, bd=1)
        tarjeta.pack(fill=tk.X, pady=5)
        tarjeta.columnconfigure(0, weight=1)
        
        contenido = tk.Frame(tarjeta, bg="white")
        contenido.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        contenido.columnconfigure(1, weight=1)
        
        avatar = tk.Frame(contenido, bg="#3498db", width=40, height=40)
        avatar.pack(side=tk.LEFT, padx=(0, 10))
        avatar.pack_propagate(False)
        
        inicial = participante.get('nombre', 'X')[0].upper()
        tk.Label(avatar, text=inicial, font=("Arial", 16, "bold"),
                bg="#3498db", fg="white").pack(expand=True)
        
        info_frame = tk.Frame(contenido, bg="white")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        nombre = tk.Label(info_frame, text=participante.get('nombre', ''),
                         font=("Arial", 11, "bold"), bg="white")
        nombre.pack(anchor=tk.W)
        
        info_texto = f"Entrada: {participante.get('hora_entrada', 'N/A')} | " \
                    f"Salida: {participante.get('hora_salida', 'N/A')} | " \
                    f"Horas: {participante.get('horas_trabajadas', '0')}"
        info = tk.Label(info_frame, text=info_texto, font=("Arial", 9),
                       bg="white", fg="#7f8c8d")
        info.pack(anchor=tk.W, pady=(3, 0))
        
        botones = tk.Frame(contenido, bg="white")
        botones.pack(side=tk.RIGHT, padx=(10, 0))
        
        btn_editar = tk.Button(botones, text="Editar", width=8,
                              command=lambda: self.on_editar(idx, participante))
        btn_editar.pack(side=tk.LEFT, padx=2)
        
        btn_eliminar = tk.Button(botones, text="Eliminar", width=8,
                                bg="#e74c3c", fg="white",
                                command=lambda: self.on_eliminar(idx))
        btn_eliminar.pack(side=tk.LEFT, padx=2)
        
    def actualizar(self, participantes: List[Dict]):
        self.participantes_data = participantes
        self._actualizar_participantes()
