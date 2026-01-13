"""
Barra de Estado Moderna para el Control de Pagos
Muestra: Sincronización, API status, Datos guardados, Hora actual, Cambios pendientes
"""
import tkinter as tk
from datetime import datetime
import threading
import time


class BarraEstadoModerna:
    """Barra de estado en la parte inferior de la ventana con información en tiempo real"""
    
    def __init__(self, parent, tema_global, callback_status=None):
        """
        Args:
            parent: Frame padre donde insertar la barra
            tema_global: Dict con colores del tema
            callback_status: Callable para obtener estado del sistema (opcional)
        """
        self.parent = parent
        self.tema_global = tema_global
        self.callback_status = callback_status
        self.running = True
        self.estado_actual = {
            'sync': '✓ Sincronizado',
            'api': '🟢 API Online',
            'saved': '✓ Guardado',
            'changes': '0 cambios pendientes',
            'hora': ''
        }
        
        # Crear frame principal - USAR GRID (no pack)
        self.frame = tk.Frame(parent, bg=tema_global.get('bg_secundario', '#f0f0f0'), 
                             height=35, relief=tk.SUNKEN, bd=1)
        # NO usar pack() aquí - se agregará con grid() en control_pagos.py
        self.frame.pack_propagate(False)
        
        # Configurar grid
        self.frame.columnconfigure(0, weight=0)  # Sync status
        self.frame.columnconfigure(1, weight=0)  # API status
        self.frame.columnconfigure(2, weight=0)  # Saved status
        self.frame.columnconfigure(3, weight=1)  # Espacio expandible
        self.frame.columnconfigure(4, weight=0)  # Cambios
        self.frame.columnconfigure(5, weight=0)  # Hora
        
        # Color de texto
        fg_color = tema_global.get('fg_principal', '#333333')
        bg_card = tema_global.get('bg_secundario', '#f0f0f0')
        
        # Labels de estado - Sincronización
        self.label_sync = tk.Label(self.frame, text="⟳ Sincronizando...", 
                                   bg=bg_card, fg=fg_color, font=('Arial', 9), padx=8)
        self.label_sync.grid(row=0, column=0, sticky='w', padx=(5, 0), pady=5)
        
        # API Status
        self.label_api = tk.Label(self.frame, text="🔴 Conectando...", 
                                  bg=bg_card, fg=fg_color, font=('Arial', 9), padx=8)
        self.label_api.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        # Saved status
        self.label_saved = tk.Label(self.frame, text="💾 Guardado", 
                                    bg=bg_card, fg=fg_color, font=('Arial', 9), padx=8)
        self.label_saved.grid(row=0, column=2, sticky='w', padx=5, pady=5)
        
        # Espacio expandible
        spacer = tk.Frame(self.frame, bg=bg_card)
        spacer.grid(row=0, column=3, sticky='ew')
        
        # Cambios pendientes
        self.label_cambios = tk.Label(self.frame, text="0 cambios", 
                                      bg=bg_card, fg=fg_color, font=('Arial', 9, 'bold'), padx=8)
        self.label_cambios.grid(row=0, column=4, sticky='e', padx=5, pady=5)
        
        # Hora actual
        self.label_hora = tk.Label(self.frame, text="", 
                                   bg=bg_card, fg=fg_color, font=('Arial', 9), padx=8)
        self.label_hora.grid(row=0, column=5, sticky='e', padx=(5, 5), pady=5)
        
        # Iniciar actualización de hora en thread
        self.thread_hora = threading.Thread(target=self._actualizar_hora_continuo, daemon=True)
        self.thread_hora.start()
    
    def _actualizar_hora_continuo(self):
        """Actualiza la hora cada segundo en un thread separado"""
        while self.running:
            try:
                hora_actual = datetime.now().strftime("%H:%M:%S")
                self.label_hora.config(text=hora_actual)
                time.sleep(1)
            except:
                pass
    
    def actualizar_sync(self, estado):
        """Actualizar estado de sincronización"""
        self.estado_actual['sync'] = estado
        self.label_sync.config(text=f"⟳ {estado}")
    
    def actualizar_api(self, online=True):
        """Actualizar estado de API"""
        if online:
            self.estado_actual['api'] = "🟢 API Online"
            self.label_api.config(text="🟢 API Online", fg='#27ae60')
        else:
            self.estado_actual['api'] = "🔴 API Offline"
            self.label_api.config(text="🔴 API Offline", fg='#e74c3c')
    
    def actualizar_saved(self, guardado=True, cambios_pendientes=0):
        """Actualizar estado de guardado"""
        if guardado and cambios_pendientes == 0:
            self.label_saved.config(text="✓ Guardado", fg='#27ae60')
            self.estado_actual['saved'] = "✓ Guardado"
        else:
            self.label_saved.config(text="⚠ Sin guardar", fg='#f39c12')
            self.estado_actual['saved'] = "⚠ Sin guardar"
        
        # Actualizar cambios pendientes
        if cambios_pendientes > 0:
            self.label_cambios.config(text=f"{cambios_pendientes} cambios", fg='#e74c3c')
        else:
            self.label_cambios.config(text="0 cambios", fg='#27ae60')
        
        self.estado_actual['changes'] = f"{cambios_pendientes} cambios"
    
    def mostrar_mensaje_temporal(self, mensaje, duracion=2):
        """Mostrar un mensaje temporal en la barra (ej: "Guardado correctamente")"""
        texto_original = self.label_saved.cget('text')
        self.label_saved.config(text=mensaje, fg='#27ae60')
        
        def restaurar():
            time.sleep(duracion)
            self.label_saved.config(text=texto_original)
        
        thread = threading.Thread(target=restaurar, daemon=True)
        thread.start()
    
    def destruir(self):
        """Detener threads y destruir la barra"""
        self.running = False
        if hasattr(self, 'frame'):
            self.frame.destroy()
