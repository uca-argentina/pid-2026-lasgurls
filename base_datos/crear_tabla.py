from base_datos.configuracion import engine
from base_datos.usuario_tabla import Base
from base_datos.agenda_tabla import AgendaTabla
from base_datos.categoria_tabla import CategoriaTabla
from base_datos.solicitud_tabla import SolicitudTabla
from base_datos.juntada_tabla import JuntadaTabla
from base_datos.juntada_invitados_tabla import JuntadaInvitadosTabla
from base_datos.comentario_tabla import ComentarioTabla
from base_datos.grupo_tabla import GrupoTabla
from base_datos.grupo_miembros_tabla import GrupoMiembrosTabla

Base.metadata.create_all(engine)
print("tablas creadas!")
