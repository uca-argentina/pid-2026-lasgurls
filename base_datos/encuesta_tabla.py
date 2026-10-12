from sqlalchemy import Column, Integer, String, Date, Time, DateTime, ForeignKey
from base_datos.usuario_tabla import Base


class EncuestaTabla(Base):
    __tablename__ = "encuestas"

    id = Column(Integer, primary_key=True)
    organizador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    titulo = Column(String(255), nullable=False)
    estado = Column(String(20), nullable=False, default="abierta")
    juntada_id = Column(Integer, nullable=True)
    fecha_creacion = Column(DateTime, nullable=False)
    ubicacion = Column(String(120), nullable=True)


class EncuestaOpcionTabla(Base):
    __tablename__ = "encuesta_opciones"

    id = Column(Integer, primary_key=True)
    encuesta_id = Column(Integer, ForeignKey("encuestas.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)


class EncuestaInvitadoTabla(Base):
    __tablename__ = "encuesta_invitados"

    id = Column(Integer, primary_key=True)
    encuesta_id = Column(Integer, ForeignKey("encuestas.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)


class EncuestaVotoTabla(Base):
    __tablename__ = "encuesta_votos"

    id = Column(Integer, primary_key=True)
    opcion_id = Column(Integer, ForeignKey("encuesta_opciones.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)