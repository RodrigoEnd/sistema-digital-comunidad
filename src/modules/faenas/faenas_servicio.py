"""Servicio de lógica de negocio para faenas."""
from datetime import datetime
from typing import Any, Dict, List, Optional
import requests


class FaenasServicio:
    """Reglas de negocio para faenas sin dependencias de UI."""

    def __init__(self, api_url: str):
        self.api_url = api_url

    def calcular_resumen_anual(self, faenas: List[Dict[str, Any]], anio: int) -> Dict[str, Any]:
        """Calcula puntos por persona para un año específico.
        
        Returns:
            Dict con 'puntos' (dict folio->data), 'max_puntos', 'anio'
        """
        puntos = {}
        
        for faena in faenas:
            if self._anio_de_faena(faena) != anio:
                continue
            
            peso = faena.get('peso', 0)
            for p in faena.get('participantes', []):
                clave = p.get('folio') or p.get('nombre')
                if clave not in puntos:
                    puntos[clave] = {
                        'folio': p.get('folio', ''),
                        'nombre': p.get('nombre', ''),
                        'puntos': 0
                    }
                
                # Aplicar peso_aplicado (0.9 para quien contrató, 1.0 para resto)
                multiplicador = p.get('peso_aplicado', 1.0)
                puntos[clave]['puntos'] += peso * multiplicador
        
        max_puntos = max((v['puntos'] for v in puntos.values()), default=1)
        
        return {
            'puntos': puntos,
            'max_puntos': max_puntos,
            'anio': anio,
            'total_personas': len(puntos)
        }

    def obtener_años_disponibles(self, faenas: List[Dict[str, Any]]) -> List[int]:
        """Extrae lista de años con faenas registradas."""
        años = {datetime.now().year}
        for f in faenas:
            años.add(self._anio_de_faena(f))
        return sorted(años, reverse=True)

    def sincronizar_participantes_con_censo(
        self, 
        faenas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Sincroniza folios de participantes con datos del censo.
        
        Returns:
            Dict con 'actualizados', 'total_participantes', 'habitantes_cache'
        """
        try:
            resp = requests.get(f"{self.api_url}/habitantes", timeout=5)
            if resp.status_code != 200:
                return {'ok': False, 'error': 'No se pudo obtener habitantes'}
            
            data = resp.json()
            habitantes = data.get('habitantes', [])
            
            # Crear mapeo nombre -> habitante
            nombre_a_hab = {
                h.get('nombre', '').strip().lower(): h 
                for h in habitantes if h.get('nombre')
            }
            
            actualizados = 0
            total_participantes = 0
            
            for faena in faenas:
                for participante in faena.get('participantes', []):
                    total_participantes += 1
                    nombre = participante.get('nombre', '').strip().lower()
                    folio_actual = participante.get('folio', '')
                    
                    if nombre in nombre_a_hab:
                        folio_censo = nombre_a_hab[nombre].get('folio', '')
                        if folio_actual != folio_censo and folio_censo:
                            participante['folio'] = folio_censo
                            actualizados += 1
            
            return {
                'ok': True,
                'actualizados': actualizados,
                'total_participantes': total_participantes,
                'habitantes_cache': habitantes
            }
        except Exception as exc:  # noqa: BLE001
            return {'ok': False, 'error': str(exc)}

    def filtrar_resumen_por_criterio(
        self, 
        puntos: Dict[str, Dict[str, Any]], 
        criterio: str
    ) -> Dict[str, Dict[str, Any]]:
        """Filtra resumen por nombre o folio."""
        if not criterio:
            return puntos
        
        criterio_lower = criterio.lower().strip()
        return {
            k: v for k, v in puntos.items()
            if criterio_lower in v.get('folio', '').lower()
            or criterio_lower in v.get('nombre', '').lower()
        }

    def calcular_color_por_puntaje(self, puntos: float, max_puntos: float) -> str:
        """Calcula color degradado de rojo a verde según ratio de puntos.
        Usa colores suaves y agradables a la vista.
        
        Returns:
            Color hex (ej: '#ef4444', '#22c55e')
        """
        if max_puntos == 0:
            return '#6b7280'  # gris neutro
        
        ratio = min(puntos / max_puntos, 1.0)
        
        # Colores suaves: rojo -> amarillo -> verde
        if ratio < 0.5:
            # Rojo suave a amarillo suave
            # Rojo: #ef4444 (239, 68, 68)
            # Amarillo: #fbbf24 (251, 191, 36)
            t = ratio * 2  # 0 a 1
            r = int(239 + (251 - 239) * t)
            g = int(68 + (191 - 68) * t)
            b = int(68 + (36 - 68) * t)
        else:
            # Amarillo suave a verde suave
            # Amarillo: #fbbf24 (251, 191, 36)
            # Verde: #22c55e (34, 197, 94)
            t = (ratio - 0.5) * 2  # 0 a 1
            r = int(251 + (34 - 251) * t)
            g = int(191 + (197 - 191) * t)
            b = int(36 + (94 - 36) * t)
        
        return f'#{r:02x}{g:02x}{b:02x}'

    def validar_puede_editar_faena(self, faena: Dict[str, Any], dias_limite: int = 7) -> Dict[str, Any]:
        """Valida si una faena puede editarse según días transcurridos.
        
        Returns:
            Dict con 'puede_editar' (bool), 'dias_transcurridos', 'mensaje'
        """
        if not faena:
            return {'puede_editar': False, 'mensaje': 'No hay faena seleccionada'}
        
        fecha_str = faena.get('fecha', '')
        if not fecha_str:
            return {'puede_editar': True, 'mensaje': 'Sin fecha, permitir edición'}
        
        try:
            fecha_faena = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            hoy = datetime.now().date()
            dias = (hoy - fecha_faena).days
            
            puede = dias <= dias_limite
            mensaje = (
                f"Puede editar (hace {dias} días)"
                if puede
                else f"No puede editar (hace {dias} días, límite {dias_limite})"
            )
            
            return {
                'puede_editar': puede,
                'dias_transcurridos': dias,
                'mensaje': mensaje
            }
        except ValueError:
            return {'puede_editar': True, 'mensaje': 'Fecha inválida, permitir edición'}

    @staticmethod
    def _anio_de_faena(faena: Dict[str, Any]) -> int:
        """Extrae año de una faena."""
        try:
            return datetime.strptime(faena.get('fecha', ''), "%Y-%m-%d").year
        except (ValueError, TypeError):
            return datetime.now().year
