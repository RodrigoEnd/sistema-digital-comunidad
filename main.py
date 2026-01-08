"""
Sistema de Gestión Comunitaria
Punto de entrada principal con autenticación integrada
"""

import subprocess
import sys
import time
import os
import tkinter as tk
from tkinter import messagebox

# Agregar la carpeta src al path para poder importar los módulos
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

import requests
from config import MODO_OFFLINE

def verificar_api():
    """Verificar si la API está activa"""
    try:
        response = requests.get("http://127.0.0.1:5000/api/ping", timeout=2)
        return response.status_code == 200
    except:
        return False

def iniciar_api():
    """Iniciar el servidor API en segundo plano"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        api_path = os.path.join(script_dir, "src", "api_local.py")
        
        # Iniciar API en segundo plano
        proceso = subprocess.Popen(
            [sys.executable, api_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        print("Iniciando servidor API...")
        # Esperar a que la API esté lista
        for i in range(15):
            time.sleep(0.5)
            if verificar_api():
                print("API iniciada correctamente")
                return True
        
        print("ADVERTENCIA: La API tardó en iniciar, pero continuamos...")
        return True
    except Exception as e:
        print(f"Error al iniciar API: {e}")
        return False

def iniciar_censo():
    """Iniciar el sistema de censo de habitantes"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        censo_path = os.path.join(script_dir, "src", "censo_habitantes.py")
        
        print("\n" + "="*60)
        print("SISTEMA DE GESTION COMUNITARIA")
        print("="*60)
        print("Iniciando Sistema de Censo de Habitantes...")
        print("="*60 + "\n")
        
        # Cambiar al directorio src para que los imports funcionen
        os.chdir(os.path.join(script_dir, "src"))
        
        # Ejecutar censo (bloquea hasta que se cierre)
        subprocess.run([sys.executable, censo_path])
        
    except Exception as e:
        print(f"Error al iniciar censo: {e}")
        import traceback
        traceback.print_exc()
        input("Presiona Enter para salir...")

def main():
    """Función principal con menú de selección"""
    print("\n" + "="*60)
    print("SISTEMA DE GESTION COMUNITARIA")
    print("="*60)
    print("1. Censo de Habitantes")
    print("2. Control de Pagos (con autenticación)")
    print("3. Salir")
    print("="*60)
    
    # Verificar/iniciar API (omitir si modo offline)
    if not MODO_OFFLINE:
        if not verificar_api():
            print("\nLa API no está activa. Iniciando...")
            if not iniciar_api():
                print("ERROR: No se pudo iniciar la API")
                input("Presiona Enter para salir...")
                return
        else:
            print("\n✓ API activa")
    else:
        print("\nModo offline: API no requerida")
    
    opcion = input("\nSeleccione una opción (1-3): ").strip()
    
    if opcion == "1":
        # Iniciar censo
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            censo_path = os.path.join(script_dir, "src", "censo_habitantes.py")
            os.chdir(os.path.join(script_dir, "src"))
            subprocess.run([sys.executable, censo_path])
        except Exception as e:
            print(f"Error al iniciar censo: {e}")
            input("Presiona Enter para salir...")
    
    elif opcion == "2":
        # Iniciar control de pagos con autenticación
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            os.chdir(os.path.join(script_dir, "src"))
            
            # Importar e iniciar control de pagos con login
            from control_pagos import main as control_main
            control_main()
            
        except Exception as e:
            print(f"Error al iniciar control de pagos: {e}")
            import traceback
            traceback.print_exc()
            input("Presiona Enter para salir...")
    
    elif opcion == "3":
        print("\nSaliendo del sistema...")
        return
    
    else:
        print("\nOpción inválida")
        input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
