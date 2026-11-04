from base_datos.configuracion import engine
from base_datos.pago_deuda_tabla import PagoDeudaTabla
from base_datos.juntada_tabla import JuntadaTabla


def migrar(motor=engine):
    PagoDeudaTabla.__table__.create(motor, checkfirst=True)


if __name__ == "__main__":
    migrar()
    print("Tabla pagos_deuda lista")