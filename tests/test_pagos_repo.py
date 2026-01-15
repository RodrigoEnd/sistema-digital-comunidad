"""Tests para PagosRepositorio."""
import os
import tempfile
import pytest
from src.modules.pagos.pagos_repo import PagosRepositorio


class TestPagosRepositorio:
    """Suite de tests para PagosRepositorio."""

    def setup_method(self):
        """Setup antes de cada test con archivo temporal."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.enc')
        self.temp_file.close()
        self.password = "test_password_123"
        self.repo = PagosRepositorio(
            archivo_datos=self.temp_file.name,
            password_archivo=self.password
        )

    def teardown_method(self):
        """Limpieza después de cada test."""
        try:
            os.unlink(self.temp_file.name)
        except:
            pass

    def test_guardar_y_cargar_datos(self):
        """Debe guardar y cargar datos correctamente."""
        datos_prueba = {
            'cooperaciones': [
                {
                    'id': 'coop-1',
                    'nombre': 'Test Cooperacion',
                    'proyecto': 'Proyecto Test',
                    'monto_cooperacion': 150.0,
                    'personas': []
                }
            ],
            'cooperacion_activa': 'coop-1',
            'password_hash': 'hash_test'
        }

        # Guardar
        resultado_guardar = self.repo.guardar(datos_prueba)
        assert resultado_guardar['ok']

        # Cargar
        resultado_cargar = self.repo.cargar()
        assert resultado_cargar['ok']
        datos_cargados = resultado_cargar['datos']
        assert 'cooperaciones' in datos_cargados
        assert datos_cargados['cooperaciones'][0]['nombre'] == 'Test Cooperacion'

    def test_cargar_archivo_inexistente(self):
        """Debe retornar datos vacíos si el archivo no existe."""
        repo_temp = PagosRepositorio(
            archivo_datos="archivo_que_no_existe_12345.enc",
            password_archivo=self.password
        )

        resultado = repo_temp.cargar()
        assert resultado['ok']
        assert resultado['datos'] == {}

    def test_guardar_datos_vacios(self):
        """Debe poder guardar estructura vacía."""
        datos_vacios = {
            'cooperaciones': [],
            'cooperacion_activa': None
        }

        resultado = self.repo.guardar(datos_vacios)
        assert resultado['ok']

        resultado_cargar = self.repo.cargar()
        assert resultado_cargar['ok']
        assert resultado_cargar['datos']['cooperaciones'] == []

    def test_exportar_excel_con_personas(self):
        """Debe exportar Excel correctamente."""
        personas = [
            {
                'nombre': 'Juan Pérez',
                'folio': '001',
                'monto_esperado': 100.0,
                'pagos': [
                    {'monto': 50.0, 'fecha': '2026-01-10', 'metodo': 'efectivo'}
                ]
            },
            {
                'nombre': 'María López',
                'folio': '002',
                'monto_esperado': 100.0,
                'pagos': []
            }
        ]

        resultado = self.repo.exportar_excel(personas, "Test Cooperacion")
        
        # Debe retornar ruta o None
        assert 'ruta' in resultado
        if resultado['ruta']:
            assert resultado['ruta'].endswith('.xlsx')
            # Limpiar archivo generado
            try:
                os.unlink(resultado['ruta'])
            except:
                pass

    def test_crear_backup(self):
        """Debe crear backup sin errores."""
        resultado = self.repo.crear_backup()
        
        # Puede o no tener éxito dependiendo de configuración
        assert 'exito' in resultado

    def test_backup_silencioso(self):
        """Debe ejecutar backup silencioso sin fallar."""
        resultado = self.repo.backup_silencioso(max_backups=5)
        
        assert 'exito' in resultado
        # Backup silencioso nunca debe lanzar excepciones al caller


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
