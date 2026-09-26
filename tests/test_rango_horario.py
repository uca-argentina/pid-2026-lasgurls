from datetime import date, datetime, time
from dominio.modulo_utilidades.rango_horario import rango_del_evento, termina_al_dia_siguiente, ya_empezo


def test_evento_del_mismo_dia():
    inicio, fin = rango_del_evento(date(2026, 9, 25), time(18, 0), time(21, 0))

    assert inicio == datetime(2026, 9, 25, 18, 0)
    assert fin == datetime(2026, 9, 25, 21, 0)
    assert not termina_al_dia_siguiente(date(2026, 9, 25), time(18, 0), time(21, 0))

def test_evento_que_termina_al_dia_siguiente():
    inicio, fin = rango_del_evento(date(2026, 9, 25), time(23, 0), time(3, 0))

    assert inicio == datetime(2026, 9, 25, 23, 0)
    assert fin == datetime(2026, 9, 26, 3, 0)
    assert termina_al_dia_siguiente(date(2026, 9, 25), time(23, 0), time(3, 0))

def test_evento_que_termina_justo_a_medianoche_no_pasa_al_dia_siguiente():
    inicio, fin = rango_del_evento(date(2026, 9, 25), time(20, 0), time(0, 0))

    assert fin == datetime(2026, 9, 26, 0, 0)
    assert not termina_al_dia_siguiente(date(2026, 9, 25), time(20, 0), time(0, 0))

def test_ya_empezo():
    ahora = datetime(2026, 9, 25, 18, 0)

    assert ya_empezo(date(2026, 9, 25), time(17, 59), ahora)
    assert ya_empezo(date(2026, 9, 25), time(18, 0), ahora)
    assert not ya_empezo(date(2026, 9, 25), time(18, 1), ahora)
    assert not ya_empezo(date(2026, 9, 26), time(9, 0), ahora)
