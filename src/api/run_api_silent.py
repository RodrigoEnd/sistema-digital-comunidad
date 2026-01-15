#!/usr/bin/env python
"""
Ejecutador silencioso de API - Wrapper ultra-minimalista para evitar cualquier output
"""
import sys
import os
import logging

# ===== SILENCIAR PRIMERO, ANTES DE CUALQUIER OTRO IMPORT =====
# Redirigir stdout y stderr a /dev/null INMEDIATAMENTE
_devnull = open(os.devnull, 'w')
sys.stdout = _devnull
sys.stderr = _devnull

# Desactivar todos los logs
logging.disable(logging.CRITICAL)
for name in logging.Logger.manager.loggerDict:
    logging.getLogger(name).disabled = True
    logging.getLogger(name).setLevel(logging.CRITICAL)

# Ahora importar - sin output visible
try:
    from src.api.api_local import app
    
    # Ejecutar sin debug ni reloader ni verbosity
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True,
        processes=1
    )
except Exception as e:
    # Si falla el import absoluto, intentar relativo
    try:
        from .api_local import app
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True,
            processes=1
        )
    except:
        pass
