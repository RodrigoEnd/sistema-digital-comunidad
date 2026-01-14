from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
import logging
from io import StringIO

# Configurar path para imports cuando se ejecuta directamente
proyecto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if proyecto_raiz not in sys.path:
    sys.path.insert(0, proyecto_raiz)

# Suprimir logs de Flask completamente cuando se ejecuta en segundo plano
if __name__ == '__main__':
    # Desactivar logs de Flask
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    log.disabled = True
    
    # Redirigir stdout/stderr al null para que no muestre nada
    null_stream = StringIO()
    sys.stdout = null_stream
    sys.stderr = null_stream

# NO cargar la BD al import time - hacerlo lazy
db = None

def obtener_db():
    """Obtener instancia de BD (lazy loading)"""
    global db
    if db is None:
        try:
            from src.core.base_datos import BaseDatos
            db = BaseDatos()
        except Exception as e:
            print(f"ERROR al inicializar BD: {e}", file=sys.stderr)
            # Retornar un objeto dummy para que el ping siga funcionando
            class BDDummy:
                def obtener_todos(self):
                    return []
            db = BDDummy()
    return db

app = Flask(__name__)
CORS(app)  # Permitir conexiones locales entre aplicaciones

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
            'mensaje': 'El nombre es obligatorio'
        }), 400
    
    habitante, mensaje = db_inst.agregar_habitante(nombre)
    
    if habitante:
        return jsonify({
            'success': True,
            'mensaje': mensaje,
            'habitante': habitante
        })
    else:
        return jsonify({
            'success': False,
            'mensaje': mensaje
        }), 400

@app.route('/api/habitantes/<folio>', methods=['PATCH'])
def actualizar_habitante(folio):
    """Actualizar estado o nota de un habitante"""
    db_inst = obtener_db()
    datos = request.get_json() or {}
    cambios = {}
    if 'activo' in datos:
        cambios['activo'] = bool(datos.get('activo'))
    if 'nota' in datos:
        cambios['nota'] = datos.get('nota')

    actualizado = db_inst.actualizar_habitante(folio, cambios)
    if actualizado:
        return jsonify({
            'success': True,
            'habitante': actualizado
        })
    return jsonify({
        'success': False,
        'mensaje': 'Habitante no encontrado'
    }), 404

@app.route('/api/folio/siguiente', methods=['GET'])
def obtener_siguiente_folio():
    """Obtener el siguiente folio disponible sin crear habitante"""
    db_inst = obtener_db()
    folio = db_inst.obtener_siguiente_folio()
    return jsonify({
        'success': True,
        'folio': folio
    })

@app.route('/api/sync/verificar', methods=['POST'])
def verificar_y_agregar():
    """Verificar si existe un habitante, si no, agregarlo"""
    db_inst = obtener_db()
    datos = request.get_json()
    nombre = datos.get('nombre', '').strip()
    
    if not nombre:
        return jsonify({
            'success': False,
            'mensaje': 'El nombre es obligatorio'
        }), 400
    
    # Buscar si existe
    habitante = db_inst.obtener_habitante_por_nombre(nombre)
    
    if habitante:
        return jsonify({
            'success': True,
            'existe': True,
            'habitante': habitante,
            'mensaje': 'Habitante ya existe'
        })
    else:
        # Agregar nuevo
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

if __name__ == '__main__':
    try:
        # Ejecutar API en silencio completo - sin mostrar nada en consola
        app.run(
            host='127.0.0.1', 
            port=5000, 
            debug=False, 
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        # Si hay error, escribir a un archivo de log silenciosamente
        try:
            import os
            log_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'SistemaComunidad')
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, 'api_error.log'), 'a') as f:
                f.write(f"Error en API: {e}\n")
        except:
            pass

