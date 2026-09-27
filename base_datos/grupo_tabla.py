from sqlalchemy import Column, Integer, String, ForeignKey
from base_datos.usuario_tabla import Base


class GrupoTabla(Base):
    __tablename__="grupos"

    id=Column(Integer,primary_key=True)
    creadorID=Column(Integer,ForeignKey("usuarios.id"),nullable=False)
    nombre=Column(String(30),nullable=False)
