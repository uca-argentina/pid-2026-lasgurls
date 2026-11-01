import pytest
from decimal import Decimal
from dominio.gasto import Gasto


def test_gastoEnPartesIguales():
    gasto=Gasto(1,8,8," Pizzas ","3000",[8,9,55])

    assert gasto.descripcion=="Pizzas"
    assert gasto.monto==Decimal("3000.00")
    assert gasto.reparto=={8:Decimal("1000.00"),9:Decimal("1000.00"),55:Decimal("1000.00")}


def test_losCentavosQueSobranSeLosLlevaElPrimero():
    gasto=Gasto(1,8,8,"Bebidas","1000",[8,9,55])

    assert gasto.reparto=={8:Decimal("333.34"),9:Decimal("333.33"),55:Decimal("333.33")}
    assert sum(gasto.reparto.values())==gasto.monto


def test_montoConComaDecimal():
    gasto=Gasto(1,8,8,"Helado","1500,50",[8,9])

    assert gasto.monto==Decimal("1500.50")
    assert gasto.reparto=={8:Decimal("750.25"),9:Decimal("750.25")}


def test_elQuePagaPuedeNoEstarEnLaDivision():
    gasto=Gasto(1,8,9,"Regalo para caro","2000",[9,55])

    assert gasto.pagadorID==9
    assert 8 not in gasto.reparto


def test_gastoPersonalizado():
    gasto=Gasto(1,8,8,"Cena","5000",[8,9],partes={8:"3000",9:"2000"})

    assert gasto.reparto=={8:Decimal("3000.00"),9:Decimal("2000.00")}


def test_partesPersonalizadasQueNoSumanElTotalSonInvalidas():
    with pytest.raises(ValueError) as error:
        Gasto(1,8,8,"Cena","5000",[8,9],partes={8:"3000",9:"1000"})
    assert str(error.value)=="Las partes tienen que sumar el total del gasto"


def test_partesDeOtrasPersonasSonInvalidas():
    with pytest.raises(ValueError) as error:
        Gasto(1,8,8,"Cena","5000",[8,9],partes={8:"3000",55:"2000"})
    assert str(error.value)=="Las partes tienen que ser de las mismas personas que dividen el gasto"


def test_parteEnCeroEsInvalida():
    with pytest.raises(ValueError) as error:
        Gasto(1,8,8,"Cena","5000",[8,9],partes={8:"5000",9:"0"})
    assert str(error.value)=="Cada parte tiene que ser un monto mayor a 0 con hasta 2 decimales"


def test_gastoSinDescripcionEsInvalido():
    with pytest.raises(ValueError) as error:
        Gasto(1,8,8,"   ","1000",[8])
    assert str(error.value)=="El gasto tiene que tener una descripcion"


def test_descripcionDemasiadoLargaEsInvalida():
    with pytest.raises(ValueError) as error:
        Gasto(1,8,8,"x"*61,"1000",[8])
    assert str(error.value)=="La descripcion puede tener hasta 60 caracteres"


@pytest.mark.parametrize("monto,mensaje",[
    ("abc","El monto tiene que ser un numero"),
    ("","El monto tiene que ser un numero"),
    ("NaN","El monto tiene que ser un numero"),
    ("0","El monto tiene que ser mayor a 0"),
    ("-50","El monto tiene que ser mayor a 0"),
    ("10.555","El monto puede tener hasta 2 decimales"),
])
def test_montosInvalidos(monto,mensaje):
    with pytest.raises(ValueError) as error:
        Gasto(1,8,8,"Pizzas",monto,[8])
    assert str(error.value)==mensaje


def test_gastoSinPersonasEsInvalido():
    with pytest.raises(ValueError) as error:
        Gasto(1,8,8,"Pizzas","1000",[])
    assert str(error.value)=="Elegi al menos una persona para dividir el gasto"


def test_personasRepetidasSonInvalidas():
    with pytest.raises(ValueError) as error:
        Gasto(1,8,8,"Pizzas","1000",[8,8])
    assert str(error.value)=="Hay personas repetidas en la division"
