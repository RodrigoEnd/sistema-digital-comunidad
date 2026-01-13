"""
Módulo de utilidades y funciones compartidas
Responsable de: funciones auxiliares, formateo, búsquedas
"""

import tkinter as tk
from datetime import datetime
from src.modules.pagos.pagos_constantes import PATRONES


class UtiliPagos:
    """Utilidades compartidas para el módulo de pagos"""
    
    @staticmethod
    def formatear_dinero(monto):
        """Formatear dinero con símbolo y decimales"""
        return f"${monto:.2f}"
    
    @staticmethod
    def formatear_porcentaje(valor):
        """Formatear porcentaje"""
        return f"{valor:.1f}%"
    
    @staticmethod
    def formatear_fecha(fecha_str):
        """Formatear fecha para mostrar"""
        if not fecha_str:
            return '-'
        try:
            fecha = datetime.strptime(fecha_str, PATRONES['datetime_formato'])
            return fecha.strftime(PATRONES['fecha_formato'])
        except:
            return fecha_str
    
    @staticmethod
    def obtener_estado_color(estado, tema_global):
        """
        Obtener color basado en estado
        
        Args:
            estado: tipo de estado ('completado', 'parcial', 'pendiente', etc)
            tema_global: dict con colores del tema
        
        Returns:
            tuple (foreground, background)
        """
        colores_estado = {
            'completado': (tema_global.get('success', '#4CAF50'), '#E8F5E9'),
            'parcial': (tema_global.get('warning', '#FFC107'), '#FFF9E6'),
            'pendiente': (tema_global.get('error', '#F44336'), '#FFEBEE'),
            'excedente': (tema_global.get('accent_primary', '#2196F3'), '#E3F2FD'),
            'inactivo': ('#757575', '#F5F5F5'),
        }
        return colores_estado.get(estado, (tema_global['fg_principal'], tema_global['bg_secundario']))
    
    @staticmethod
    def obtener_emoji_estado(estado):
        """Obtener emoji según estado"""
        emojis = {
            'completado': '🟢',
            'parcial': '🟡',
            'pendiente': '🔴',
            'excedente': '🔵',
            'inactivo': '⚫'
        }
        return emojis.get(estado, '⚪')
    
    @staticmethod
    def truncar_texto(texto, max_chars=50, sufijo='...'):
        """Truncar texto si excede longitud máxima"""
        if len(texto) > max_chars:
            return texto[:max_chars - len(sufijo)] + sufijo
        return texto
    
    @staticmethod
    def buscar_similitud(texto1, texto2):
        """
        Calcular similitud entre dos textos (0-1)
        Usa coincidencia simple de palabras
        
        Returns:
            float entre 0 y 1
        """
        texto1 = texto1.lower().split()
        texto2 = texto2.lower().split()
        
        if not texto1 or not texto2:
            return 0.0
        
        coincidencias = sum(1 for palabra in texto1 if palabra in texto2)
        total = max(len(texto1), len(texto2))
        
        return coincidencias / total if total > 0 else 0.0
    
    @staticmethod
    def filtrar_personas_por_criterio(personas, criterio, valor):
        """
        Filtrar personas por criterio
        
        Args:
            personas: lista de personas
            criterio: 'nombre', 'folio', 'estado'
            valor: valor a buscar
        
        Returns:
            lista filtrada
        """
        if not valor:
            return personas
        
        valor_lower = str(valor).lower()
        resultados = []
        
        for persona in personas:
            if criterio == 'nombre':
                if valor_lower in persona.get('nombre', '').lower():
                    resultados.append(persona)
            elif criterio == 'folio':
                if valor_lower in persona.get('folio', '').lower():
                    resultados.append(persona)
        
        return resultados
    
    @staticmethod
    def ordenar_personas(personas, columna, reversa=False):
        """
        Ordenar personas por columna
        
        Args:
            personas: lista de personas
            columna: nombre de columna a ordenar
            reversa: si True, orden inverso
        
        Returns:
            lista ordenada
        """
        def clave(persona):
            if columna == 'nombre':
                return persona.get('nombre', '').lower()
            elif columna == 'folio':
                return persona.get('folio', '').lower()
            elif columna == 'monto':
                return persona.get('monto_esperado', 0)
            elif columna == 'pagado':
                return sum(p['monto'] for p in persona.get('pagos', []))
            elif columna == 'estado':
                pagado = sum(p['monto'] for p in persona.get('pagos', []))
                esperado = persona.get('monto_esperado', 100)
                if pagado >= esperado:
                    return 0  # Completado
                elif pagado > 0:
                    return 1  # Parcial
                else:
                    return 2  # Pendiente
            else:
                return 0
        
        return sorted(personas, key=clave, reverse=reversa)
    
    @staticmethod
    def generar_id_temporal():
        """Generar ID temporal para elementos UI"""
        import time
        return f"temp_{int(time.time() * 1000)}"
    
    @staticmethod
    def validar_folio(folio):
        """Validar formato de folio"""
        if not folio or not folio.strip():
            return False, "El folio no puede estar vacío"
        
        if len(folio) > 50:
            return False, "El folio es demasiado largo (máximo 50 caracteres)"
        
        return True, "Folio válido"
    
    @staticmethod
    def crear_resumen_persona(persona):
        """
        Crear resumen de texto para una persona
        
        Returns:
            str con información resumida
        """
        folio = persona.get('folio', 'SIN-FOLIO')
        nombre = persona.get('nombre', 'Desconocido')
        
        pagado = sum(p['monto'] for p in persona.get('pagos', []))
        esperado = persona.get('monto_esperado', 100)
        pendiente = max(0, esperado - pagado)
        
        estado_emoji = UtiliPagos.obtener_emoji_estado(
            'completado' if pendiente <= 0 else 'parcial' if pagado > 0 else 'pendiente'
        )
        
        return (
            f"{estado_emoji} {nombre}\n"
            f"Folio: {folio}\n"
            f"Pagado: {UtiliPagos.formatear_dinero(pagado)} / "
            f"Esperado: {UtiliPagos.formatear_dinero(esperado)}"
        )
    
    @staticmethod
    def calcular_estadisticas_grupo(personas):
        """
        Calcular estadísticas generales del grupo
        
        Returns:
            dict con estadísticas
        """
        if not personas:
            return {
                'total_personas': 0,
                'total_esperado': 0,
                'total_pagado': 0,
                'total_pendiente': 0,
                'promedio_pagado': 0,
                'porcentaje_general': 0
            }
        
        total_esperado = sum(p.get('monto_esperado', 100) for p in personas)
        total_pagado = sum(
            sum(pago['monto'] for pago in p.get('pagos', []))
            for p in personas
        )
        
        return {
            'total_personas': len(personas),
            'total_esperado': total_esperado,
            'total_pagado': total_pagado,
            'total_pendiente': max(0, total_esperado - total_pagado),
            'promedio_pagado': total_pagado / len(personas) if personas else 0,
            'porcentaje_general': (total_pagado / total_esperado * 100) if total_esperado > 0 else 0
        }
