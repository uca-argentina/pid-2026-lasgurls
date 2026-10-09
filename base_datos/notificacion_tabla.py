from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey
from base_datos.usuario_tabla import Base


class NotificacionTabla(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    tipo = Column(String(20), nullable=False)
    texto = Column(String(255), nullable=False)
    juntada_id = Column(Integer, nullable=True)
    fecha_juntada = Column(Date, nullable=True)
    leida = Column(Boolean, nullable=False, default=False)
    fecha_hora = Column(DateTime, nullable=False)
