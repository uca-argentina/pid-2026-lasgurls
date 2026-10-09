from sqlalchemy import select, update
from base_datos.configuracion import Session
from base_datos.notificacion_tabla import NotificacionTabla
from base_datos.juntada_invitados_tabla import JuntadaInvitadosTabla
from base_datos.usuario_tabla import UsuarioTabla

MAXIMO_TEXTO = 255


def notificar(sesion, usuarios_ids, tipo, texto, ahora, juntada=None):
    for usuario_id in set(usuarios_ids):
        sesion.add(NotificacionTabla(
            usuario_id=usuario_id,
            tipo=tipo,
            texto=texto[:MAXIMO_TEXTO],
            juntada_id=juntada.id if juntada is not None else None,
            fecha_juntada=juntada.fecha if juntada is not None else None,
            fecha_hora=ahora,
        ))


def resaltar(texto):
    return f"**{texto.replace('*', '')}**"


def nombre_de_usuario(sesion, usuario_id):
    usuario = sesion.get(UsuarioTabla, usuario_id)
    return resaltar(usuario.nombre) if usuario is not None else "Alguien"


def participantes(sesion, juntada):
    consulta = select(JuntadaInvitadosTabla.usuario_id).where(
        JuntadaInvitadosTabla.juntada_id == juntada.id,
        JuntadaInvitadosTabla.estado != "No",
    )
    return [juntada.organizador_id] + list(sesion.scalars(consulta).all())


def obtener_no_leidas(usuario_id):
    with Session() as sesion:
        consulta = (
            select(NotificacionTabla)
            .where(NotificacionTabla.usuario_id == usuario_id, NotificacionTabla.leida.is_(False))
            .order_by(NotificacionTabla.fecha_hora.desc(), NotificacionTabla.id.desc())
        )
        return sesion.scalars(consulta).all()


def juntadas_reprogramadas(usuario_id, juntadas_ids):
    if not juntadas_ids:
        return set()
    with Session() as sesion:
        consulta = select(NotificacionTabla.juntada_id).where(
            NotificacionTabla.usuario_id == usuario_id,
            NotificacionTabla.tipo == "reprogramacion",
            NotificacionTabla.juntada_id.in_(juntadas_ids),
        )
        return set(sesion.scalars(consulta).all())


def marcar_leidas_de_juntadas(sesion, usuario_id, juntadas_ids, tipo):
    sesion.execute(
        update(NotificacionTabla)
        .where(
            NotificacionTabla.usuario_id == usuario_id,
            NotificacionTabla.juntada_id.in_(juntadas_ids),
            NotificacionTabla.tipo == tipo,
            NotificacionTabla.leida.is_(False),
        )
        .values(leida=True)
    )


def marcar_leidas(usuario_id):
    with Session() as sesion:
        sesion.execute(
            update(NotificacionTabla)
            .where(NotificacionTabla.usuario_id == usuario_id, NotificacionTabla.leida.is_(False))
            .values(leida=True)
        )
        sesion.commit()
