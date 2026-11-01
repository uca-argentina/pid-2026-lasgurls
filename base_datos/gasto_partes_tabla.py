from sqlalchemy import Column, Integer, Numeric, ForeignKey
from base_datos.usuario_tabla import Base


class GastoPartesTabla(Base):
    __tablename__="gasto_partes"

    id=Column(Integer,primary_key=True)
    gastoID=Column(Integer,ForeignKey("gastos.id"),nullable=False)
    usuarioID=Column(Integer,ForeignKey("usuarios.id"),nullable=False)
    monto=Column(Numeric(12,2),nullable=False)
