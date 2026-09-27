from functools import wraps
import secrets
import unicodedata
from datetime import date, datetime, time, timedelta
import calendar as modulo_calendario
from flask import Flask, request, render_template, session, redirect, url_for, g
from dominio.usuario import Usuario
from dominio.juntada.juntada import Juntada
from dominio.agenda.agenda import Agenda
from base_datos.usuario_acciones import guardar, actualizar_perfil, dar_de_baja, actualizar_compartir_disponibilidad
from base_datos.usuario_acciones import verificar_login, buscarPorID, obtenerTodos
from base_datos.credenciales import SECRET_KEY
from amistad_acciones import enviarSolicitud, aceptarSolicitud, rechazarSolicitud, eliminarAmigo
from base_datos.solicitud_acciones import obtenerRecibidas, obtener_amigos
from base_datos.agenda_acciones import obtener_por_usuario as obtener_agenda_de_usuario
from base_datos.agenda_acciones import guardar as guardar_agenda
from base_datos.juntada_acciones import (
    guardar as guardar_juntada,
    obtener_organizadas,
    obtener_invitaciones_del_calendario,
    obtener_invitados_de_juntadas,
    responder_invitacion,
    cancelar_juntada as borrar_juntada_organizada,
    darse_de_baja as bajarse_de_juntada,
)
from base_datos.disponibilidad_amigo_acciones import obtener_disponibilidad
from base_datos.categoria_acciones import obtener_categorias, crear_categoria, borrar_categoria, puede_usar_categoria
from dominio.categoria import Categoria, COLORES
from dominio.modulo_utilidades.rango_horario import rango_del_evento, termina_al_dia_siguiente, ya_empezo
from dominio.disponibilidad.buscador_huecos import buscar_huecos, huecos_del_dia, proxima_media_hora


NOMBRES_MES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
DIAS_SEMANA = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
DIAS_SEMANA_LARGO = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
DURACIONES_JUNTADA = [
    (30, "30 min"), (60, "1 h"), (90, "1 h 30 min"), (120, "2 h"), (180, "3 h"),
    (240, "4 h"), (360, "6 h"), (480, "8 h"), (720, "12 h"),
]

app= Flask(__name__)
app.config["SECRET_KEY"]=SECRET_KEY

def login_requerido(vista):
    @wraps(vista)
    def decorador(*args, **kwargs):
        if "usuarioID" not in session:
            return redirect(url_for("mostrar_login"))
        usuario=buscarPorID(session["usuarioID"])
        if usuario is None or not usuario.activo:
            session.clear()
            return redirect(url_for("mostrar_login"))
        g.usuario=usuario
        return vista(*args, **kwargs)
    return decorador

def volver_a(destino_por_defecto):
    destino=request.form.get("volver","")
    if destino.startswith("/") and not destino.startswith("//") and "\\" not in destino:
        return redirect(destino)
    return redirect(destino_por_defecto)

@app.template_filter("iniciales")
def iniciales(nombre):
    return "".join(parte[0] for parte in nombre.split()[:2]).upper() or "?"

@app.template_global()
def texto_horario(fecha,hora_inicio,hora_fin):
    texto=f"{hora_inicio:%H:%M} a {hora_fin:%H:%M}"
    return texto+" (+1)" if termina_al_dia_siguiente(fecha,hora_inicio,hora_fin) else texto

def nombre_del_dia(dia):
    return f"{DIAS_SEMANA_LARGO[dia.weekday()].capitalize()} {dia.day} de {NOMBRES_MES[dia.month]}"

def a_texto(momento):
    return momento.strftime("%Y-%m-%dT%H:%M")

def dias_de_la_semana(lunes):
    return [lunes+timedelta(days=i) for i in range(7)]

def titulo_semana(lunes):
    domingo=lunes+timedelta(days=6)
    if lunes.month==domingo.month:
        return f"{lunes.day} – {domingo.day} de {NOMBRES_MES[lunes.month]} de {domingo.year}"
    return f"{lunes.day} de {NOMBRES_MES[lunes.month]} – {domingo.day} de {NOMBRES_MES[domingo.month]} de {domingo.year}"

def sin_acentos(texto):
    return "".join(letra for letra in unicodedata.normalize("NFD",texto.casefold()) if not unicodedata.combining(letra))

def invitaciones_del_usuario(inicio,fin):
    if "invitaciones" not in g:
        g.invitaciones=obtener_invitaciones_del_calendario(g.usuario.id,inicio,fin)
    return g.invitaciones

def solicitudes_recibidas():
    if "solicitudes" not in g:
        g.solicitudes=[
            {"solicitud":solicitud,"emisor":emisor}
            for solicitud,emisor in obtenerRecibidas(g.usuario.id)
        ]
    return g.solicitudes

@app.context_processor
def datos_del_header():
    usuario=g.get("usuario")
    if usuario is None:
        return {}

    hoy=date.today()
    invitaciones=[
        {"juntada":juntada,"estado":invitacion.estado,"organizador":organizador}
        for invitacion,juntada,organizador,*_ in invitaciones_del_usuario(hoy,hoy)
        if invitacion.estado in ("Pendiente","Tal vez") and juntada.fecha>=hoy
    ]
    invitaciones.sort(key=lambda item: (item["juntada"].fecha, item["juntada"].hora_inicio))

    solicitudes=solicitudes_recibidas()
    pendientes=len(solicitudes)+sum(1 for item in invitaciones if item["estado"]=="Pendiente")

    return {
        "usuario_actual":usuario,
        "notificaciones_juntadas":invitaciones,
        "notificaciones_amistad":solicitudes,
        "notificaciones_pendientes":pendientes,
    }

@app.route("/registro", methods=["POST"])
def registro():
    nombre=request.form.get("nombre")
    email=request.form.get("email")
    password=request.form.get("password")

    try:
        usuario=Usuario(email,password,nombre)
        guardar(usuario)
    except ValueError as error:
        return render_template("registro.html", error=str(error), nombre=nombre, email=email), 400

    return redirect(url_for("mostrar_login", registrado="1"))


@app.route("/registro", methods = ["GET"])
def mostrar_registro():
    return render_template("registro.html", error=None, nombre="", email="")

@app.route("/login",methods=["GET"])
def mostrar_login():
    return render_template("login.html")

@app.route("/login",methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    usuario_encontrado=verificar_login(email,password)
    if usuario_encontrado is None:
        return render_template("login.html", error="Email o contraseña incorrectos"), 401
 
    session.clear()
    session["usuarioID"]=usuario_encontrado.id
    return redirect(url_for("mostrar_calendario"))





@app.route("/logout",methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("mostrar_login"))

def pagina_perfil(nombre, email, error, guardado, compartir_disponibilidad):
    return render_template(
        "perfil.html", nombre=nombre, email=email, error=error, guardado=guardado,
        categorias=obtener_categorias(g.usuario.id), colores=COLORES,
        compartir_disponibilidad=compartir_disponibilidad,
    )
    


@app.route("/perfil",methods=["GET","POST"])
@login_requerido
def mostrar_perfil():
    usuario=g.usuario

    if "perfil_token" not in session:
        session["perfil_token"]=secrets.token_hex(32)
    nombre=usuario.nombre
    email=usuario.email
    error=None
    estado=200

    if request.method=="POST":
        if not secrets.compare_digest(request.form.get("token",""),session["perfil_token"]):
            return "El formulario venció. Recargá la página e intentá nuevamente.",400
        nombre=request.form.get("nombre","")
        compartir_disponibilidad = "compartir_disponibilidad" in request.form
        try:
            actualizar_perfil(session["usuarioID"],nombre)
            actualizar_compartir_disponibilidad(session["usuarioID"],compartir_disponibilidad)
        except ValueError as problema:
            error=str(problema)
            estado=400
        else:
            session["perfil_guardado"]=True
            return redirect(url_for("mostrar_perfil"))

    guardado=session.pop("perfil_guardado",False)
    return pagina_perfil(nombre, email, error, guardado, usuario.compartir_disponibilidad), estado

@app.route("/perfil/baja",methods=["POST"])
@login_requerido
def baja_cuenta():
    token=session.get("perfil_token")
    if not token or not secrets.compare_digest(request.form.get("token",""),token):
        return "El formulario venció. Recargá la página e intentá nuevamente.",400
    usuario=g.usuario
    try:
        if request.form.get("confirmar")!="si":
            raise ValueError("Confirmá que querés dar de baja tu cuenta")
        dar_de_baja(session["usuarioID"],request.form.get("password",""))
    except ValueError as error:
        return pagina_perfil(usuario.nombre,usuario.email,str(error),False),400
    session.clear()
    return redirect(url_for("mostrar_login",baja="1"))

@app.route("/calendario",methods=["GET"])
@login_requerido
def mostrar_calendario():
    usuario_id=session["usuarioID"]

    fecha_parametro=request.args.get("fecha")
    try:
        fecha_seleccionada=date.fromisoformat(fecha_parametro) if fecha_parametro else date.today()
    except ValueError:
        fecha_seleccionada=date.today()

    semanas=modulo_calendario.Calendar(firstweekday=0).monthdatescalendar(
        fecha_seleccionada.year, fecha_seleccionada.month
    )
    lunes=fecha_seleccionada-timedelta(days=fecha_seleccionada.weekday())
    desde=semanas[0][0]-timedelta(days=1)
    hasta=semanas[-1][-1]
    eventos=[]

    for agenda,categoria,color in obtener_agenda_de_usuario(usuario_id,desde,hasta):
        eventos.append({
            "fecha":agenda.fecha,"titulo":agenda.titulo,"hora_inicio":agenda.hora_inicio,"hora_fin":agenda.hora_fin,
            "tipo":"personal","detalle":"Solo lo ves vos.","juntada_id":None,"categoria":categoria,"color":color,
        })

    organizadas={}
    for juntada,nombre_invitado,estado,categoria,color in obtener_organizadas(usuario_id,desde,hasta):
        invitados=organizadas.setdefault(juntada.id,(juntada,[],categoria,color))[1]
        if nombre_invitado is not None:
            invitados.append((nombre_invitado,estado))

    for juntada,invitados,categoria,color in organizadas.values():
        confirmados=sum(1 for _,estado in invitados if estado=="Si")
        eventos.append({
            "fecha":juntada.fecha,"titulo":juntada.titulo,"hora_inicio":juntada.hora_inicio,"hora_fin":juntada.hora_fin,
            "tipo":"organizo","detalle":f"Organizás · {confirmados} de {len(invitados)} confirmaron",
            "juntada_id":juntada.id,"categoria":categoria,"color":color,
            "personas":[persona(g.usuario.nombre,"organiza",es_vos=True)]+[persona(nombre,estado) for nombre,estado in invitados],
        })

    invitaciones=[
        fila for fila in invitaciones_del_usuario(desde,hasta) if desde<=fila[1].fecha<=hasta
    ]
    invitados_por_juntada={}
    for juntada_id,invitado_id,nombre,estado in obtener_invitados_de_juntadas([fila[1].id for fila in invitaciones]):
        invitados_por_juntada.setdefault(juntada_id,[]).append(persona(nombre,estado,es_vos=invitado_id==usuario_id))

    for invitacion,juntada,organizador,categoria,color in invitaciones:
        respuesta={"Si":"Confirmaste","Tal vez":"Dijiste tal vez"}.get(invitacion.estado,"Todavía no respondiste")
        eventos.append({
            "fecha":juntada.fecha,"titulo":juntada.titulo,"hora_inicio":juntada.hora_inicio,"hora_fin":juntada.hora_fin,
            "tipo":{"Si":"confirmada","Tal vez":"tal_vez"}.get(invitacion.estado,"pendiente"),
            "detalle":f"Te invitó {organizador} · {respuesta}",
            "juntada_id":juntada.id,"categoria":categoria,"color":color,
            "personas":[persona(organizador,"organiza")]+invitados_por_juntada.get(juntada.id,[]),
        })

    ahora=datetime.now()
    inicio_semana=datetime.combine(lunes,time(0))
    fin_semana=inicio_semana+timedelta(days=7)
    dias_con_eventos=set()
    eventos_de_la_semana=[]
    for evento in eventos:
        inicio,fin=rango_del_evento(evento["fecha"],evento["hora_inicio"],evento["hora_fin"])
        dias_con_eventos.add(evento["fecha"])
        if termina_al_dia_siguiente(evento["fecha"],evento["hora_inicio"],evento["hora_fin"]):
            dias_con_eventos.add(fin.date())
        if inicio<fin_semana and fin>inicio_semana:
            eventos_de_la_semana.append({
                "inicio":a_texto(inicio),"fin":a_texto(fin),"titulo":evento["titulo"],"tipo":evento["tipo"],
                "detalle":evento["detalle"],"personas":evento.get("personas",[]),
                "categoria":evento.get("categoria"),"color":evento.get("color"),
                "cuando":f"{nombre_del_dia(evento['fecha'])} · {texto_horario(evento['fecha'],evento['hora_inicio'],evento['hora_fin'])}",
                **acciones_del_evento(evento,ahora),
            })

    datos={
        "fecha":fecha_seleccionada.isoformat(),
        "dias":[{
            "fecha":dia.isoformat(),"titulo":DIAS_SEMANA[dia.weekday()].capitalize(),"numero":dia.day,
            "nombre":nombre_del_dia(dia),
        } for dia in dias_de_la_semana(lunes)],
        "eventos":eventos_de_la_semana,
        "urls":{"nuevo_evento":url_for("mostrar_nueva_agenda"),"nueva_juntada":url_for("mostrar_nueva_juntada")},
    }

    inicio_mes=fecha_seleccionada.replace(day=1)
    return render_template(
        "calendario.html",
        datos=datos,
        fecha_seleccionada=fecha_seleccionada,
        titulo=titulo_semana(lunes),
        semana_anterior=lunes-timedelta(days=7),
        semana_siguiente=lunes+timedelta(days=7),
        dias_semana_elegida=dias_de_la_semana(lunes),
        dias_con_eventos=dias_con_eventos,
        semanas=semanas,
        hoy=date.today(),
        mes_anterior=(inicio_mes-timedelta(days=1)).replace(day=1),
        mes_siguiente=(inicio_mes+timedelta(days=31)).replace(day=1),
        nombre_mes=NOMBRES_MES[fecha_seleccionada.month],
        dias_semana=DIAS_SEMANA,
    )

def persona(nombre,estado,es_vos=False):
    return {"nombre":"Vos" if es_vos else nombre,"iniciales":iniciales(nombre),"estado":estado}

def acciones_del_evento(evento,ahora):
    tipo=evento["tipo"]
    todavia_no_empezo=not ya_empezo(evento["fecha"],evento["hora_inicio"],ahora)
    juntada_id=evento["juntada_id"]
    return {
        "responder":url_for("responder_juntada",juntada_id=juntada_id) if tipo in ("pendiente","tal_vez") else None,
        "cancelar":url_for("cancelar_juntada",juntada_id=juntada_id) if tipo=="organizo" and todavia_no_empezo else None,
        "abandonar":url_for("abandonar_juntada",juntada_id=juntada_id) if tipo=="confirmada" and todavia_no_empezo else None,
    }

def volver_al_calendario():
    fecha_parametro=request.form.get("fecha")
    return volver_a(url_for("mostrar_calendario", fecha=fecha_parametro) if fecha_parametro else url_for("mostrar_calendario"))

def horario_sugerido(minutos):
    try:
        inicio=datetime.strptime(request.args.get("hora",""),"%H:%M")
    except ValueError:
        return "",""
    return f"{inicio:%H:%M}",f"{inicio+timedelta(minutes=minutos):%H:%M}"

@app.route("/agenda/nueva",methods=["GET"])
@login_requerido
def mostrar_nueva_agenda():
    hora_desde,hora_hasta=horario_sugerido(60)
    return formulario_evento(fecha_pedida(),hora_desde=hora_desde,hora_hasta=hora_hasta)

def formulario_evento(fecha_sugerida,error=None,hora_desde="",hora_hasta=""):
    return formulario_con_horario(
        "agenda_nueva.html",fecha_sugerida,60,error,hora_desde,hora_hasta,
        categorias=obtener_categorias(g.usuario.id),colores=COLORES,
    )

@app.route("/agenda/nueva", methods=["POST"])
@login_requerido
def crear_agenda():
    usuario_id = session["usuarioID"]
    fecha_parametro = request.form.get("fecha", "")
    categoria_id = request.form.get("categoria", type=int)
    visibilidad = request.form.get("visibilidad", "ocupado")

    try:
        if categoria_id is not None and not puede_usar_categoria(categoria_id, usuario_id):
            raise ValueError("Elegí una categoría válida")
        fecha_formateada = datetime.strptime(fecha_parametro, "%Y-%m-%d").strftime("%d/%m/%Y")
        agenda = Agenda(
            usuario_id=usuario_id,
            fecha=fecha_formateada,
            titulo_reunion=request.form.get("titulo"),
            hora_inicio=request.form.get("hora_inicio"),
            hora_fin=request.form.get("hora_fin"),
            categoria_id=categoria_id,
            visibilidad=visibilidad,
        )
    except ValueError as error:
        return formulario_evento(fecha_parametro, error=str(error)), 400

    guardar_agenda(agenda)
    return redirect(url_for("mostrar_calendario", fecha=fecha_parametro))

def fecha_pedida():
    return max(request.args.get("fecha",""),date.today().isoformat())

def formulario_con_horario(plantilla,fecha_sugerida,duracion_inicial,error=None,hora_desde="",hora_hasta="",**datos):
    return render_template(
        plantilla, fecha_sugerida=fecha_sugerida, error=error, duraciones=DURACIONES_JUNTADA,
        duracion_inicial=duracion_inicial, hora_desde=hora_desde, hora_hasta=hora_hasta,
        hoy=date.today().isoformat(), **datos,
    )

def formulario_juntada(amigos,fecha_sugerida,seleccionados,error=None,hora_desde="",hora_hasta=""):
    return formulario_con_horario(
        "juntada_nueva.html",fecha_sugerida,120,error,hora_desde,hora_hasta,amigos=amigos,seleccionados=seleccionados,
        categorias=obtener_categorias(g.usuario.id),colores=COLORES,
    )

@app.route("/juntada/nueva",methods=["GET"])
@login_requerido
def mostrar_nueva_juntada():
    amigos=obtener_amigos(session["usuarioID"])
    invitado_id=request.args.get("invitado",type=int)
    seleccionados=[amigo.id for amigo in amigos if amigo.id==invitado_id]
    hora_desde,hora_hasta=horario_sugerido(120)
    return formulario_juntada(amigos,fecha_pedida(),seleccionados,hora_desde=hora_desde,hora_hasta=hora_hasta)

@app.route("/juntada/nueva",methods=["POST"])
@login_requerido
def crear_juntada():
    usuario_id=session["usuarioID"]
    fecha_parametro=request.form.get("fecha","")
    invitados_ids=[int(id) for id in request.form.getlist("invitados")]
    amigos=obtener_amigos(usuario_id)
    amigos_ids=[amigo.id for amigo in amigos]
    visibilidad = request.form.get("visibilidad", "ocupado")


    if not set(invitados_ids).issubset(set(amigos_ids)):
        seleccionados=[id for id in invitados_ids if id in amigos_ids]
        return formulario_juntada(amigos,fecha_parametro,seleccionados,"Solo podés invitar a tus amigos."), 400

    categoria_id=request.form.get("categoria",type=int)
    try:
        if categoria_id is not None and not puede_usar_categoria(categoria_id,usuario_id):
            raise ValueError("Elegí una categoría válida")
        fecha_formateada=datetime.strptime(fecha_parametro, "%Y-%m-%d").strftime("%d/%m/%Y")
        juntada=Juntada(
            organizador=usuario_id,
            fecha=fecha_formateada,
            titulo_juntada=request.form.get("titulo"),
            hora_inicio=request.form.get("hora_inicio"),
            hora_fin=request.form.get("hora_fin"),
            amigos_invitados=invitados_ids,
            categoria_id=categoria_id,
            visibilidad=visibilidad,
        )
    except ValueError as error:
        return formulario_juntada(amigos,fecha_parametro,invitados_ids,str(error)), 400

    guardar_juntada(juntada)
    return redirect(url_for("mostrar_calendario", fecha=fecha_parametro))

@app.route("/juntada/<int:juntada_id>/responder",methods=["POST"])
@login_requerido
def responder_juntada(juntada_id):
    responder_invitacion(juntada_id, session["usuarioID"], request.form.get("respuesta"))
    return volver_al_calendario()

@app.route("/juntada/<int:juntada_id>/cancelar",methods=["POST"])
@login_requerido
def cancelar_juntada(juntada_id):
    if not borrar_juntada_organizada(juntada_id, session["usuarioID"], datetime.now()):
        return "No se puede cancelar esta juntada.", 400
    return volver_al_calendario()

@app.route("/juntada/<int:juntada_id>/abandonar",methods=["POST"])
@login_requerido
def abandonar_juntada(juntada_id):
    if not bajarse_de_juntada(juntada_id, session["usuarioID"], datetime.now()):
        return "No te podés dar de baja de esta juntada.", 400
    return volver_al_calendario()

@app.route("/amistad",methods=["GET"])
@login_requerido
def mostrar_amistad():
    nombre=request.args.get("nombre","")
    usuarios=obtenerTodos()
    buscado=sin_acentos(nombre.strip())
    personas=[usuario for usuario in usuarios if buscado and buscado in sin_acentos(usuario.nombre)]
    amigos=obtener_amigos(session["usuarioID"])
    amigos_ids={amigo.id for amigo in amigos}
    sugerencias=[
        usuario for usuario in usuarios
        if usuario.id != session["usuarioID"]
    ]

    return render_template(
        "amistad.html",
        personas=personas,
        nombre=nombre,
        recibidas=solicitudes_recibidas(),
        sugerencias=sugerencias,
        amigos=amigos,
        amigos_ids=amigos_ids
    )

@app.route("/amistad/enviar/<int:receptorID>",methods=["POST"])
@login_requerido
def enviar_solicitud(receptorID):
    emisorID=session["usuarioID"]
    receptor=buscarPorID(receptorID)
    if receptor is None or not receptor.activo:
        return "Ese usuario no está disponible.",400
    solicitud=enviarSolicitud(emisorID,receptorID)

    if solicitud is None:
        return "No se puede enviar esta solicitud.", 400

    return redirect(url_for("mostrar_amistad"))

@app.route("/amistad/aceptar/<int:solicitudID>",methods=["POST"])
@login_requerido
def aceptar_solicitud(solicitudID):
    aceptada=aceptarSolicitud(solicitudID,session["usuarioID"])

    if not aceptada:
        return "No se puede aceptar esta solicitud.", 400

    return volver_a(url_for("mostrar_amistad"))

@app.route("/amistad/rechazar/<int:solicitudID>",methods=["POST"])
@login_requerido
def rechazar_solicitud(solicitudID):
    rechazada=rechazarSolicitud(solicitudID,session["usuarioID"])

    if not rechazada:
        return "No se puede rechazar esta solicitud.", 400

    return volver_a(url_for("mostrar_amistad"))

@app.route("/categorias",methods=["POST"])
@login_requerido
def crear_categoria_propia():
    try:
        return crear_categoria(session["usuarioID"],Categoria(request.form.get("nombre"),request.form.get("color")))
    except ValueError as error:
        return {"error":str(error)},400

@app.route("/categorias/<int:categoria_id>/borrar",methods=["POST"])
@login_requerido
def borrar_categoria_propia(categoria_id):
    if not borrar_categoria(categoria_id,session["usuarioID"]):
        return "No se puede borrar esta categoría.", 400
    return redirect(url_for("mostrar_perfil"))

@app.route("/notificaciones",methods=["GET"])
@login_requerido
def mostrar_notificaciones():
    return render_template("_notificaciones.html")

@app.route("/amistad/eliminar/<int:amigoID>",methods=["POST"])
@login_requerido
def eliminar_amigo(amigoID):
    eliminado=eliminarAmigo(session["usuarioID"],amigoID)

    if not eliminado:
        return "No se puede eliminar esta amistad.", 400

    return redirect(url_for("mostrar_amistad"))

@app.route("/disponibilidad",methods=["GET"])
@login_requerido
def consultar_disponibilidad():
    try:
        fecha=date.fromisoformat(request.args.get("fecha",""))
    except ValueError:
        return {"error":"Elegí una fecha válida."},400
    minutos=request.args.get("duracion",type=int)
    if minutos is None or not 0<minutos<=24*60:
        return {"error":"Elegí una duración válida."},400

    duracion=timedelta(minutes=minutos)
    lunes=fecha-timedelta(days=fecha.weekday())
    dias=[lunes+timedelta(days=i) for i in range(7)]
    inicio=datetime.combine(lunes,time(0))
    fin=inicio+timedelta(days=7)+duracion
    try:
        ocupados=obtener_disponibilidad(session["usuarioID"],request.args.getlist("amigos",type=int),lunes,fin.date())
    except ValueError as error:
        return {"error":str(error)},403

    todos=[bloque for bloques in ocupados.values() for bloque in bloques]
    desde=max(inicio,proxima_media_hora(datetime.now()))
    huecos=buscar_huecos(todos,desde,fin,duracion)

    return {
        "yo":session["usuarioID"],
        "titulo":titulo_semana(lunes),
        "desde":a_texto(desde),
        "ocupados":{usuario_id:[[a_texto(inicio),a_texto(fin)] for inicio,fin in bloques] for usuario_id,bloques in ocupados.items()},
        "dias":[{
            "fecha":dia.isoformat(),
            "titulo":DIAS_SEMANA[dia.weekday()].capitalize(),
            "numero":dia.day,
            "nombre":nombre_del_dia(dia),
            "huecos":[{"inicio":a_texto(inicio),"fin":a_texto(fin)} for inicio,fin in huecos_del_dia(huecos,dia,duracion)],
        } for dia in dias],
    }

if __name__ == "__main__":
    app.run(debug=True, port=5001)
