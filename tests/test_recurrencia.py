from datetime import date, datetime
import pytest
from dominio.juntada.juntada import Juntada
from dominio.juntada.recurrencia import Recurrencia, texto_de_repeticion, un_anio_despues

AHORA = datetime(2026, 9, 1, 12, 0)


def test_juntada_sin_repeticion_tiene_una_sola_fecha():
    juntada = Juntada(2, "15/09/2026", "Asado", "20:00", "23:00", [1], ahora=AHORA)
    assert juntada.fechas == [date(2026, 9, 15)]


def test_repeticion_semanal():
    juntada = Juntada(2, "15/09/2026", "Fútbol", "20:00", "22:00", [1], ahora=AHORA,
                      recurrencia=Recurrencia("semanal", "06/10/2026"))
    assert juntada.fechas == [date(2026, 9, 15), date(2026, 9, 22), date(2026, 9, 29), date(2026, 10, 6)]


def test_repeticion_diaria():
    fechas = Recurrencia("diaria", "18/09/2026").fechas_desde(date(2026, 9, 15))
    assert fechas == [date(2026, 9, 15), date(2026, 9, 16), date(2026, 9, 17), date(2026, 9, 18)]


def test_repeticion_quincenal():
    fechas = Recurrencia("quincenal", "13/10/2026").fechas_desde(date(2026, 9, 15))
    assert fechas == [date(2026, 9, 15), date(2026, 9, 29), date(2026, 10, 13)]


def test_repeticion_mensual():
    fechas = Recurrencia("mensual", "20/12/2026").fechas_desde(date(2026, 9, 15))
    assert fechas == [date(2026, 9, 15), date(2026, 10, 15), date(2026, 11, 15), date(2026, 12, 15)]


def test_repeticion_mensual_saltea_meses_sin_ese_dia():
    fechas = Recurrencia("mensual", "31/05/2027").fechas_desde(date(2027, 1, 31))
    assert fechas == [date(2027, 1, 31), date(2027, 3, 31), date(2027, 5, 31)]


def test_repeticion_hasta_un_anio_es_valida():
    fechas = Recurrencia("semanal", "15/09/2027").fechas_desde(date(2026, 9, 15))
    assert fechas[-1] <= date(2027, 9, 15)
    assert len(fechas) == 53


def test_repeticion_de_mas_de_un_anio_es_invalida():
    with pytest.raises(ValueError) as error:
        Juntada(2, "15/09/2026", "Fútbol", "20:00", "22:00", [1], ahora=AHORA,
                recurrencia=Recurrencia("semanal", "16/09/2027"))
    assert str(error.value) == "La juntada se puede repetir hasta un año después de la primera fecha"


def test_repeticion_que_termina_antes_de_empezar_es_invalida():
    with pytest.raises(ValueError) as error:
        Recurrencia("semanal", "15/09/2026").fechas_desde(date(2026, 9, 15))
    assert str(error.value) == "La repetición tiene que terminar después de la primera fecha"


def test_frecuencia_invalida():
    with pytest.raises(ValueError) as error:
        Recurrencia("anual", "15/10/2026")
    assert str(error.value) == "Elegí cada cuánto se repite la juntada"


def test_repeticion_sin_fecha_de_fin_es_invalida():
    with pytest.raises(ValueError) as error:
        Recurrencia("semanal", "")
    assert str(error.value) == "Elegí hasta qué fecha se repite la juntada"


def test_un_anio_desde_29_de_febrero():
    fechas = Recurrencia("diaria", "28/02/2029").fechas_desde(date(2028, 2, 29))
    assert fechas[-1] == date(2029, 2, 28)


def test_texto_de_repeticion_semanal_dice_el_dia():
    assert texto_de_repeticion("semanal", date(2026, 10, 13)) == "Todos los martes"
    assert texto_de_repeticion("semanal", date(2026, 10, 17)) == "Todos los sábados"


def test_juntada_sin_repeticion_no_tiene_texto():
    assert texto_de_repeticion(None, date(2026, 10, 13)) is None


def test_un_anio_despues():
    assert un_anio_despues(date(2026, 10, 13)) == date(2027, 10, 13)
