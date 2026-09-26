from sqlalchemy import inspect, select, text
from base_datos.configuracion import engine
from base_datos.categoria_tabla import CategoriaTabla
from dominio.categoria import CATEGORIAS_DE_FABRICA


def migrar(motor=engine):
    CategoriaTabla.__table__.create(motor, checkfirst=True)

    with motor.begin() as conexion:
        for tabla in ("agendas", "juntadas"):
            columnas = [columna["name"] for columna in inspect(conexion).get_columns(tabla)]
            if "categoria_id" in columnas:
                continue
            if motor.dialect.name == "mysql":
                conexion.execute(text(
                    f"ALTER TABLE {tabla} ADD COLUMN categoria_id INT NULL, "
                    f"ADD CONSTRAINT fk_{tabla}_categoria FOREIGN KEY (categoria_id) REFERENCES categorias(id)"
                ))
            else:
                conexion.execute(text(f"ALTER TABLE {tabla} ADD COLUMN categoria_id INTEGER NULL"))

        consulta = select(CategoriaTabla.nombre).where(CategoriaTabla.usuario_id.is_(None))
        existentes = set(conexion.scalars(consulta))
        for nombre, color in CATEGORIAS_DE_FABRICA:
            if nombre not in existentes:
                conexion.execute(CategoriaTabla.__table__.insert().values(usuario_id=None, nombre=nombre, color=color))


if __name__ == "__main__":
    migrar()
    print("Categorías listas")
