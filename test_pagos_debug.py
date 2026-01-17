"""Script de prueba directo para Control de Pagos"""
import sys
import os

# Agregar ruta del proyecto
sys.path.insert(0, os.path.dirname(__file__))

import tkinter as tk
from src.modules.pagos.control_pagos import SistemaControlPagos

def main():
    print("[TEST] Iniciando test de Control de Pagos...")
    
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal temporalmente
    
    try:
        # Crear instancia del sistema
        app = SistemaControlPagos(root)
        
        # Simular usuario autenticado (tus credenciales)
        usuario_test = {
            'nombre': 'nieto',
            'rol': 'admin',
            'password': 'admin'  # Ajusta según tus credenciales
        }
        
        # Mock del gestor de autenticación
        class MockGestorAuth:
            ROLES = {
                'admin': {
                    'permisos': ['*']
                }
            }
        
        gestor_auth_mock = MockGestorAuth()
        
        print("[TEST] Configurando usuario...")
        app.set_usuario(usuario_test, gestor_auth_mock)
        
        print("[TEST] Interfaz configurada correctamente")
        print(f"[TEST] Cooperaciones cargadas: {len(app.cooperaciones)}")
        print(f"[TEST] Cooperación actual: {app.cooperacion_actual}")
        print(f"[TEST] Selector de cooperación existe: {hasattr(app, 'coop_selector')}")
        
        if hasattr(app, 'coop_selector'):
            print(f"[TEST] Valores en selector: {app.coop_selector['values']}")
            print(f"[TEST] Valor actual en selector: {app.coop_selector.get()}")
        
        # Mostrar ventana
        root.deiconify()
        
        print("\n[TEST] Ventana abierta. Prueba el botón 'Agregar Persona'")
        print("[TEST] Presiona Ctrl+C en la terminal para cerrar\n")
        
        root.mainloop()
        
    except Exception as e:
        print(f"[ERROR] Error en el test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
