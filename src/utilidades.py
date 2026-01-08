"""
Utilidades del sistema
Funciones auxiliares para mantenimiento y correccion de datos
"""

import requests
from logger import registrar_operacion, registrar_error

def detectar_folios_duplicados(personas):
    """
    Detecta folios duplicados en una lista de personas
    
    Args:
        personas (list): Lista de personas
        
    Returns:
        dict: Diccionario con folios duplicados y las personas que los usan
    """
    folios_dict = {}
    duplicados = {}
    
    for persona in personas:
        folio = persona.get('folio', 'SIN-FOLIO')
        nombre = persona.get('nombre', 'Sin nombre')
        
        if folio in folios_dict:
            # Es un duplicado
            if folio not in duplicados:
                duplicados[folio] = [folios_dict[folio]]
            duplicados[folio].append(nombre)
        else:
            folios_dict[folio] = nombre
    
    return duplicados

def corregir_folios_duplicados(personas, api_url):
    """
    Corrige folios duplicados sincronizando con el censo
    
    Args:
        personas (list): Lista de personas
        api_url (str): URL de la API
        
    Returns:
        dict: Resultado de la correccion
    """
    try:
        duplicados = detectar_folios_duplicados(personas)
        
        if not duplicados:
            return {'exito': True, 'mensaje': 'No se encontraron folios duplicados', 'corregidos': 0}
        
        corregidos = 0
        errores = []
        
        for folio, nombres in duplicados.items():
            print(f"Folio duplicado detectado: {folio} usado por {len(nombres)} personas")
            
            # Para cada nombre, obtener el folio correcto del censo
            for nombre in nombres:
                # Buscar la persona en la lista
                persona = next((p for p in personas if p.get('nombre') == nombre and p.get('folio') == folio), None)
                
                if persona:
                    # Obtener folio correcto del censo
                    try:
                        response = requests.get(f"{api_url}/habitantes/nombre/{nombre}", timeout=5)
                        if response.status_code == 200:
                            data = response.json()
                            if data['success'] and data['habitante']:
                                folio_correcto = data['habitante']['folio']
                                
                                # Actualizar solo si es diferente
                                if folio_correcto != folio:
                                    persona['folio'] = folio_correcto
                                    corregidos += 1
                                    print(f"  -> {nombre}: {folio} -> {folio_correcto}")
                                    registrar_operacion('CORRECCION_FOLIO', f'{nombre}', 
                                                      {'folio_anterior': folio, 'folio_nuevo': folio_correcto})
                    except Exception as e:
                        error_msg = f"Error corrigiendo {nombre}: {str(e)}"
                        errores.append(error_msg)
                        print(f"  -> {error_msg}")
        
        mensaje = f"Se corrigieron {corregidos} folios duplicados"
        if errores:
            mensaje += f". {len(errores)} errores encontrados"
        
        return {
            'exito': True,
            'mensaje': mensaje,
            'corregidos': corregidos,
            'errores': errores,
            'duplicados_encontrados': len(duplicados)
        }
        
    except Exception as e:
        registrar_error('utilidades', 'corregir_folios_duplicados', str(e))
        return {'exito': False, 'error': str(e)}

def sincronizar_todas_personas_con_censo(personas, api_url):
    """
    Sincroniza todas las personas con el censo para obtener folios correctos
    
    Args:
        personas (list): Lista de personas
        api_url (str): URL de la API
        
    Returns:
        dict: Resultado de la sincronizacion
    """
    try:
        sincronizados = 0
        errores = []
        
        for persona in personas:
            nombre = persona.get('nombre', '')
            folio_actual = persona.get('folio', 'SIN-FOLIO')
            
            try:
                # Buscar en el censo
                response = requests.get(f"{api_url}/habitantes/nombre/{nombre}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data['success'] and data['habitante']:
                        folio_censo = data['habitante']['folio']
                        
                        if folio_censo != folio_actual:
                            persona['folio'] = folio_censo
                            sincronizados += 1
                            print(f"{nombre}: {folio_actual} -> {folio_censo}")
                            registrar_operacion('SINCRONIZACION_FOLIO', f'{nombre}',
                                              {'folio_anterior': folio_actual, 'folio_censo': folio_censo})
            except Exception as e:
                error_msg = f"Error sincronizando {nombre}: {str(e)}"
                errores.append(error_msg)
        
        return {
            'exito': True,
            'mensaje': f'Se sincronizaron {sincronizados} personas',
            'sincronizados': sincronizados,
            'errores': errores
        }
        
    except Exception as e:
        registrar_error('utilidades', 'sincronizar_todas_personas_con_censo', str(e))
        return {'exito': False, 'error': str(e)}

def validar_integridad_datos(cooperaciones):
    """
    Valida la integridad de los datos de cooperaciones
    
    Args:
        cooperaciones (list): Lista de cooperaciones
        
    Returns:
        dict: Resultado de la validacion con problemas encontrados
    """
    problemas = []
    
    for idx, coop in enumerate(cooperaciones):
        # Validar campos obligatorios
        if 'id' not in coop:
            problemas.append(f"Cooperacion {idx}: Falta campo 'id'")
        if 'nombre' not in coop:
            problemas.append(f"Cooperacion {idx}: Falta campo 'nombre'")
        if 'personas' not in coop:
            problemas.append(f"Cooperacion {idx}: Falta campo 'personas'")
            continue
        
        personas = coop.get('personas', [])
        
        # Detectar folios duplicados en esta cooperacion
        duplicados = detectar_folios_duplicados(personas)
        if duplicados:
            for folio, nombres in duplicados.items():
                problemas.append(f"Cooperacion '{coop.get('nombre')}': Folio {folio} duplicado en {nombres}")
        
        # Validar datos de personas
        for p_idx, persona in enumerate(personas):
            if 'nombre' not in persona or not persona['nombre']:
                problemas.append(f"Cooperacion '{coop.get('nombre')}': Persona {p_idx} sin nombre")
            
            if 'folio' not in persona or persona['folio'] == 'SIN-FOLIO':
                problemas.append(f"Cooperacion '{coop.get('nombre')}': {persona.get('nombre', 'Sin nombre')} sin folio")
            
            if 'monto_esperado' not in persona:
                problemas.append(f"Cooperacion '{coop.get('nombre')}': {persona.get('nombre', 'Sin nombre')} sin monto_esperado")
    
    return {
        'valido': len(problemas) == 0,
        'problemas': problemas,
        'total_problemas': len(problemas)
    }
