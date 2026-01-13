"""
Tests Unitarios - Validadores
Prueba las funciones de validacion de entrada
"""

import pytest
from src.core.validadores import (
    ErrorValidacion,
    validar_nombre,
    validar_monto,
    validar_folio,
    validar_email,
    validar_telefono,
    validar_edad,
    validar_genero,
    validar_campo_obligatorio,
    validar_rango_numerico,
    validar_largo_string,
    validar_estado_pago,
    validar_fecha_formato,
    sanitizar_entrada
)


# ============================================================================
# TESTS PARA VALIDAR_NOMBRE
# ============================================================================

class TestValidarNombre:
    """Suite de tests para validar_nombre"""
    
    def test_nombre_valido(self):
        """Nombre valido debe pasar"""
        resultado = validar_nombre("Juan Perez")
        assert resultado == "Juan Perez"
    
    def test_nombre_con_espacios(self):
        """Debe remover espacios al inicio/final"""
        resultado = validar_nombre("  Maria Garcia  ")
        assert resultado == "Maria Garcia"
    
    def test_nombre_muy_corto(self):
        """Nombre muy corto debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_nombre("Jo")
    
    def test_nombre_muy_largo(self):
        """Nombre muy largo debe fallar"""
        nombre_largo = "A" * 101
        with pytest.raises(ErrorValidacion):
            validar_nombre(nombre_largo)
    
    def test_nombre_vacio(self):
        """Nombre vacio debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_nombre("")
    
    def test_nombre_solo_espacios(self):
        """Nombre solo con espacios debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_nombre("   ")
    
    def test_nombre_con_caracteres_invalidos(self):
        """Caracteres invalidos deben fallar"""
        with pytest.raises(ErrorValidacion):
            validar_nombre("Juan@123")
    
    def test_nombre_con_acentos(self):
        """Acentos deben ser permitidos"""
        resultado = validar_nombre("José García")
        assert resultado == "José García"


# ============================================================================
# TESTS PARA VALIDAR_MONTO
# ============================================================================

class TestValidarMonto:
    """Suite de tests para validar_monto"""
    
    def test_monto_valido(self):
        """Monto valido debe pasar"""
        resultado = validar_monto(100.50)
        assert resultado == 100.50
    
    def test_monto_string_valido(self):
        """Monto como string debe convertirse"""
        resultado = validar_monto("50.25")
        assert resultado == 50.25
    
    def test_monto_cero(self):
        """Monto cero debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_monto(0)
    
    def test_monto_negativo(self):
        """Monto negativo debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_monto(-50)
    
    def test_monto_invalido(self):
        """Monto invalido debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_monto("abc")
    
    def test_monto_redondeo(self):
        """Monto con muchos decimales debe redondearse"""
        resultado = validar_monto(100.567)
        assert resultado == 100.57
    
    def test_monto_minimo(self):
        """Monto menor al minimo debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_monto(0.001)


# ============================================================================
# TESTS PARA VALIDAR_FOLIO
# ============================================================================

class TestValidarFolio:
    """Suite de tests para validar_folio"""
    
    def test_folio_valido(self):
        """Folio valido debe pasar"""
        resultado = validar_folio("HAB-0001")
        assert resultado == "HAB-0001"
    
    def test_folio_minusculas(self):
        """Folio en minusculas debe convertirse"""
        resultado = validar_folio("hab-0001")
        assert resultado == "HAB-0001"
    
    def test_folio_invalido_formato(self):
        """Folio con formato invalido debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_folio("PAG-0001")
    
    def test_folio_muy_corto(self):
        """Folio muy corto debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_folio("HAB-01")


# ============================================================================
# TESTS PARA VALIDAR_EMAIL
# ============================================================================

class TestValidarEmail:
    """Suite de tests para validar_email"""
    
    def test_email_valido(self):
        """Email valido debe pasar"""
        resultado = validar_email("user@example.com")
        assert resultado == "user@example.com"
    
    def test_email_vacio_permitido(self):
        """Email vacio es permitido"""
        resultado = validar_email("")
        assert resultado == ""
    
    def test_email_invalido(self):
        """Email sin @ debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_email("userexample.com")
    
    def test_email_muy_largo(self):
        """Email muy largo debe fallar"""
        email_largo = "a" * 100 + "@example.com"
        with pytest.raises(ErrorValidacion):
            validar_email(email_largo)


# ============================================================================
# TESTS PARA VALIDAR_EDAD
# ============================================================================

class TestValidarEdad:
    """Suite de tests para validar_edad"""
    
    def test_edad_valida(self):
        """Edad valida debe pasar"""
        resultado = validar_edad(25)
        assert resultado == 25
    
    def test_edad_string(self):
        """Edad como string debe convertirse"""
        resultado = validar_edad("30")
        assert resultado == 30
    
    def test_edad_cero(self):
        """Edad cero debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_edad(0)
    
    def test_edad_negativa(self):
        """Edad negativa debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_edad(-5)
    
    def test_edad_muy_alta(self):
        """Edad mayor a 120 debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_edad(121)
    
    def test_edad_invalida(self):
        """Edad invalida debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_edad("abc")


# ============================================================================
# TESTS PARA VALIDAR_GENERO
# ============================================================================

class TestValidarGenero:
    """Suite de tests para validar_genero"""
    
    def test_genero_masculino(self):
        """Genero M debe pasar"""
        resultado = validar_genero("M")
        assert resultado == "M"
    
    def test_genero_femenino(self):
        """Genero F debe pasar"""
        resultado = validar_genero("f")
        assert resultado == "F"
    
    def test_genero_otro(self):
        """Genero O debe pasar"""
        resultado = validar_genero("o")
        assert resultado == "O"
    
    def test_genero_invalido(self):
        """Genero invalido debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_genero("X")


# ============================================================================
# TESTS PARA VALIDAR_RANGO_NUMERICO
# ============================================================================

class TestValidarRangoNumerico:
    """Suite de tests para validar_rango_numerico"""
    
    def test_valor_en_rango(self):
        """Valor en rango debe pasar"""
        resultado = validar_rango_numerico(50, 0, 100, "valor")
        assert resultado == 50
    
    def test_valor_menor_minimo(self):
        """Valor menor al minimo debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_rango_numerico(-1, 0, 100, "valor")
    
    def test_valor_mayor_maximo(self):
        """Valor mayor al maximo debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_rango_numerico(101, 0, 100, "valor")


# ============================================================================
# TESTS PARA VALIDAR_LARGO_STRING
# ============================================================================

class TestValidarLargoString:
    """Suite de tests para validar_largo_string"""
    
    def test_string_en_rango(self):
        """String en rango debe pasar"""
        resultado = validar_largo_string("hola", 1, 10, "campo")
        assert resultado == "hola"
    
    def test_string_muy_corto(self):
        """String muy corto debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_largo_string("a", 3, 10, "campo")
    
    def test_string_muy_largo(self):
        """String muy largo debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_largo_string("a" * 11, 1, 10, "campo")


# ============================================================================
# TESTS PARA VALIDAR_ESTADO_PAGO
# ============================================================================

class TestValidarEstadoPago:
    """Suite de tests para validar_estado_pago"""
    
    def test_estado_pendiente(self):
        """Estado pendiente debe pasar"""
        resultado = validar_estado_pago("PENDIENTE")
        assert resultado == "pendiente"
    
    def test_estado_completo(self):
        """Estado completo debe pasar"""
        resultado = validar_estado_pago("Completo")
        assert resultado == "completo"
    
    def test_estado_invalido(self):
        """Estado invalido debe fallar"""
        with pytest.raises(ErrorValidacion):
            validar_estado_pago("DESCONOCIDO")


# ============================================================================
# TESTS PARA SANITIZAR_ENTRADA
# ============================================================================

class TestSanitizarEntrada:
    """Suite de tests para sanitizar_entrada"""
    
    def test_remover_espacios(self):
        """Debe remover espacios al inicio/final"""
        resultado = sanitizar_entrada("  hola  ")
        assert resultado == "hola"
    
    def test_reemplazar_espacios_multiples(self):
        """Debe reemplazar multiples espacios"""
        resultado = sanitizar_entrada("hola    mundo")
        assert resultado == "hola mundo"
    
    def test_entrada_no_string(self):
        """Entrada no string debe retornarse sin cambios"""
        resultado = sanitizar_entrada(123)
        assert resultado == 123
