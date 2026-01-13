"""
Módulo de gestión de API y sincronización con censo
Responsable de: conectar API, sincronizar folios, watchdog
"""

import requests
import subprocess
import threading
import time
from src.config import MODO_OFFLINE, API_URL
from src.core.logger import registrar_operacion, registrar_error
from src.modules.pagos.pagos_constantes import TIMERS, PATRONES


class GestorAPI:
    """Gestor de conexión con API local y censo"""
    
    def __init__(self, api_url=API_URL):
        self.api_url = api_url
        self.api_activa = False
        self.api_caida_notificada = False
        self.watchdog_thread = None
    
    def verificar_api(self):
        """Verificar si la API está activa"""
        if MODO_OFFLINE:
            return True
        
        try:
            respuesta = requests.get(f"{self.api_url}/health", timeout=2)
            self.api_activa = respuesta.status_code == 200
            
            if self.api_activa and self.api_caida_notificada:
                self.api_caida_notificada = False
                registrar_operacion('API', 'API_RECUPERADA', 'API local recuperada')
            
            return self.api_activa
        
        except Exception as e:
            self.api_activa = False
            return False
    
    def asegurar_api_activa(self):
        """Comprueba la API y la levanta si no está activa"""
        if MODO_OFFLINE:
            registrar_operacion('SISTEMA', 'MODO_OFFLINE', 'Sistema en modo offline')
            return True
        
        if self.verificar_api():
            return True
        
        # Intentar iniciar API local
        try:
            self._iniciar_api_local()
            time.sleep(2)  # Esperar a que se inicie
            
            if self.verificar_api():
                registrar_operacion('API', 'API_INICIADA', 'API local iniciada automáticamente')
                return True
            else:
                registrar_operacion('API', 'API_FALLBACK', 'API no disponible, usando modo offline')
                return True
        
        except Exception as e:
            registrar_error('pagos_gestor_api', 'asegurar_api_activa', f'Error inicializando API: {str(e)}')
            registrar_operacion('API', 'API_FALLBACK', 'Continuando en modo offline')
            return True
    
    def _iniciar_api_local(self):
        """Iniciar API local en background"""
        try:
            import sys
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))
            proyecto_raiz = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
            script_path = os.path.join(proyecto_raiz, "src", "api", "api_local.py")
            
            subprocess.Popen([
                sys.executable,
                script_path
            ], 
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        
        except Exception as e:
            registrar_error('pagos_gestor_api', '_iniciar_api_local', str(e))
    
    def iniciar_watchdog_api(self, callback_api_caida=None):
        """
        Hilo de monitoreo para reintentar API local
        
        Args:
            callback_api_caida: función a llamar si API cae
        """
        def monitor():
            while True:
                time.sleep(TIMERS['watchdog_api_intervalo'] / 1000)  # Convertir a segundos
                
                if not self.verificar_api():
                    if not self.api_caida_notificada and not MODO_OFFLINE:
                        self.api_caida_notificada = True
                        registrar_operacion(
                            'API',
                            'API_NO_DISPONIBLE',
                            'API local no disponible, modo offline'
                        )
                        if callback_api_caida:
                            callback_api_caida()
                
                else:
                    if self.api_caida_notificada:
                        self.api_caida_notificada = False
        
        self.watchdog_thread = threading.Thread(target=monitor, daemon=True)
        self.watchdog_thread.start()
    
    def obtener_persona_censo(self, nombre):
        """
        Obtener datos de una persona del censo
        
        Args:
            nombre: nombre de la persona a buscar
        
        Returns:
            dict con datos de la persona o None
        """
        if MODO_OFFLINE or not self.verificar_api():
            return None
        
        try:
            respuesta = requests.post(
                f"{self.api_url}/censo/buscar",
                json={'nombre': nombre},
                timeout=5
            )
            
            if respuesta.status_code == 200:
                datos = respuesta.json()
                return datos.get('persona')
        
        except Exception as e:
            registrar_error('pagos_gestor_api', 'obtener_persona_censo', str(e))
        
        return None
    
    def crear_persona_censo(self, nombre, datos_adicionales=None):
        """
        Crear una nueva persona en el censo
        
        Args:
            nombre: nombre de la persona
            datos_adicionales: dict con datos adicionales
        
        Returns:
            dict con datos de la persona creada o None
        """
        if MODO_OFFLINE or not self.verificar_api():
            return None
        
        try:
            payload = {'nombre': nombre}
            if datos_adicionales:
                payload.update(datos_adicionales)
            
            respuesta = requests.post(
                f"{self.api_url}/censo/crear",
                json=payload,
                timeout=5
            )
            
            if respuesta.status_code == 201:
                return respuesta.json().get('persona')
        
        except Exception as e:
            registrar_error('pagos_gestor_api', 'crear_persona_censo', str(e))
        
        return None
    
    def detectar_folios_duplicados(self, personas):
        """
        Detectar folios duplicados en la lista de personas
        
        Returns:
            dict con folios duplicados y sus nombres
        """
        duplicados = {}
        folios_vistos = {}
        
        for persona in personas:
            folio = persona.get('folio')
            if not folio:
                continue
            
            if folio in folios_vistos:
                if folio not in duplicados:
                    duplicados[folio] = [folios_vistos[folio]['nombre']]
                duplicados[folio].append(persona['nombre'])
            else:
                folios_vistos[folio] = persona
        
        return duplicados
    
    def sincronizar_folios_con_censo(self, personas):
        """
        Sincronizar folios de personas con el censo
        
        Args:
            personas: lista de personas a sincronizar
        
        Returns:
            dict con resultado de sincronización
        """
        if MODO_OFFLINE or not self.verificar_api():
            return {'exito': False, 'mensaje': 'API no disponible'}
        
        sincronizadas = 0
        errores = []
        
        try:
            for persona in personas:
                if not persona.get('folio') or persona.get('folio', '').startswith(PATRONES['folio_local_prefix']):
                    # Buscar en censo
                    datos_censo = self.obtener_persona_censo(persona['nombre'])
                    
                    if datos_censo and datos_censo.get('folio'):
                        persona['folio'] = datos_censo['folio']
                        sincronizadas += 1
            
            return {
                'exito': True,
                'sincronizadas': sincronizadas,
                'errores': errores
            }
        
        except Exception as e:
            registrar_error('pagos_gestor_api', 'sincronizar_folios_con_censo', str(e))
            return {
                'exito': False,
                'mensaje': str(e),
                'errores': [str(e)]
            }
    
    def generar_folio_local(self):
        """
        Genera un folio local único cuando no hay API
        
        Returns:
            str con folio local
        """
        base = PATRONES['folio_local_prefix']
        intento = 0
        
        while True:
            folio = f"{base}-{int(time.time())}-{intento}"
            intento += 1
            
            if intento > 100:
                break
        
        return folio
    
    def obtener_estado_api(self):
        """Obtener información del estado de la API"""
        if MODO_OFFLINE:
            return {
                'disponible': True,
                'modo': 'offline',
                'mensaje': 'Funcionando en modo offline'
            }
        
        if self.verificar_api():
            return {
                'disponible': True,
                'modo': 'online',
                'url': self.api_url,
                'mensaje': 'API conectada'
            }
        else:
            return {
                'disponible': False,
                'modo': 'desconectado',
                'url': self.api_url,
                'mensaje': 'API no disponible'
            }
