import os

if os.environ.get("DB_HOST"):
    HOST = os.environ["DB_HOST"]
    PUERTO = os.environ["DB_PUERTO"]
    USUARIO = os.environ["DB_USUARIO"]
    PASSWORD = os.environ["DB_PASSWORD"]
    BASE = os.environ["DB_BASE"]
    SECRET_KEY = os.environ["SECRET_KEY"]
else:
    from base_datos.credenciales import HOST, PUERTO, USUARIO, PASSWORD, BASE, SECRET_KEY
