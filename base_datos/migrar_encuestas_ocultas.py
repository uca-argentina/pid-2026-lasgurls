from base_datos.configuracion import engine
from base_datos.encuesta_tabla import EncuestaOcultaTabla


def migrar(motor=engine):
    EncuestaOcultaTabla.__table__.create(motor, checkfirst=True)


if __name__ == "__main__":
    migrar()
    print("Tabla encuestas_ocultas lista")
