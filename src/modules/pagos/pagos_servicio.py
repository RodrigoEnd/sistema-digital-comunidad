import time
from typing import Any, Dict, List, Optional, Set

import requests


class PagosServicio:
    """Reglas de negocio sin dependencias de UI para pagos/cooperaciones."""

    def __init__(self, api_url: str):
        self.api_url = api_url

    def aplicar_cooperacion_activa(
        self,
        cooperaciones: List[Dict[str, Any]],
        coop_activa_id: Optional[str],
        proyecto_actual: str,
        monto_cooperacion: float,
    ) -> Dict[str, Any]:
        """Devuelve el estado normalizado de la cooperación activa.

        Si no existe cooperación activa, crea una por defecto.
        """
        coop = self._buscar_cooperacion(cooperaciones, coop_activa_id)
        if coop is None and cooperaciones:
            coop = cooperaciones[0]
            coop_activa_id = coop.get("id")
        if coop is None:
            coop = {
                "id": f"coop-{int(time.time())}",
                "nombre": "Cooperacion General",
                "proyecto": proyecto_actual,
                "monto_cooperacion": monto_cooperacion,
                "personas": [],
            }
            cooperaciones.append(coop)
            coop_activa_id = coop["id"]

        personas = coop.setdefault("personas", [])
        monto = coop.get("monto_cooperacion", monto_cooperacion)
        proyecto = coop.get("proyecto", proyecto_actual)
        nombre = coop.get("nombre", "Cooperacion")

        return {
            "cooperaciones": cooperaciones,
            "coop_activa_id": coop_activa_id,
            "personas": personas,
            "monto_cooperacion": monto,
            "proyecto_actual": proyecto,
            "cooperacion_actual": nombre,
            "coop": coop,
        }

    def sincronizar_con_censo(self, coop: Dict[str, Any]) -> Dict[str, Any]:
        """Sincroniza habitantes del censo con la cooperación (sin UI).

        - Agrega nuevos habitantes que no estén en la cooperación.
        - No elimina; solo devuelve sugerencias para UI.
        """
        if not coop:
            return {"ok": False, "error": "No hay cooperación activa"}

        try:
            response = requests.get(f"{self.api_url}/habitantes", timeout=6)
            if response.status_code != 200:
                return {"ok": False, "error": "No se pudo obtener habitantes"}

            data = response.json()
            habitantes = data.get("habitantes", [])
            total_censo = data.get("total", len(habitantes))

            nombres_censo: Set[str] = {h.get("nombre", "").strip().lower() for h in habitantes if h.get("nombre")}
            personas_no_en_censo = [
                p for p in coop.get("personas", []) if p.get("nombre", "").strip().lower() not in nombres_censo
            ]

            existentes = {p.get("nombre", "").lower(): p for p in coop.get("personas", [])}
            agregados = 0
            for hab in habitantes:
                nombre = (hab.get("nombre") or "").strip()
                folio = hab.get("folio", "SIN-FOLIO")
                if not nombre:
                    continue
                if nombre.lower() not in existentes:
                    nuevo = {
                        "nombre": nombre,
                        "folio": folio,
                        "monto_esperado": coop.get("monto_cooperacion", 0),
                        "pagos": [],
                        "notas": "",
                    }
                    coop.setdefault("personas", []).append(nuevo)
                    agregados += 1

            return {
                "ok": True,
                "habitantes": habitantes,
                "total_censo": total_censo,
                "agregados": agregados,
                "personas_no_en_censo": personas_no_en_censo,
                "nombres_censo": nombres_censo,
            }
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}

    @staticmethod
    def _buscar_cooperacion(cooperaciones: List[Dict[str, Any]], coop_activa_id: Optional[str]) -> Optional[Dict[str, Any]]:
        for coop in cooperaciones:
            if coop.get("id") == coop_activa_id:
                return coop
        return None
