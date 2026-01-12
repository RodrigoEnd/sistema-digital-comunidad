"""Repositorio de persistencia para faenas."""
from datetime import datetime
from typing import Any, Dict, List

from src.auth.seguridad import seguridad
from src.core.logger import registrar_error, registrar_operacion


class FaenasRepositorio:
    """Encapsula operaciones de persistencia para faenas."""

    def __init__(self, archivo_datos: str, password_archivo: str):
        self.archivo_datos = archivo_datos
        self.password_archivo = password_archivo

    def cargar(self) -> Dict[str, Any]:
        """Carga faenas desde archivo cifrado."""
        try:
            if seguridad.archivo_existe(self.archivo_datos):
                datos = seguridad.descifrar_archivo(self.archivo_datos, self.password_archivo)
                if datos:
                    return {'ok': True, 'faenas': datos.get('faenas', [])}
            return {'ok': True, 'faenas': []}
        except Exception as exc:  # noqa: BLE001
            registrar_error('faenas', 'cargar_datos', str(exc))
            return {'ok': False, 'error': str(exc), 'faenas': []}

    def guardar(self, faenas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Guarda faenas en archivo cifrado."""
        try:
            datos = {
                'faenas': faenas,
                'fecha_guardado': datetime.now().isoformat()
            }
            ok = seguridad.cifrar_archivo(datos, self.archivo_datos, self.password_archivo)
            if ok:
                registrar_operacion(
                    'GUARDAR_FAENAS',
                    'Faenas guardadas correctamente',
                    {'total_faenas': len(faenas)}
                )
            return {'ok': bool(ok)}
        except Exception as exc:  # noqa: BLE001
            registrar_error('faenas', 'guardar_datos', str(exc))
            return {'ok': False, 'error': str(exc)}
