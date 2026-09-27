from sqlalchemy import select, delete
from base_datos.configuracion import Session
from base_datos.grupo_tabla import GrupoTabla
from base_datos.grupo_miembros_tabla import GrupoMiembrosTabla
from base_datos.usuario_tabla import UsuarioTabla
from base_datos.solicitud_acciones import obtener_amigos_de_usuario


def guardar(grupo):
    with Session() as sesion:
        fila=GrupoTabla(creadorID=grupo.creadorID,nombre=grupo.nombre)
        sesion.add(fila)
        sesion.flush()
        for miembroID in grupo.miembrosIDs:
            sesion.add(GrupoMiembrosTabla(grupoID=fila.id,usuarioID=miembroID))
        sesion.commit()
        return fila.id

def borrar(grupoID,creadorID):
    with Session() as sesion:
        grupo=sesion.get(GrupoTabla,grupoID)
        if grupo is None or grupo.creadorID!=creadorID:
            return False
        sesion.execute(delete(GrupoMiembrosTabla).where(GrupoMiembrosTabla.grupoID==grupoID))
        sesion.delete(grupo)
        sesion.commit()
        return True

def obtenerDeUsuario(usuarioID):
    amigosIDs=set(obtener_amigos_de_usuario(usuarioID))
    with Session() as sesion:
        consulta=(
            select(GrupoTabla,UsuarioTabla)
            .join(GrupoMiembrosTabla,GrupoMiembrosTabla.grupoID==GrupoTabla.id)
            .join(UsuarioTabla,UsuarioTabla.id==GrupoMiembrosTabla.usuarioID)
            .where(GrupoTabla.creadorID==usuarioID)
            .order_by(GrupoTabla.nombre,UsuarioTabla.nombre)
        )
        grupos={}
        for grupo,miembro in sesion.execute(consulta).all():
            miembros=grupos.setdefault(grupo.id,(grupo,[]))[1]
            if miembro.id in amigosIDs:
                miembros.append(miembro)
        return list(grupos.values())
