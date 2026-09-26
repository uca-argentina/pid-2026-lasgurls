from datetime import date, datetime, timedelta
import pytest
from dominio.disponibilidad.buscador_huecos import unir_ocupados, buscar_huecos, huecos_del_dia, proxima_media_hora


def hora(dia, horas, minutos=0):
    return datetime(2026, 9, dia, horas, minutos)

DIA = hora(25, 0)
FIN_DEL_DIA = hora(26, 0)
DOS_HORAS = timedelta(hours=2)


def test_une_bloques_que_se_superponen_o_se_tocan():
    ocupados = [(hora(25, 14), hora(25, 16)), (hora(25, 10), hora(25, 12)), (hora(25, 15), hora(25, 17)), (hora(25, 12), hora(25, 13))]

    assert unir_ocupados(ocupados) == [(hora(25, 10), hora(25, 13)), (hora(25, 14), hora(25, 17))]

def test_dia_sin_ocupados_esta_todo_libre():
    assert buscar_huecos([], DIA, FIN_DEL_DIA, DOS_HORAS) == [(DIA, FIN_DEL_DIA)]

def test_encuentra_los_huecos_entre_ocupados_de_varias_personas():
    vos = [(hora(25, 0), hora(25, 9)), (hora(25, 20), hora(25, 23))]
    juan = [(hora(25, 12), hora(25, 14))]
    ana = [(hora(25, 13), hora(25, 17))]

    huecos = buscar_huecos(vos + juan + ana, DIA, FIN_DEL_DIA, DOS_HORAS)

    assert huecos == [(hora(25, 9), hora(25, 12)), (hora(25, 17), hora(25, 20))]

def test_descarta_huecos_mas_cortos_que_la_duracion():
    ocupados = [(hora(25, 0), hora(25, 10)), (hora(25, 11), hora(25, 23))]

    assert buscar_huecos(ocupados, DIA, FIN_DEL_DIA, DOS_HORAS) == []

def test_acepta_un_hueco_justo_del_largo_pedido():
    ocupados = [(hora(25, 0), hora(25, 10)), (hora(25, 12), FIN_DEL_DIA)]

    assert buscar_huecos(ocupados, DIA, FIN_DEL_DIA, DOS_HORAS) == [(hora(25, 10), hora(25, 12))]

def test_una_fiesta_del_dia_anterior_ocupa_la_madrugada():
    fiesta = [(hora(24, 23), hora(25, 3))]

    assert buscar_huecos(fiesta, DIA, FIN_DEL_DIA, DOS_HORAS) == [(hora(25, 3), FIN_DEL_DIA)]

def test_la_duracion_tiene_que_ser_positiva():
    with pytest.raises(ValueError):
        buscar_huecos([], DIA, FIN_DEL_DIA, timedelta(0))

def test_huecos_del_dia_corta_lo_que_viene_de_antes_y_de_despues():
    huecos = [(hora(24, 20), hora(25, 8)), (hora(25, 15), hora(26, 20))]

    resultado = huecos_del_dia(huecos, date(2026, 9, 25), DOS_HORAS)

    assert resultado == [(hora(25, 0), hora(25, 8)), (hora(25, 15), FIN_DEL_DIA)]

def test_huecos_del_dia_permite_terminar_pasada_la_medianoche():
    huecos = [(hora(25, 23), hora(26, 10))]

    resultado = huecos_del_dia(huecos, date(2026, 9, 25), timedelta(hours=4))

    assert resultado == [(hora(25, 23), hora(26, 3))]

def test_huecos_del_dia_ignora_huecos_de_otros_dias():
    huecos = [(hora(26, 10), hora(26, 18))]

    assert huecos_del_dia(huecos, date(2026, 9, 25), DOS_HORAS) == []

def test_proxima_media_hora():
    assert proxima_media_hora(hora(25, 14, 10)) == hora(25, 14, 30)
    assert proxima_media_hora(hora(25, 14, 30)) == hora(25, 14, 30)
    assert proxima_media_hora(hora(25, 14, 31)) == hora(25, 15, 0)
