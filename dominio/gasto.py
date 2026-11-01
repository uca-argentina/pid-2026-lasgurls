from decimal import Decimal, InvalidOperation

largoMaximo=60
centavo=Decimal("0.01")


def leerMonto(valor):
    try:
        monto=Decimal(str(valor).strip().replace(",","."))
    except InvalidOperation:
        raise ValueError("El monto tiene que ser un numero")
    if not monto.is_finite():
        raise ValueError("El monto tiene que ser un numero")
    if monto<=0:
        raise ValueError("El monto tiene que ser mayor a 0")
    if monto!=monto.quantize(centavo):
        raise ValueError("El monto puede tener hasta 2 decimales")
    return monto.quantize(centavo)


class Gasto:
    def __init__(self,juntadaID,creadorID,pagadorID,descripcion,monto,participantesIDs,partes=None):
        self.juntadaID=juntadaID
        self.creadorID=creadorID
        self.pagadorID=pagadorID
        self.descripcion=(descripcion or "").strip()
        self.validarDescripcion()
        self.monto=leerMonto(monto)
        self.participantesIDs=list(participantesIDs or [])
        self.validarParticipantes()
        if partes is None:
            self.reparto=self.repartirEnPartesIguales()
        else:
            self.reparto=self.repartirPersonalizado(partes)

    def validarDescripcion(self):
        if not self.descripcion:
            raise ValueError("El gasto tiene que tener una descripcion")
        if len(self.descripcion)>largoMaximo:
            raise ValueError(f"La descripcion puede tener hasta {largoMaximo} caracteres")

    def validarParticipantes(self):
        if not self.participantesIDs:
            raise ValueError("Elegi al menos una persona para dividir el gasto")
        if len(set(self.participantesIDs))!=len(self.participantesIDs):
            raise ValueError("Hay personas repetidas en la division")

    def repartirEnPartesIguales(self):
        cantidad=len(self.participantesIDs)
        parte=(self.monto/cantidad).quantize(centavo,rounding="ROUND_DOWN")
        reparto={usuarioID:parte for usuarioID in self.participantesIDs}
        reparto[self.participantesIDs[0]]+=self.monto-parte*cantidad
        return reparto

    def repartirPersonalizado(self,partes):
        if set(partes)!=set(self.participantesIDs):
            raise ValueError("Las partes tienen que ser de las mismas personas que dividen el gasto")
        reparto={}
        for usuarioID in self.participantesIDs:
            try:
                reparto[usuarioID]=leerMonto(partes[usuarioID])
            except ValueError:
                raise ValueError("Cada parte tiene que ser un monto mayor a 0 con hasta 2 decimales")
        if sum(reparto.values())!=self.monto:
            raise ValueError("Las partes tienen que sumar el total del gasto")
        return reparto
