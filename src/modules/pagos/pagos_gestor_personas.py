"""
Módulo de gestión de personas y pagos
Responsable de: CRUD de personas, registro de pagos, cálculos de estados
"""

import tkinter as tk
from datetime import datetime
from src.core.logger import registrar_operacion, registrar_transaccion, registrar_error
from src.core.validadores import validar_nombre, validar_monto
from src.modules.pagos.pagos_constantes import PATRONES


class GestorPersonas:
    """Gestor centralizado de personas y pagos"""
    
    def __init__(self):
        self.personas = []
    
    def cargar_personas(self, personas):
        """Cargar personas de una cooperación"""
        self.personas = personas if personas else []
    
    def obtener_persona_por_folio(self, folio):
        """Obtener una persona por folio"""
        return next((p for p in self.personas if p.get('folio') == folio), None)
    
    def crear_persona(self, nombre, folio=None, monto=100.0, notas=''):
        """Crear una nueva persona"""
        validar_nombre(nombre)
        validar_monto(monto)
        
        # Generar folio si no se proporciona
        if not folio:
            folio = self._generar_folio()
        
        # Verificar que no exista
        if self.obtener_persona_por_folio(folio):
            raise ValueError(f"Ya existe una persona con folio {folio}")
        
        persona = {
            'nombre': nombre.strip(),
            'folio': folio,
            'monto': monto,
            'monto_esperado': monto,
            'pagos': [],
            'notas': notas,
            'fecha_creacion': datetime.now().strftime(PATRONES['datetime_formato']),
            'activo': True
        }
        
        self.personas.append(persona)
        
        registrar_operacion(
            'CREAR_PERSONA',
            f'Persona creada: {nombre}',
            {'folio': folio, 'monto': monto}
        )
        
        return persona
    
    def editar_persona(self, folio, nombre=None, notas=None, monto_esperado=None):
        """Editar datos de una persona"""
        persona = self.obtener_persona_por_folio(folio)
        if not persona:
            raise ValueError(f"Persona con folio {folio} no encontrada")
        
        cambios = {}
        
        if nombre is not None:
            validar_nombre(nombre)
            cambios['nombre_anterior'] = persona['nombre']
            persona['nombre'] = nombre.strip()
            cambios['nombre_nuevo'] = nombre.strip()
        
        if notas is not None:
            cambios['notas_anterior'] = persona.get('notas')
            persona['notas'] = notas.strip()
            cambios['notas_nuevas'] = notas.strip()
        
        if monto_esperado is not None:
            validar_monto(monto_esperado)
            cambios['monto_anterior'] = persona.get('monto_esperado')
            persona['monto_esperado'] = monto_esperado
            cambios['monto_nuevo'] = monto_esperado
        
        persona['fecha_modificacion'] = datetime.now().strftime(PATRONES['datetime_formato'])
        
        if cambios:
            registrar_operacion(
                'EDITAR_PERSONA',
                f'Persona editada: {persona["nombre"]}',
                {**cambios, 'folio': folio}
            )
    
    def eliminar_persona(self, folio):
        """Eliminar una persona"""
        persona = self.obtener_persona_por_folio(folio)
        if not persona:
            raise ValueError(f"Persona con folio {folio} no encontrada")
        
        self.personas = [p for p in self.personas if p.get('folio') != folio]
        
        registrar_operacion(
            'ELIMINAR_PERSONA',
            f'Persona eliminada: {persona["nombre"]}',
            {'folio': folio}
        )
    
    def registrar_pago(self, folio, monto, notas=''):
        """Registrar un pago para una persona"""
        persona = self.obtener_persona_por_folio(folio)
        if not persona:
            raise ValueError(f"Persona con folio {folio} no encontrada")
        
        validar_monto(monto)
        
        pago = {
            'monto': monto,
            'fecha': datetime.now().strftime(PATRONES['datetime_formato']),
            'notas': notas.strip() if notas else ''
        }
        
        persona['pagos'].append(pago)
        persona['fecha_ultimo_pago'] = datetime.now().strftime(PATRONES['datetime_formato'])
        
        registrar_transaccion(
            'PAGO',
            f'Pago registrado para {persona["nombre"]}',
            {'folio': folio, 'monto': monto, 'notas': notas}
        )
        
        return pago
    
    def obtener_estado_persona(self, folio):
        """
        Obtener estado detallado de una persona
        
        Returns:
            dict con: pagado, pendiente, porcentaje, estado_texto
        """
        persona = self.obtener_persona_por_folio(folio)
        if not persona:
            return None
        
        monto_esperado = persona.get('monto_esperado', persona.get('monto', 100))
        total_pagado = sum(pago['monto'] for pago in persona.get('pagos', []))
        pendiente = monto_esperado - total_pagado
        porcentaje = (total_pagado / monto_esperado * 100) if monto_esperado > 0 else 0
        
        # Determinar estado - LÓGICA CORREGIDA
        if total_pagado >= monto_esperado:
            estado = 'completado' if total_pagado == monto_esperado else 'excedente'
        elif total_pagado > 0:
            estado = 'parcial'
        else:
            estado = 'sin_pagar'
        
        return {
            'folio': folio,
            'nombre': persona['nombre'],
            'esperado': monto_esperado,
            'pagado': total_pagado,
            'pendiente': pendiente,
            'porcentaje': porcentaje,
            'estado': estado,
            'num_pagos': len(persona.get('pagos', [])),
            'ultimo_pago': persona.get('fecha_ultimo_pago'),
            'activo': persona.get('activo', True)
        }
    
    def obtener_resumen_grupo(self):
        """Obtener resumen de todo el grupo"""
        total_esperado = 0
        total_pagado = 0
        total_pendiente = 0
        personas_pagadas = 0
        personas_parciales = 0
        personas_sin_pagar = 0
        
        for persona in self.personas:
            if not persona.get('activo', True):
                continue
            
            monto_esperado = persona.get('monto_esperado', persona.get('monto', 100))
            pagado = sum(pago['monto'] for pago in persona.get('pagos', []))
            pendiente = max(0, monto_esperado - pagado)
            
            total_esperado += monto_esperado
            total_pagado += pagado
            total_pendiente += pendiente
            
            if pagado >= monto_esperado:
                personas_pagadas += 1
            elif pagado > 0:
                personas_parciales += 1
            else:
                personas_sin_pagar += 1
        
        porcentaje_general = (total_pagado / total_esperado * 100) if total_esperado > 0 else 0
        
        return {
            'total_esperado': total_esperado,
            'total_pagado': total_pagado,
            'total_pendiente': total_pendiente,
            'porcentaje_general': porcentaje_general,
            'personas_pagadas': personas_pagadas,
            'personas_parciales': personas_parciales,
            'personas_sin_pagar': personas_sin_pagar,
            'total_personas': len([p for p in self.personas if p.get('activo', True)])
        }
    
    def buscar_personas(self, criterio, valor):
        """
        Buscar personas por criterio
        
        Args:
            criterio: 'nombre', 'folio', 'estado'
            valor: valor a buscar
        
        Returns:
            Lista de personas que coinciden
        """
        resultados = []
        valor_lower = str(valor).lower()
        
        for persona in self.personas:
            if criterio == 'nombre':
                if valor_lower in persona['nombre'].lower():
                    resultados.append(persona)
            elif criterio == 'folio':
                if valor_lower in persona.get('folio', '').lower():
                    resultados.append(persona)
            elif criterio == 'estado':
                estado = self.obtener_estado_persona(persona['folio'])
                if estado and estado['estado'] == valor_lower:
                    resultados.append(persona)
        
        return resultados
    
    def validar_nombre_unico(self, nombre, folio_excluir=None):
        """
        Validar que un nombre no esté duplicado
        
        Args:
            nombre: Nombre a validar
            folio_excluir: Folio a excluir de la validación (para ediciones)
        
        Returns:
            True si el nombre es único, False si está duplicado
        """
        nombre_normalizado = nombre.strip().lower()
        
        for persona in self.personas:
            # Excluir la persona que se está editando
            if folio_excluir and persona.get('folio') == folio_excluir:
                continue
            
            # Comparar nombres (case insensitive)
            if persona['nombre'].strip().lower() == nombre_normalizado:
                return False
        
        return True
    
    def obtener_nombres_similares(self, nombre, max_resultados=5):
        """Buscar nombres similares para evitar duplicados"""
        nombre_lower = nombre.lower()
        palabras_busqueda = nombre_lower.split()
        similares = []
        
        for persona in self.personas:
            nombre_pers = persona['nombre'].lower()
            # Verificar coincidencias
            coincidencias = sum(1 for palabra in palabras_busqueda if palabra in nombre_pers)
            if coincidencias > 0:
                similares.append((persona, coincidencias))
        
        # Ordenar por coincidencias (descendente) y límitar
        similares.sort(key=lambda x: x[1], reverse=True)
        return [p[0] for p in similares[:max_resultados]]
    
    def activar_persona(self, folio, activo=True):
        """Activar o desactivar una persona"""
        persona = self.obtener_persona_por_folio(folio)
        if not persona:
            raise ValueError(f"Persona con folio {folio} no encontrada")
        
        persona['activo'] = activo
        registrar_operacion(
            'CAMBIAR_ESTADO_PERSONA',
            f'Estado de {persona["nombre"]}: {"Activo" if activo else "Inactivo"}',
            {'folio': folio, 'activo': activo}
        )
    
    def exportar_para_guardado(self):
        """Exportar personas en formato para guardado"""
        return self.personas
    
    def _generar_folio(self):
        """Generar un folio único"""
        # Usar contador basado en folios locales existentes
        folios_locales = [
            p.get('folio') for p in self.personas 
            if p.get('folio', '').startswith(PATRONES['folio_local_prefix'])
        ]
        
        contador = 1
        while f"{PATRONES['folio_local_prefix']}-{contador}" in folios_locales:
            contador += 1
        
        return f"{PATRONES['folio_local_prefix']}-{contador}"
