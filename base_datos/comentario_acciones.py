from sqlalchemy import select
from base_datos.configuracion import Session
from base_datos.comentario_tabla import ComentarioTabla
from base_datos.juntada_tabla import JuntadaTabla
from base_datos.juntada_invitados_tabla import JuntadaInvitadosTabla
from base_datos.usuario_tabla import UsuarioTabla
from base_datos.notificacion_acciones import notificar, nombre_de_usuario, participantes, resaltar


def guardar(comentario,ahora):
    with Session() as sesion:
        if not puedeComentar(sesion,comentario.juntadaID,comentario.usuarioID):
            return False
        fila=ComentarioTabla(
            juntadaID=comentario.juntadaID,
            usuarioID=comentario.usuarioID,
            texto=comentario.texto,
            fechaHora=ahora
        )
        sesion.add(fila)
        juntada=sesion.get(JuntadaTabla,comentario.juntadaID)
        destinatarios=[usuarioID for usuarioID in participantes(sesion,juntada) if usuarioID!=comentario.usuarioID]
        resumen=comentario.texto.replace("*","")
        resumen=resumen if len(resumen)<=80 else resumen[:80]+"…"
        texto=f"{nombre_de_usuario(sesion,comentario.usuarioID)} comentó en {resaltar(juntada.titulo)}: «{resumen}»"
        notificar(sesion,destinatarios,"comentario",texto,ahora,juntada)
        sesion.commit()
        return True

def puedeComentar(sesion,juntadaID,usuarioID):
    juntada=sesion.get(JuntadaTabla,juntadaID)
    if juntada is None:
        return False
    if juntada.organizador_id==usuarioID:
        return True
    consulta=select(JuntadaInvitadosTabla).where(
        JuntadaInvitadosTabla.juntada_id==juntadaID,
        JuntadaInvitadosTabla.usuario_id==usuarioID,
        JuntadaInvitadosTabla.estado!="No"
    )
    return sesion.scalars(consulta).first() is not None

def obtenerDeJuntadas(juntadasIDs):
    if not juntadasIDs:
        return []
    with Session() as sesion:
        consulta=(
            select(ComentarioTabla,UsuarioTabla.nombre)
            .join(UsuarioTabla,UsuarioTabla.id==ComentarioTabla.usuarioID)
            .where(ComentarioTabla.juntadaID.in_(juntadasIDs))
            .order_by(ComentarioTabla.fechaHora,ComentarioTabla.id)
        )
        return sesion.execute(consulta).all()
