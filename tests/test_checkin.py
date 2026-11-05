import pytest
from datetime import date, datetime, time, timedelta
from dominio.gamificacion.checkin import Posicion, generar_codigo, leer_codigo, se_puede_hacer_checkin, se_puede_habilitar, checkin_cerrado

SECRETO="secreto-de-prueba"
OBELISCO=Posicion(-34.60373,-58.38157,20)
AHORA=datetime(2026,11,4,21,0,0)


def test_elCodigoGeneradoSePuedeLeer():
    codigo=generar_codigo(SECRETO,42,OBELISCO,AHORA)

    juntada_id,posicion=leer_codigo(SECRETO,codigo,AHORA+timedelta(seconds=5))

    assert juntada_id==42
    assert posicion.latitud==pytest.approx(-34.60373)
    assert posicion.longitud==pytest.approx(-58.38157)


def test_elCodigoVenceALos30Segundos():
    codigo=generar_codigo(SECRETO,42,OBELISCO,AHORA)

    with pytest.raises(ValueError) as error:
        leer_codigo(SECRETO,codigo,AHORA+timedelta(seconds=31))
    assert str(error.value)=="El QR venció. Escaneá el que se ve ahora en la pantalla"


def test_unCodigoDelFuturoNoSirve():
    codigo=generar_codigo(SECRETO,42,OBELISCO,AHORA+timedelta(minutes=5))

    with pytest.raises(ValueError):
        leer_codigo(SECRETO,codigo,AHORA)


def test_unCodigoModificadoNoSirve():
    codigo=generar_codigo(SECRETO,42,OBELISCO,AHORA)
    trucho=codigo.replace(":42:",":43:")

    with pytest.raises(ValueError) as error:
        leer_codigo(SECRETO,trucho,AHORA)
    assert str(error.value)=="Ese QR no es de una juntada de JuntApp"


def test_unCodigoConOtroSecretoNoSirve():
    codigo=generar_codigo("otro-secreto",42,OBELISCO,AHORA)

    with pytest.raises(ValueError):
        leer_codigo(SECRETO,codigo,AHORA)


def test_unQrCualquieraNoSirve():
    with pytest.raises(ValueError) as error:
        leer_codigo(SECRETO,"https://www.google.com",AHORA)
    assert str(error.value)=="Ese QR no es de una juntada de JuntApp"


def test_dosPersonasEnElMismoBarEstanCerca():
    amiga=Posicion(-34.60410,-58.38160,30)

    assert OBELISCO.esta_cerca_de(amiga)


def test_alguienEnSuCasaNoEstaCerca():
    palermo=Posicion(-34.58800,-58.43000,15)

    assert not OBELISCO.esta_cerca_de(palermo)


def test_laToleranciaCreceConLaImprecisionDelGps():
    a_250_metros=Posicion(-34.60598,-58.38157,250)

    assert a_250_metros.distancia_a(OBELISCO)==pytest.approx(250,abs=5)
    assert a_250_metros.esta_cerca_de(OBELISCO)
    assert not Posicion(-34.60598,-58.38157,10).esta_cerca_de(Posicion(-34.60373,-58.38157,10))


def test_laToleranciaTieneUnMaximo():
    lejos=Posicion(-34.61000,-58.38157,4000)

    assert not lejos.esta_cerca_de(OBELISCO)


def test_sinUbicacionNoSePuede():
    with pytest.raises(ValueError) as error:
        Posicion(None,None,None)
    assert str(error.value)=="Necesitamos tu ubicación para hacer el check-in"


def test_ubicacionFueraDelMapaEsInvalida():
    with pytest.raises(ValueError):
        Posicion(120,-58,10)


def test_ubicacionMuyImprecisaEsInvalida():
    with pytest.raises(ValueError):
        Posicion(-34.6,-58.38,20000)


def test_elCheckinSeAbre15MinutosAntes():
    fecha=date(2026,11,4)

    assert not se_puede_hacer_checkin(fecha,time(21,0),time(23,0),datetime(2026,11,4,20,44))
    assert se_puede_hacer_checkin(fecha,time(21,0),time(23,0),datetime(2026,11,4,20,45))


def test_elCheckinSeCierraUnaHoraDespuesDelFin():
    fecha=date(2026,11,4)

    assert se_puede_hacer_checkin(fecha,time(21,0),time(23,0),datetime(2026,11,5,0,0))
    assert not se_puede_hacer_checkin(fecha,time(21,0),time(23,0),datetime(2026,11,5,0,1))


def test_elCheckinFuncionaEnJuntadasQuePasanLaMedianoche():
    fecha=date(2026,11,4)

    assert se_puede_hacer_checkin(fecha,time(23,0),time(2,0),datetime(2026,11,5,1,30))


def test_elOrganizadorPuedeHabilitarElCheckinDesde24HorasAntes():
    fecha=date(2026,11,5)

    assert not se_puede_habilitar(fecha,time(21,0),time(23,0),datetime(2026,11,4,20,59))
    assert se_puede_habilitar(fecha,time(21,0),time(23,0),datetime(2026,11,4,21,0))
    assert se_puede_habilitar(fecha,time(21,0),time(23,0),datetime(2026,11,5,19,0))


def test_despuesDelCierreNoSePuedeHabilitar():
    fecha=date(2026,11,5)

    assert not se_puede_habilitar(fecha,time(21,0),time(23,0),datetime(2026,11,6,0,1))
    assert checkin_cerrado(fecha,time(21,0),time(23,0),datetime(2026,11,6,0,1))
    assert not checkin_cerrado(fecha,time(21,0),time(23,0),datetime(2026,11,5,19,0))
