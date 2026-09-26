from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey
from base_datos.usuario_tabla import Base
from base_datos.categoria_tabla import CategoriaTabla


class AgendaTabla(Base):
    __tablename__ = "agendas"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    titulo = Column(String(255), nullable=False)
    fecha = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    categoria_id = Column(Integer, ForeignKey(CategoriaTabla.id), nullable=True)
