from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from base_datos.usuario_tabla import Base


class AsistenciaTabla(Base):
    __tablename__ = "asistencias"
    __table_args__ = (UniqueConstraint("juntada_id", "usuario_id"),)

    id = Column(Integer, primary_key=True)
    juntada_id = Column(Integer, ForeignKey("juntadas.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha_hora = Column(DateTime, nullable=False)
