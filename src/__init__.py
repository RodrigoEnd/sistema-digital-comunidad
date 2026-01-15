"""
Sistema Digital para Comunidades - Paquete Principal
====================================================

Estructura modular del sistema:
- auth/: Autenticación y seguridad
- core/: Utilidades core (logging, validación, base de datos, gestor de datos global)
- modules/: Módulos de negocio principales
  - censo/: Gestión de censo de habitantes
  - pagos/: Control y gestión de pagos
  - faenas/: Gestión de faenas comunitarias
  - indicadores/: Indicadores de estado
  - historial/: Registro histórico
- ui/: Componentes y temas visuales
- tools/: Herramientas auxiliares
"""

__version__ = "1.0.0"
__author__ = "Sistema Digital"

# Importaciones principales
from . import auth
from . import core
from . import modules
from . import ui
from . import tools

__all__ = [
    "api",
    "auth", 
    "core",
    "modules",
    "ui",
    "tools",
]
