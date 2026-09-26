from base_datos.configuracion import engine
from base_datos.usuario_tabla import Base
from base_datos.agenda_tabla import AgendaTabla
from base_datos.categoria_tabla import CategoriaTabla
from base_datos.solicitud_tabla import SolicitudTabla
from base_datos.juntada_tabla import JuntadaTabla
from base_datos.juntada_invitados_tabla import JuntadaInvitadosTabla

Base.metadata.create_all(engine)
print("tablas creadas!")
