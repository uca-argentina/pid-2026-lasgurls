from sqlalchemy import select, delete
from base_datos.configuracion import Session
from base_datos.gasto_tabla import GastoTabla
from base_datos.gasto_partes_tabla import GastoPartesTabla
from base_datos.pago_deuda_tabla import PagoDeudaTabla
from dominio.saldos import calcularSaldos, simplificar, ajustarPagos
from base_datos.juntada_tabla import JuntadaTabla
from base_datos.juntada_invitados_tabla import JuntadaInvitadosTabla
from base_datos.usuario_tabla import UsuarioTabla
from base_datos.notificacion_acciones import participantes


def guardar(gasto,ahora):
    with Session() as sesion:
        juntada=sesion.get(JuntadaTabla,gasto.juntadaID)
        if juntada is None:
            return None
        personas=set(participantes(sesion,juntada))
        if gasto.creadorID not in personas or gasto.pagadorID not in personas or not set(gasto.participantesIDs)<=personas:
            return None
        fila=GastoTabla(
            juntadaID=gasto.juntadaID,
            creadorID=gasto.creadorID,
            pagadorID=gasto.pagadorID,
            descripcion=gasto.descripcion,
            monto=gasto.monto,
            fechaHora=ahora
        )
        sesion.add(fila)
        sesion.flush()
        for usuarioID,monto in gasto.reparto.items():
            sesion.add(GastoPartesTabla(gastoID=fila.id,usuarioID=usuarioID,monto=monto))
        sesion.commit()
        return fila.id

def borrar(gastoID,usuarioID):
    with Session() as sesion:
        gasto=sesion.get(GastoTabla,gastoID)
        if gasto is None or gasto.creadorID!=usuarioID:
            return False
        juntadaID=gasto.juntadaID
        sesion.execute(delete(GastoPartesTabla).where(GastoPartesTabla.gastoID==gastoID))
        sesion.delete(gasto)
        sesion.flush()
        ajustarPagosDeJuntada(sesion,juntadaID)
        sesion.commit()
        return True

def ajustarPagosDeJuntada(sesion,juntadaID):
    filas=sesion.scalars(select(PagoDeudaTabla).where(PagoDeudaTabla.juntadaID==juntadaID).order_by(PagoDeudaTabla.fechaHora,PagoDeudaTabla.id)).all()
    pagos=[{"deudorID":fila.deudorID,"acreedorID":fila.acreedorID,"monto":fila.monto} for fila in filas]
    for fila,monto in zip(filas,ajustarPagos(gastosDeJuntada(sesion,juntadaID),pagos)):
        if monto==0:
            sesion.delete(fila)
        elif monto!=fila.monto:
            fila.monto=monto

def borrarDeJuntada(sesion,juntadaID):
    gastosIDs=select(GastoTabla.id).where(GastoTabla.juntadaID==juntadaID)
    sesion.execute(delete(GastoPartesTabla).where(GastoPartesTabla.gastoID.in_(gastosIDs)))
    sesion.execute(delete(GastoTabla).where(GastoTabla.juntadaID==juntadaID))
    sesion.execute(delete(PagoDeudaTabla).where(PagoDeudaTabla.juntadaID==juntadaID))

def personasDeJuntadas(juntadasIDs):
    if not juntadasIDs:
        return {}
    with Session() as sesion:
        personas={}
        consultaOrganizadores=(
            select(JuntadaTabla.id,UsuarioTabla.id,UsuarioTabla.nombre)
            .join(UsuarioTabla,UsuarioTabla.id==JuntadaTabla.organizador_id)
            .where(JuntadaTabla.id.in_(juntadasIDs))
        )
        for juntadaID,usuarioID,nombre in sesion.execute(consultaOrganizadores).all():
            personas[juntadaID]=[{"id":usuarioID,"nombre":nombre}]
        consultaInvitados=(
            select(JuntadaInvitadosTabla.juntada_id,UsuarioTabla.id,UsuarioTabla.nombre)
            .join(UsuarioTabla,UsuarioTabla.id==JuntadaInvitadosTabla.usuario_id)
            .where(JuntadaInvitadosTabla.juntada_id.in_(juntadasIDs),JuntadaInvitadosTabla.estado!="No")
            .order_by(UsuarioTabla.nombre)
        )
        for juntadaID,usuarioID,nombre in sesion.execute(consultaInvitados).all():
            personas.setdefault(juntadaID,[]).append({"id":usuarioID,"nombre":nombre})
        return personas

def obtenerDeJuntadas(juntadasIDs):
    if not juntadasIDs:
        return []
    with Session() as sesion:
        consultaGastos=(
            select(GastoTabla,UsuarioTabla.nombre)
            .join(UsuarioTabla,UsuarioTabla.id==GastoTabla.pagadorID)
            .where(GastoTabla.juntadaID.in_(juntadasIDs))
            .order_by(GastoTabla.fechaHora,GastoTabla.id)
        )
        gastos=[]
        porID={}
        for fila,pagador in sesion.execute(consultaGastos).all():
            gasto={
                "id":fila.id,"juntadaID":fila.juntadaID,"creadorID":fila.creadorID,
                "pagadorID":fila.pagadorID,"pagador":pagador,
                "descripcion":fila.descripcion,"monto":fila.monto,"partes":[],
            }
            gastos.append(gasto)
            porID[fila.id]=gasto
        if not gastos:
            return []
        consultaPartes=(
            select(GastoPartesTabla,UsuarioTabla.nombre)
            .join(UsuarioTabla,UsuarioTabla.id==GastoPartesTabla.usuarioID)
            .where(GastoPartesTabla.gastoID.in_(list(porID)))
            .order_by(UsuarioTabla.nombre)
        )
        for parte,nombre in sesion.execute(consultaPartes).all():
            porID[parte.gastoID]["partes"].append({"usuarioID":parte.usuarioID,"nombre":nombre,"monto":parte.monto})
        return gastos
    
    
def gastosDeJuntada(sesion,juntadaID):
    gastos=[]
    gastosFilas=sesion.scalars(select(GastoTabla).where(GastoTabla.juntadaID==juntadaID)).all()
    for fila in gastosFilas:
        partes=sesion.scalars(select(GastoPartesTabla).where(GastoPartesTabla.gastoID==fila.id)).all()
        gastos.append({"pagadorID":fila.pagadorID,"monto":fila.monto,"partes":[{"usuarioID":parte.usuarioID,"monto":parte.monto} for parte in partes]})
    return gastos

def transferenciasPendientes(sesion,juntadaID):
    gastos=gastosDeJuntada(sesion,juntadaID)
    pagos=[
        {"deudorID":pago.deudorID,"acreedorID":pago.acreedorID,"monto":pago.monto}
        for pago in sesion.scalars(select(PagoDeudaTabla).where(PagoDeudaTabla.juntadaID==juntadaID)).all()
    ]
    return simplificar(calcularSaldos(gastos,pagos))

def saldosDeJuntadas(juntadasIDs):
    """{juntadaID: {"pendientes":[...],"saldadas":[...]}}"""
    if not juntadasIDs:
        return {}
    with Session() as sesion:
        resultado={juntadaID:{"pendientes":[],"saldadas":[]} for juntadaID in juntadasIDs}
        nombres=dict(sesion.execute(select(UsuarioTabla.id,UsuarioTabla.nombre)).all())
        for juntadaID in juntadasIDs:
            for deudorID,acreedorID,monto in transferenciasPendientes(sesion,juntadaID):
                resultado[juntadaID]["pendientes"].append({
                    "deudorID":deudorID,"deudor":nombres.get(deudorID,""),
                    "acreedorID":acreedorID,"acreedor":nombres.get(acreedorID,""),"monto":monto,
                })
        consultaPagos=select(PagoDeudaTabla).where(PagoDeudaTabla.juntadaID.in_(juntadasIDs)).order_by(PagoDeudaTabla.fechaHora,PagoDeudaTabla.id)
        for pago in sesion.scalars(consultaPagos).all():
            resultado[pago.juntadaID]["saldadas"].append({
                "deudorID":pago.deudorID,"deudor":nombres.get(pago.deudorID,""),
                "acreedorID":pago.acreedorID,"acreedor":nombres.get(pago.acreedorID,""),
                "monto":pago.monto,"fechaHora":pago.fechaHora,
            })
        return resultado

def saldarDeuda(juntadaID,usuarioID,deudorID,acreedorID,monto,ahora):
    """Devuelve None si se registró, o el motivo por el que no se pudo"""
    with Session() as sesion:
        if sesion.get(JuntadaTabla,juntadaID) is None:
            return "La juntada no existe"
        if usuarioID not in (deudorID,acreedorID):
            return "Solo quienes forman parte de la deuda pueden marcarla como saldada"
        if (deudorID,acreedorID,monto) not in transferenciasPendientes(sesion,juntadaID):
            return "Esa deuda cambió o ya estaba saldada"
        sesion.add(PagoDeudaTabla(
            juntadaID=juntadaID,deudorID=deudorID,acreedorID=acreedorID,
            registradoPorID=usuarioID,monto=monto,fechaHora=ahora
        ))
        sesion.commit()
        return None
