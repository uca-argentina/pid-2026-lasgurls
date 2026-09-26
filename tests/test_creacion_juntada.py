from datetime import datetime
from dominio.juntada.juntada import Juntada
import pytest

AHORA = datetime(2026, 9, 1, 12, 0)


def test_creacion_correcta_de_juntada():
    datos = Juntada(2, "15/09/2026", "Juntada de Estudio", "18:00", "21:00", [1, 3, 5], ahora=AHORA)
    resultado = datos.registrar_juntada()

    assert resultado == {
        "organizador": 2,
        "titulo_juntada": "Juntada de Estudio",
        "fecha": "2026-09-15",
        "hora_inicio": "18:00:00",
        "hora_fin": "21:00:00",
        "amigos_invitados": [1, 3, 5],
    }


def test_juntada_que_termina_al_dia_siguiente_es_valida():
    juntada = Juntada(2, "15/09/2026", "Fiesta", "23:00", "03:00", [1, 3, 5], ahora=AHORA)
    resultado = juntada.registrar_juntada()

    assert resultado["hora_inicio"] == "23:00:00"
    assert resultado["hora_fin"] == "03:00:00"


def test_datos_hora_inicio_igual_a_hora_fin_es_invalido():
    with pytest.raises(ValueError) as error:
        Juntada(2, "15/09/2026", "Juntada", "18:00", "18:00", [1, 3, 5], ahora=AHORA)
    assert str(error.value) == "La hora de inicio y la de finalización no pueden ser iguales"


def test_formato_fecha_invalido():
    with pytest.raises(ValueError) as error:
        Juntada(2, "15-09-2026", "Juntada", "18:00", "21:00", [1, 3, 5], ahora=AHORA)
    assert str(error.value) == "Formato de fecha inválido: '15-09-2026' (se espera DD/MM/AAAA)"


def test_formato_horario_invalido():
    with pytest.raises(ValueError) as error:
        Juntada(2, "15/09/2026", "Juntada", "18", "21:00", [1, 3, 5], ahora=AHORA)
    assert str(error.value) == "Formato de hora de inicio inválido: '18' (se espera HH:MM)"


def test_titulo_vacio_es_invalido():
    with pytest.raises(ValueError) as error:
        Juntada(2, "15/09/2026", "", "18:00", "21:00", [1, 3, 5], ahora=AHORA)
    assert str(error.value) == "El campo título no puede estar vacío"


def test_organizador_vacio_es_invalido():
    with pytest.raises(ValueError) as error:
        Juntada(None, "15/09/2026", "Juntada", "18:00", "21:00", [1, 3, 5], ahora=AHORA)
    assert str(error.value) == "El campo responsable no puede estar vacío"


def test_amigos_invitados_vacio_es_invalido():
    with pytest.raises(ValueError) as error:
        Juntada(2, "15/09/2026", "Juntada", "18:00", "21:00", [], ahora=AHORA)
    assert str(error.value) == "La juntada debe tener al menos un invitado"


def test_organizador_no_puede_invitarse_a_si_mismo():
    with pytest.raises(ValueError) as error:
        Juntada(3, "15/09/2026", "Juntada", "18:00", "21:00", [1, 3, 5], ahora=AHORA)
    assert str(error.value) == "El organizador no puede invitarse a sí mismo"


def test_juntada_en_un_dia_que_ya_paso_es_invalida():
    with pytest.raises(ValueError) as error:
        Juntada(2, "31/08/2026", "Juntada", "18:00", "21:00", [1], ahora=AHORA)
    assert str(error.value) == "La juntada no puede empezar en un horario que ya pasó"


def test_juntada_de_hoy_en_una_hora_que_ya_paso_es_invalida():
    with pytest.raises(ValueError) as error:
        Juntada(2, "01/09/2026", "Juntada", "11:30", "13:00", [1], ahora=AHORA)
    assert str(error.value) == "La juntada no puede empezar en un horario que ya pasó"


def test_juntada_de_hoy_mas_tarde_es_valida():
    juntada = Juntada(2, "01/09/2026", "Juntada", "12:00", "13:00", [1], ahora=datetime(2026, 9, 1, 12, 0, 45))

    assert juntada.registrar_juntada()["hora_inicio"] == "12:00:00"
