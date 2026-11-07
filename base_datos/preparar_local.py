import os
import sys
from datetime import date, datetime, time, timedelta
from base_datos.configuracion import engine, Session, USA_AIVEN, RUTA_LOCAL
from base_datos.usuario_tabla import Base, UsuarioTabla
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
from base_datos.pago_deuda_tabla import PagoDeudaTabla
from base_datos.asistencia_tabla import AsistenciaTabla
from base_datos.estilo_perfil_tabla import EstiloPerfilTabla
from dominio.usuario import Usuario
from dominio.gasto import Gasto
from dominio.categoria import CATEGORIAS_DE_FABRICA

PASSWORD = "Juntapp1!"
PERSONAS = [
    ("marina@juntapp.com", "Marina Mercadal"),
    ("juana@juntapp.com", "Juana Pérez"),
    ("pedro@juntapp.com", "Pedro Gómez"),
    ("caro@juntapp.com", "Caro López"),
]


def crear_base():
    engine.dispose()
    if os.path.exists(RUTA_LOCAL):
        os.remove(RUTA_LOCAL)
    Base.metadata.create_all(engine)


def cargar_categorias(sesion):
    if sesion.query(CategoriaTabla).filter(CategoriaTabla.usuario_id.is_(None)).first() is None:
        for nombre, color in CATEGORIAS_DE_FABRICA:
            sesion.add(CategoriaTabla(usuario_id=None, nombre=nombre, color=color))
        sesion.flush()


def asegurar_base_local():
    if USA_AIVEN:
        return
    Base.metadata.create_all(engine)
    with Session() as sesion:
        cargar_categorias(sesion)
        sesion.commit()


def agregar_juntada(sesion, organizador, titulo, inicio, horas, invitados, categoria=None, ubicacion=None):
    fin = inicio + timedelta(hours=horas)
    juntada = JuntadaTabla(
        organizador_id=organizador, titulo=titulo, fecha=inicio.date(),
        hora_inicio=inicio.time(), hora_fin=fin.time(), categoria_id=categoria,
        visibilidad="detalle", ubicacion=ubicacion,
    )
    sesion.add(juntada)
    sesion.flush()
    for usuario_id, estado in invitados:
        sesion.add(JuntadaInvitadosTabla(juntada_id=juntada.id, usuario_id=usuario_id, estado=estado))
    return juntada


def agregar_gasto(sesion, juntada, pagador, descripcion, monto, participantes, momento):
    gasto = Gasto(juntada.id, pagador, pagador, descripcion, monto, participantes)
    fila = GastoTabla(
        juntadaID=juntada.id, creadorID=pagador, pagadorID=pagador,
        descripcion=gasto.descripcion, monto=gasto.monto, fechaHora=momento,
    )
    sesion.add(fila)
    sesion.flush()
    for usuario_id, parte in gasto.reparto.items():
        sesion.add(GastoPartesTabla(gastoID=fila.id, usuarioID=usuario_id, monto=parte))


def cargar_datos():
    ahora = datetime.now().replace(second=0, microsecond=0)
    hoy = ahora.date()
    with Session() as sesion:
        cargar_categorias(sesion)
        social = sesion.query(CategoriaTabla).filter_by(nombre="Social").first().id

        ids = []
        for email, nombre in PERSONAS:
            usuario = Usuario(email, PASSWORD, nombre)
            fila = UsuarioTabla(email=usuario.email, password=usuario.password, nombre=usuario.nombre)
            sesion.add(fila)
            sesion.flush()
            ids.append(fila.id)
        marina, juana, pedro, caro = ids

        for emisor, receptor in ((marina, juana), (marina, pedro), (marina, caro), (juana, pedro), (juana, caro)):
            sesion.add(SolicitudTabla(emisorID=emisor, receptorID=receptor, estado="Aceptada"))

        grupo = GrupoTabla(creadorID=marina, nombre="Las de la facu")
        sesion.add(grupo)
        sesion.flush()
        for miembro in (juana, caro):
            sesion.add(GrupoMiembrosTabla(grupoID=grupo.id, usuarioID=miembro))

        for semanas in (3, 2, 1):
            inicio = datetime.combine(hoy - timedelta(weeks=semanas), time(18, 0))
            cafe = agregar_juntada(sesion, marina, "Café de los viernes", inicio, 2, [(juana, "Si"), (pedro, "Si")], social, "Café Tortoni")
            for usuario_id in (marina, juana, pedro):
                sesion.add(AsistenciaTabla(juntada_id=cafe.id, usuario_id=usuario_id, fecha_hora=inicio + timedelta(minutes=10)))

        inicio_hoy = ahora - timedelta(minutes=30)
        pizza = agregar_juntada(
            sesion, marina, "Pizza en lo de Caro", inicio_hoy, 3,
            [(juana, "Si"), (pedro, "Pendiente"), (caro, "Tal vez")], social, "Av. Corrientes 1234",
        )
        agregar_gasto(sesion, pizza, marina, "Pizzas", "12000", [marina, juana, caro], ahora - timedelta(minutes=20))
        agregar_gasto(sesion, pizza, juana, "Bebidas", "3000", [marina, juana], ahora - timedelta(minutes=15))
        sesion.add(ComentarioTabla(juntadaID=pizza.id, usuarioID=juana, texto="Llevo el helado", fechaHora=ahora - timedelta(minutes=40)))

        agregar_juntada(sesion, juana, "Cine", datetime.combine(hoy + timedelta(days=1), time(20, 0)), 3, [(marina, "Pendiente"), (caro, "Si")], social)

        sesion.add(AgendaTabla(
            usuario_id=marina, titulo="Clase de PID", fecha=hoy + timedelta(days=2),
            hora_inicio=time(9, 0), hora_fin=time(12, 0), visibilidad="ocupado",
        ))
        sesion.add(EstiloPerfilTabla(usuario_id=juana, color="#d16d8e", forma="estrella"))
        sesion.commit()


if __name__ == "__main__":
    if USA_AIVEN:
        print("Este script solo arma la base local. Sacá JUNTAPP_AIVEN para usarlo.")
        sys.exit(1)
    crear_base()
    cargar_datos()
    print(f"Base local lista en {RUTA_LOCAL}")
    print(f"Usuarios: {', '.join(email for email, _ in PERSONAS)} (contraseña {PASSWORD})")
