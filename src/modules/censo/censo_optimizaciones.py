"""
Funciones optimizadas para el censo
Reemplazan las funciones originales para evitar congelamiento con grandes volúmenes
"""

import threading
import tkinter as tk
from src.core.logger import registrar_error
from src.config import CENSO_BATCH_INSERT_SIZE, CENSO_UPDATE_UI_EVERY_N
from .censo_utils import estado_texto_color_tag, resumir_nota


def cargar_habitantes_async(self):
    """Cargar todos los habitantes desde el gestor (as\u00edncrono)"""
    if hasattr(self, '_carga_en_progreso') and self._carga_en_progreso:
        print("[Censo] Ya hay una carga en progreso, ignorando...")
        return
    
    self._carga_en_progreso = True
    
    def _cargar_thread():
        try:
            print("[Censo] Iniciando carga de habitantes...")
            habitantes = self.gestor.obtener_habitantes(incluir_inactivos=True)
            
            # Actualizar en hilo principal
            self.root.after(0, lambda: _finalizar_carga_async(self, habitantes))
            
        except Exception as e:
            print(f"Error cargando habitantes: {e}")
            registrar_error('censo_habitantes', 'cargar_habitantes', str(e))
            self._carga_en_progreso = False
    
    # Ejecutar en thread separado
    thread = threading.Thread(target=_cargar_thread, daemon=True)
    thread.start()


def _finalizar_carga_async(self, habitantes):
    """Finaliza la carga de habitantes en el hilo principal"""
    try:
        self.habitantes = habitantes
        if hasattr(self, 'habitantes_filtrados'):
            self.habitantes_filtrados = habitantes.copy()
        
        # Actualizar UI solo si la tabla existe
        if hasattr(self, 'tree'):
            actualizar_tabla_incremental(self, habitantes)
        
        print(f"[Censo] ✓ {len(habitantes)} habitantes cargados")
    finally:
        self._carga_en_progreso = False


def actualizar_tabla_incremental(self, habitantes):
    """Actualizar tabla de forma rápida sin bloquear UI con optimización por lotes"""
    try:
        if not hasattr(self, 'tree'):
            return
        
        # Prevenir actualizaciones visuales durante la modificación
        self.tree.configure(takefocus=False)
        
        # Limpiar tabla rápidamente
        items = self.tree.get_children()
        if items:
            self.tree.delete(*items)
        
        # Optimización: Preparar datos primero, insertar después
        datos_preparados = []
        for hab in habitantes:
            activo = hab.get('activo', True)
            estado_icono, _color, tag = estado_texto_color_tag(activo)
            nota_resumen = resumir_nota(hab.get('nota', ''))

            datos_preparados.append({
                'values': (
                    hab['folio'],
                    hab['nombre'],
                    hab.get('fecha_registro', ''),
                    estado_icono,
                    nota_resumen
                ),
                'tags': (tag,)
            })
        
        # Insertar en lotes de 100 para evitar lag
        BATCH_SIZE = CENSO_BATCH_INSERT_SIZE
        for i in range(0, len(datos_preparados), BATCH_SIZE):
            batch = datos_preparados[i:i+BATCH_SIZE]
            for item in batch:
                self.tree.insert('', tk.END, values=item['values'], tags=item['tags'])
            
            # Permitir que la UI responda cada cierto número de lotes
            if i > 0 and i % (CENSO_UPDATE_UI_EVERY_N * 6) == 0:  # 300 items
                self.tree.update_idletasks()
        
        # Reactivar redibujado
        self.tree.configure(takefocus=True)
        
        # Actualizar contadores de forma asíncrona
        if hasattr(self, 'total_label'):
            self.total_label.config(text=f"Total Habitantes: {len(habitantes)}")
        
        # Actualizar indicadores y barra de estado de forma asíncrona (no bloquear)
        if hasattr(self, 'root'):
            self.root.after_idle(self._actualizar_indicadores_y_barra_async)
        
    except Exception as e:
        print(f"Error actualizando tabla: {e}")
        registrar_error('censo_habitantes', '_actualizar_tabla_incremental', str(e))
        # Reactivar redibujado en caso de error
        if hasattr(self, 'tree'):
            self.tree.configure(takefocus=True)
