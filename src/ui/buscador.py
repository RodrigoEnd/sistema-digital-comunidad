"""
Sistema de busqueda avanzada con filtros
Permite buscar y filtrar datos por multiples criterios
"""

from datetime import datetime
from src.core.logger import registrar_error

class BuscadorAvanzado:
    """Buscador con filtros avanzados"""
    
    def buscar_personas(self, personas, criterios):
        """
        Busca personas con criterios avanzados
        
        Args:
            personas (list): Lista de personas
            criterios (dict): Diccionario con filtros:
                - nombre: str (busqueda por nombre)
                - folio: str (busqueda por folio)
                - estado_pago: 'PAGADO', 'PENDIENTE', 'PARCIAL'
                - monto_minimo: float
                - monto_maximo: float
                - fecha_registro_inicio: 'DD/MM/YYYY'
                - fecha_registro_fin: 'DD/MM/YYYY'
                
        Returns:
            list: Personas que coinciden con los criterios
        """
        try:
            resultados = personas.copy()
            
            # Filtro por nombre (busqueda parcial)
            if 'nombre' in criterios and criterios['nombre']:
                nombre_busca = criterios['nombre'].lower()
                resultados = [
                    p for p in resultados
                    if nombre_busca in p.get('nombre', '').lower()
                ]
            
            # Filtro por folio (busqueda exacta o parcial)
            if 'folio' in criterios and criterios['folio']:
                folio_busca = criterios['folio'].upper()
                resultados = [
                    p for p in resultados
                    if folio_busca in p.get('folio', '').upper()
                ]
            
            # Filtro por estado de pago
            if 'estado_pago' in criterios and criterios['estado_pago']:
                estado = criterios['estado_pago']
                resultados_filtrados = []
                
                for persona in resultados:
                    monto_esperado = persona.get('monto_esperado', 0)
                    pagos = persona.get('pagos', [])
                    total_pagado = sum(p.get('monto', 0) for p in pagos)
                    pendiente = max(0, monto_esperado - total_pagado)
                    
                    if estado == 'PAGADO' and pendiente == 0:
                        resultados_filtrados.append(persona)
                    elif estado == 'PENDIENTE' and total_pagado == 0:
                        resultados_filtrados.append(persona)
                    elif estado == 'PARCIAL' and total_pagado > 0 and pendiente > 0:
                        resultados_filtrados.append(persona)
                
                resultados = resultados_filtrados
            
            # Filtro por monto minimo
            if 'monto_minimo' in criterios and criterios['monto_minimo'] is not None:
                monto_min = float(criterios['monto_minimo'])
                resultados_filtrados = []
                
                for persona in resultados:
                    pagos = persona.get('pagos', [])
                    total_pagado = sum(p.get('monto', 0) for p in pagos)
                    if total_pagado >= monto_min:
                        resultados_filtrados.append(persona)
                
                resultados = resultados_filtrados
            
            # Filtro por monto maximo
            if 'monto_maximo' in criterios and criterios['monto_maximo'] is not None:
                monto_max = float(criterios['monto_maximo'])
                resultados_filtrados = []
                
                for persona in resultados:
                    pagos = persona.get('pagos', [])
                    total_pagado = sum(p.get('monto', 0) for p in pagos)
                    if total_pagado <= monto_max:
                        resultados_filtrados.append(persona)
                
                resultados = resultados_filtrados
            
            # Filtro por fecha de registro
            if 'fecha_registro_inicio' in criterios or 'fecha_registro_fin' in criterios:
                fecha_inicio = None
                fecha_fin = None
                
                if 'fecha_registro_inicio' in criterios:
                    fecha_inicio = datetime.strptime(criterios['fecha_registro_inicio'], '%d/%m/%Y')
                
                if 'fecha_registro_fin' in criterios:
                    fecha_fin = datetime.strptime(criterios['fecha_registro_fin'], '%d/%m/%Y')
                
                resultados_filtrados = []
                for persona in resultados:
                    fecha_registro_str = persona.get('fecha_registro', '')
                    try:
                        fecha_registro = datetime.strptime(fecha_registro_str, '%d/%m/%Y')
                        
                        valido = True
                        if fecha_inicio and fecha_registro < fecha_inicio:
                            valido = False
                        if fecha_fin and fecha_registro > fecha_fin:
                            valido = False
                        
                        if valido:
                            resultados_filtrados.append(persona)
                    except:
                        pass
                
                resultados = resultados_filtrados
            
            return resultados
            
        except Exception as e:
            registrar_error('buscador', 'buscar_personas', str(e))
            return []
    
    def buscar_pagos(self, pagos, criterios):
        """
        Busca pagos con criterios avanzados
        
        Args:
            pagos (list): Lista de pagos
            criterios (dict): Diccionario con filtros:
                - monto_minimo: float
                - monto_maximo: float
                - fecha_inicio: 'DD/MM/YYYY'
                - fecha_fin: 'DD/MM/YYYY'
                - nombre_persona: str (busqueda parcial)
                
        Returns:
            list: Pagos que coinciden
        """
        try:
            resultados = pagos.copy()
            
            # Filtro por monto minimo
            if 'monto_minimo' in criterios and criterios['monto_minimo'] is not None:
                monto_min = float(criterios['monto_minimo'])
                resultados = [
                    p for p in resultados
                    if float(p.get('monto', 0)) >= monto_min
                ]
            
            # Filtro por monto maximo
            if 'monto_maximo' in criterios and criterios['monto_maximo'] is not None:
                monto_max = float(criterios['monto_maximo'])
                resultados = [
                    p for p in resultados
                    if float(p.get('monto', 0)) <= monto_max
                ]
            
            # Filtro por fecha
            if 'fecha_inicio' in criterios or 'fecha_fin' in criterios:
                fecha_inicio = None
                fecha_fin = None
                
                if 'fecha_inicio' in criterios:
                    fecha_inicio = datetime.strptime(criterios['fecha_inicio'], '%d/%m/%Y')
                
                if 'fecha_fin' in criterios:
                    fecha_fin = datetime.strptime(criterios['fecha_fin'], '%d/%m/%Y')
                
                resultados_filtrados = []
                for pago in resultados:
                    fecha_pago_str = pago.get('fecha', '')
                    try:
                        fecha_pago = datetime.strptime(fecha_pago_str, '%d/%m/%Y')
                        
                        valido = True
                        if fecha_inicio and fecha_pago < fecha_inicio:
                            valido = False
                        if fecha_fin and fecha_pago > fecha_fin:
                            valido = False
                        
                        if valido:
                            resultados_filtrados.append(pago)
                    except:
                        pass
                
                resultados = resultados_filtrados
            
            return resultados
            
        except Exception as e:
            registrar_error('buscador', 'buscar_pagos', str(e))
            return []
    
    def obtener_estadisticas_pagos(self, pagos):
        """
        Obtiene estadisticas de un conjunto de pagos
        
        Args:
            pagos (list): Lista de pagos
            
        Returns:
            dict: Estadisticas
        """
        if not pagos:
            return {
                'total_pagos': 0,
                'monto_total': 0,
                'monto_promedio': 0,
                'monto_minimo': 0,
                'monto_maximo': 0
            }
        
        montos = [float(p.get('monto', 0)) for p in pagos]
        
        return {
            'total_pagos': len(pagos),
            'monto_total': sum(montos),
            'monto_promedio': sum(montos) / len(montos) if montos else 0,
            'monto_minimo': min(montos) if montos else 0,
            'monto_maximo': max(montos) if montos else 0
        }
    
    def obtener_estadisticas_personas(self, personas):
        """
        Obtiene estadisticas de un conjunto de personas
        
        Args:
            personas (list): Lista de personas
            
        Returns:
            dict: Estadisticas
        """
        if not personas:
            return {
                'total_personas': 0,
                'pagadas': 0,
                'pendientes': 0,
                'parciales': 0,
                'porcentaje_pagadas': 0
            }
        
        pagadas = 0
        pendientes = 0
        parciales = 0
        
        for persona in personas:
            monto_esperado = persona.get('monto_esperado', 0)
            pagos = persona.get('pagos', [])
            total_pagado = sum(p.get('monto', 0) for p in pagos)
            pendiente = max(0, monto_esperado - total_pagado)
            
            if pendiente == 0:
                pagadas += 1
            elif total_pagado == 0:
                pendientes += 1
            else:
                parciales += 1
        
        return {
            'total_personas': len(personas),
            'pagadas': pagadas,
            'pendientes': pendientes,
            'parciales': parciales,
            'porcentaje_pagadas': (pagadas / len(personas) * 100) if personas else 0
        }

# Instancia global
buscador = BuscadorAvanzado()
