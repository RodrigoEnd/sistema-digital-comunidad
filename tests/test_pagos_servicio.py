"""Tests para PagosServicio."""
import time
import pytest
from unittest.mock import Mock, patch
from src.modules.pagos.pagos_servicio import PagosServicio


class TestPagosServicio:
    """Suite de tests para PagosServicio."""

    def setup_method(self):
        """Setup antes de cada test."""
        self.servicio = PagosServicio(api_url="http://localhost:5000/api")

    def test_aplicar_cooperacion_activa_crea_cooperacion_por_defecto(self):
        """Debe crear cooperación por defecto si no existe ninguna."""
        cooperaciones = []
        resultado = self.servicio.aplicar_cooperacion_activa(
            cooperaciones=cooperaciones,
            coop_activa_id=None,
            proyecto_actual="Proyecto Test",
            monto_cooperacion=150.0
        )

        assert resultado['cooperaciones']
        assert len(resultado['cooperaciones']) == 1
        assert resultado['cooperaciones'][0]['nombre'] == "Cooperacion General"
        assert resultado['monto_cooperacion'] == 150.0
        assert resultado['proyecto_actual'] == "Proyecto Test"

    def test_aplicar_cooperacion_activa_usa_existente(self):
        """Debe usar cooperación existente si hay ID válido."""
        coop_id = f"coop-{int(time.time())}"
        cooperaciones = [{
            'id': coop_id,
            'nombre': 'Test Coop',
            'proyecto': 'Proyecto Existente',
            'monto_cooperacion': 200.0,
            'personas': []
        }]

        resultado = self.servicio.aplicar_cooperacion_activa(
            cooperaciones=cooperaciones,
            coop_activa_id=coop_id,
            proyecto_actual="Default",
            monto_cooperacion=100.0
        )

        assert resultado['coop_activa_id'] == coop_id
        assert resultado['cooperacion_actual'] == 'Test Coop'
        assert resultado['monto_cooperacion'] == 200.0

    @patch('requests.get')
    def test_sincronizar_con_censo_agrega_nuevos(self, mock_get):
        """Debe agregar habitantes nuevos desde el censo."""
        # Mock de respuesta de API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'habitantes': [
                {'nombre': 'Juan Pérez', 'folio': '001'},
                {'nombre': 'María López', 'folio': '002'}
            ],
            'total': 2
        }
        mock_get.return_value = mock_response

        coop = {
            'id': 'test-1',
            'personas': [],
            'monto_cooperacion': 100.0
        }

        resultado = self.servicio.sincronizar_con_censo(coop)

        assert resultado['ok']
        assert resultado['agregados'] == 2
        assert len(coop['personas']) == 2
        assert coop['personas'][0]['nombre'] == 'Juan Pérez'

    @patch('requests.get')
    def test_sincronizar_con_censo_detecta_no_en_censo(self, mock_get):
        """Debe detectar personas en cooperación que no están en censo."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'habitantes': [
                {'nombre': 'Juan Pérez', 'folio': '001'}
            ],
            'total': 1
        }
        mock_get.return_value = mock_response

        coop = {
            'id': 'test-1',
            'personas': [
                {'nombre': 'Persona Inexistente', 'folio': '999', 'pagos': []}
            ],
            'monto_cooperacion': 100.0
        }

        resultado = self.servicio.sincronizar_con_censo(coop)

        assert resultado['ok']
        assert len(resultado['personas_no_en_censo']) == 1
        assert resultado['personas_no_en_censo'][0]['nombre'] == 'Persona Inexistente'

    @patch('requests.get')
    def test_sincronizar_con_censo_no_duplica(self, mock_get):
        """No debe duplicar personas ya existentes."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'habitantes': [
                {'nombre': 'Juan Pérez', 'folio': '001'}
            ],
            'total': 1
        }
        mock_get.return_value = mock_response

        coop = {
            'id': 'test-1',
            'personas': [
                {'nombre': 'Juan Pérez', 'folio': '001', 'pagos': []}
            ],
            'monto_cooperacion': 100.0
        }

        resultado = self.servicio.sincronizar_con_censo(coop)

        assert resultado['ok']
        assert resultado['agregados'] == 0
        assert len(coop['personas']) == 1

    @patch('requests.get')
    def test_sincronizar_con_censo_maneja_error_api(self, mock_get):
        """Debe manejar correctamente errores de API."""
        mock_get.side_effect = Exception("Connection timeout")

        coop = {'id': 'test-1', 'personas': []}
        resultado = self.servicio.sincronizar_con_censo(coop)

        assert not resultado['ok']
        assert 'error' in resultado


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
