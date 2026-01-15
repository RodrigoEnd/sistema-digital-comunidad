"""
Importa nombres de habitantes desde un TXT (líneas con formato "N. Nombre - Pago")
usando GestorDatosGlobal.

Uso:
    python tools/cargar_habitantes_desde_txt.py datos/faenas_pagos.txt

Solo importa nombres; ignora los montos.
"""

import re
import sys
import os
from typing import List
from pathlib import Path

# Agregar directorio padre al path para que encuentre src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.gestor_datos_global import obtener_gestor
from src.core.logger import registrar_operacion, registrar_error


def extraer_nombres(desde_txt: str) -> List[str]:
    nombres = []
    with open(desde_txt, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            # Quitar comentarios al final de la línea
            linea = linea.split("#", 1)[0].strip()
            # Formatos soportados: "1. Nombre - 300" o "Nombre - 300" o solo "Nombre"
            m = re.match(r"(?:\d+\.\s*)?([^\-]+?)(?:\s*-.*)?$", linea)
            if not m:
                continue
            nombre = m.group(1).strip()
            # Limpiar caracteres especiales (?) si existen
            nombre = nombre.rstrip('(?)')
            nombre = nombre.strip()
            if nombre:
                nombres.append(nombre)
    return nombres


def enviar_a_gestor(nombres: List[str]) -> None:
    total = len(nombres)
    print(f"Importando {total} nombres al gestor...")
    creados = 0
    repetidos = 0
    errores = 0
    
    gestor = obtener_gestor()

    for i, nombre in enumerate(nombres, 1):
        try:
            print(f"[{i}/{total}] {nombre}...", end=" ", flush=True)
            habitante, resultado = gestor.obtener_o_crear_habitante(nombre)
            
            if habitante:
                if resultado == "creado":
                    creados += 1
                    print("[NUEVO]")
                else:
                    repetidos += 1
                    print("[existe]")
            else:
                errores += 1
                print("[ERROR] No se pudo crear")
                
        except Exception as exc:
            errores += 1
            print(f"[ERROR] {str(exc)[:40]}")
            registrar_error("cargar_habitantes", f"Error con {nombre}: {str(exc)}", "enviar_a_gestor", str(exc))

    print(f"\n=== Resumen ===")
    print(f"Creados: {creados}")
    print(f"Repetidos: {repetidos}")
    print(f"Errores: {errores}")
    print(f"Total procesados: {creados + repetidos + errores}/{total}")
    
    registrar_operacion("BATCH_IMPORT", "cargar_habitantes_desde_txt", 
                       f"Carga batch: {creados} creados, {repetidos} repetidos, {errores} errores")


def main():
    if len(sys.argv) < 2:
        print("Uso: python tools/cargar_habitantes_desde_txt.py <ruta_txt>")
        sys.exit(1)

    ruta = sys.argv[1]
    nombres = extraer_nombres(ruta)
    if not nombres:
        print("No se encontraron nombres en el archivo.")
        sys.exit(1)

    enviar_a_gestor(nombres)


if __name__ == "__main__":
    main()
