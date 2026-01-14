import tkinter as tk
from typing import Callable


class GestorAtajosRapidos:
    def __init__(self, root, callbacks: dict):
        self.root = root
        self.callbacks = callbacks
        self._configurar_atajos()
        
    def _configurar_atajos(self):
        self.root.bind('<Control-n>', lambda e: self._llamar_callback('nueva_faena'))
        self.root.bind('<Control-s>', lambda e: self._llamar_callback('guardar'))
        self.root.bind('<Control-f>', lambda e: self._llamar_callback('buscar'))
        self.root.bind('<Control-e>', lambda e: self._llamar_callback('exportar'))
        self.root.bind('<Escape>', lambda e: self._llamar_callback('cancelar'))
        self.root.bind('<F5>', lambda e: self._llamar_callback('actualizar'))
        self.root.bind('<F1>', lambda e: self._llamar_callback('ayuda'))
        
    def _llamar_callback(self, accion: str):
        callback = self.callbacks.get(accion)
        if callback:
            callback()
            
    def agregar_atajo(self, tecla: str, callback: Callable):
        self.root.bind(tecla, lambda e: callback())
        
    def obtener_atajos_disponibles(self) -> dict:
        return {
            'Ctrl+N': 'Nueva faena',
            'Ctrl+S': 'Guardar',
            'Ctrl+F': 'Buscar',
            'Ctrl+E': 'Exportar',
            'Escape': 'Cancelar',
            'F5': 'Actualizar',
            'F1': 'Ayuda'
        }
