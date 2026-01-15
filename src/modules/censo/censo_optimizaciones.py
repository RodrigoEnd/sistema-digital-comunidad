"""
Funciones optimizadas para el censo
Reemplazan las funciones originales para evitar congelamiento con grandes volúmenes
"""

import threading
import tkinter as tk
from src.core.logger import registrar_error
from src.config import CENSO_NOTA_MAX_DISPLAY


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
    """Actualizar tabla de forma rápida sin bloquear UI"""
    try:
        if not hasattr(self, 'tree'):
            return
        
        # Deshabilitar redibujado temporal
        self.tree.configure(takefocus=False)
        
        # Limpiar tabla rápidamente
        items = self.tree.get_children()
        if items:
            self.tree.delete(*items)
        
        # Insertar directamente sin lotes - más rápido para <1000 items
        for hab in habitantes:
            activo = hab.get('activo', True)
            estado_icono = "● Activo" if activo else "● Inactivo"
            tag = 'activo' if activo else 'inactivo'
            nota = hab.get('nota', '')
            
            self.tree.insert('', tk.END,
                           values=(hab['folio'],
                                  hab['nombre'],
                                  hab.get('fecha_registro', ''),
                                  estado_icono,
                                  nota[:CENSO_NOTA_MAX_DISPLAY] + '...' if len(nota) > CENSO_NOTA_MAX_DISPLAY else nota),
                           tags=(tag,))
        
        # Reactivar redibujado
        self.tree.configure(takefocus=True)
        
        # Actualizar contadores
        if hasattr(self, 'total_label'):
            self.total_label.config(text=f"Total Habitantes: {len(habitantes)}")
        if hasattr(self, '_actualizar_indicadores_estado'):
            self._actualizar_indicadores_estado()
        if hasattr(self, '_actualizar_barra_estado'):
            self._actualizar_barra_estado()
        
    except Exception as e:
        print(f"Error actualizando tabla: {e}")
        registrar_error('censo_habitantes', '_actualizar_tabla_incremental', str(e))
        # Reactivar redibujado en caso de error
        if hasattr(self, 'tree'):
            self.tree.configure(takefocus=True)
