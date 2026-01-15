"""Tests para FaenasServicio."""
import pytest
from datetime import datetime
from src.modules.faenas.faenas_servicio import FaenasServicio


class TestFaenasServicio:
    """Suite de tests para FaenasServicio."""

    def setup_method(self):
        """Setup antes de cada test."""
        self.servicio = FaenasServicio(api_url="http://localhost:5000/api")

    def test_calcular_resumen_anual_sin_faenas(self):
        """Debe retornar resumen vacío si no hay faenas."""
        faenas = []
        resultado = self.servicio.calcular_resumen_anual(faenas, 2026)

        assert resultado['puntos'] == {}
        assert resultado['max_puntos'] == 1
        assert resultado['total_personas'] == 0

    def test_calcular_resumen_anual_con_faenas(self):
        """Debe calcular puntos correctamente."""
        faenas = [
            {
                'fecha': '2026-01-15',
                'peso': 1.0,
                'participantes': [
                    {'folio': '001', 'nombre': 'Juan', 'peso_aplicado': 1.0},
                    {'folio': '002', 'nombre': 'María', 'peso_aplicado': 0.9}
                ]
            },
            {
                'fecha': '2026-02-20',
                'peso': 2.0,
                'participantes': [
                    {'folio': '001', 'nombre': 'Juan', 'peso_aplicado': 1.0}
                ]
            }
        ]

        resultado = self.servicio.calcular_resumen_anual(faenas, 2026)

        assert '001' in resultado['puntos']
        assert '002' in resultado['puntos']
        assert resultado['puntos']['001']['puntos'] == 3.0  # 1.0*1.0 + 2.0*1.0
        assert resultado['puntos']['002']['puntos'] == 0.9  # 1.0*0.9
        assert resultado['max_puntos'] == 3.0

    def test_calcular_resumen_filtra_por_anio(self):
        """Debe filtrar faenas por año."""
        faenas = [
            {
                'fecha': '2025-01-15',
                'peso': 1.0,
                'participantes': [
                    {'folio': '001', 'nombre': 'Juan', 'peso_aplicado': 1.0}
                ]
            },
            {
                'fecha': '2026-01-15',
                'peso': 1.0,
                'participantes': [
                    {'folio': '002', 'nombre': 'María', 'peso_aplicado': 1.0}
                ]
            }
        ]

        resultado = self.servicio.calcular_resumen_anual(faenas, 2026)

        assert '001' not in resultado['puntos']
        assert '002' in resultado['puntos']

    def test_obtener_años_disponibles(self):
        """Debe extraer años únicos de faenas."""
        faenas = [
            {'fecha': '2025-03-15'},
            {'fecha': '2025-06-20'},
            {'fecha': '2026-01-10'}
        ]

        años = self.servicio.obtener_años_disponibles(faenas)

        assert 2025 in años
        assert 2026 in años
        assert datetime.now().year in años
        assert años == sorted(años, reverse=True)

    def test_filtrar_resumen_por_criterio_nombre(self):
        """Debe filtrar por nombre."""
        puntos = {
            '001': {'folio': '001', 'nombre': 'Juan Pérez', 'puntos': 5.0},
            '002': {'folio': '002', 'nombre': 'María López', 'puntos': 3.0}
        }

        resultado = self.servicio.filtrar_resumen_por_criterio(puntos, 'juan')

        assert '001' in resultado
        assert '002' not in resultado

    def test_filtrar_resumen_por_criterio_folio(self):
        """Debe filtrar por folio."""
        puntos = {
            '001': {'folio': '001', 'nombre': 'Juan Pérez', 'puntos': 5.0},
            '002': {'folio': '002', 'nombre': 'María López', 'puntos': 3.0}
        }

        resultado = self.servicio.filtrar_resumen_por_criterio(puntos, '002')

        assert '001' not in resultado
        assert '002' in resultado

    def test_calcular_color_por_puntaje(self):
        """Debe retornar colores válidos en gradiente."""
        color_bajo = self.servicio.calcular_color_por_puntaje(1.0, 10.0)
        color_medio = self.servicio.calcular_color_por_puntaje(5.0, 10.0)
        color_alto = self.servicio.calcular_color_por_puntaje(10.0, 10.0)

        assert color_bajo.startswith('#')
        assert len(color_bajo) == 7
        assert color_medio.startswith('#')
        assert color_alto.startswith('#')

    def test_validar_puede_editar_faena_reciente(self):
        """Debe permitir editar faena reciente."""
        faena = {'fecha': datetime.now().strftime("%Y-%m-%d")}
        
        resultado = self.servicio.validar_puede_editar_faena(faena, dias_limite=7)

        assert resultado['puede_editar']
        assert resultado['dias_transcurridos'] == 0

    def test_validar_puede_editar_faena_antigua(self):
        """No debe permitir editar faena antigua."""
        from datetime import timedelta
        fecha_antigua = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        faena = {'fecha': fecha_antigua}

        resultado = self.servicio.validar_puede_editar_faena(faena, dias_limite=7)

        assert not resultado['puede_editar']
        assert resultado['dias_transcurridos'] == 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
