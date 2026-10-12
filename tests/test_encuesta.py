from datetime import datetime
import pytest
from dominio.encuesta import Encuesta

AHORA = datetime(2026, 10, 12, 10, 0)
OPCIONES = [("20/10/2026", "18:00", "20:00"), ("21/10/2026", "18:00", "20:00"), ("22/10/2026", "19:00", "21:00")]


def crear(opciones=None, invitados=None, organizador=1):
    return Encuesta(organizador, "Cena", opciones or OPCIONES, invitados or [2, 3, 4], ahora=AHORA)


def test_crea_encuesta_abierta_valida():
    e = crear()
    assert e.estado == "abierta"
    assert len(e.opciones) == 3


def test_menos_de_dos_opciones_falla():
    with pytest.raises(ValueError, match="al menos 2"):
        crear(opciones=OPCIONES[:1])


def test_mas_de_cinco_opciones_falla():
    muchas = [(f"{d}/10/2026", "18:00", "20:00") for d in range(20, 26)]
    with pytest.raises(ValueError, match="máximo 5"):
        crear(opciones=muchas)


def test_opciones_repetidas_fallan():
    with pytest.raises(ValueError, match="repetidas"):
        crear(opciones=[OPCIONES[0], OPCIONES[0]])


def test_opcion_en_el_pasado_falla():
    with pytest.raises(ValueError, match="ya pasó"):
        crear(opciones=[("11/10/2026", "18:00", "20:00"), OPCIONES[0]])


def test_opcion_con_horas_iguales_falla():
    with pytest.raises(ValueError, match="no pueden ser iguales"):
        crear(opciones=[("20/10/2026", "18:00", "18:00"), OPCIONES[0]])


def test_sin_invitados_falla():
    with pytest.raises(ValueError, match="al menos un invitado"):
        Encuesta(1, "Cena", OPCIONES, [], ahora=AHORA)


def test_organizador_no_puede_invitarse():
    with pytest.raises(ValueError, match="a sí mismo"):
        crear(invitados=[1, 2])


def test_titulo_vacio_falla():
    with pytest.raises(ValueError, match="título"):
        Encuesta(1, "  ", OPCIONES, [2], ahora=AHORA)


def test_invitado_puede_votar_varias_opciones():
    e = crear()
    e.votar(2, [0, 2])
    assert e.resultados() == [1, 0, 1]


def test_invitado_puede_cambiar_su_voto():
    e = crear()
    e.votar(2, [0])
    e.votar(2, [1])
    assert e.resultados() == [0, 1, 0]


def test_no_invitado_no_puede_votar():
    with pytest.raises(ValueError, match="invitados"):
        crear().votar(99, [0])


def test_organizador_tambien_puede_votar():
    e = crear()
    e.votar(1, [0])
    e.votar(2, [0, 1])
    assert e.resultados() == [2, 1, 0]


def test_voto_sin_opciones_falla():
    with pytest.raises(ValueError, match="al menos una"):
        crear().votar(2, [])


def test_opcion_inexistente_falla():
    with pytest.raises(ValueError, match="inexistente"):
        crear().votar(2, [7])


def test_ganadora_unica():
    e = crear()
    e.votar(2, [1])
    e.votar(3, [1, 2])
    assert e.opciones_ganadoras() == [1]


def test_empate_devuelve_todas_las_empatadas():
    e = crear()
    e.votar(2, [0])
    e.votar(3, [2])
    assert e.opciones_ganadoras() == [0, 2]


def test_sin_votos_no_hay_ganadoras():
    assert crear().opciones_ganadoras() == []


def test_confirmar_cierra_y_devuelve_la_opcion():
    e = crear()
    e.votar(2, [1])
    opcion = e.confirmar(1, 1)
    assert e.estado == "cerrada"
    assert opcion.fecha.day == 21
    assert e.opcion_confirmada is opcion


def test_confirmar_en_empate_permite_elegir_entre_empatadas():
    e = crear()
    e.votar(2, [0])
    e.votar(3, [2])
    assert e.confirmar(1, 2).fecha.day == 22


def test_no_se_puede_confirmar_una_opcion_menos_votada():
    e = crear()
    e.votar(2, [0])
    e.votar(3, [0, 1])
    with pytest.raises(ValueError, match="más votadas"):
        e.confirmar(1, 1)


def test_no_se_puede_confirmar_sin_votos():
    with pytest.raises(ValueError, match="sin votos"):
        crear().confirmar(1, 0)


def test_solo_el_organizador_confirma_o_cierra():
    e = crear()
    e.votar(2, [0])
    with pytest.raises(ValueError, match="organizador"):
        e.confirmar(2, 0)
    with pytest.raises(ValueError, match="organizador"):
        e.cerrar(2)


def test_organizador_puede_cerrar_sin_que_voten_todos():
    e = crear()
    e.votar(2, [0])
    e.cerrar(1)
    assert e.estado == "cerrada"


def test_encuesta_cerrada_no_admite_votos_ni_confirmacion():
    e = crear()
    e.votar(2, [0])
    e.cerrar(1)
    with pytest.raises(ValueError, match="cerrada"):
        e.votar(3, [0])
    with pytest.raises(ValueError, match="cerrada"):
        e.confirmar(1, 0)
    with pytest.raises(ValueError, match="cerrada"):
        e.cerrar(1)
        
def test_la_encuesta_guarda_el_lugar():
    e = Encuesta(1, "Cena", OPCIONES, [2], ahora=AHORA, ubicacion="  UCA  ")
    assert e.ubicacion == "UCA"


def test_el_lugar_es_opcional():
    assert crear().ubicacion == ""


def test_lugar_demasiado_largo_falla():
    with pytest.raises(ValueError, match="120"):
        Encuesta(1, "Cena", OPCIONES, [2], ahora=AHORA, ubicacion="x" * 121)