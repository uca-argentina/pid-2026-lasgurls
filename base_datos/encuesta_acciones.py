from sqlalchemy import select, delete, or_
from base_datos.configuracion import Session
from base_datos.encuesta_tabla import EncuestaTabla, EncuestaOpcionTabla, EncuestaInvitadoTabla, EncuestaVotoTabla, EncuestaOcultaTabla
from base_datos.juntada_tabla import JuntadaTabla
from base_datos.juntada_acciones import agregar_juntada
from base_datos.notificacion_acciones import notificar, nombre_de_usuario, resaltar
from base_datos.usuario_tabla import UsuarioTabla
from dominio.encuesta import Encuesta, OpcionEncuesta, ABIERTA
from dominio.juntada.juntada import Juntada


def crear(encuesta, ahora):
    """Guarda la encuesta (ya validada) con sus opciones e invitados y avisa a los invitados."""
    with Session() as sesion:
        fila = EncuestaTabla(
            organizador_id=encuesta.organizador, titulo=encuesta.titulo,
            estado=encuesta.estado, fecha_creacion=ahora, ubicacion=encuesta.ubicacion or None,
        )
        sesion.add(fila)
        sesion.flush()
        for opcion in encuesta.opciones:
            sesion.add(EncuestaOpcionTabla(
                encuesta_id=fila.id, fecha=opcion.fecha,
                hora_inicio=opcion.hora_inicio, hora_fin=opcion.hora_fin,
            ))
        for usuario_id in encuesta.invitados:
            sesion.add(EncuestaInvitadoTabla(encuesta_id=fila.id, usuario_id=usuario_id))
        texto = f"{nombre_de_usuario(sesion, encuesta.organizador)} armó la encuesta {resaltar(encuesta.titulo)}: votá cuándo te queda mejor"
        notificar(sesion, encuesta.invitados, "encuesta", texto, ahora, encuesta_id=fila.id)
        sesion.commit()
        return fila.id


def _cargar(sesion, encuesta_id):
    """Devuelve (fila, opciones_filas, dominio) o None si no existe. Los índices del dominio siguen el orden de opciones_filas."""
    fila = sesion.get(EncuestaTabla, encuesta_id)
    if fila is None:
        return None
    opciones = sesion.scalars(
        select(EncuestaOpcionTabla).where(EncuestaOpcionTabla.encuesta_id == encuesta_id).order_by(EncuestaOpcionTabla.id)
    ).all()
    invitados = sesion.scalars(
        select(EncuestaInvitadoTabla.usuario_id).where(EncuestaInvitadoTabla.encuesta_id == encuesta_id)
    ).all()
    indice_de = {opcion.id: i for i, opcion in enumerate(opciones)}
    votos = {}
    filas_votos = sesion.execute(
        select(EncuestaVotoTabla.usuario_id, EncuestaVotoTabla.opcion_id)
        .where(EncuestaVotoTabla.opcion_id.in_(indice_de.keys()))
    ).all()
    for usuario_id, opcion_id in filas_votos:
        votos.setdefault(usuario_id, set()).add(indice_de[opcion_id])
    dominio = Encuesta.desde_datos(
        fila.organizador_id, fila.titulo,
        [OpcionEncuesta.desde_datos(o.fecha, o.hora_inicio, o.hora_fin) for o in opciones],
        invitados, votos, fila.estado, fila.ubicacion,
    )
    return fila, opciones, dominio


def votar(encuesta_id, usuario_id, opciones_ids, ahora):
    """Reemplaza el voto del usuario. Lanza ValueError si no corresponde."""
    with Session() as sesion:
        cargada = _cargar(sesion, encuesta_id)
        if cargada is None:
            raise ValueError("La encuesta no existe")
        _, opciones, dominio = cargada
        ids = [o.id for o in opciones]
        if any(id not in ids for id in opciones_ids):
            raise ValueError("Opción inexistente")
        dominio.votar(usuario_id, [ids.index(id) for id in opciones_ids])
        sesion.execute(delete(EncuestaVotoTabla).where(
            EncuestaVotoTabla.usuario_id == usuario_id, EncuestaVotoTabla.opcion_id.in_(ids)))
        for id in set(opciones_ids):
            sesion.add(EncuestaVotoTabla(opcion_id=id, usuario_id=usuario_id))
        if usuario_id != dominio.organizador:
            texto = f"{nombre_de_usuario(sesion, usuario_id)} votó en la encuesta {resaltar(dominio.titulo)}"
            notificar(sesion, [dominio.organizador], "voto", texto, ahora, encuesta_id=encuesta_id)
        sesion.commit()


def cerrar(encuesta_id, usuario_id, ahora):
    """Cierra la encuesta sin elegir fecha: no se hace la juntada, y se avisa a los invitados."""
    with Session() as sesion:
        cargada = _cargar(sesion, encuesta_id)
        if cargada is None:
            raise ValueError("La encuesta no existe")
        fila, _, dominio = cargada
        dominio.cerrar(usuario_id)
        fila.estado = dominio.estado
        texto = (f"{nombre_de_usuario(sesion, dominio.organizador)} cerró la encuesta {resaltar(dominio.titulo)} "
                 f"sin elegir fecha: la juntada se cancela")
        notificar(sesion, dominio.invitados, "cancelacion", texto, ahora, encuesta_id=encuesta_id)
        sesion.commit()


def confirmar(encuesta_id, usuario_id, opcion_id, ahora):
    """Todo o nada: crea la juntada con los invitados, cierra la encuesta y avisa. Devuelve el id de la juntada."""
    with Session() as sesion:
        cargada = _cargar(sesion, encuesta_id)
        if cargada is None:
            raise ValueError("La encuesta no existe")
        fila, opciones, dominio = cargada
        ids = [o.id for o in opciones]
        if opcion_id not in ids:
            raise ValueError("Opción inexistente")
        elegida = dominio.confirmar(usuario_id, ids.index(opcion_id))
        juntada = Juntada(
            organizador=dominio.organizador,
            fecha=elegida.fecha.strftime("%d/%m/%Y"),
            titulo_juntada=dominio.titulo,
            hora_inicio=elegida.hora_inicio.strftime("%H:%M"),
            hora_fin=elegida.hora_fin.strftime("%H:%M"),
            amigos_invitados=dominio.invitados,
            ahora=ahora,
            ubicacion=dominio.ubicacion,
        )
        juntada_fila = agregar_juntada(sesion, juntada)[0]
        fila.estado = dominio.estado
        fila.juntada_id = juntada_fila.id
        texto = (f"{nombre_de_usuario(sesion, dominio.organizador)} confirmó {resaltar(dominio.titulo)} "
                 f"para el {elegida.fecha:%d/%m} a las {elegida.hora_inicio:%H:%M}")
        notificar(sesion, dominio.invitados, "encuesta_confirmada", texto, ahora, juntada_fila)
        sesion.commit()
        return juntada_fila.id


def obtener_detalle(encuesta_id, usuario_id):
    """Datos para mostrar la encuesta, o None si no existe o el usuario no participa."""
    with Session() as sesion:
        cargada = _cargar(sesion, encuesta_id)
        if cargada is None:
            return None
        fila, opciones, dominio = cargada
        if usuario_id != dominio.organizador and usuario_id not in dominio.invitados:
            return None
        participantes = [dominio.organizador] + dominio.invitados
        nombres = dict(sesion.execute(
            select(UsuarioTabla.id, UsuarioTabla.nombre).where(UsuarioTabla.id.in_(participantes))).all())
        ganadoras = dominio.opciones_ganadoras()
        return {
            "id": fila.id,
            "titulo": dominio.titulo,
            "estado": dominio.estado,
            "juntada_id": fila.juntada_id,
            "ubicacion": dominio.ubicacion,
            "organizador_id": dominio.organizador,
            "organizador": nombres.get(dominio.organizador, ""),
            "es_organizador": usuario_id == dominio.organizador,
            "participantes": [{"id": u, "nombre": nombres.get(u, ""), "voto": u in dominio.votos} for u in participantes],
            "opciones": [{
                "id": opcion.id,
                "fecha": opcion.fecha,
                "hora_inicio": opcion.hora_inicio,
                "hora_fin": opcion.hora_fin,
                "votos": dominio.cantidad_de_votos(i),
                "votantes": [nombres.get(u, "") for u in participantes if i in dominio.votos.get(u, set())],
                "marcada": i in dominio.votos.get(usuario_id, set()),
                "ganadora": i in ganadoras,
            } for i, opcion in enumerate(opciones)],
        }


def obtener_de_usuario(usuario_id):
    with Session() as sesion:
        ocultas = select(EncuestaOcultaTabla.encuesta_id).where(EncuestaOcultaTabla.usuario_id == usuario_id)
        consulta = (
            select(EncuestaTabla.id)
            .where(
                or_(
                    EncuestaTabla.organizador_id == usuario_id,
                    EncuestaTabla.id.in_(select(EncuestaInvitadoTabla.encuesta_id).where(EncuestaInvitadoTabla.usuario_id == usuario_id)),
                ),
                EncuestaTabla.id.not_in(ocultas),
            )
            .order_by(EncuestaTabla.fecha_creacion.desc(), EncuestaTabla.id.desc())
        )
        resumenes = [_resumen(sesion, encuesta_id, usuario_id) for encuesta_id in sesion.scalars(consulta).all()]
    orden = {"votar": 0, "abierta": 1, "confirmada": 2, "cancelada": 3}
    resumenes.sort(key=lambda resumen: orden[resumen["situacion"]])
    return resumenes


def _resumen(sesion, encuesta_id, usuario_id):
    fila, opciones, dominio = _cargar(sesion, encuesta_id)
    participantes = [dominio.organizador] + dominio.invitados
    nombre_organizador = sesion.get(UsuarioTabla, dominio.organizador)
    juntada = sesion.get(JuntadaTabla, fila.juntada_id) if fila.juntada_id else None
    if dominio.estado == ABIERTA:
        situacion = "abierta" if usuario_id in dominio.votos else "votar"
    else:
        situacion = "confirmada" if juntada is not None else "cancelada"
    return {
        "id": fila.id,
        "titulo": dominio.titulo,
        "situacion": situacion,
        "organizador": nombre_organizador.nombre if nombre_organizador else "",
        "es_organizador": usuario_id == dominio.organizador,
        "ubicacion": dominio.ubicacion,
        "participantes": len(participantes),
        "votaron": sum(1 for usuario in participantes if usuario in dominio.votos),
        "cantidad_opciones": len(opciones),
        "ganadoras": [
            {"fecha": opciones[i].fecha, "hora_inicio": opciones[i].hora_inicio, "hora_fin": opciones[i].hora_fin,
             "votos": dominio.cantidad_de_votos(i)}
            for i in dominio.opciones_ganadoras()
        ],
        "juntada": juntada,
        "juntada_id": fila.juntada_id,
    }


def ocultar(encuesta_id, usuario_id):
    with Session() as sesion:
        cargada = _cargar(sesion, encuesta_id)
        if cargada is None:
            raise ValueError("La encuesta no existe")
        fila, _, dominio = cargada
        if usuario_id != dominio.organizador and usuario_id not in dominio.invitados:
            raise ValueError("No participás de esta encuesta")
        if dominio.estado == ABIERTA:
            raise ValueError("No podés borrar una encuesta que todavía está abierta")
        ya_oculta = sesion.scalars(select(EncuestaOcultaTabla).where(
            EncuestaOcultaTabla.encuesta_id == encuesta_id, EncuestaOcultaTabla.usuario_id == usuario_id)).first()
        if ya_oculta is None:
            sesion.add(EncuestaOcultaTabla(encuesta_id=encuesta_id, usuario_id=usuario_id))
        sesion.commit()
