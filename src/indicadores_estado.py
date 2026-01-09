"""
Módulo para calcular indicadores de estado de habitantes basados en pagos y faenas.
Proporciona colorimetría rojo-verde para visualizar deuda y participación.
"""

import os
from datetime import datetime
from seguridad import seguridad
from config import ARCHIVO_PAGOS, ARCHIVO_FAENAS, PASSWORD_CIFRADO


class CalculadorIndicadores:
    """Calcula el estado de pagos y faenas de cada habitante."""
    
    @staticmethod
    def obtener_estado_pagos(folio, nombre):
        """
        Calcula el estado de pagos de una persona.
        Retorna: ratio (0.0 a 1.0) donde 0=debe mucho (rojo), 1=no debe (verde)
        """
        try:
            datos_pagos = seguridad.descifrar_archivo(ARCHIVO_PAGOS, PASSWORD_CIFRADO) or {}
            
            # Buscar en todas las cooperaciones
            cooperaciones = datos_pagos.get('cooperaciones', [])
            deuda_total = 0.0
            pagos_totales = 0.0
            
            for coop in cooperaciones:
                monto_coop = coop.get('monto_cooperacion', 100.0)
                personas = coop.get('personas', [])
                
                for persona in personas:
                    if persona.get('folio') == folio and persona.get('nombre') == nombre:
                        # Calcular deuda
                        monto_esperado = persona.get('monto_esperado', monto_coop)
                        pagos = persona.get('pagos', [])
                        pagado = sum(p.get('monto', 0) for p in pagos)
                        deuda = max(0, monto_esperado - pagado)
                        
                        deuda_total += deuda
                        pagos_totales += pagado
            
            # Calcular ratio: 0 = mucha deuda, 1 = sin deuda
            # Si no hay deuda = 1.0 (verde)
            # Si hay deuda = proporción de lo que debe
            if deuda_total == 0:
                return 1.0
            
            # Si debe más de 3 periodos, máximo rojo
            deuda_normalizada = min(deuda_total, 300.0) / 300.0
            ratio = max(0.0, 1.0 - deuda_normalizada)
            return ratio
            
        except Exception as e:
            print(f"Error calculando estado de pagos: {e}")
            return 0.5  # Gris por defecto
    
    @staticmethod
    def obtener_estado_faenas(folio, nombre):
        """
        Calcula el estado de participación en faenas.
        Retorna: ratio (0.0 a 1.0) donde 0=no participa (rojo), 1=participa activo (verde)
        """
        try:
            datos_faenas = seguridad.descifrar_archivo(ARCHIVO_FAENAS, PASSWORD_CIFRADO) or {}
            faenas = datos_faenas.get('faenas', [])
            
            # Contar faenas del año actual
            año_actual = datetime.now().year
            faenas_año = [f for f in faenas if datetime.strptime(f.get('fecha', '2000-01-01'), "%Y-%m-%d").year == año_actual]
            
            if not faenas_año:
                return 0.5  # Sin datos
            
            # Contar participaciones
            participaciones = 0
            para_participar = len(faenas_año)
            
            for faena in faenas_año:
                participantes = faena.get('participantes', [])
                for p in participantes:
                    if p.get('folio') == folio and p.get('nombre') == nombre:
                        participaciones += 1
                        break
            
            # Ratio: participaciones / faenas_año
            if participaciones == 0:
                return 0.0  # No ha participado (rojo)
            
            ratio = min(1.0, participaciones / para_participar)
            return ratio
            
        except Exception as e:
            print(f"Error calculando estado de faenas: {e}")
            return 0.5  # Gris por defecto
    
    @staticmethod
    def color_por_ratio(ratio):
        """
        Convierte un ratio (0.0 a 1.0) a color hexadecimal.
        0.0 = Rojo (#dc3545)
        0.5 = Amarillo (#ffc107)
        1.0 = Verde (#28a745)
        """
        # Rojo a Amarillo: 0.0 a 0.5
        # Amarillo a Verde: 0.5 a 1.0
        
        if ratio < 0.5:
            # Rojo a Amarillo
            t = ratio * 2  # Normalizar a 0-1
            r = int(220 + (255 - 220) * t)
            g = int(53 + (193 - 53) * t)
            b = int(69 - 69 * t)
        else:
            # Amarillo a Verde
            t = (ratio - 0.5) * 2  # Normalizar a 0-1
            r = int(255 + (40 - 255) * t)
            g = int(193 + (167 - 193) * t)
            b = int(0 + (69 - 0) * t)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    @staticmethod
    def obtener_texto_estado(ratio, tipo='pagos'):
        """Retorna texto descriptivo del estado."""
        if tipo == 'pagos':
            if ratio >= 0.9:
                return "Al día ✓"
            elif ratio >= 0.7:
                return "Poco adeudo"
            elif ratio >= 0.4:
                return "Debe mucho"
            else:
                return "Crítico"
        else:  # faenas
            if ratio >= 0.8:
                return "Muy activo"
            elif ratio >= 0.6:
                return "Participante"
            elif ratio >= 0.3:
                return "Poco activo"
            else:
                return "Ausente"


def calcular_estado_habitante(folio, nombre):
    """
    Calcula el estado combinado de un habitante (pagos y faenas).
    Retorna dict con ratios, colores y textos.
    """
    calc = CalculadorIndicadores()
    
    ratio_pagos = calc.obtener_estado_pagos(folio, nombre)
    ratio_faenas = calc.obtener_estado_faenas(folio, nombre)
    
    return {
        'pagos': {
            'ratio': ratio_pagos,
            'color': calc.color_por_ratio(ratio_pagos),
            'texto': calc.obtener_texto_estado(ratio_pagos, 'pagos')
        },
        'faenas': {
            'ratio': ratio_faenas,
            'color': calc.color_por_ratio(ratio_faenas),
            'texto': calc.obtener_texto_estado(ratio_faenas, 'faenas')
        }
    }
