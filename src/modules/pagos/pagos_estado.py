"""
Módulo de gestión centralizada de estados de pago
Responsable de: Definir y determinar estados de forma única y consistente
Objetivo: Una única fuente de verdad para lógica de estados

IMPORTANTE: Este módulo DEBE ser usado en lugar de lógica duplicada en otros archivos
"""

from enum import Enum
from src.core.logger import registrar_operacion


class EstadoPago(Enum):
    """Estados posibles de un pago"""
    PENDIENTE = 'pendiente'      # Sin pagos
    PARCIAL = 'parcial'          # Pagado menos que esperado
    COMPLETADO = 'completado'    # Pagado exactamente lo esperado
    EXCEDENTE = 'excedente'      # Pagado más que esperado


class GestorEstadoPago:
    """
    Gestor centralizado de estados de pago
    Proporciona una única fuente de verdad para la lógica de estados
    """
    
    # Definición de estados con metadatos
    ESTADOS = {
        'pendiente': {
            'nombre': 'Pendiente',
            'emoji': '',
            'símbolo': '',
            'descripción': 'Sin pagos registrados',
            'color_fg': 'error',
            'color_bg': '#FFEBEE',
            'enum': EstadoPago.PENDIENTE
        },
        'parcial': {
            'nombre': 'Parcial',
            'emoji': '',
            'símbolo': '',
            'descripción': 'Pagado parcialmente',
            'color_fg': 'warning',
            'color_bg': '#FFF9E6',
            'enum': EstadoPago.PARCIAL
        },
        'completado': {
            'nombre': 'Pagado',
            'emoji': '',
            'símbolo': '',
            'descripción': 'Pago completado',
            'color_fg': 'success',
            'color_bg': '#E8F5E9',
            'enum': EstadoPago.COMPLETADO
        },
        'excedente': {
            'nombre': 'Excedente',
            'emoji': '',
            'símbolo': '',
            'descripción': 'Pagado más de lo esperado',
            'color_fg': 'accent_primary',
            'color_bg': '#E3F2FD',
            'enum': EstadoPago.EXCEDENTE
        }
    }
    
    @staticmethod
    def obtener_estado(total_pagado, monto_esperado):
        """
        Obtener estado basado en montos - ÚNICA FUENTE DE VERDAD
        
        Args:
            total_pagado: float - Total pagado por la persona
            monto_esperado: float - Monto esperado/esperado
        
        Returns:
            str - Estado en formato 'pendiente', 'parcial', 'completado', 'excedente'
        
        NOTA: Esta es la ÚNICA función que debe usarse para determinar estados
        """
        if total_pagado > monto_esperado:
            return 'excedente'
        elif total_pagado == monto_esperado:
            return 'completado'
        elif total_pagado > 0:
            return 'parcial'
        else:
            return 'pendiente'
    
    @staticmethod
    def obtener_datos_estado(estado, tema_global=None):
        """
        Obtener datos completos de un estado
        
        Args:
            estado: str - Nombre del estado ('pendiente', 'parcial', 'completado', 'excedente')
            tema_global: dict - Colores del tema (opcional)
        
        Returns:
            dict con: nombre, emoji, símbolo, descripción, colores
        """
        datos = GestorEstadoPago.ESTADOS.get(estado, {})
        
        if not datos:
            return {
                'nombre': 'Desconocido',
                'emoji': '?',
                'símbolo': '?',
                'descripción': 'Estado no reconocido',
                'color_fg': '#000000',
                'color_bg': '#F5F5F5',
                'color_tema_fg': '#000000' if not tema_global else tema_global.get('fg_principal', '#000000'),
                'color_tema_bg': '#F5F5F5' if not tema_global else tema_global.get('bg_secundario', '#F5F5F5')
            }
        
        # Si se proporciona tema, mapear colores de tema
        color_fg = datos['color_fg']
        if tema_global:
            color_fg = tema_global.get(color_fg, datos['color_fg'])
        
        return {
            'nombre': datos['nombre'],
            'emoji': datos['emoji'],
            'símbolo': datos['símbolo'],
            'descripción': datos['descripción'],
            'color_fg': color_fg,
            'color_bg': datos['color_bg'],
            'enum': datos['enum']
        }
    
    @staticmethod
    def obtener_emoji_estado(estado):
        """Obtener solo el emoji de un estado"""
        datos = GestorEstadoPago.ESTADOS.get(estado, {})
        return datos.get('emoji', '')
    
    @staticmethod
    def obtener_nombre_estado(estado):
        """Obtener solo el nombre de un estado"""
        datos = GestorEstadoPago.ESTADOS.get(estado, {})
        return datos.get('nombre', 'Desconocido')
    
    @staticmethod
    def obtener_color_fg(estado, tema_global):
        """Obtener color de foreground para un estado"""
        datos = GestorEstadoPago.ESTADOS.get(estado, {})
        color_key = datos.get('color_fg', 'fg_principal')
        return tema_global.get(color_key, '#000000')
    
    @staticmethod
    def validar_transicion(estado_anterior, estado_nuevo):
        """
        Validar si una transición de estado es válida
        
        Args:
            estado_anterior: str - Estado anterior
            estado_nuevo: str - Estado nuevo
        
        Returns:
            tuple (bool, str) - (es_válida, mensaje)
        
        Transiciones válidas:
        - pendiente → parcial, completado, excedente
        - parcial → completado, excedente
        - completado → completado (sin cambio), excedente (más pagos)
        - excedente → excedente (sin cambio)
        """
        transiciones_validas = {
            'pendiente': ['parcial', 'completado', 'excedente'],
            'parcial': ['completado', 'excedente'],
            'completado': ['completado', 'excedente'],
            'excedente': ['excedente']
        }
        
        if estado_anterior not in transiciones_validas:
            return False, f"Estado anterior inválido: {estado_anterior}"
        
        if estado_nuevo not in transiciones_validas[estado_anterior]:
            return False, f"Transición inválida: {estado_anterior} → {estado_nuevo}"
        
        return True, "Transición válida"
    
    @staticmethod
    def calcular_estado_detallado(persona, monto_esperado):
        """
        Calcular estado detallado de una persona
        
        Args:
            persona: dict - Datos de la persona con 'pagos'
            monto_esperado: float - Monto esperado
        
        Returns:
            dict con: estado, total_pagado, pendiente, porcentaje, num_pagos, último_pago
        """
        total_pagado = sum(pago.get('monto', 0) for pago in persona.get('pagos', []))
        pendiente = max(0, monto_esperado - total_pagado)
        porcentaje = (total_pagado / monto_esperado * 100) if monto_esperado > 0 else 0
        
        estado = GestorEstadoPago.obtener_estado(total_pagado, monto_esperado)
        
        # Obtener fecha del último pago
        último_pago = None
        if persona.get('pagos'):
            último = persona['pagos'][-1]
            último_pago = f"{último.get('fecha', '')} {último.get('hora', '')}".strip()
        
        return {
            'estado': estado,
            'total_pagado': total_pagado,
            'pendiente': pendiente,
            'porcentaje': porcentaje,
            'num_pagos': len(persona.get('pagos', [])),
            'último_pago': último_pago,
            'completo': estado in ['completado', 'excedente'],
            'parcial': estado == 'parcial',
            'pendiente_bool': estado == 'pendiente'
        }
    
    @staticmethod
    def registrar_cambio_estado(persona_folio, estado_anterior, estado_nuevo, 
                               usuario_usuario, gestor_historial):
        """
        Registrar un cambio de estado en el historial
        
        Args:
            persona_folio: str - Folio de la persona
            estado_anterior: str - Estado anterior
            estado_nuevo: str - Estado nuevo
            usuario_usuario: str - Usuario que hizo el cambio
            gestor_historial: Instancia de GestorHistorial
        """
        es_válida, mensaje = GestorEstadoPago.validar_transicion(estado_anterior, estado_nuevo)
        
        if not es_válida:
            registrar_operacion(
                'TRANSICION_ESTADO_INVALIDA',
                f'Intento de transición inválida',
                {'folio': persona_folio, 'anterior': estado_anterior, 'nuevo': estado_nuevo},
                usuario_usuario
            )
            return False
        
        # Registrar cambio válido
        if gestor_historial:
            gestor_historial.registrar_cambio(
                'CAMBIO_ESTADO',
                'PERSONA',
                persona_folio,
                {
                    'estado_anterior': estado_anterior,
                    'estado_nuevo': estado_nuevo,
                    'transicion': f"{estado_anterior} → {estado_nuevo}"
                },
                usuario_usuario
            )
        
        registrar_operacion(
            'CAMBIO_ESTADO_PERSONA',
            f'Estado de persona actualizado: {estado_anterior} → {estado_nuevo}',
            {'folio': persona_folio},
            usuario_usuario
        )
        
        return True


# Funciones de compatibilidad para código antiguo
def obtener_estado(total_pagado, monto_esperado):
    """Función de compatibilidad - usar GestorEstadoPago.obtener_estado() en su lugar"""
    return GestorEstadoPago.obtener_estado(total_pagado, monto_esperado)


def obtener_emoji_estado(estado):
    """Función de compatibilidad - usar GestorEstadoPago.obtener_emoji_estado() en su lugar"""
    return GestorEstadoPago.obtener_emoji_estado(estado)
