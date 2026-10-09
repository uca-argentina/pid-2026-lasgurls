from base_datos.configuracion import engine
from base_datos.notificacion_tabla import NotificacionTabla


def migrar(motor=engine):
    NotificacionTabla.__table__.create(motor, checkfirst=True)


if __name__ == "__main__":
    migrar()
    print("Tabla de notificaciones lista")
