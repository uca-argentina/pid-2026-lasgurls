import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_LOCAL = os.path.join(RAIZ, "juntapp.db")
USA_AIVEN = bool(os.environ.get("DB_HOST") or os.environ.get("JUNTAPP_AIVEN"))

if USA_AIVEN:
    from base_datos.secretos import HOST, PUERTO, USUARIO, PASSWORD, BASE
    DATABASE_URL = f"mysql+pymysql://{USUARIO}:{PASSWORD}@{HOST}:{PUERTO}/{BASE}?ssl_ca=ca.pem"
    engine = create_engine(DATABASE_URL, pool_reset_on_return=None)
else:
    DATABASE_URL = f"sqlite:///{RUTA_LOCAL}"
    engine = create_engine(DATABASE_URL)

    @event.listens_for(engine, "connect")
    def activar_claves_foraneas(conexion, _):
        cursor = conexion.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

Session = sessionmaker(bind=engine)
