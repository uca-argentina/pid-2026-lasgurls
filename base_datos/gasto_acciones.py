from sqlalchemy import select, delete
from base_datos.configuracion import Session
from base_datos.gasto_tabla import GastoTabla
from base_datos.gasto_partes_tabla import GastoPartesTabla
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
        sesion.execute(delete(GastoPartesTabla).where(GastoPartesTabla.gastoID==gastoID))
        sesion.delete(gasto)
        sesion.commit()
        return True

def borrarDeJuntada(sesion,juntadaID):
    gastosIDs=select(GastoTabla.id).where(GastoTabla.juntadaID==juntadaID)
    sesion.execute(delete(GastoPartesTabla).where(GastoPartesTabla.gastoID.in_(gastosIDs)))
    sesion.execute(delete(GastoTabla).where(GastoTabla.juntadaID==juntadaID))

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
