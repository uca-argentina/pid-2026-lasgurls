from sqlalchemy import inspect, text
from base_datos.configuracion import engine


def migrar(motor=engine):
    with motor.begin() as conexion:
        conexion.execute(text("SET SESSION lock_wait_timeout=10"))
        for tabla in ("agendas","juntadas"):
            columnas=[columna["name"] for columna in inspect(conexion).get_columns(tabla)]
            if "ubicacion" not in columnas:
                conexion.execute(text(f"ALTER TABLE {tabla} ADD COLUMN ubicacion VARCHAR(120) NULL"))


if __name__=="__main__":
    migrar()
    print("Columna ubicacion lista")
