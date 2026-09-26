from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base_datos.credenciales import HOST, PUERTO, USUARIO, PASSWORD, BASE

DATABASE_URL = f"mysql+pymysql://{USUARIO}:{PASSWORD}@{HOST}:{PUERTO}/{BASE}?ssl_ca=ca.pem"

engine = create_engine(DATABASE_URL, pool_reset_on_return=None)
Session = sessionmaker(bind=engine)