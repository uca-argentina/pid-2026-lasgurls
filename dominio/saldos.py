from decimal import Decimal

cero=Decimal("0.00")


def calcularSaldos(gastos,pagos=()):
    """Saldo de cada persona: positivo = le deben, negativo = debe.
    gastos: [{"pagadorID","monto","partes":[{"usuarioID","monto"}]}]
    pagos: [{"deudorID","acreedorID","monto"}] (deudas ya saldadas)"""
    saldos={}
    for gasto in gastos:
        saldos[gasto["pagadorID"]]=saldos.get(gasto["pagadorID"],cero)+gasto["monto"]
        for parte in gasto["partes"]:
            saldos[parte["usuarioID"]]=saldos.get(parte["usuarioID"],cero)-parte["monto"]
    for pago in pagos:
        saldos[pago["deudorID"]]=saldos.get(pago["deudorID"],cero)+pago["monto"]
        saldos[pago["acreedorID"]]=saldos.get(pago["acreedorID"],cero)-pago["monto"]
    return saldos


def simplificar(saldos):
    """Devuelve [(deudorID,acreedorID,monto)] con la menor cantidad de pagos posible"""
    acreedores=sorted([[usuarioID,saldo] for usuarioID,saldo in saldos.items() if saldo>0],key=lambda x:(-x[1],x[0]))
    deudores=sorted([[usuarioID,-saldo] for usuarioID,saldo in saldos.items() if saldo<0],key=lambda x:(-x[1],x[0]))
    transferencias=[]
    while acreedores and deudores:
        acreedor=acreedores[0]
        deudor=deudores[0]
        monto=min(acreedor[1],deudor[1])
        transferencias.append((deudor[0],acreedor[0],monto))
        acreedor[1]-=monto
        deudor[1]-=monto
        if acreedor[1]==0:
            acreedores.pop(0)
        if deudor[1]==0:
            deudores.pop(0)
        acreedores.sort(key=lambda x:(-x[1],x[0]))
        deudores.sort(key=lambda x:(-x[1],x[0]))
    return transferencias