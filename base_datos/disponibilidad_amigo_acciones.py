from datetime import timedelta
from sqlalchemy import select, union_all
from base_datos.configuracion import Session
from base_datos.agenda_tabla import AgendaTabla
from base_datos.juntada_tabla import JuntadaTabla
from base_datos.juntada_invitados_tabla import JuntadaInvitadosTabla
from base_datos.solicitud_acciones import obtener_amigos_de_usuario
from dominio.modulo_utilidades.rango_horario import rango_del_evento


def obtener_disponibilidad(usuario_solicitante_id, amigos_ids, desde, hasta):
    if not set(amigos_ids).issubset(obtener_amigos_de_usuario(usuario_solicitante_id)):
        raise ValueError("Solo podés ver la disponibilidad de tus amigos")

    usuarios_ids = [usuario_solicitante_id, *amigos_ids]
    fechas = (desde - timedelta(days=1), hasta)

    agenda = select(
        AgendaTabla.usuario_id, AgendaTabla.fecha, AgendaTabla.hora_inicio, AgendaTabla.hora_fin
    ).where(AgendaTabla.usuario_id.in_(usuarios_ids), AgendaTabla.fecha.between(*fechas))

    organizadas = select(
        JuntadaTabla.organizador_id, JuntadaTabla.fecha, JuntadaTabla.hora_inicio, JuntadaTabla.hora_fin
    ).where(JuntadaTabla.organizador_id.in_(usuarios_ids), JuntadaTabla.fecha.between(*fechas))

    confirmadas = (
        select(JuntadaInvitadosTabla.usuario_id, JuntadaTabla.fecha, JuntadaTabla.hora_inicio, JuntadaTabla.hora_fin)
        .join(JuntadaTabla, JuntadaTabla.id == JuntadaInvitadosTabla.juntada_id)
        .where(
            JuntadaInvitadosTabla.usuario_id.in_(usuarios_ids),
            JuntadaInvitadosTabla.estado == "Si",
            JuntadaTabla.fecha.between(*fechas),
        )
    )

    with Session() as sesion:
        filas = sesion.execute(union_all(agenda, organizadas, confirmadas)).all()

    ocupados = {usuario_id: [] for usuario_id in usuarios_ids}
    for usuario_id, fecha, hora_inicio, hora_fin in filas:
        ocupados[usuario_id].append(rango_del_evento(fecha, hora_inicio, hora_fin))
    return ocupados
