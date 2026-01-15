"""Iniciar API con output visible para debug"""
import sys
import os

# Configurar path
proyecto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
if proyecto_raiz not in sys.path:
    sys.path.insert(0, proyecto_raiz)

# Importar sin silenciar
from src.api.api_local import app

print("Iniciando API en http://127.0.0.1:5000")
print("Presiona Ctrl+C para detener")

app.run(
    host='127.0.0.1',
    port=5000,
    debug=True,  # Con debug para ver errores
    use_reloader=False,
    threaded=True
)
