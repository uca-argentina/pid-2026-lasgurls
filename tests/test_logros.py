import pytest
from datetime import datetime
from dominio.gamificacion.logros import Logros, Estilo, resumen_del_mes


def test_sinJuntadasNoHayLogros():
    logros=Logros([])

    assert logros.cumplidas==0
    assert logros.racha_actual==0
    assert logros.racha_maxima==0
    assert logros.palabra is None
    assert logros.desbloqueados()==set()


def test_laRachaCuentaLasCumplidasSeguidas():
    logros=Logros([True,True,True])

    assert logros.racha_actual==3
    assert logros.racha_maxima==3
    assert logros.tiene_fuego


def test_faltarCortaLaRachaPeroNoLaMejor():
    logros=Logros([True,True,True,True,False,True])

    assert logros.racha_actual==1
    assert logros.racha_maxima==4
    assert not logros.tiene_fuego


def test_palabraCumplida():
    logros=Logros([True,True,True,False])

    assert logros.palabra==75


def test_laPrimeraJuntadaDesbloqueaElColor():
    assert Logros([True]).desbloqueados()=={"color"}


def test_loDesbloqueadoNoSePierdeAunqueSeCorteLaRacha():
    logros=Logros([True,True,True,True,True,False])

    assert logros.racha_actual==0
    assert logros.desbloqueados()=={"color","forma","marco"}


def test_rachaDe10DesbloqueaTodo():
    assert Logros([True]*10).desbloqueados()=={"color","forma","marco","titulo"}


def test_elProximoDesbloqueoCuentaDesdeLaRachaActual():
    proximo=Logros([True,True,True,False,True]).proximo()

    assert proximo["clave"]=="marco"
    assert proximo["faltan"]==4


def test_sinJuntadasElProximoEsElColor():
    proximo=Logros([]).proximo()

    assert proximo["clave"]=="color"
    assert proximo["faltan"]==1


def test_conTodoDesbloqueadoNoHayProximo():
    assert Logros([True]*10).proximo() is None


def test_estiloVacioSiempreEsValido():
    estilo=Estilo("","","","",False,set())

    assert estilo.color is None
    assert estilo.forma is None
    assert not estilo.degrade


def test_estiloDesbloqueado():
    estilo=Estilo("#5b7fa6","estrella","dorado",None,False,{"color","forma","marco"})

    assert estilo.color=="#5b7fa6"
    assert estilo.forma=="estrella"
    assert estilo.marco=="dorado"


def test_noSePuedeUsarAlgoBloqueado():
    with pytest.raises(ValueError) as error:
        Estilo(None,"estrella",None,None,False,{"color"})
    assert str(error.value)=="Todavía no desbloqueaste: forma del avatar"


def test_noSePuedeUsarElDegradeSinDesbloquearlo():
    with pytest.raises(ValueError) as error:
        Estilo(None,None,None,None,True,{"color","forma","marco"})
    assert str(error.value)=="Todavía no desbloqueaste el nombre con degradé"


def test_noSePuedeUsarUnColorInventado():
    with pytest.raises(ValueError) as error:
        Estilo("red;background:url(x)",None,None,None,False,{"color"})
    assert str(error.value)=="Elegí un color de la lista"


def test_noSePuedeUsarUnTituloInventado():
    with pytest.raises(ValueError):
        Estilo(None,None,None,"Reina del universo",False,{"color","forma","marco","titulo"})


def test_resumenDelMes():
    juntadas=[
        {"inicio":datetime(2026,11,1,20),"organizada":True,"companeros":[(2,"Sofi"),(3,"Caro")]},
        {"inicio":datetime(2026,11,8,20),"organizada":False,"companeros":[(2,"Sofi")]},
        {"inicio":datetime(2026,10,30,20),"organizada":False,"companeros":[(3,"Caro")]},
    ]

    resumen=resumen_del_mes(juntadas,2026,11)

    assert resumen["cantidad"]==2
    assert resumen["organizadas"]==1
    assert resumen["personas"]==2
    assert resumen["mas_vista"]=={"nombre":"Sofi","veces":2}


def test_resumenDeUnMesSinJuntadas():
    resumen=resumen_del_mes([],2026,11)

    assert resumen["cantidad"]==0
    assert resumen["mas_vista"] is None
