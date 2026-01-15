from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
import logging
import warnings

# ==================== SILENCIAR COMPLETAMENTE - ORDEN CRÍTICO ====================
# COMENTADO TEMPORALMENTE PARA DEBUG
# 1. Redirigir stdout/stderr ANTES de cualquier import que produzca output
# _devnull = open(os.devnull, 'w')
# sys.stdout = _devnull
# sys.stderr = _devnull

# 2. Desactivar warnings de Python
# warnings.filterwarnings('ignore')

# 3. Desactivar todos los logs
# logging.disable(logging.CRITICAL)
# for logger in ['flask', 'werkzeug', 'urllib3', 'requests']:
#     logging.getLogger(logger).disabled = True
#     logging.getLogger(logger).setLevel(logging.CRITICAL)

# Configurar path para imports cuando se ejecuta directamente
proyecto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if proyecto_raiz not in sys.path:
    sys.path.insert(0, proyecto_raiz)

# Crear app Flask con logging desactivado
app = Flask(__name__)
# app.logger.disabled = True
# app.logger.setLevel(logging.CRITICAL)

# Desactivar logs de werkzeug (el logger de Flask)
# log_werkzeug = logging.getLogger('werkzeug')
# log_werkzeug.disabled = True
# log_werkzeug.setLevel(logging.CRITICAL)

# Activar CORS sin mostrar logs
CORS(app)

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

@app.route('/api/habitantes/<folio>', methods=['PATCH', 'DELETE'])
def modificar_habitante(folio):
    """Actualizar o eliminar un habitante según el método HTTP"""
    db_inst = obtener_db()
    
    if request.method == 'PATCH':
        # Actualizar estado o nota
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
    
    elif request.method == 'DELETE':
        # Eliminar habitante (soft delete)
        try:
            exito, mensaje = db_inst.eliminar_habitante(folio)
            if exito:
                return jsonify({
                    'success': True,
                    'message': mensaje
                })
            else:
                return jsonify({
                    'success': False,
                    'message': mensaje
                }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error al eliminar habitante: {str(e)}'
            }), 500

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
        # Ejecutar API en silencio completo - modo producción
        app.run(
            host='127.0.0.1', 
            port=5000, 
            debug=False, 
            use_reloader=False,
            threaded=True,
            processes=1
        )
    except Exception:
        # Ignorar cualquier error silenciosamente
        pass

