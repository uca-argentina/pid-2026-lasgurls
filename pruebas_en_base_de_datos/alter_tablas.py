from sqlalchemy import text
from base_datos.configuracion import engine

with engine.connect() as conexion:
    conexion.execute(text("ALTER TABLE usuarios ADD COLUMN compartir_disponibilidad BOOLEAN NOT NULL DEFAULT TRUE"))
    conexion.execute(text("ALTER TABLE agendas ADD COLUMN visibilidad VARCHAR(20) NOT NULL DEFAULT 'ocupado'"))
    conexion.execute(text("ALTER TABLE juntadas ADD COLUMN visibilidad VARCHAR(20) NOT NULL DEFAULT 'ocupado'"))
    conexion.commit()

print("Columnas agregadas correctamente")