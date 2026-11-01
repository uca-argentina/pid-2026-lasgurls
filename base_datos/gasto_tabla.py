from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from base_datos.usuario_tabla import Base


class GastoTabla(Base):
    __tablename__="gastos"

    id=Column(Integer,primary_key=True)
    juntadaID=Column(Integer,ForeignKey("juntadas.id"),nullable=False)
    creadorID=Column(Integer,ForeignKey("usuarios.id"),nullable=False)
    pagadorID=Column(Integer,ForeignKey("usuarios.id"),nullable=False)
    descripcion=Column(String(60),nullable=False)
    monto=Column(Numeric(12,2),nullable=False)
    fechaHora=Column(DateTime,nullable=False)
