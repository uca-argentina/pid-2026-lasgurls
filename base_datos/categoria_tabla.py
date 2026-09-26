from sqlalchemy import Column, Integer, String, ForeignKey
from base_datos.usuario_tabla import Base


class CategoriaTabla(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    nombre = Column(String(30), nullable=False)
    color = Column(String(7), nullable=False)
