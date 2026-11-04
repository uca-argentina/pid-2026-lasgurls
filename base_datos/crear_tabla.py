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
from base_datos.notificacion_tabla import NotificacionTabla
from base_datos.encuesta_tabla import EncuestaTabla, EncuestaOpcionTabla, EncuestaInvitadoTabla, EncuestaVotoTabla, EncuestaOcultaTabla
from base_datos.gasto_tabla import GastoTabla
from base_datos.gasto_partes_tabla import GastoPartesTabla
from base_datos.asistencia_tabla import AsistenciaTabla
from base_datos.estilo_perfil_tabla import EstiloPerfilTabla

Base.metadata.create_all(engine)
print("tablas creadas!")
