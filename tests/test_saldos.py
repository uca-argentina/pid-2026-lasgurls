from decimal import Decimal
from dominio.saldos import calcularSaldos, simplificar, ajustarPagos
from dominio.gasto import Gasto


def gastoDe(g):
    return {"pagadorID":g.pagadorID,"monto":g.monto,"partes":[{"usuarioID":u,"monto":m} for u,m in g.reparto.items()]}


def test_unGastoEnPartesIgualesLeDebenAlQuePago():
    saldos=calcularSaldos([gastoDe(Gasto(1,8,8,"Pizza","3000",[8,9,55]))])

    assert saldos=={8:Decimal("2000.00"),9:Decimal("-1000.00"),55:Decimal("-1000.00")}
    assert simplificar(saldos)==[(9,8,Decimal("1000.00")),(55,8,Decimal("1000.00"))]


def test_lasDeudasCruzadasSeSimplifican():
    gastos=[gastoDe(Gasto(1,8,8,"Cena","2000",[8,9])),gastoDe(Gasto(1,9,9,"Taxi","1000",[8,9]))]

    assert simplificar(calcularSaldos(gastos))==[(9,8,Decimal("500.00"))]


def test_deudaEnCadena_seResuelveConMenosPagos():
    # 9 le debe 100 a 8 y 55 le debe 100 a 9: alcanza con que 55 le pague 100 a 8
    gastos=[
        gastoDe(Gasto(1,8,8,"A","200",[9,8],partes={9:"100",8:"100"})),
        gastoDe(Gasto(1,9,9,"B","200",[55,9],partes={55:"100",9:"100"})),
    ]

    assert simplificar(calcularSaldos(gastos))==[(55,8,Decimal("100.00"))]


def test_unPagoSaldaLaDeuda():
    gastos=[gastoDe(Gasto(1,8,8,"Pizza","3000",[8,9,55]))]
    pagos=[{"deudorID":9,"acreedorID":8,"monto":Decimal("1000.00")}]

    assert simplificar(calcularSaldos(gastos,pagos))==[(55,8,Decimal("1000.00"))]


def test_todoSaldadoNoDejaDeudas():
    gastos=[gastoDe(Gasto(1,8,8,"Pizza","3000",[8,9,55]))]
    pagos=[{"deudorID":9,"acreedorID":8,"monto":Decimal("1000.00")},{"deudorID":55,"acreedorID":8,"monto":Decimal("1000.00")}]

    assert simplificar(calcularSaldos(gastos,pagos))==[]


def test_sinGastosNoHayDeudas():
    assert simplificar(calcularSaldos([]))==[]


def test_losCentavosCierranExactos():
    saldos=calcularSaldos([gastoDe(Gasto(1,8,8,"Bebidas","1000",[8,9,55]))])

    assert sum(saldos.values())==Decimal("0.00")
    assert sum(monto for _,_,monto in simplificar(saldos))==Decimal("666.66")

def test_siSeBorraElGastoElPagoYaNoVale():
    pagos=[{"deudorID":9,"acreedorID":8,"monto":Decimal("500.00")}]

    assert ajustarPagos([],pagos)==[Decimal("0.00")]


def test_losPagosQueSiguenSiendoDeudaSeMantienen():
    gastos=[gastoDe(Gasto(1,8,8,"Pizza","3000",[8,9,55]))]
    pagos=[{"deudorID":9,"acreedorID":8,"monto":Decimal("1000.00")}]

    assert ajustarPagos(gastos,pagos)==[Decimal("1000.00")]


def test_unPagoMasGrandeQueLaDeudaQueQuedaSeAchica():
    gastos=[gastoDe(Gasto(1,8,8,"Coca","1000",[8,9]))]
    pagos=[{"deudorID":9,"acreedorID":8,"monto":Decimal("1500.00")}]

    assert ajustarPagos(gastos,pagos)==[Decimal("500.00")]


def test_despuesDeAjustarNoQuedanDeudasAlReves():
    gastos=[gastoDe(Gasto(1,8,8,"Coca","1000",[8,9]))]
    pagos=[{"deudorID":9,"acreedorID":8,"monto":Decimal("500.00")},{"deudorID":9,"acreedorID":8,"monto":Decimal("500.00")}]
    ajustados=[{**pago,"monto":monto} for pago,monto in zip(pagos,ajustarPagos(gastos,pagos))]

    assert simplificar(calcularSaldos(gastos,ajustados))==[]
