from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from base_datos.usuario_tabla import Base


class PagoDeudaTabla(Base):
    __tablename__="pagos_deuda"

    id=Column(Integer,primary_key=True)
    juntadaID=Column(Integer,ForeignKey("juntadas.id"),nullable=False)
    deudorID=Column(Integer,ForeignKey("usuarios.id"),nullable=False)
    acreedorID=Column(Integer,ForeignKey("usuarios.id"),nullable=False)
    registradoPorID=Column(Integer,ForeignKey("usuarios.id"),nullable=False)
    monto=Column(Numeric(12,2),nullable=False)
    fechaHora=Column(DateTime,nullable=False)