from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey
from base_datos.usuario_tabla import Base
from base_datos.categoria_tabla import CategoriaTabla


class JuntadaTabla(Base):
    __tablename__ = "juntadas"

    id = Column(Integer, primary_key=True)
    organizador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    titulo = Column(String(255), nullable=False)
    fecha = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    categoria_id = Column(Integer, ForeignKey(CategoriaTabla.id), nullable=True)
    visibilidad=Column(String(20),nullable=False,default="ocupado")
