from sqlalchemy import select
from base_datos.configuracion import Session
from base_datos.juntada_tabla import JuntadaTabla
from base_datos.juntada_invitados_tabla import JuntadaInvitadosTabla
from base_datos.usuario_tabla import UsuarioTabla
from base_datos.asistencia_tabla import AsistenciaTabla
from base_datos.estilo_perfil_tabla import EstiloPerfilTabla
from dominio.modulo_utilidades.rango_horario import rango_del_evento
from dominio.gamificacion.checkin import se_puede_hacer_checkin


def _ya_asistio(sesion, juntada_id, usuario_id):
    consulta = select(AsistenciaTabla.id).where(
        AsistenciaTabla.juntada_id == juntada_id,
        AsistenciaTabla.usuario_id == usuario_id,
    )
    return sesion.scalars(consulta).first() is not None


def registrar_checkin(juntada_id, usuario_id, ahora):
    with Session() as sesion:
        juntada = sesion.get(JuntadaTabla, juntada_id)
        if juntada is None:
            raise ValueError("No encontramos esa juntada")
        if juntada.organizador_id == usuario_id:
            raise ValueError("Organizás esta juntada: mostrale el QR a los demás")
        consulta = select(JuntadaInvitadosTabla).where(
            JuntadaInvitadosTabla.juntada_id == juntada_id,
            JuntadaInvitadosTabla.usuario_id == usuario_id,
        )
        invitacion = sesion.scalars(consulta).first()
        if invitacion is None or invitacion.estado == "No":
            raise ValueError("No estás en la lista de esta juntada")
        if not se_puede_hacer_checkin(juntada.fecha, juntada.hora_inicio, juntada.hora_fin, ahora):
            raise ValueError("El check-in solo se puede hacer durante la juntada")
        titulo = juntada.titulo
        if _ya_asistio(sesion, juntada_id, usuario_id):
            return titulo
        invitacion.estado = "Si"
        sesion.add(AsistenciaTabla(juntada_id=juntada_id, usuario_id=usuario_id, fecha_hora=ahora))
        if not _ya_asistio(sesion, juntada_id, juntada.organizador_id):
            sesion.add(AsistenciaTabla(juntada_id=juntada_id, usuario_id=juntada.organizador_id, fecha_hora=ahora))
        sesion.commit()
        return titulo


def presentes(juntada_id):
    with Session() as sesion:
        consulta = (
            select(UsuarioTabla.id, UsuarioTabla.nombre)
            .join(AsistenciaTabla, AsistenciaTabla.usuario_id == UsuarioTabla.id)
            .where(AsistenciaTabla.juntada_id == juntada_id)
            .order_by(AsistenciaTabla.fecha_hora, UsuarioTabla.nombre)
        )
        return sesion.execute(consulta).all()


def juntadas_con_asistencia(usuario_id, juntadas_ids):
    if not juntadas_ids:
        return set()
    with Session() as sesion:
        consulta = select(AsistenciaTabla.juntada_id).where(
            AsistenciaTabla.usuario_id == usuario_id,
            AsistenciaTabla.juntada_id.in_(juntadas_ids),
        )
        return set(sesion.scalars(consulta).all())


def historiales(usuarios_ids, ahora):
    usuarios_ids = list(set(usuarios_ids))
    if not usuarios_ids:
        return {}
    with Session() as sesion:
        compromisos = {usuario_id: {} for usuario_id in usuarios_ids}
        consulta = select(JuntadaTabla).where(JuntadaTabla.organizador_id.in_(usuarios_ids))
        for juntada in sesion.scalars(consulta).all():
            compromisos[juntada.organizador_id][juntada.id] = (juntada, True)
        consulta = (
            select(JuntadaInvitadosTabla.usuario_id, JuntadaTabla)
            .join(JuntadaTabla, JuntadaTabla.id == JuntadaInvitadosTabla.juntada_id)
            .where(JuntadaInvitadosTabla.usuario_id.in_(usuarios_ids), JuntadaInvitadosTabla.estado == "Si")
        )
        for usuario_id, juntada in sesion.execute(consulta).all():
            compromisos[usuario_id][juntada.id] = (juntada, False)

        juntadas_ids = {juntada_id for por_juntada in compromisos.values() for juntada_id in por_juntada}
        asistentes = {}
        if juntadas_ids:
            consulta = (
                select(AsistenciaTabla.juntada_id, UsuarioTabla.id, UsuarioTabla.nombre)
                .join(UsuarioTabla, UsuarioTabla.id == AsistenciaTabla.usuario_id)
                .where(AsistenciaTabla.juntada_id.in_(juntadas_ids))
            )
            for juntada_id, usuario_id, nombre in sesion.execute(consulta).all():
                asistentes.setdefault(juntada_id, {})[usuario_id] = nombre

    resultado = {}
    for usuario_id, por_juntada in compromisos.items():
        historial = []
        for juntada, organizada in por_juntada.values():
            presentes_de_juntada = asistentes.get(juntada.id, {})
            if not presentes_de_juntada:
                continue
            inicio, fin = rango_del_evento(juntada.fecha, juntada.hora_inicio, juntada.hora_fin)
            cumplio = usuario_id in presentes_de_juntada
            if fin > ahora and not cumplio:
                continue
            historial.append({
                "inicio": inicio,
                "cumplio": cumplio,
                "organizada": organizada,
                "companeros": [(otro_id, nombre) for otro_id, nombre in presentes_de_juntada.items() if otro_id != usuario_id],
            })
        historial.sort(key=lambda item: item["inicio"])
        resultado[usuario_id] = historial
    return resultado


def estilos_de(usuarios_ids):
    usuarios_ids = list(set(usuarios_ids))
    if not usuarios_ids:
        return {}
    with Session() as sesion:
        consulta = select(EstiloPerfilTabla).where(EstiloPerfilTabla.usuario_id.in_(usuarios_ids))
        return {estilo.usuario_id: estilo for estilo in sesion.scalars(consulta).all()}


def guardar_estilo(usuario_id, estilo):
    with Session() as sesion:
        fila = sesion.get(EstiloPerfilTabla, usuario_id)
        if fila is None:
            fila = EstiloPerfilTabla(usuario_id=usuario_id)
            sesion.add(fila)
        fila.color = estilo.color
        fila.forma = estilo.forma
        fila.marco = estilo.marco
        fila.titulo = estilo.titulo
        fila.degrade = estilo.degrade
        sesion.commit()
