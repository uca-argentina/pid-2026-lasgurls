from sqlalchemy import inspect, text
from base_datos.configuracion import engine


def migrar(motor=engine):
    with motor.begin() as conexion:
        conexion.execute(text("SET SESSION lock_wait_timeout=10"))
        columnas=[columna["name"] for columna in inspect(conexion).get_columns("notificaciones")]
        if "encuesta_id" not in columnas:
            conexion.execute(text("ALTER TABLE notificaciones ADD COLUMN encuesta_id INTEGER NULL"))


if __name__=="__main__":
    migrar()
    print("Columna encuesta_id de notificaciones lista")