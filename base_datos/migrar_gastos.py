from sqlalchemy import text
from base_datos.configuracion import engine
from base_datos.juntada_tabla import JuntadaTabla
from base_datos.gasto_tabla import GastoTabla
from base_datos.gasto_partes_tabla import GastoPartesTabla


def migrar(motor=engine):
    with motor.begin() as conexion:
        conexion.execute(text("SET SESSION lock_wait_timeout=10"))
        GastoTabla.__table__.create(conexion,checkfirst=True)
        GastoPartesTabla.__table__.create(conexion,checkfirst=True)


if __name__=="__main__":
    migrar()
    print("Tablas de gastos listas")
