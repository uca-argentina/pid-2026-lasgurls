from sqlalchemy import Column, Integer, String, ForeignKey
from base_datos.usuario_tabla import Base


class JuntadaInvitadosTabla(Base):
    __tablename__ = "juntada_invitados"

    id = Column(Integer, primary_key=True)
    juntada_id=Column(Integer, ForeignKey("juntadas.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    estado=Column(String(20),nullable=False,default="Pendiente")
    
