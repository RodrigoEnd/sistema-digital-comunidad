"""
Módulo de gestión segura de eliminación de personas
Responsable de: Hacer backup de personas antes de eliminarlas para auditoría

BUG FIX #5: Previene pérdida permanente de datos al eliminar
"""

import json
import os
from datetime import datetime
from src.core.logger import registrar_operacion, registrar_error


class GestorEliminacionSegura:
    """
    Gestor seguro de eliminación de personas
    Mantiene un archivo de auditoría de personas eliminadas
    """
    
    # Archivo para almacenar registro de eliminaciones
    ARCHIVO_HISTORIAL_ELIMINACIONES = 'datos/historial_eliminaciones.json'
    
    @staticmethod
    def asegurar_directorio():
        """Asegurar que existe el directorio de datos"""
        directorio = os.path.dirname(GestorEliminacionSegura.ARCHIVO_HISTORIAL_ELIMINACIONES)
        if directorio and not os.path.exists(directorio):
            try:
                os.makedirs(directorio, exist_ok=True)
            except Exception as e:
                registrar_error('GestorEliminacionSegura', 'asegurar_directorio', str(e))
    
    @staticmethod
    def cargar_historial_eliminaciones():
        """
        Cargar historial de personas eliminadas
        
        Returns:
            list - Lista de personas eliminadas
        """
        GestorEliminacionSegura.asegurar_directorio()
        
        if not os.path.exists(GestorEliminacionSegura.ARCHIVO_HISTORIAL_ELIMINACIONES):
            return []
        
        try:
            with open(GestorEliminacionSegura.ARCHIVO_HISTORIAL_ELIMINACIONES, 'r', encoding='utf-8') as f:
                datos = json.load(f)
                return datos.get('eliminaciones', [])
        except Exception as e:
            registrar_error('GestorEliminacionSegura', 'cargar_historial_eliminaciones', str(e))
            return []
    
    @staticmethod
    def guardar_historial_eliminaciones(eliminaciones):
        """
        Guardar historial de personas eliminadas
        
        Args:
            eliminaciones: list - Lista de personas eliminadas
        """
        GestorEliminacionSegura.asegurar_directorio()
        
        try:
            datos = {
                'version': '1.0',
                'fecha_actualización': datetime.now().isoformat(),
                'total_eliminaciones': len(eliminaciones),
                'eliminaciones': eliminaciones
            }
            
            with open(GestorEliminacionSegura.ARCHIVO_HISTORIAL_ELIMINACIONES, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)
                
            registrar_operacion(
                'GUARDAR_HISTORIAL_ELIMINACIONES',
                f'Historial de {len(eliminaciones)} eliminaciones guardado',
                {}
            )
        except Exception as e:
            registrar_error('GestorEliminacionSegura', 'guardar_historial_eliminaciones', str(e))
    
    @staticmethod
    def hacer_backup_persona(persona, motivo='Eliminación de usuario', usuario='Sistema'):
        """
        Hacer backup de una persona antes de eliminarla
        
        Args:
            persona: dict - Datos de la persona a hacer backup
            motivo: str - Razón de la eliminación
            usuario: str - Usuario que realiza la eliminación
        
        Returns:
            dict - Registro de backup creado
        """
        backup = {
            'fecha_eliminación': datetime.now().isoformat(),
            'usuario_que_eliminó': usuario,
            'motivo': motivo,
            'datos_persona': persona.copy(),  # Copia completa
            'información_audit': {
                'folio': persona.get('folio', 'SIN-FOLIO'),
                'nombre': persona.get('nombre', 'SIN-NOMBRE'),
                'total_pagado': sum(p.get('monto', 0) for p in persona.get('pagos', [])),
                'total_esperado': persona.get('monto_esperado', 0),
                'número_pagos': len(persona.get('pagos', [])),
                'cooperación': persona.get('cooperación', 'Desconocida')
            }
        }
        
        # Cargar historial existente
        historial = GestorEliminacionSegura.cargar_historial_eliminaciones()
        
        # Agregar nuevo backup
        historial.append(backup)
        
        # Guardar actualizado
        GestorEliminacionSegura.guardar_historial_eliminaciones(historial)
        
        # Registrar en log
        registrar_operacion(
            'BACKUP_ELIMINACION',
            f'Backup realizado para persona: {persona.get("nombre", "SIN-NOMBRE")}',
            {
                'folio': persona.get('folio', 'SIN-FOLIO'),
                'motivo': motivo,
                'usuario': usuario
            }
        )
        
        return backup
    
    @staticmethod
    def recuperar_persona_eliminada(folio):
        """
        Recuperar datos de una persona que fue eliminada
        
        Args:
            folio: str - Folio de la persona a recuperar
        
        Returns:
            dict - Datos de la persona o None si no existe
        """
        historial = GestorEliminacionSegura.cargar_historial_eliminaciones()
        
        for registro in historial:
            if registro['datos_persona'].get('folio') == folio:
                return registro
        
        return None
    
    @staticmethod
    def obtener_resumen_eliminaciones(filtro_usuario=None):
        """
        Obtener resumen de eliminaciones
        
        Args:
            filtro_usuario: str - Filtrar por usuario específico (opcional)
        
        Returns:
            dict - Resumen estadístico
        """
        historial = GestorEliminacionSegura.cargar_historial_eliminaciones()
        
        if filtro_usuario:
            historial = [e for e in historial if e['usuario_que_eliminó'] == filtro_usuario]
        
        total_pagado = sum(e['información_audit']['total_pagado'] for e in historial)
        total_personas = len(historial)
        
        return {
            'total_personas_eliminadas': total_personas,
            'total_dinero_en_eliminadas': total_pagado,
            'promedio_pagado_persona': total_pagado / total_personas if total_personas > 0 else 0,
            'eliminaciones_por_usuario': _contar_eliminaciones_por_usuario(historial),
            'historial': historial
        }
    
    @staticmethod
    def restaurar_persona(folio, personas_lista, usuario='Sistema'):
        """
        Restaurar una persona eliminada (si aún no existe)
        
        Args:
            folio: str - Folio de la persona a restaurar
            personas_lista: list - Lista de personas actual
            usuario: str - Usuario que restaura
        
        Returns:
            tuple (bool, str, dict) - (éxito, mensaje, persona_restaurada)
        """
        # Verificar que no exista ya
        if any(p.get('folio') == folio for p in personas_lista):
            return False, "La persona ya existe en la lista actual", None
        
        # Buscar en eliminadas
        registro = GestorEliminacionSegura.recuperar_persona_eliminada(folio)
        
        if not registro:
            return False, f"No se encontró backup de persona con folio {folio}", None
        
        # Restaurar
        persona_restaurada = registro['datos_persona'].copy()
        personas_lista.append(persona_restaurada)
        
        registrar_operación = None
        try:
            from src.core.logger import registrar_operacion as reg_op
            reg_op(
                'RESTAURAR_PERSONA',
                f'Persona restaurada: {persona_restaurada.get("nombre")}',
                {
                    'folio': folio,
                    'usuario_que_restauró': usuario,
                    'fecha_original_eliminación': registro['fecha_eliminación']
                }
            )
        except:
            pass
        
        return True, f"Persona {persona_restaurada.get('nombre')} restaurada exitosamente", persona_restaurada


def _contar_eliminaciones_por_usuario(historial):
    """Contar eliminaciones por usuario"""
    conteo = {}
    for e in historial:
        usuario = e.get('usuario_que_eliminó', 'Desconocido')
        conteo[usuario] = conteo.get(usuario, 0) + 1
    return conteo
