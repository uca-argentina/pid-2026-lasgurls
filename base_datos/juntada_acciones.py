from sqlalchemy import select, update, delete
from base_datos.configuracion import Session
from base_datos.juntada_tabla import JuntadaTabla
from base_datos.juntada_invitados_tabla import JuntadaInvitadosTabla
from base_datos.usuario_tabla import UsuarioTabla
from base_datos.categoria_tabla import CategoriaTabla
from base_datos.comentario_tabla import ComentarioTabla
from base_datos.notificacion_acciones import notificar, nombre_de_usuario, resaltar
from dominio.modulo_utilidades.rango_horario import ya_empezo
from dominio.juntada.recurrencia import texto_de_repeticion

RESPUESTAS = {"Si": ("confirmacion", "confirmó"), "No": ("rechazo", "no va a"), "Tal vez": ("tal_vez", "dijo tal vez a")}


def guardar(juntada):
    repeticion = juntada.recurrencia.frecuencia if juntada.recurrencia else None
    with Session() as sesion:
        filas = []
        for fecha in juntada.fechas:
            juntada_tabla = JuntadaTabla(
                organizador_id=juntada.organizador,
                titulo=juntada.titulo_juntada,
                fecha=fecha,
                hora_inicio=juntada.hora_inicio,
                hora_fin=juntada.hora_fin,
                categoria_id=juntada.categoria_id,
                visibilidad=juntada.visibilidad,
                repeticion=repeticion,
            )
            sesion.add(juntada_tabla)
            filas.append(juntada_tabla)
        sesion.flush()

        for juntada_tabla in filas:
            if repeticion:
                juntada_tabla.serie_id = filas[0].id
            for usuario_id in juntada.amigos_invitados:
                invitado = JuntadaInvitadosTabla(
                    juntada_id=juntada_tabla.id,
                    usuario_id=usuario_id,
                    estado="Pendiente",
                )
                sesion.add(invitado)

        sesion.commit()

        return filas[0].id

def obtener_por_id(juntada_id):
    with Session() as sesion:
        return sesion.get(JuntadaTabla, juntada_id)

def obtener_invitaciones_de_usuario(usuario_id):
    with Session() as sesion:
        consulta = select(JuntadaInvitadosTabla).where(
            JuntadaInvitadosTabla.usuario_id == usuario_id
        )
        return sesion.scalars(consulta).all()

def obtener_invitados_de_juntada(juntada_id):
    with Session() as sesion:
        consulta = select(JuntadaInvitadosTabla).where(
            JuntadaInvitadosTabla.juntada_id == juntada_id
        )
        return sesion.scalars(consulta).all()

def responder_invitacion(juntada_id, usuario_id, nueva_respuesta, ahora, toda_la_serie=False):
    if nueva_respuesta not in ("Si", "No", "Tal vez"):
        return False

    with Session() as sesion:
        juntadas_ids = _juntadas_de_la_serie(sesion, juntada_id) if toda_la_serie else [juntada_id]
        consulta = (
            update(JuntadaInvitadosTabla)
            .where(
                (JuntadaInvitadosTabla.juntada_id.in_(juntadas_ids)) &
                (JuntadaInvitadosTabla.usuario_id == usuario_id) &
                (JuntadaInvitadosTabla.estado.in_(["Tal vez","Pendiente"]))
            )
            .values(estado=nueva_respuesta)
        )

        resultado = sesion.execute(consulta)

        if resultado.rowcount > 0:
            juntada = sesion.get(JuntadaTabla, juntada_id)
            cuando = f"({texto_de_repeticion(juntada.repeticion, juntada.fecha)})" if toda_la_serie and juntada.serie_id else f"del {juntada.fecha:%d/%m}"
            tipo, verbo = RESPUESTAS[nueva_respuesta]
            texto = f"{nombre_de_usuario(sesion, usuario_id)} {verbo} {resaltar(juntada.titulo)} {cuando}"
            notificar(sesion, [juntada.organizador_id], tipo, texto, ahora, juntada)

        if resultado.rowcount > 0 and nueva_respuesta == "No":
            for id in juntadas_ids:
                _borrar_si_todos_rechazaron(sesion, id, ahora)

        sesion.commit()

        return resultado.rowcount > 0


def _juntadas_de_la_serie(sesion, juntada_id):
    juntada = sesion.get(JuntadaTabla, juntada_id)
    if juntada is None or juntada.serie_id is None:
        return [juntada_id]
    consulta = select(JuntadaTabla.id).where(JuntadaTabla.serie_id == juntada.serie_id)
    return sesion.scalars(consulta).all()


def cancelar_juntada(juntada_id, organizador_id, ahora):
    with Session() as sesion:
        juntada = sesion.get(JuntadaTabla, juntada_id)
        if juntada is None or juntada.organizador_id != organizador_id or ya_empezo(juntada.fecha, juntada.hora_inicio, ahora):
            return False
        consulta = select(JuntadaInvitadosTabla.usuario_id).where(
            JuntadaInvitadosTabla.juntada_id == juntada_id,
            JuntadaInvitadosTabla.estado != "No",
        )
        texto = f"{nombre_de_usuario(sesion, organizador_id)} canceló {resaltar(juntada.titulo)} del {juntada.fecha:%d/%m}"
        notificar(sesion, sesion.scalars(consulta).all(), "cancelacion", texto, ahora)
        _borrar_juntada(sesion, juntada_id)
        sesion.commit()
        return True


def darse_de_baja(juntada_id, usuario_id, ahora):
    with Session() as sesion:
        juntada = sesion.get(JuntadaTabla, juntada_id)
        if juntada is None or ya_empezo(juntada.fecha, juntada.hora_inicio, ahora):
            return False

        consulta = (
            update(JuntadaInvitadosTabla)
            .where(
                (JuntadaInvitadosTabla.juntada_id == juntada_id) &
                (JuntadaInvitadosTabla.usuario_id == usuario_id) &
                (JuntadaInvitadosTabla.estado == "Si")
            )
            .values(estado="No")
        )
        resultado = sesion.execute(consulta)

        if resultado.rowcount == 1:
            texto = f"{nombre_de_usuario(sesion, usuario_id)} se bajó de {resaltar(juntada.titulo)} del {juntada.fecha:%d/%m}"
            notificar(sesion, [juntada.organizador_id], "baja", texto, ahora, juntada)
            _borrar_si_todos_rechazaron(sesion, juntada_id, ahora)

        sesion.commit()
        return resultado.rowcount == 1


def _borrar_si_todos_rechazaron(sesion, juntada_id, ahora):
    consulta = select(JuntadaInvitadosTabla.estado).where(JuntadaInvitadosTabla.juntada_id == juntada_id)
    estados = sesion.scalars(consulta).all()

    if estados and all(estado == "No" for estado in estados):
        juntada = sesion.get(JuntadaTabla, juntada_id)
        texto = f"Nadie va a ir a {resaltar(juntada.titulo)} del {juntada.fecha:%d/%m}, así que se eliminó"
        notificar(sesion, [juntada.organizador_id], "eliminada", texto, ahora)
        _borrar_juntada(sesion, juntada_id)


def _borrar_juntada(sesion, juntada_id):
    sesion.execute(delete(ComentarioTabla).where(ComentarioTabla.juntadaID==juntada_id))
    sesion.execute(delete(JuntadaInvitadosTabla).where(JuntadaInvitadosTabla.juntada_id == juntada_id))
    sesion.execute(delete(JuntadaTabla).where(JuntadaTabla.id == juntada_id))


def obtener_organizadas(usuario_id, fecha, fecha_fin=None):
    with Session() as sesion:
        consulta = (
            select(JuntadaTabla, UsuarioTabla.nombre, JuntadaInvitadosTabla.estado, CategoriaTabla.nombre, CategoriaTabla.color)
            .outerjoin(CategoriaTabla, CategoriaTabla.id == JuntadaTabla.categoria_id)
            .outerjoin(JuntadaInvitadosTabla, JuntadaInvitadosTabla.juntada_id == JuntadaTabla.id)
            .outerjoin(UsuarioTabla, UsuarioTabla.id == JuntadaInvitadosTabla.usuario_id)
            .where(
                JuntadaTabla.organizador_id == usuario_id,
                JuntadaTabla.fecha.between(fecha, fecha_fin or fecha)
            )
            .order_by(JuntadaTabla.id, UsuarioTabla.nombre)
        )
        return sesion.execute(consulta).all()

def obtener_invitaciones_del_calendario(usuario_id, fecha, fecha_fin=None):
    with Session() as sesion:
        consulta=(
            select(JuntadaInvitadosTabla,JuntadaTabla,UsuarioTabla.nombre,CategoriaTabla.nombre,CategoriaTabla.color)
            .join(JuntadaTabla,JuntadaTabla.id==JuntadaInvitadosTabla.juntada_id)
            .join(UsuarioTabla,UsuarioTabla.id==JuntadaTabla.organizador_id)
            .outerjoin(CategoriaTabla,CategoriaTabla.id==JuntadaTabla.categoria_id)
            .where(
                JuntadaInvitadosTabla.usuario_id==usuario_id,
                JuntadaInvitadosTabla.estado!="No",
                (JuntadaTabla.fecha.between(fecha,fecha_fin or fecha)) |
                JuntadaInvitadosTabla.estado.in_(["Pendiente","Tal vez"])
            )
        )
        return sesion.execute(consulta).all()


def obtener_invitados_de_juntadas(juntadas_ids):
    if not juntadas_ids:
        return []
    with Session() as sesion:
        consulta = (
            select(JuntadaInvitadosTabla.juntada_id, UsuarioTabla.id, UsuarioTabla.nombre, JuntadaInvitadosTabla.estado)
            .join(UsuarioTabla, UsuarioTabla.id == JuntadaInvitadosTabla.usuario_id)
            .where(JuntadaInvitadosTabla.juntada_id.in_(juntadas_ids))
            .order_by(UsuarioTabla.nombre)
        )
        return sesion.execute(consulta).all()
