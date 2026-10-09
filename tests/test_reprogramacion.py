from datetime import date, datetime, time
import pytest
from dominio.juntada.reprogramacion import Reprogramacion

AHORA = datetime(2026, 9, 1, 12, 0)


def test_reprogramacion_correcta():
    reprogramacion = Reprogramacion("20/09/2026", "21:00", "23:00", AHORA)
    assert reprogramacion.fecha == date(2026, 9, 20)
    assert reprogramacion.hora_inicio == time(21, 0)
    assert reprogramacion.hora_fin == time(23, 0)


def test_reprogramar_a_un_horario_que_ya_paso_es_invalido():
    with pytest.raises(ValueError) as error:
        Reprogramacion("01/09/2026", "10:00", "11:00", AHORA)
    assert str(error.value) == "La juntada no puede empezar en un horario que ya pasó"


def test_reprogramar_con_horas_iguales_es_invalido():
    with pytest.raises(ValueError) as error:
        Reprogramacion("20/09/2026", "21:00", "21:00", AHORA)
    assert str(error.value) == "La hora de inicio y la de finalización no pueden ser iguales"


def test_reprogramar_al_mismo_horario_es_invalido():
    reprogramacion = Reprogramacion("20/09/2026", "21:00", "23:00", AHORA)
    with pytest.raises(ValueError) as error:
        reprogramacion.validar_que_cambie(date(2026, 9, 20), time(21, 0), time(23, 0))
    assert str(error.value) == "Elegí una fecha u horario distinto al actual"


def test_cambiar_solo_el_horario_es_valido():
    reprogramacion = Reprogramacion("20/09/2026", "22:00", "23:00", AHORA)
    reprogramacion.validar_que_cambie(date(2026, 9, 20), time(21, 0), time(23, 0))


def test_reprogramacion_que_termina_al_dia_siguiente_es_valida():
    reprogramacion = Reprogramacion("20/09/2026", "23:00", "02:00", AHORA)
    assert reprogramacion.hora_fin == time(2, 0)
