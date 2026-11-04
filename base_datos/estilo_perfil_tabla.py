from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, false
from base_datos.usuario_tabla import Base


class EstiloPerfilTabla(Base):
    __tablename__ = "estilos_perfil"

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    color = Column(String(7), nullable=True)
    forma = Column(String(20), nullable=True)
    marco = Column(String(20), nullable=True)
    titulo = Column(String(40), nullable=True)
    degrade = Column(Boolean, nullable=False, default=False, server_default=false())
