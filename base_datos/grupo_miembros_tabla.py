from sqlalchemy import Column, Integer, ForeignKey
from base_datos.usuario_tabla import Base


class GrupoMiembrosTabla(Base):
    __tablename__="grupo_miembros"

    id=Column(Integer,primary_key=True)
    grupoID=Column(Integer,ForeignKey("grupos.id"),nullable=False)
    usuarioID=Column(Integer,ForeignKey("usuarios.id"),nullable=False)
