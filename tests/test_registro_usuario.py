import pytest

from dominio.usuario import Usuario



def test_usuario_valido_se_crea_sin_error():
    usuario = Usuario("test@gmail.com", "Contra123!!", "Test")
    assert usuario.email == "test@gmail.com"
    assert usuario.nombre == "Test"


def test_password_se_guarda_hasheada_no_en_texto_plano():
    usuario = Usuario("test@gmail.com", "Contra123!!", "Test")
    assert usuario.password != "Contra123!!"



def test_nombre_vacio_lanza_error():
    with pytest.raises(ValueError) as error:
        Usuario("test@gmail.com", "Contra123!!", "")
    assert str(error.value) == "El nombre no debe estar vacío"


def test_nombre_solo_espacios_lanza_error():
    with pytest.raises(ValueError) as error:
        Usuario("test@gmail.com", "Contra123!!", "   ")
    assert str(error.value) == "El nombre no debe estar vacío"



def test_email_vacio_lanza_error():
    with pytest.raises(ValueError) as error:
        Usuario("", "Contra123!!", "Test")
    assert str(error.value) == "El email no puede estar vacío"


def test_email_sin_arroba_lanza_error():
    with pytest.raises(ValueError) as error:
        Usuario("testgmail.com", "Contra123!!", "Test")
    assert str(error.value) == "El correo debe contener un @"


def test_email_con_doble_arroba_lanza_error():
    with pytest.raises(ValueError) as error:
        Usuario("test@@gmail.com", "Contra123!!", "Test")
    assert str(error.value) == "El correo debe contener un @"


def test_email_con_espacio_lanza_error():
    with pytest.raises(ValueError) as error:
        Usuario("te st@gmail.com", "Contra123!!", "Test")
    assert str(error.value) == "El email no puede contener espacios"


def test_email_sin_dominio_lanza_error():
    with pytest.raises(ValueError) as error:
        Usuario("test@", "Contra123!!", "Test")
    assert str(error.value) == "El email no es válido"


def test_email_sin_usuario_lanza_error():
    with pytest.raises(ValueError) as error:
        Usuario("@gmail.com", "Contra123!!", "Test")
    assert str(error.value) == "El email no es válido"


def test_email_sin_punto_en_dominio_lanza_error():
    with pytest.raises(ValueError) as error:
        Usuario("test@gmailcom", "Contra123!!", "Test")
    assert str(error.value) == "El email debe tener un dominio válido como '.com' "

def test_email_se_normaliza_a_minusculas():
    usuario = Usuario("Test@Gmail.com", "Contra123!!", "Test")
    assert usuario.email == "test@gmail.com"




def test_password_vacia_lanza_error():
    with pytest.raises(ValueError) as error:
        Usuario("test@gmail.com", "", "Test")
    assert str(error.value) == "La contraseña debe tener al menos 8 caracteres"


def test_password_menos_de_8_caracteres_lanza_error():
    with pytest.raises(ValueError) as error:
        Usuario("test@gmail.com", "Abc1!", "Test")
    assert str(error.value) == "La contraseña debe tener al menos 8 caracteres"


def test_password_de_exactamente_8_caracteres_es_valida():
    usuario = Usuario("test@gmail.com", "Abcdef1!", "Test")
    assert usuario.email == "test@gmail.com"


def test_password_muy_larga_lanza_error():
    password_larga = "A1!" + "a" * 100
    with pytest.raises(ValueError) as error:
        Usuario("test@gmail.com", password_larga, "Test")
    assert str(error.value) == "La contraseña no puede tener más de 72 caracteres"


def test_password_sin_mayuscula_lanza_error():
    with pytest.raises(ValueError) as error:
        Usuario("test@gmail.com", "contra123!!", "Test")
    assert str(error.value) == "La contraseña debe tener al menos una mayúscula"


def test_password_sin_simbolo_lanza_error():
    with pytest.raises(ValueError) as error:
        Usuario("test@gmail.com", "Contra123", "Test")
    assert str(error.value) == "La contraseña debe tener al menos un símbolo"

