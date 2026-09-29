from sqlalchemy import Column, Integer, String, Boolean, true
from sqlalchemy.orm import declarative_base
 
Base = declarative_base()
 
 
class UsuarioTabla(Base):
    __tablename__ = "usuarios"
 
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    nombre = Column(String(255), nullable=False)
    activo=Column(Boolean,nullable=False,default=True,server_default=true())
    compartir_disponibilidad= Column (Boolean, nullable=False, default=True, server_default=true())
