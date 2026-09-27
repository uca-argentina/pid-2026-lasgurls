from sqlalchemy import select
from base_datos.configuracion import Session
from base_datos.agenda_tabla import AgendaTabla
from base_datos.categoria_tabla import CategoriaTabla


def guardar(agenda):
    with Session() as sesion:
        agenda_tabla = AgendaTabla(
            usuario_id=agenda.usuario_id,
            titulo=agenda.titulo_reunion,
            fecha=agenda.fecha,
            hora_inicio=agenda.hora_inicio,
            hora_fin=agenda.hora_fin,
            categoria_id=agenda.categoria_id,
            visibilidad=agenda.visibilidad
        )
        sesion.add(agenda_tabla)
        sesion.commit()

def obtener_por_usuario(usuario_id, fecha=None, fecha_fin=None):
    with Session() as sesion:
        consulta = (
            select(AgendaTabla, CategoriaTabla.nombre, CategoriaTabla.color)
            .outerjoin(CategoriaTabla, CategoriaTabla.id == AgendaTabla.categoria_id)
            .where(AgendaTabla.usuario_id == usuario_id)
        )
        if fecha is not None:
            consulta=consulta.where(AgendaTabla.fecha.between(fecha,fecha_fin or fecha))
        return sesion.execute(consulta).all()
