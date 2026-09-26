from sqlalchemy import select, update, or_
from base_datos.configuracion import Session
from base_datos.categoria_tabla import CategoriaTabla
from base_datos.agenda_tabla import AgendaTabla
from base_datos.juntada_tabla import JuntadaTabla


def _de_fabrica_o_del_usuario(usuario_id):
    return or_(CategoriaTabla.usuario_id.is_(None), CategoriaTabla.usuario_id == usuario_id)


def obtener_categorias(usuario_id):
    with Session() as sesion:
        consulta = (
            select(CategoriaTabla)
            .where(_de_fabrica_o_del_usuario(usuario_id))
            .order_by(CategoriaTabla.usuario_id.is_not(None), CategoriaTabla.id)
        )
        return sesion.scalars(consulta).all()


def crear_categoria(usuario_id, categoria):
    with Session() as sesion:
        nombres = sesion.scalars(select(CategoriaTabla.nombre).where(_de_fabrica_o_del_usuario(usuario_id))).all()
        if any(categoria.se_llama_igual_que(nombre) for nombre in nombres):
            raise ValueError("Ya tenés una categoría con ese nombre")
        fila = CategoriaTabla(usuario_id=usuario_id, nombre=categoria.nombre, color=categoria.color)
        sesion.add(fila)
        sesion.commit()
        return {"id": fila.id, "nombre": fila.nombre, "color": fila.color}


def borrar_categoria(categoria_id, usuario_id):
    with Session() as sesion:
        fila = sesion.get(CategoriaTabla, categoria_id)
        if fila is None or fila.usuario_id != usuario_id:
            return False
        for tabla in (AgendaTabla, JuntadaTabla):
            sesion.execute(update(tabla).where(tabla.categoria_id == categoria_id).values(categoria_id=None))
        sesion.delete(fila)
        sesion.commit()
        return True


def puede_usar_categoria(categoria_id, usuario_id):
    with Session() as sesion:
        fila = sesion.get(CategoriaTabla, categoria_id)
        return fila is not None and fila.usuario_id in (None, usuario_id)
