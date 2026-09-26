from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from base_datos.usuario_tabla import Base


class ComentarioTabla(Base):
    __tablename__="comentarios"

    id=Column(Integer,primary_key=True)
    juntadaID=Column(Integer,ForeignKey("juntadas.id"),nullable=False)
    usuarioID=Column(Integer,ForeignKey("usuarios.id"),nullable=False)
    texto=Column(String(500),nullable=False)
    fechaHora=Column(DateTime,nullable=False)
