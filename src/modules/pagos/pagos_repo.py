from datetime import datetime
from typing import Any, Dict, Optional

from src.auth.seguridad import seguridad
from src.core.logger import registrar_error, registrar_operacion
from src.tools.backups import GestorBackups
from src.tools.exportador import ExportadorExcel


class PagosRepositorio:
    """Encapsula operaciones de persistencia y exportación para pagos."""

    def __init__(self, archivo_datos: str, password_archivo: str):
        self.archivo_datos = archivo_datos
        self.password_archivo = password_archivo
        self.exportador = ExportadorExcel()
        self.gestor_backups = GestorBackups()

    # Persistencia cifrada
    def guardar(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        try:
            ok = seguridad.cifrar_archivo(datos, self.archivo_datos, self.password_archivo)
            return {"ok": bool(ok)}
        except Exception as exc:  # noqa: BLE001
            registrar_error("GUARDAR_PAGOS", str(exc))
            return {"ok": False, "error": str(exc)}

    def cargar(self) -> Dict[str, Any]:
        try:
            if seguridad.archivo_existe(self.archivo_datos):
                datos = seguridad.descifrar_archivo(self.archivo_datos, self.password_archivo)
                return {"ok": True, "datos": datos or {}}
            return {"ok": True, "datos": {}}
        except Exception as exc:  # noqa: BLE001
            registrar_error("CARGAR_PAGOS", str(exc))
            return {"ok": False, "error": str(exc), "datos": {}}

    # Exportaciones y backups
    def exportar_excel(self, personas: list, nombre_coop: str) -> Dict[str, Optional[str]]:
        try:
            nombre_archivo = f"{nombre_coop}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            ruta_archivo = self.exportador.exportar_personas_cooperacion(
                personas, nombre_coop, nombre_archivo
            )
            if ruta_archivo:
                registrar_operacion(
                    "EXPORTAR_EXCEL",
                    "Datos exportados a Excel",
                    {
                        "cooperacion": nombre_coop,
                        "archivo": ruta_archivo,
                        "total_personas": len(personas),
                    },
                )
            return {"ruta": ruta_archivo}
        except Exception as exc:  # noqa: BLE001
            registrar_error("EXPORTAR_EXCEL", str(exc))
            return {"ruta": None, "error": str(exc)}

    def crear_backup(self) -> Dict[str, Any]:
        try:
            return self.gestor_backups.crear_backup_completo()
        except Exception as exc:  # noqa: BLE001
            registrar_error("CREAR_BACKUP", str(exc))
            return {"exito": False, "error": str(exc)}

    def backup_silencioso(self, max_backups: int = 10) -> Dict[str, Any]:
        """Backup sin alertas; pensado para cierre de aplicación."""
        try:
            resultado = self.gestor_backups.crear_backup_completo()
            if resultado.get("exito"):
                try:
                    self.gestor_backups.limpiar_backups_antiguos(max_backups)
                except Exception:
                    # Limpieza fallida no debe interrumpir el cierre
                    pass
            return resultado
        except Exception as exc:  # noqa: BLE001
            registrar_error("BACKUP_AUTO", str(exc))
            return {"exito": False, "error": str(exc)}
