from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os

# Configurar path para imports cuando se ejecuta directamente
proyecto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if proyecto_raiz not in sys.path:
    sys.path.insert(0, proyecto_raiz)

from src.core.base_datos import db

app = Flask(__name__)
CORS(app)  # Permitir conexiones locales entre aplicaciones

@app.route('/api/habitantes', methods=['GET'])
def obtener_habitantes():
    """Obtener todos los habitantes"""
    return jsonify({
        'success': True,
        'habitantes': db.obtener_todos(),
        'total': len(db.obtener_todos())
    })

@app.route('/api/habitantes/buscar', methods=['GET'])
def buscar_habitantes():
    """Buscar habitantes por criterio"""
    criterio = request.args.get('q', '')
    resultados = db.buscar_habitante(criterio)
    
    return jsonify({
        'success': True,
        'resultados': resultados,
        'total': len(resultados)
    })

@app.route('/api/habitantes/nombre/<nombre>', methods=['GET'])
def obtener_por_nombre(nombre):
    """Obtener habitante por nombre exacto"""
    habitante = db.obtener_habitante_por_nombre(nombre)
    
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
    datos = request.get_json()
    nombre = datos.get('nombre', '').strip()
    
    if not nombre:
        return jsonify({
            'success': False,
            'mensaje': 'El nombre es obligatorio'
        }), 400
    
    habitante, mensaje = db.agregar_habitante(nombre)
    
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
    datos = request.get_json() or {}
    cambios = {}
    if 'activo' in datos:
        cambios['activo'] = bool(datos.get('activo'))
    if 'nota' in datos:
        cambios['nota'] = datos.get('nota')

    actualizado = db.actualizar_habitante(folio, cambios)
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
    folio = db.obtener_siguiente_folio()
    return jsonify({
        'success': True,
        'folio': folio
    })

@app.route('/api/sync/verificar', methods=['POST'])
def verificar_y_agregar():
    """Verificar si existe un habitante, si no, agregarlo"""
    datos = request.get_json()
    nombre = datos.get('nombre', '').strip()
    
    if not nombre:
        return jsonify({
            'success': False,
            'mensaje': 'El nombre es obligatorio'
        }), 400
    
    # Buscar si existe
    habitante = db.obtener_habitante_por_nombre(nombre)
    
    if habitante:
        return jsonify({
            'success': True,
            'existe': True,
            'habitante': habitante,
            'mensaje': 'Habitante ya existe'
        })
    else:
        # Agregar nuevo
        nuevo_habitante, mensaje = db.agregar_habitante(nombre)
        return jsonify({
            'success': True,
            'existe': False,
            'habitante': nuevo_habitante,
            'mensaje': 'Habitante agregado al censo'
        })

@app.route('/api/ping', methods=['GET'])
def ping():
    """Verificar que la API está funcionando"""
    return jsonify({
        'success': True,
        'mensaje': 'API Local funcionando correctamente',
        'total_habitantes': len(db.obtener_todos())
    })

if __name__ == '__main__':
    print("\n" + "="*50)
    print("API LOCAL INICIADA")
    print("="*50)
    print(f"Total habitantes en base de datos: {len(db.obtener_todos())}")
    print("Endpoints disponibles:")
    print("  GET    /api/habitantes")
    print("  GET    /api/habitantes/buscar?q=criterio")
    print("  GET    /api/habitantes/nombre/<nombre>")
    print("  POST   /api/habitantes")
    print("  PATCH  /api/habitantes/<folio>")
    print("  POST   /api/sync/verificar")
    print("  GET    /api/folio/siguiente")
    print("  GET    /api/ping")
    print("="*50)
    print("Presiona Ctrl+C para detener el servidor\n")
    
    app.run(host='127.0.0.1', port=5000, debug=False)
