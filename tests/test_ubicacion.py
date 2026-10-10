import pytest
from datetime import datetime
from dominio.ubicacion import Ubicacion
from dominio.agenda.agenda import Agenda
from dominio.juntada.juntada import Juntada

AHORA=datetime(2026,9,1,12,0)


def test_ubicacionValida():
    ubicacion=Ubicacion("  Cafe Martinez, Av. Corrientes 1234 ")

    assert ubicacion.texto=="Cafe Martinez, Av. Corrientes 1234"


def test_ubicacionVaciaEsValida():
    assert Ubicacion("   ").texto==""
    assert Ubicacion(None).texto==""


def test_ubicacionDemasiadoLargaEsInvalida():
    with pytest.raises(ValueError) as error:
        Ubicacion("x"*121)
    assert str(error.value)=="El lugar puede tener hasta 120 caracteres"


def test_ubicacionDeExactamente120CaracteresEsValida():
    assert len(Ubicacion("x"*120).texto)==120


def test_enlaceAlMapa():
    ubicacion=Ubicacion("Cafe Martinez, Av. Corrientes 1234")

    assert ubicacion.enlaceMapa()=="https://www.google.com/maps/search/?api=1&query=Cafe+Martinez%2C+Av.+Corrientes+1234"


def test_sinUbicacionNoHayEnlace():
    assert Ubicacion("").enlaceMapa() is None


def test_agendaGuardaLaUbicacion():
    agenda=Agenda(1,"15/09/2026","Gimnasio","18:00","19:00",ahora=AHORA,ubicacion=" Smart Fit Palermo ")

    assert agenda.ubicacion=="Smart Fit Palermo"


def test_agendaSinUbicacionQuedaVacia():
    agenda=Agenda(1,"15/09/2026","Gimnasio","18:00","19:00",ahora=AHORA)

    assert agenda.ubicacion==""


def test_agendaConUbicacionDemasiadoLargaEsInvalida():
    with pytest.raises(ValueError) as error:
        Agenda(1,"15/09/2026","Gimnasio","18:00","19:00",ahora=AHORA,ubicacion="x"*121)
    assert str(error.value)=="El lugar puede tener hasta 120 caracteres"


def test_juntadaGuardaLaUbicacion():
    juntada=Juntada(1,"15/09/2026","Asado","20:00","23:00",[2],ahora=AHORA,ubicacion="Casa de Caro")

    assert juntada.ubicacion=="Casa de Caro"
