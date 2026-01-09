import os
import random
from uuid import uuid4
from datetime import datetime, date
import sys

# Configurar path para imports cuando se ejecuta directamente
if __name__ == "__main__":
    # Agregar la raíz del proyecto al path
    proyecto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    if proyecto_raiz not in sys.path:
        sys.path.insert(0, proyecto_raiz)

from src.auth.seguridad import seguridad
from src.config import ARCHIVO_FAENAS, PASSWORD_CIFRADO
try:
    from src.core.base_datos import db
except Exception:
    db = None

NOMBRES_FAENAS = [
    "Limpieza de calles",
    "Reparación de barda",
    "Poda de árboles",
    "Mantenimiento del parque",
    "Desazolve de drenaje",
    "Pintura de la escuela",
    "Limpieza del panteón",
    "Rehabilitación de alumbrado",
    "Construcción de banqueta",
    "Señalización vial"
]

PESOS = [3, 5, 7, 9, 4, 6, 8, 2, 10, 1]

def fecha_random_2025(indice):
    # Distribuye en meses distintos para variedad
    mes = (indice % 12) + 1
    dia = random.randint(5, 25)
    return f"2025-{mes:02d}-{dia:02d}"


def generar_simulacion_2025():
    # Cargar habitantes
    if not db:
        print("No se encontró base de datos local de habitantes.")
        habitantes = []
    else:
        try:
            habitantes = db.obtener_todos() or []
        except Exception:
            habitantes = []
    
    if not habitantes:
        print("ADVERTENCIA: No hay habitantes; la simulación usará nombres genéricos.")
        habitantes = [
            {'folio': f'H{100+i:03d}', 'nombre': f'Habitante {i+1}'} for i in range(30)
        ]
    
    # Cargar faenas existentes
    datos = seguridad.descifrar_archivo(ARCHIVO_FAENAS, PASSWORD_CIFRADO) or {}
    faenas = datos.get('faenas', [])

    # Generar 10 faenas del 2025
    for i, (nombre_faena, peso) in enumerate(zip(NOMBRES_FAENAS, PESOS)):
        fecha = fecha_random_2025(i)
        faena = {
            'id': uuid4().hex[:8],
            'fecha': fecha,
            'nombre': nombre_faena,
            'peso': peso,
            'hora_inicio': '8:00 AM',
            'hora_fin': '12:00 PM',
            'es_programada': False,
            'participantes': [],
            'pagos_sustitutos': [],
            'monto_pago_faena': None,
        }
        
        # Selección de participantes
        poblacion = habitantes.copy()
        random.shuffle(poblacion)
        n_total = min(24, len(poblacion))
        seleccion = poblacion[:n_total]
        
        # Distribución: 50% asistencia directa, 25% sustituye con habitante, 10% sustituye con externo, resto no asiste
        n_directo = max(6, int(n_total * 0.5))
        n_hab = max(4, int(n_total * 0.25))
        n_ext = max(2, int(n_total * 0.10))
        
        # Asistencia directa
        for h in seleccion[:n_directo]:
            faena['participantes'].append({
                'folio': h.get('folio', ''),
                'nombre': h.get('nombre', ''),
                'hora_registro': datetime.now().isoformat(),
                'peso_aplicado': 1.0
            })
        
        # Sustituciones con habitante: elegir pares (pagador, trabajador)
        hab_pagadores = seleccion[n_directo:n_directo+n_hab]
        trabajadores_pool = [h for h in habitantes if h not in seleccion[:n_directo] and h not in hab_pagadores]
        random.shuffle(trabajadores_pool)
        
        for idx, pagador in enumerate(hab_pagadores):
            if not trabajadores_pool:
                break
            trabajador = trabajadores_pool.pop()
            if trabajador.get('folio') == pagador.get('folio'):
                continue
            
            # Pagador con 90%
            faena['participantes'].append({
                'folio': pagador.get('folio', ''),
                'nombre': pagador.get('nombre', ''),
                'hora_registro': datetime.now().isoformat(),
                'sustitucion_tipo': 'habitante',
                'trabajador_folio': trabajador.get('folio', ''),
                'trabajador_nombre': trabajador.get('nombre', ''),
                'peso_aplicado': 0.9
            })
            # Trabajador con 100%
            faena['participantes'].append({
                'folio': trabajador.get('folio', ''),
                'nombre': trabajador.get('nombre', ''),
                'hora_registro': datetime.now().isoformat(),
                'peso_aplicado': 1.0
            })
        
        # Sustituciones con externo
        ext_pagadores = seleccion[n_directo+n_hab:n_directo+n_hab+n_ext]
        for pagador in ext_pagadores:
            nombre_ext = random.choice([
                'Albañil José', 'Maestro Luis', 'Oficial Pedro', 'Técnico Raul', 'Jardinero Miguel'
            ])
            faena['participantes'].append({
                'folio': pagador.get('folio', ''),
                'nombre': pagador.get('nombre', ''),
                'hora_registro': datetime.now().isoformat(),
                'sustitucion_tipo': 'externo',
                'trabajador_nombre': nombre_ext,
                'peso_aplicado': 1.0
            })
        
        faenas.append(faena)
    
    # Guardar cifrado
    out = {
        'faenas': faenas,
        'tema': datos.get('tema', 'claro'),
        'fecha_guardado': datetime.now().isoformat(),
    }
    seguridad.cifrar_archivo(out, ARCHIVO_FAENAS, PASSWORD_CIFRADO)
    
    print("Simulación generada: 10 faenas en 2025 con asistencias y sustituciones.")


if __name__ == '__main__':
    generar_simulacion_2025()
