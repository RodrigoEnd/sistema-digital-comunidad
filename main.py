"""
Sistema de Gestión Comunitaria
Punto de entrada principal - Inicia menú gráfico
"""

import sys
import os

# Configurar rutas de importación
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar y ejecutar menú principal GUI
from menu_principal import main as menu_main

if __name__ == "__main__":
    menu_main()

