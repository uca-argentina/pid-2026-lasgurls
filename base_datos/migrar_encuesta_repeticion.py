from sqlalchemy import inspect, text
from base_datos.configuracion import engine


def migrar(motor=engine):
    with motor.begin() as conexion:
        columnas = [columna["name"] for columna in inspect(conexion).get_columns("encuestas")]
        if "repeticion" not in columnas:
            conexion.execute(text("ALTER TABLE encuestas ADD COLUMN repeticion VARCHAR(20) NULL"))


if __name__ == "__main__":
    migrar()
    print("Columna repeticion de encuestas lista")
