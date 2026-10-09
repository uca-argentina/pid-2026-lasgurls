from sqlalchemy import inspect, text
from base_datos.configuracion import engine


def migrar(motor=engine):
    with motor.begin() as conexion:
        columnas = [columna["name"] for columna in inspect(conexion).get_columns("juntadas")]
        if "serie_id" not in columnas:
            conexion.execute(text("ALTER TABLE juntadas ADD COLUMN serie_id INTEGER NULL"))
        if "repeticion" not in columnas:
            conexion.execute(text("ALTER TABLE juntadas ADD COLUMN repeticion VARCHAR(20) NULL"))


if __name__ == "__main__":
    migrar()
    print("Columnas de repetición listas")
