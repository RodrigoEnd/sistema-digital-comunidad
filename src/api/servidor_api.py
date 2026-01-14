"""
Servidor API Local - Ejecuta en hilo separado sin crear ventana externa
Se importa y ejecuta directamente en el proceso principal
"""
import sys
import os
import threading
import logging

# Suprimir logs completamente
logging.disable(logging.CRITICAL)
for logger_name in ['flask', 'werkzeug', 'urllib3']:
    logging.getLogger(logger_name).disabled = True

# Configurar path
proyecto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if proyecto_raiz not in sys.path:
    sys.path.insert(0, proyecto_raiz)

from flask import Flask, jsonify, request
from flask_cors import CORS

# Crear app Flask global (sin debug)
app = Flask(__name__)
app.logger.disabled = True
app.config['TESTING'] = False
app.config['DEBUG'] = False

CORS(app)

# NO cargar la BD al import time - hacerlo lazy
_db = None

def obtener_db():
    """Obtener instancia de BD (lazy loading)"""
    global _db
    if _db is None:
        try:
            from src.core.base_datos import BaseDatos
            _db = BaseDatos()
        except Exception as e:
            # Objeto dummy si falla
            class BDDummy:
                def obtener_todos(self):
                    return []
            _db = BDDummy()
    return _db


@app.route('/api/habitantes', methods=['GET'])
def obtener_habitantes():
    """Obtener todos los habitantes"""
    db_inst = obtener_db()
    return jsonify({
        'success': True,
        'habitantes': db_inst.obtener_todos(),
        'total': len(db_inst.obtener_todos())
    })


@app.route('/api/habitantes/buscar', methods=['GET'])
def buscar_habitantes():
    """Buscar habitantes por criterio"""
    db_inst = obtener_db()
    criterio = request.args.get('q', '')
    resultados = db_inst.buscar_habitante(criterio)
    
    return jsonify({
        'success': True,
        'resultados': resultados,
        'total': len(resultados)
    })


@app.route('/api/habitantes/nombre/<nombre>', methods=['GET'])
def obtener_por_nombre(nombre):
    """Obtener habitante por nombre exacto"""
    db_inst = obtener_db()
    habitante = db_inst.obtener_habitante_por_nombre(nombre)
    
    if habitante:
        return jsonify({
            'success': True,
            'habitante': habitante
        })
    else:
        return jsonify({
            'success': False,
            'mensaje': 'Habitante no encontrado'
        }), 404


@app.route('/api/habitantes', methods=['POST'])
def agregar_habitante():
    """Agregar nuevo habitante"""
    db_inst = obtener_db()
    datos = request.get_json()
    nombre = datos.get('nombre', '').strip()
    
    if not nombre:
        return jsonify({
            'success': False,
            'mensaje': 'Nombre vacío'
        }), 400
    
    habitante = db_inst.obtener_habitante_por_nombre(nombre)
    if habitante:
        return jsonify({
            'success': True,
            'existe': True,
            'habitante': habitante,
            'mensaje': 'Habitante ya existe'
        })
    else:
        nuevo_habitante, mensaje = db_inst.agregar_habitante(nombre)
        return jsonify({
            'success': True,
            'existe': False,
            'habitante': nuevo_habitante,
            'mensaje': 'Habitante agregado al censo'
        })


@app.route('/ping', methods=['GET'])
def ping():
    """Verificar que la API está funcionando"""
    db_inst = obtener_db()
    try:
        total = len(db_inst.obtener_todos())
    except:
        total = 0
    
    return jsonify({
        'success': True,
        'mensaje': 'API Local funcionando correctamente',
        'total_habitantes': total
    })


def iniciar_servidor_api():
    """Inicia el servidor Flask en modo silencioso (no bloqueante)"""
    try:
        # Usar run() con threaded=True para que sea no-bloqueante
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except:
        pass


# Variable global para controlar el hilo
_hilo_api = None


def iniciar_api_en_hilo():
    """Inicia el API en un hilo daemon separado"""
    global _hilo_api
    
    if _hilo_api is not None and _hilo_api.is_alive():
        return  # Ya está corriendo
    
    _hilo_api = threading.Thread(target=iniciar_servidor_api, daemon=True)
    _hilo_api.start()


if __name__ == '__main__':
    # Si se ejecuta directamente, iniciar servidor
    iniciar_servidor_api()
