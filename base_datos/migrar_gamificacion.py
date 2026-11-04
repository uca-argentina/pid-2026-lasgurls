from sqlalchemy import text
from base_datos.configuracion import engine
from base_datos.juntada_tabla import JuntadaTabla
from base_datos.asistencia_tabla import AsistenciaTabla
from base_datos.estilo_perfil_tabla import EstiloPerfilTabla


def migrar(motor=engine):
    with motor.begin() as conexion:
        conexion.execute(text("SET SESSION lock_wait_timeout=10"))
        AsistenciaTabla.__table__.create(conexion,checkfirst=True)
        EstiloPerfilTabla.__table__.create(conexion,checkfirst=True)


if __name__=="__main__":
    migrar()
    print("Tablas de gamificacion listas")
